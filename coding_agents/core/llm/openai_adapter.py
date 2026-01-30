"""OpenAI adapter (GPT-4o-mini default)."""

from __future__ import annotations

import os
from typing import Any, Optional

from pydantic import SecretStr

from coding_agents.core.llm.base import BaseLLM, LLMResult


class OpenAILLM(BaseLLM):
    """OpenAI Chat Completions; default model GPT-4o-mini."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
    ) -> None:
        api_key_str = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key_str:
            raise ValueError("OPENAI_API_KEY not set")

        self._api_key: str = api_key_str
        self._model: str = model
        self._temperature: float = temperature

    @property
    def model_name(self) -> str:
        return self._model

    def invoke(self, prompt: str, **kwargs: Any) -> LLMResult:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as e:
            raise ImportError("langchain-openai required for OpenAILLM") from e

        temperature = float(kwargs.get("temperature", self._temperature))

        llm = ChatOpenAI(
            model=self._model,
            temperature=temperature,
            api_key=SecretStr(self._api_key),
        )

        msg = llm.invoke(prompt)

        # LangChain message usually has `.content`, but be defensive
        content_obj = getattr(msg, "content", msg)
        content = content_obj if isinstance(content_obj, str) else str(content_obj)

        return LLMResult(content=content, raw=msg)
