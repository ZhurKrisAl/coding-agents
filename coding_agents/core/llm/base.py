"""Unified LLM interface for agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResult:
    """Result of LLM invocation."""

    content: str
    model: str
    usage: dict[str, int] | None = None


class BaseLLM(ABC):
    """Abstract LLM adapter."""

    @abstractmethod
    def invoke(self, prompt: str, **kwargs: object) -> LLMResult:
        """Invoke model with prompt; return structured result."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier for logging."""
        ...
