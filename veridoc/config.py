"""Central settings. Every value can be overridden with an environment variable."""

import os

LLM_MODEL = os.getenv("VERIDOC_LLM_MODEL", "llama-3.3-70b-versatile")
EMBED_MODEL = os.getenv("VERIDOC_EMBED_MODEL", "all-MiniLM-L6-v2")
NLI_MODEL = os.getenv("VERIDOC_NLI_MODEL", "cross-encoder/nli-deberta-v3-small")

# ~300-500 tokens per chunk, with overlap so facts on a boundary are not lost.
CHUNK_TOKENS = int(os.getenv("VERIDOC_CHUNK_TOKENS", "350"))
CHUNK_OVERLAP_TOKENS = int(os.getenv("VERIDOC_CHUNK_OVERLAP", "60"))

TOP_K = int(os.getenv("VERIDOC_TOP_K", "4"))
# If even the best chunk is less similar than this, the question is treated as
# off-topic and we abstain without spending an LLM call.
MIN_SIMILARITY = float(os.getenv("VERIDOC_MIN_SIMILARITY", "0.15"))
# Minimum entailment probability for the NLI verifier to call a claim supported.
NLI_THRESHOLD = float(os.getenv("VERIDOC_NLI_THRESHOLD", "0.5"))
