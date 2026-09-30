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
    """Groq chat-completions client with retry on rate limits / network errors.

    If the primary model's daily token cap is exhausted (HTTP 429, "tokens per day"), the call moves on
    to the next model in `fallback_models` instead of failing. `last_model` records which model answered.
    """

    def __init__(self, api_key: str | None = None, model: str = config.LLM_MODEL, retries: int = 4,
                 fallback_models: list[str] | None = None):
        api_key = api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise MissingAPIKey("GROQ_API_KEY is not set. Add it to .env or the Streamlit secrets.")
        from groq import Groq

        self._client = Groq(api_key=api_key)
        self.model = model
        self.retries = retries
        self.fallback_models = config.FALLBACK_MODELS if fallback_models is None else fallback_models
        self.last_model = model

    def _create(self, model: str, system: str, user: str, json_mode: bool, max_tokens: int) -> str:
        kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
        if model.startswith("openai/gpt-oss") and config.LLM_REASONING_EFFORT:
            kwargs["reasoning_effort"] = config.LLM_REASONING_EFFORT
        response = self._client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0,
            max_tokens=max_tokens,
            **kwargs,
        )
        return response.choices[0].message.content or ""

    def complete(self, system: str, user: str, *, json_mode: bool = False, max_tokens: int = 1024) -> str:
        import groq

        models = [self.model, *self.fallback_models]
        for index, model in enumerate(models):
            for attempt in range(self.retries + 1):
                try:
                    text = self._create(model, system, user, json_mode, max_tokens)
                    self.last_model = model
                    return text
                except groq.RateLimitError as exc:
                    daily_cap = "per day" in str(exc) or "TPD" in str(exc)
                    if daily_cap or attempt == self.retries:
                        if index == len(models) - 1:
                            raise
                        break  # try the next model
                    time.sleep(2**attempt)
                except groq.APIConnectionError:
                    if attempt == self.retries:
                        raise
                    time.sleep(2**attempt)
        raise AssertionError("unreachable")
