"""Context propagation using contextvars for asynchronous and multi-threaded agent execution."""

import contextlib
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass


def generate_trace_id() -> str:
    """Generate a unique trace ID (hex UUID)."""
    return uuid.uuid4().hex


def generate_span_id() -> str:
    """Generate a unique span ID (16-char hex)."""
    return uuid.uuid4().hex[:16]


@dataclass(frozen=True)
class TraceContext:
    """Immutable context carried across synchronous and asynchronous task boundaries."""

    trace_id: str
    session_id: str
    agent_id: str
    current_span_id: str | None = None
    parent_span_id: str | None = None

    def child_context(self, new_span_id: str) -> "TraceContext":
        """Create a child context where the current span becomes the parent."""
        return TraceContext(
            trace_id=self.trace_id,
            session_id=self.session_id,
            agent_id=self.agent_id,
            current_span_id=new_span_id,
            parent_span_id=self.current_span_id,
        )


_CURRENT_CONTEXT: ContextVar[TraceContext | None] = ContextVar("aog_trace_context", default=None)


def get_current_context() -> TraceContext | None:
    """Retrieve the currently active TraceContext in this execution scope."""
    return _CURRENT_CONTEXT.get()


def set_current_context(context: TraceContext | None) -> Token[TraceContext | None]:
    """Set the active TraceContext and return the token for restoration."""
    return _CURRENT_CONTEXT.set(context)


def reset_context(token: Token[TraceContext | None]) -> None:
    """Reset the context to the state saved in the token."""
    with contextlib.suppress(ValueError, LookupError):
        _CURRENT_CONTEXT.reset(token)



@contextmanager
def with_context(context: TraceContext | None) -> Generator[TraceContext | None, None, None]:
    """Context manager for temporarily activating a TraceContext."""
    token = set_current_context(context)
    try:
        yield context
    finally:
        reset_context(token)
