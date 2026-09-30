"""PDF parsing and chunking.

Chunks never cross a page boundary, so every chunk has an exact page number
that can be shown as a citation.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from . import config


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    page: int
    source: str
    index: int


def approx_tokens(text: str) -> int:
    """Cheap token estimate (English averages ~1.3 tokens per word)."""
    return int(len(text.split()) * 1.3) + 1


def _clean_block(text: str) -> str:
    text = re.sub(r"-\n(?=[a-z])", "", text)  # re-join words hyphenated across lines
    return re.sub(r"\s+", " ", text).strip()


def join_blocks(blocks: list[str]) -> str:
    """Join text blocks, starting a new paragraph only after a finished sentence or a heading.

    Some PDFs emit one block per visual line, so joining everything with blank lines would
    cut sentences in half.
    """
    out = ""
    for block in (b for b in blocks if b):
        if out:
            heading = len(out.split("\n")[-1].split()) < 8 and not re.search(r"[.!?:,;]$", out)
            out += "\n\n" + block if heading or re.search(r"[.!?]$", out) else " " + block
        else:
            out = block
    return out


def extract_pages(data: bytes) -> list[tuple[int, str]]:
    """Return [(page_number, text)] for every page that contains text."""
    import fitz  # PyMuPDF

    pages: list[tuple[int, str]] = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        for number, page in enumerate(doc, start=1):
            blocks = page.get_text("blocks", sort=True)
            text = join_blocks([_clean_block(b[4]) for b in blocks if b[6] == 0])  # b[6]==0: text
            if text:
                pages.append((number, text))
    return pages


_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")


def split_sentences(text: str) -> list[str]:
    sentences: list[str] = []
    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = paragraph.strip()
        if paragraph:
            sentences.extend(s.strip() for s in _SENTENCE_END.split(paragraph) if s.strip())
    merged: list[str] = []
    for sentence in sentences:  # re-attach list/heading numbers such as "1." to what follows
        if merged and re.fullmatch(r"\d+\.", merged[-1]):
            merged[-1] = f"{merged[-1]} {sentence}"
        else:
            merged.append(sentence)
    return merged


def _hard_split(sentence: str, max_tokens: int) -> list[str]:
    """Break a single over-long 'sentence' (tables, lists) on word boundaries."""
    words = sentence.split()
    step = max(1, int(max_tokens / 1.3))
    return [" ".join(words[i : i + step]) for i in range(0, len(words), step)]


def chunk_text(
    text: str,
    max_tokens: int = config.CHUNK_TOKENS,
    overlap_tokens: int = config.CHUNK_OVERLAP_TOKENS,
) -> list[str]:
    units: list[str] = []
    for sentence in split_sentences(text):
        if approx_tokens(sentence) > max_tokens:
            units.extend(_hard_split(sentence, max_tokens))
        else:
            units.append(sentence)

    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0
    for unit in units:
        tokens = approx_tokens(unit)
        if current and current_tokens + tokens > max_tokens:
            chunks.append(" ".join(current))
            kept: list[str] = []
            kept_tokens = 0
            for previous in reversed(current):  # carry trailing sentences as overlap
                previous_tokens = approx_tokens(previous)
                if kept_tokens + previous_tokens > overlap_tokens:
                    break
                kept.insert(0, previous)
                kept_tokens += previous_tokens
            current, current_tokens = kept, kept_tokens
        current.append(unit)
        current_tokens += tokens
    if current:
        chunks.append(" ".join(current))
    return chunks


def chunk_pages(
    pages: list[tuple[int, str]],
    source: str,
    max_tokens: int = config.CHUNK_TOKENS,
    overlap_tokens: int = config.CHUNK_OVERLAP_TOKENS,
) -> list[Chunk]:
    doc_id = hashlib.sha1(source.encode() + repr(pages).encode()).hexdigest()[:8]
    chunks: list[Chunk] = []
    for page, text in pages:
        for piece in chunk_text(text, max_tokens, overlap_tokens):
            index = len(chunks)
            chunks.append(Chunk(f"{doc_id}:{index}", piece, page, source, index))
    return chunks
