"""Tracer core coordinating context, span lifecycle, and event emission."""

from collections.abc import Sequence
from contextvars import Token
from datetime import UTC, datetime
from typing import Any

from aog.context import (
    TraceContext,
    generate_span_id,
    generate_trace_id,
    get_current_context,
    reset_context,
    set_current_context,
)
from aog.events.enums import EventStatus, EventType
from aog.events.models import AgentEvent, ErrorInfo
from aog.exporters.base import Exporter
from aog.redaction.sanitizer import Sanitizer
from aog.tracing.span import Span


class Tracer:
    """Manages creation, execution, and dispatch of spans and trace events."""

    def __init__(
        self,
        exporter: Exporter,
        sanitizer: Sanitizer | None = None,
        default_agent_id: str = "default-agent",
        fail_open: bool = True,
    ) -> None:
        self.exporter = exporter
        self.sanitizer = sanitizer or Sanitizer()
        self.default_agent_id = default_agent_id
        self.fail_open = fail_open

    def start_span(
        self,
        name: str,
        event_type: EventType = EventType.TOOL,
        parent_context: TraceContext | None = None,
        attributes: dict[str, Any] | None = None,
        input_data: Any = None,
    ) -> tuple[Span, Token[TraceContext | None]]:
        """Start a new span, bind it to contextvars, and return the span and context token."""
        ctx = parent_context or get_current_context()
        span_id = generate_span_id()

        if ctx is None:
            trace_id = generate_trace_id()
            session_id = trace_id
            agent_id = self.default_agent_id
            parent_span_id = None
            new_ctx = TraceContext(
                trace_id=trace_id,
                session_id=session_id,
                agent_id=agent_id,
                current_span_id=span_id,
                parent_span_id=None,
            )
        else:
            trace_id = ctx.trace_id
            session_id = ctx.session_id
            agent_id = ctx.agent_id
            parent_span_id = ctx.current_span_id
            new_ctx = ctx.child_context(span_id)

        token = set_current_context(new_ctx)

        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            session_id=session_id,
            agent_id=agent_id,
            name=name,
            event_type=event_type,
            parent_span_id=parent_span_id,
            attributes=attributes,
            sanitizer=self.sanitizer,
        )
        if input_data is not None:
            span.set_input(input_data)

        return span, token

    def end_span(
        self,
        span: Span,
        token: Token[TraceContext | None],
        status: EventStatus | None = None,
    ) -> AgentEvent:
        """Finish a span, restore prior context, and emit event to exporter."""
        try:
            event = span.finish(status=status)
            self._emit([event])
            return event
        finally:
            reset_context(token)

    def record_event(
        self,
        name: str,
        event_type: EventType = EventType.TOOL,
        status: EventStatus = EventStatus.OK,
        input_data: Any = None,
        output_data: Any = None,
        attributes: dict[str, Any] | None = None,
        duration_ms: float | None = None,
        tokens_in: int | None = None,
        tokens_out: int | None = None,
        model: str | None = None,
        provider: str | None = None,
        cost_usd: float | None = None,
        error: ErrorInfo | None = None,
        event_id: str | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        parent_span_id: str | None = None,
        session_id: str | None = None,
        agent_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> AgentEvent:
        """Record and emit a standalone event within current active context."""
        ctx = get_current_context()
        actual_span_id = span_id or generate_span_id()
        actual_event_id = event_id or actual_span_id
        actual_trace_id = trace_id or (ctx.trace_id if ctx else generate_trace_id())
        actual_session_id = session_id or (ctx.session_id if ctx else actual_trace_id)
        actual_agent_id = agent_id or (ctx.agent_id if ctx else self.default_agent_id)
        actual_parent_span_id = (
            parent_span_id
            if parent_span_id is not None
            else (ctx.current_span_id if ctx else None)
        )
        actual_timestamp = timestamp or datetime.now(UTC)

        sanitized_input = self.sanitizer.sanitize(input_data) if input_data is not None else None
        if sanitized_input is not None and not isinstance(sanitized_input, dict):
            sanitized_input = {"data": sanitized_input}

        sanitized_output = self.sanitizer.sanitize(output_data) if output_data is not None else None
        if sanitized_output is not None and not isinstance(sanitized_output, dict):
            sanitized_output = {"data": sanitized_output}

        event = AgentEvent(
            event_id=actual_event_id,
            trace_id=actual_trace_id,
            span_id=actual_span_id,
            parent_span_id=actual_parent_span_id,
            session_id=actual_session_id,
            agent_id=actual_agent_id,
            event_type=event_type,
            name=name,
            timestamp=actual_timestamp,
            status=status,
            input=sanitized_input,
            output=sanitized_output,
            attributes=self.sanitizer.sanitize(attributes or {}),
            duration_ms=duration_ms,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            model=model,
            provider=provider,
            cost_usd=cost_usd,
            error=error,
        )
        self._emit([event])
        return event

    def _emit(self, events: Sequence[AgentEvent]) -> None:
        try:
            self.exporter.export(events)
        except Exception:
            if not self.fail_open:
                raise
