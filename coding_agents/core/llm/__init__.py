"""LLM adapters: OpenAI (default), YandexGPT; unified interface."""

from coding_agents.core.llm.base import BaseLLM, LLMResult
from coding_agents.core.llm.openai_adapter import OpenAILLM
from coding_agents.core.llm.registry import get_llm

__all__ = ["BaseLLM", "LLMResult", "OpenAILLM", "get_llm"]
