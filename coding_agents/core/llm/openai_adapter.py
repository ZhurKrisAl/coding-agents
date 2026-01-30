"""OpenAI adapter (GPT-4o-mini default)."""

from __future__ import annotations

import os
from typing import Any

from coding_agents.core.llm.base import BaseLLM, LLMResult


class OpenAILLM(BaseLLM):
    """OpenAI Chat Completions; default model GPT-4o-mini."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
    ) -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError("OPENAI_API_KEY not set")
        self._model = model
        self._temperature = temperature

    @property
    def model_name(self) -> str:
        return self._model

    def invoke(self, prompt: str, **kwargs: Any) -> LLMResult:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError("langchain-openai required for OpenAILLM")
        llm = ChatOpenAI(
            model=self._model,
            temperature=kwargs.get("temperature", self._temperature),
            api_key=self._api_key,
        )
        msg = llm.invoke(prompt)
        content = msg.content if hasattr(msg, "content") else str(msg)
        usage = getattr(msg, "response_metadata", {}).get("usage", {}) or {}
        return LLMResult(
            content=content,
            model=self._model,
            usage={
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
            },
        )
