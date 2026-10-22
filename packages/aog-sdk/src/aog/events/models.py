"""
Event models for AOG.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_snake

from aog.events.enums import EventStatus, EventType


class ErrorInfo(BaseModel):
    """Error information captured with an event."""

    model_config = ConfigDict(frozen=True)

    type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    stacktrace: str | None = Field(None, description="Stack trace (may be redacted)")
    retryable: bool | None = Field(None, description="Whether error is retryable")


class AgentEvent(BaseModel):
    """Universal event schema for AOG."""

    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        use_enum_values=True,
        alias_generator=to_snake,
        strict=False,
        validate_assignment=True,
    )

    # Schema version
    schema_version: str = Field("1.0", description="Schema version for backwards compatibility")

    # Event identifiers
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    trace_id: str = Field(..., description="Trace identifier")
    span_id: str = Field(..., description="Span identifier")
    parent_span_id: str | None = Field(None, description="Parent span identifier for hierarchy")

    # Session information
    session_id: str = Field(..., description="Session identifier")
    agent_id: str = Field(..., description="Agent identifier")

    # Event content
    event_type: EventType = Field(..., description="Type of event")
    name: str = Field(..., description="Descriptive name of event")

    # Timeline
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: EventStatus = Field(EventStatus.OK, description="Status of the event")

    # Payload data
    input: dict[str, Any] | None = Field(None, description="Input data (may be redacted)")
    output: dict[str, Any] | None = Field(None, description="Output data (may be redacted)")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Generic attributes")

    # Duration and timing
    duration_ms: float | None = Field(None, description="Duration in milliseconds")

    # Token tracking
    tokens_in: int | None = Field(None, description="Number of input tokens")
    tokens_out: int | None = Field(None, description="Number of output tokens")

    # Model information
    model: str | None = Field(None, description="Model name")
    provider: str | None = Field(None, description="Model provider")

    # Cost tracking
    cost_usd: float | None = Field(None, description="Cost in USD")

    # Error information
    error: ErrorInfo | None = Field(None, description="Error details")

    def __hash__(self) -> int:
        """Hash based on event_id for deduplication."""
        return hash(self.event_id)

    def __eq__(self, other: Any) -> bool:
        """Equality based on event_id."""
        if not isinstance(other, AgentEvent):
            return False
        return self.event_id == other.event_id

    @property
    def is_success(self) -> bool:
        """Check if event indicates success."""
        return self.status == EventStatus.OK

    @property
    def is_error(self) -> bool:
        """Check if event indicates error."""
        return self.status == EventStatus.ERROR

    @property
    def is_cancelled(self) -> bool:
        """Check if event was cancelled."""
        return self.status == EventStatus.CANCELLED
