"""Central settings. Every value can be overridden with an environment variable."""

import os

# llama-3.3-70b-versatile was retired from Groq (model_not_found, Sept 2026); gpt-oss-120b replaces it.
LLM_MODEL = os.getenv("VERIDOC_LLM_MODEL", "openai/gpt-oss-120b")
# gpt-oss models spend hidden "reasoning" tokens; keep them low for latency and token budget.
# Tried in order when the primary model hits its daily token cap (free tier: 200k tokens/day/model).
FALLBACK_MODELS = [m.strip() for m in os.getenv("VERIDOC_FALLBACK_MODELS", "openai/gpt-oss-20b,qwen/qwen3.8-27b").split(",") if m.strip()]
LLM_REASONING_EFFORT = os.getenv("VERIDOC_REASONING_EFFORT", "low")
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
