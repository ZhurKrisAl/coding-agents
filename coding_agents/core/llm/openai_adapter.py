"""OpenAI adapter (GPT-4o-mini default)."""

from __future__ import annotations

import os
from typing import Any

from pydantic import SecretStr

from coding_agents.core.llm.base import BaseLLM, LLMResult


class OpenAILLM(BaseLLM):
    """OpenAI Chat Completions; default model gpt-4o-mini."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
    ) -> None:
        api_key_str = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key_str:
            raise ValueError("OPENAI_API_KEY not set")

        self._api_key = SecretStr(api_key_str)
        self._model = model
        self._temperature = temperature

    @property
    def model_name(self) -> str:
        return self._model

    def invoke(self, prompt: str, **kwargs: Any) -> LLMResult:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as err:
            raise ImportError("langchain-openai required for OpenAILLM") from err

        llm = ChatOpenAI(
            model=self._model,
            temperature=float(kwargs.get("temperature", self._temperature)),
            api_key=self._api_key,
        )

        response = llm.invoke(prompt)

        content = getattr(response, "content", None)
        if not isinstance(content, str):
            content = str(content)

        usage: dict[str, Any] = {}
        meta = getattr(response, "response_metadata", None)
        if isinstance(meta, dict):
            u = meta.get("usage")
            if isinstance(u, dict):
                usage = u

        return LLMResult(
            content=content,
            model=self._model,
            raw=response,
            usage=usage,
        )
