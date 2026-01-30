"""YandexGPT adapter (optional)."""

from __future__ import annotations

import os
from typing import Any

from coding_agents.core.llm.base import BaseLLM, LLMResult


class YandexLLM(BaseLLM):
    """YandexGPT via Yandex Cloud API; requires YANDEX_API_KEY and YANDEX_FOLDER_ID."""

    def __init__(
        self,
        api_key: str | None = None,
        folder_id: str | None = None,
        model: str = "yandexgpt/latest",
        temperature: float = 0.2,
    ) -> None:
        self._api_key = api_key or os.environ.get("YANDEX_API_KEY")
        self._folder_id = folder_id or os.environ.get("YANDEX_FOLDER_ID")
        if not self._api_key or not self._folder_id:
            raise ValueError("YANDEX_API_KEY and YANDEX_FOLDER_ID required")
        self._model = model
        self._temperature = temperature

    @property
    def model_name(self) -> str:
        return self._model

    def invoke(self, prompt: str, **kwargs: Any) -> LLMResult:
        import httpx
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {"Authorization": f"Api-Key {self._api_key}"}
        payload = {
            "modelUri": model_uri,
            "completionOptions": {
                "temperature": self._temperature,
                "maxTokens": str(int(os.getenv("YANDEX_MAX_TOKENS", "1024"))),
                "stream": False,
            },
            "messages": [{"role": "user", "text": prompt}],
        }
        with httpx.Client() as client:
            r = client.post(url, json=payload, headers=headers, timeout=60)
            r.raise_for_status()
            data = r.json()
        text = ""
        for chunk in data.get("result", {}).get("alternatives", []):
            text += chunk.get("message", {}).get("text", "")
        return LLMResult(content=text, model=self._model, usage=None)
