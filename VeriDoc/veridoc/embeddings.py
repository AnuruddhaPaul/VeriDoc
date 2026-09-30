"""Embedding backends. Both return L2-normalised vectors (cosine == dot product)."""

from __future__ import annotations

import re
import zlib
from typing import Protocol

import numpy as np

from . import config


class Embedder(Protocol):
    def encode(self, texts: list[str]) -> np.ndarray: ...


class SentenceTransformerEmbedder:
    """Local sentence-transformers model (default: all-MiniLM-L6-v2)."""

    def __init__(self, model_name: str = config.EMBED_MODEL):
        self.model_name = model_name
        self._model = None

    def encode(self, texts: list[str]) -> np.ndarray:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return np.asarray(
            self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        )


_STOPWORDS = frozenset(
    "a an and are as at be by for from has have how in is it its of on or that the "
    "this to was were what when where which who why will with does do did can".split()
)


class HashingEmbedder:
    """Deterministic bag-of-words embedder with no model download.

    Used by the unit tests and as an offline fallback. It matches on shared
    vocabulary only, so retrieval quality is far below a real model.
    """

    def __init__(self, dim: int = 512):
        self.dim = dim

    def encode(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            for word in re.findall(r"[a-z0-9]+", text.lower()):
                if word in _STOPWORDS:
                    continue
                word = word[:-1] if len(word) > 3 and word.endswith("s") else word
                h = zlib.crc32(word.encode())
                out[row, h % self.dim] += 1.0 if (h >> 16) & 1 else -1.0
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        return out / np.where(norms == 0, 1.0, norms)
