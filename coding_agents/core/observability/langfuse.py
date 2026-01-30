"""Langfuse client: auto-init from env; graceful degradation if not configured."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Generator

_LANGFUSE_CLIENT: Any = None


def _env_configured() -> bool:
    return bool(
        os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY")
    )


def get_langfuse_client() -> Any | None:
    """Return Langfuse client if env vars set; else None (graceful degradation)."""
    global _LANGFUSE_CLIENT
    if not _env_configured():
        return None
    if _LANGFUSE_CLIENT is None:
        try:
            from langfuse import Langfuse
            _LANGFUSE_CLIENT = Langfuse(
                public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.environ.get("LANGFUSE_SECRET_KEY"),
                host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            )
        except Exception:
            _LANGFUSE_CLIENT = False  # type: ignore[assignment]
    return _LANGFUSE_CLIENT if _LANGFUSE_CLIENT is not None and _LANGFUSE_CLIENT else None


@contextmanager
def trace_agent(
    name: str,
    metadata: dict[str, Any] | None = None,
) -> Generator[Any, None, None]:
    """Context manager: create a trace for agent run; no-op if Langfuse disabled."""
    client = get_langfuse_client()
    if not client:
        yield None
        return
    try:
        trace = client.trace(name=name, metadata=metadata or {})
        yield trace
    except Exception:
        yield None
    finally:
        try:
            client.flush()
        except Exception:
            pass


def span(name: str, trace: Any | None, metadata: dict[str, Any] | None = None) -> Any:
    """Create span under trace; return no-op context if trace is None."""
    if trace is None:
        from contextlib import nullcontext
        return nullcontext(None)
    return trace.span(name=name, metadata=metadata or {})
