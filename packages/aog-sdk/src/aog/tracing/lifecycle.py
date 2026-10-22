"""Context managers for managing Span and Session lifecycles."""

import asyncio
import functools
from collections.abc import Callable
from contextvars import Token
from types import TracebackType
from typing import Any, TypeVar, cast

from aog.context import (
    TraceContext,
    generate_trace_id,
    reset_context,
    set_current_context,
)
from aog.events.enums import EventStatus, EventType
from aog.tracing.span import Span
from aog.tracing.tracer import Tracer

F = TypeVar("F", bound=Callable[..., Any])


class SpanContextManager:
    """Synchronous and asynchronous context manager and decorator for span lifecycle."""

    def __init__(
        self,
        tracer: Tracer,
        name: str,
        event_type: EventType = EventType.TOOL,
        attributes: dict[str, Any] | None = None,
        input_data: Any = None,
        parent_context: TraceContext | None = None,
    ) -> None:
        self.tracer = tracer
        self.name = name
        self.event_type = event_type
        self.attributes = attributes
        self.input_data = input_data
        self.parent_context = parent_context
        self.span: Span | None = None
        self._token: Token[TraceContext | None] | None = None

    def __enter__(self) -> Span:
        self.span, self._token = self.tracer.start_span(
            name=self.name,
            event_type=self.event_type,
            parent_context=self.parent_context,
            attributes=self.attributes,
            input_data=self.input_data,
        )
        return self.span

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        if self.span is None or self._token is None:
            return None

        if exc_val is not None:
            self.span.record_error(exc_val)
        elif self.span.status == EventStatus.OK:
            pass

        self.tracer.end_span(self.span, self._token)
        return None

    async def __aenter__(self) -> Span:
        return self.__enter__()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return self.__exit__(exc_type, exc_val, exc_tb)

    def __call__(self, func: F) -> F:
        """Allow SpanContextManager to also be used as a function decorator."""
        span_name = self.name or func.__name__

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                mgr = SpanContextManager(
                    tracer=self.tracer,
                    name=span_name,
                    event_type=self.event_type,
                    attributes=self.attributes,
                    input_data={"args": args, "kwargs": kwargs},
                )
                async with mgr as s:
                    res = await func(*args, **kwargs)
                    s.set_output(res)
                    return res

            return cast(F, async_wrapper)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            mgr = SpanContextManager(
                tracer=self.tracer,
                name=span_name,
                event_type=self.event_type,
                attributes=self.attributes,
                input_data={"args": args, "kwargs": kwargs},
            )
            with mgr as s:
                res = func(*args, **kwargs)
                s.set_output(res)
                return res

        return cast(F, sync_wrapper)


class SessionContextManager:
    """Context manager for top-level agent execution sessions."""

    def __init__(
        self,
        tracer: Tracer,
        session_id: str | None = None,
        agent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.tracer = tracer
        self.session_id = session_id or generate_trace_id()
        self.agent_id = agent_id or tracer.default_agent_id
        self.metadata = metadata or {}
        self.root_span: Span | None = None
        self._span_token: Token[TraceContext | None] | None = None
        self._session_token: Token[TraceContext | None] | None = None

    def __enter__(self) -> "SessionContextManager":
        ctx = TraceContext(
            trace_id=self.session_id,
            session_id=self.session_id,
            agent_id=self.agent_id,
            current_span_id=None,
            parent_span_id=None,
        )
        self._session_token = set_current_context(ctx)

        self.root_span, self._span_token = self.tracer.start_span(
            name=f"session:{self.agent_id}",
            event_type=EventType.SESSION,
            parent_context=ctx,
            attributes=self.metadata,
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        try:
            if self.root_span is not None and self._span_token is not None:
                if exc_val is not None:
                    self.root_span.record_error(exc_val)
                self.tracer.end_span(self.root_span, self._span_token)
        finally:
            if self._session_token is not None:
                reset_context(self._session_token)
        return None

    async def __aenter__(self) -> "SessionContextManager":
        return self.__enter__()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return self.__exit__(exc_type, exc_val, exc_tb)

    def agent(self, name: str, attributes: dict[str, Any] | None = None) -> SpanContextManager:
        """Create a child agent span in this session."""
        return SpanContextManager(
            tracer=self.tracer,
            name=name,
            event_type=EventType.AGENT,
            attributes=attributes,
        )
