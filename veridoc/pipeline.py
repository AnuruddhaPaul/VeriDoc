"""End-to-end VeriDoc pipeline: ingest -> retrieve -> generate -> verify -> decide."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from . import config
from .embeddings import Embedder, SentenceTransformerEmbedder
from .grounding import GroundingReport, VerificationError, Verifier
from .ingest import Chunk, chunk_pages, extract_pages
from .llm import LLM
from .rag import GENERATION_SYSTEM, generate_answer, is_not_found
from .store import Retrieved, VectorStore

GROUNDED = "grounded"  # every claim backed by a source
PARTIAL = "partial"  # some claims backed, some not
UNGROUNDED = "ungrounded"  # answer drafted but nothing in it could be verified
NOT_FOUND = "not_found"  # document does not contain the answer
UNVERIFIED = "unverified"  # verifier failed; answer shown with a warning
UNCHECKED = "unchecked"  # verification switched off (baseline mode)

NOT_FOUND_MESSAGE = "Not found in the document."
UNGROUNDED_MESSAGE = (
    "I could not verify an answer against the document, so I am not showing one. "
    "The unverified draft is available below."
)


@dataclass
class Result:
    question: str
    status: str
    answer: str  # what the UI should show
    draft: str = ""  # raw model output before the grounding decision
    report: GroundingReport | None = None
    sources: list[Retrieved] = field(default_factory=list)
    timings: dict[str, float] = field(default_factory=dict)
    model: str = ""  # which LLM produced the answer (differs from the default only after a rate-limit fallback)

    @property
    def abstained(self) -> bool:
        return self.status in (NOT_FOUND, UNGROUNDED)


class VeriDoc:
    def __init__(
        self,
        llm: LLM,
        verifier: Verifier | None,
        embedder: Embedder | None = None,
        top_k: int = config.TOP_K,
        min_similarity: float = config.MIN_SIMILARITY,
        persist_dir: str | None = None,
        generation_system: str = GENERATION_SYSTEM,
    ):
        self.llm = llm
        self.verifier = verifier
        self.generation_system = generation_system
        self.top_k = top_k
        self.min_similarity = min_similarity
        self.store = VectorStore(embedder or SentenceTransformerEmbedder(), persist_dir)
        self.documents: dict[str, int] = {}  # name -> chunk count

    def ingest_pdf(self, data: bytes, name: str) -> int:
        return self.ingest_pages(extract_pages(data), name)

    def ingest_pages(self, pages: list[tuple[int, str]], name: str) -> int:
        chunks: list[Chunk] = chunk_pages(pages, name)
        self.store.add(chunks)
        self.documents[name] = self.documents.get(name, 0) + len(chunks)
        return len(chunks)

    def ask(self, question: str) -> Result:
        result = self._ask(question)
        result.model = getattr(self.llm, "last_model", "")
        return result

    def _ask(self, question: str) -> Result:
        timings: dict[str, float] = {}
        t0 = time.perf_counter()
        retrieved = self.store.query(question, self.top_k)
        timings["retrieve"] = time.perf_counter() - t0

        if not retrieved or retrieved[0].score < self.min_similarity:
            return Result(question, NOT_FOUND, NOT_FOUND_MESSAGE, sources=retrieved, timings=timings)

        t0 = time.perf_counter()
        draft = generate_answer(self.llm, question, retrieved, self.generation_system)
        timings["generate"] = time.perf_counter() - t0
        if is_not_found(draft):
            return Result(question, NOT_FOUND, NOT_FOUND_MESSAGE, draft, sources=retrieved, timings=timings)

        if self.verifier is None:
            return Result(question, UNCHECKED, draft, draft, sources=retrieved, timings=timings)

        t0 = time.perf_counter()
        try:
            report = self.verifier.verify(draft, retrieved)
        except VerificationError:
            timings["verify"] = time.perf_counter() - t0
            return Result(question, UNVERIFIED, draft, draft, sources=retrieved, timings=timings)
        timings["verify"] = time.perf_counter() - t0

        if report.supported_count == len(report.verdicts):
            status, shown = GROUNDED, draft
        elif report.supported_count == 0:
            status, shown = UNGROUNDED, UNGROUNDED_MESSAGE
        else:
            status, shown = PARTIAL, draft
        return Result(question, status, shown, draft, report, retrieved, timings)
