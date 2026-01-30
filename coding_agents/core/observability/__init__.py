"""Observability: Langfuse traces, spans, prompt versions; graceful degradation."""

from coding_agents.core.observability.langfuse import get_langfuse_client, trace_agent

__all__ = ["get_langfuse_client", "trace_agent"]
