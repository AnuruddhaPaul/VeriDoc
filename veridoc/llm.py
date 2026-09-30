"""LLM access. Anything with a `complete()` method works, so the backend is swappable."""

from __future__ import annotations

import os
import time
from typing import Protocol

from . import config


class LLM(Protocol):
    def complete(self, system: str, user: str, *, json_mode: bool = False, max_tokens: int = 1024) -> str: ...


class MissingAPIKey(RuntimeError):
    pass


class GroqLLM:
    """Groq chat-completions client with retry on rate limits / network errors."""

    def __init__(self, api_key: str | None = None, model: str = config.LLM_MODEL, retries: int = 4):
        api_key = api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise MissingAPIKey("GROQ_API_KEY is not set. Add it to .env or the Streamlit secrets.")
        from groq import Groq

        self._client = Groq(api_key=api_key)
        self.model = model
        self.retries = retries

    def complete(self, system: str, user: str, *, json_mode: bool = False, max_tokens: int = 1024) -> str:
        import groq

        kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
        if self.model.startswith("openai/gpt-oss") and config.LLM_REASONING_EFFORT:
            kwargs["reasoning_effort"] = config.LLM_REASONING_EFFORT
        for attempt in range(self.retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                    temperature=0,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                return response.choices[0].message.content or ""
            except (groq.RateLimitError, groq.APIConnectionError):
                if attempt == self.retries:
                    raise
                time.sleep(2**attempt)
        raise AssertionError("unreachable")
