"""ChromaDB vector store (cosine similarity, embeddings computed by us)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import chromadb

from .embeddings import Embedder
from .ingest import Chunk


@dataclass(frozen=True)
class Retrieved:
    chunk: Chunk
    score: float  # cosine similarity, higher is better


class VectorStore:
    def __init__(self, embedder: Embedder, persist_dir: str | None = None):
        self.embedder = embedder
        client = chromadb.PersistentClient(persist_dir) if persist_dir else chromadb.EphemeralClient()
        self._collection = client.create_collection(
            f"veridoc_{uuid.uuid4().hex[:12]}", metadata={"hnsw:space": "cosine"}
        )

    def __len__(self) -> int:
        return self._collection.count()

    def add(self, chunks: list[Chunk], batch_size: int = 64) -> None:
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            self._collection.add(
                ids=[c.id for c in batch],
                documents=[c.text for c in batch],
                embeddings=self.embedder.encode([c.text for c in batch]).tolist(),
                metadatas=[{"page": c.page, "source": c.source, "index": c.index} for c in batch],
            )

    def query(self, question: str, k: int) -> list[Retrieved]:
        if len(self) == 0:
            return []
        res = self._collection.query(
            query_embeddings=self.embedder.encode([question]).tolist(),
            n_results=min(k, len(self)),
        )
        out = []
        for cid, text, meta, dist in zip(
            res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]
        ):
            chunk = Chunk(cid, text, int(meta["page"]), str(meta["source"]), int(meta["index"]))
            out.append(Retrieved(chunk, 1.0 - float(dist)))
        return out
