"""LLM registry: openai (default) or yandex."""

from __future__ import annotations

import os

from coding_agents.core.llm.base import BaseLLM
from coding_agents.core.llm.openai_adapter import OpenAILLM
from coding_agents.core.llm.yandex_adapter import YandexLLM


def get_llm(
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.2,
) -> BaseLLM:
    """Return LLM by provider: openai (default) or yandex."""
    provider = (provider or os.environ.get("CODING_AGENTS_LLM_PROVIDER", "openai")).lower()
    if provider == "yandex":
        return YandexLLM(temperature=temperature)
    return OpenAILLM(
        model=model or "gpt-4o-mini",
        temperature=temperature,
    )
