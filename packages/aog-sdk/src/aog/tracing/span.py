"""Span domain object representing an individual execution unit in AOG."""

import traceback
from datetime import UTC, datetime
from typing import Any

from aog.events.enums import EventStatus, EventType
from aog.events.models import AgentEvent, ErrorInfo
from aog.redaction.sanitizer import Sanitizer


class Span:
    """Represents an active or completed trace span."""

    def __init__(
        self,
        span_id: str,
        trace_id: str,
        session_id: str,
        agent_id: str,
        name: str,
        event_type: EventType = EventType.TOOL,
        parent_span_id: str | None = None,
        attributes: dict[str, Any] | None = None,
        sanitizer: Sanitizer | None = None,
    ) -> None:
        self.span_id = span_id
        self.trace_id = trace_id
        self.session_id = session_id
        self.agent_id = agent_id
        self.name = name
        self.event_type = event_type
        self.parent_span_id = parent_span_id
        self.attributes: dict[str, Any] = dict(attributes or {})
        self.sanitizer = sanitizer or Sanitizer()

        self.start_time: datetime = datetime.now(UTC)
        self.end_time: datetime | None = None
        self.status: EventStatus = EventStatus.OK

        self.input: dict[str, Any] | None = None
        self.output: dict[str, Any] | None = None
        self.tokens_in: int | None = None
        self.tokens_out: int | None = None
        self.model: str | None = None
        self.provider: str | None = None
        self.cost_usd: float | None = None
        self.error: ErrorInfo | None = None
        self._finished = False

    def set_attribute(self, key: str, value: Any) -> "Span":
        """Attach metadata attribute to the span."""
        self.attributes[key] = self.sanitizer.sanitize(value)
        return self

    def set_attributes(self, attrs: dict[str, Any]) -> "Span":
        """Attach multiple metadata attributes."""
        for k, v in attrs.items():
            self.set_attribute(k, v)
        return self

    def set_input(self, data: Any) -> "Span":
        """Record the input arguments or payload for this span."""
        if not self.sanitizer.config.capture_input:
            return self
        if isinstance(data, dict):
            self.input = self.sanitizer.sanitize(data)
        elif data is not None:
            self.input = {"data": self.sanitizer.sanitize(data)}
        return self

    def set_output(self, data: Any) -> "Span":
        """Record the output or return value for this span."""
        if not self.sanitizer.config.capture_output:
            return self
        if isinstance(data, dict):
            self.output = self.sanitizer.sanitize(data)
        elif data is not None:
            self.output = {"data": self.sanitizer.sanitize(data)}
        return self

    def set_tokens(self, tokens_in: int | None = None, tokens_out: int | None = None) -> "Span":
        """Record token consumption metadata."""
        if tokens_in is not None:
            self.tokens_in = tokens_in
        if tokens_out is not None:
            self.tokens_out = tokens_out
        return self

    def set_model(self, model: str, provider: str | None = None) -> "Span":
        """Set model name and provider."""
        self.model = model
        if provider:
            self.provider = provider
        return self

    def set_cost(self, cost_usd: float | None) -> "Span":
        """Set calculated cost in USD."""
        self.cost_usd = cost_usd
        return self

    def record_error(
        self,
        exc: BaseException | str,
        retryable: bool | None = None,
    ) -> "Span":
        """Mark span as failed and capture structured error info."""
        self.status = EventStatus.ERROR
        if isinstance(exc, BaseException):
            err_type = type(exc).__name__
            err_msg = str(exc) or err_type
            tb_str = "".join(traceback.format_tb(exc.__traceback__)) if exc.__traceback__ else None
        else:
            err_type = "Error"
            err_msg = str(exc)
            tb_str = None

        if self.sanitizer.config.redact_stacktraces:
            tb_str = None

        self.error = ErrorInfo(
            type=err_type,
            message=err_msg,
            stacktrace=tb_str,
            retryable=retryable,
        )
        return self

    def finish(self, status: EventStatus | None = None) -> AgentEvent:
        """Complete the span, compute duration, and construct the AgentEvent."""
        if not self._finished:
            self.end_time = datetime.now(UTC)
            self._finished = True
            if status is not None:
                self.status = status

        assert self.end_time is not None
        duration_ms = (self.end_time - self.start_time).total_seconds() * 1000.0

        return AgentEvent(
            event_id=self.span_id,
            trace_id=self.trace_id,
            span_id=self.span_id,
            parent_span_id=self.parent_span_id,
            session_id=self.session_id,
            agent_id=self.agent_id,
            event_type=self.event_type,
            name=self.name,
            timestamp=self.start_time,
            status=self.status,
            input=self.input,
            output=self.output,
            attributes=self.attributes,
            duration_ms=duration_ms,
            tokens_in=self.tokens_in,
            tokens_out=self.tokens_out,
            model=self.model,
            provider=self.provider,
            cost_usd=self.cost_usd,
            error=self.error,
        )
