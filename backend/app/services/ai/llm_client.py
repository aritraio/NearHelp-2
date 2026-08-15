"""LLM client abstraction — env-swappable provider (ADR-14).

A rate limit or outage on the vendor must never end a viva: swapping the
provider is a config change, and with no provider configured the pipeline
degrades to heuristic classification + retrieval-only guidance rather than
failing (improvements.md §1.2).
"""

import json
import logging
from typing import Any, Protocol

from app.core.config import get_settings

logger = logging.getLogger("nearhelp.ai.llm")


class LLMClient(Protocol):
    name: str

    async def generate_json(self, system: str, user: str, schema: dict) -> dict[str, Any] | None:
        """Returns parsed JSON conforming to the schema, or None on failure."""
        ...


class DisabledLLM:
    """No provider configured — every call returns None (fallback ladder)."""

    name = "disabled"

    async def generate_json(self, system: str, user: str, schema: dict[str, Any]) -> None:
        return None


class GeminiLLM:
    """Google Gemini via google-genai, structured output, one retry."""

    name = "gemini"
    _retries = 1

    def __init__(self, api_key: str, model: str) -> None:
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def generate_json(self, system: str, user: str, schema: dict[str, Any]) -> dict | None:
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_schema=schema,
        )
        for attempt in range(self._retries + 1):
            try:
                response = await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=user,
                    config=config,
                )
                if response.text is None:
                    continue
                return json.loads(response.text)
            except Exception:
                logger.warning("gemini call failed (attempt %s/%s)", attempt + 1, self._retries + 1)
        return None


_llm: LLMClient | None = None


def get_llm() -> LLMClient:
    global _llm
    if _llm is not None:
        return _llm

    settings = get_settings()
    provider = settings.llm_provider
    if provider == "none":
        _llm = DisabledLLM()
    elif provider == "gemini" or (provider == "auto" and settings.gemini_api_key):
        _llm = GeminiLLM(settings.gemini_api_key, settings.gemini_model)
    else:
        _llm = DisabledLLM()
    return _llm
