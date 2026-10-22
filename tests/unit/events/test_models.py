"""Unit tests for event models."""

import json
from datetime import UTC, datetime

import pytest
from aog.events.enums import EventStatus, EventType
from aog.events.models import AgentEvent, ErrorInfo
from pydantic import ValidationError


class TestErrorInfo:
    """Tests for ErrorInfo model."""

    def test_error_info_creation(self):
        """Test basic ErrorInfo creation."""
        error = ErrorInfo(
            type="ValueError",
            message="Invalid input",
            stacktrace="Traceback...",
            retryable=True,
        )
        assert error.type == "ValueError"
        assert error.message == "Invalid input"
        assert error.stacktrace == "Traceback..."
        assert error.retryable is True

    def test_error_info_optional_fields(self):
        """Test ErrorInfo with optional fields."""
        error = ErrorInfo(type="RuntimeError", message="Failed")
        assert error.type == "RuntimeError"
        assert error.message == "Failed"
        assert error.stacktrace is None
        assert error.retryable is None

    def test_error_info_immutable(self):
        """Test ErrorInfo is immutable (frozen)."""
        error = ErrorInfo(type="Error", message="msg")
        with pytest.raises(ValidationError):
            error.type = "OtherError"


class TestAgentEvent:
    """Tests for AgentEvent model."""

    def test_minimal_event_creation(self):
        """Test creating minimal valid event."""
        event = AgentEvent(
            trace_id="trace-123",
            span_id="span-123",
            session_id="session-123",
            agent_id="test-agent",
            event_type=EventType.TOOL,
            name="web_search",
        )
        assert event.trace_id == "trace-123"
        assert event.span_id == "span-123"
        assert event.session_id == "session-123"
        assert event.agent_id == "test-agent"
        assert event.event_type == EventType.TOOL
        assert event.name == "web_search"
        assert event.status == EventStatus.OK
        assert event.schema_version == "1.0"

    def test_event_with_parent_span(self):
        """Test event with parent span ID."""
        event = AgentEvent(
            trace_id="trace-123",
            span_id="span-456",
            parent_span_id="span-123",
            session_id="session-123",
            agent_id="test-agent",
            event_type=EventType.LLM,
            name="generate",
        )
        assert event.parent_span_id == "span-123"

    def test_event_with_input_output(self):
        """Test event with input and output."""
        event = AgentEvent(
            trace_id="trace-123",
            span_id="span-123",
            session_id="session-123",
            agent_id="test-agent",
            event_type=EventType.TOOL,
            name="search",
            input={"query": "python"},
            output={"results": ["a", "b"]},
            attributes={"provider": "tavily"},
        )
        assert event.input == {"query": "python"}
        assert event.output == {"results": ["a", "b"]}
        assert event.attributes == {"provider": "tavily"}

    def test_event_with_tokens(self):
        """Test event with token counts."""
        event = AgentEvent(
            trace_id="trace-123",
            span_id="span-123",
            session_id="session-123",
            agent_id="test-agent",
            event_type=EventType.LLM,
            name="generate",
            tokens_in=100,
            tokens_out=200,
            model="claude-3-sonnet",
            provider="anthropic",
            cost_usd=0.05,
        )
        assert event.tokens_in == 100
        assert event.tokens_out == 200
        assert event.model == "claude-3-sonnet"
        assert event.provider == "anthropic"
        assert event.cost_usd == 0.05

    def test_event_with_error(self):
        """Test event with error info."""
        error = ErrorInfo(
            type="ConnectionError",
            message="API unreachable",
            retryable=True,
        )
        event = AgentEvent(
            trace_id="trace-123",
            span_id="span-123",
            session_id="session-123",
            agent_id="test-agent",
            event_type=EventType.TOOL,
            name="search",
            status=EventStatus.ERROR,
            error=error,
        )
        assert event.status == EventStatus.ERROR
        assert event.error is not None
        assert event.error.type == "ConnectionError"
        assert event.error.retryable is True

    def test_event_is_success(self):
        """Test is_success property."""
        event = AgentEvent(
            trace_id="trace-123",
            span_id="span-123",
            session_id="session-123",
            agent_id="test-agent",
            event_type=EventType.TOOL,
            name="search",
            status=EventStatus.OK,
        )
        assert event.is_success is True
        assert event.is_error is False
        assert event.is_cancelled is False

    def test_event_is_error(self):
        """Test is_error property."""
        event = AgentEvent(
            trace_id="trace-123",
            span_id="span-123",
            session_id="session-123",
            agent_id="test-agent",
            event_type=EventType.TOOL,
            name="search",
            status=EventStatus.ERROR,
        )
        assert event.is_error is True
        assert event.is_success is False

    def test_event_is_cancelled(self):
        """Test is_cancelled property."""
        event = AgentEvent(
            trace_id="trace-123",
            span_id="span-123",
            session_id="session-123",
            agent_id="test-agent",
            event_type=EventType.TOOL,
            name="search",
            status=EventStatus.CANCELLED,
        )
        assert event.is_cancelled is True
        assert event.is_success is False
        assert event.is_error is False

    def test_event_equality_and_hash(self):
        """Test event equality and hashing based on event_id."""
        event1 = AgentEvent(
            trace_id="trace-123",
            span_id="span-123",
            session_id="session-123",
            agent_id="test-agent",
            event_type=EventType.TOOL,
            name="search",
            event_id="evt-123",
        )
        event2 = AgentEvent(
            trace_id="trace-456",
            span_id="span-456",
            session_id="session-456",
            agent_id="other-agent",
            event_type=EventType.LLM,
            name="generate",
            event_id="evt-123",
        )
        event3 = AgentEvent(
            trace_id="trace-123",
            span_id="span-123",
            session_id="session-123",
            agent_id="test-agent",
            event_type=EventType.TOOL,
            name="search",
            event_id="evt-456",
        )

        # Same event_id = equal
        assert event1 == event2
        assert hash(event1) == hash(event2)

        # Different event_id = not equal
        assert event1 != event3
        assert hash(event1) != hash(event3)

    def test_event_json_serialization(self):
        """Test event JSON serialization/deserialization.

        Note: With use_enum_values=True, enums serialize as strings.
        To reconstruct, we convert strings back to enum types.
        """
        event = AgentEvent(
            trace_id="trace-123",
            span_id="span-123",
            session_id="session-123",
            agent_id="test-agent",
            event_type=EventType.TOOL,
            name="search",
            input={"query": "test"},
            output={"result": "ok"},
            duration_ms=150.5,
            tokens_in=50,
            tokens_out=100,
        )

        # Serialize to JSON dict (with enum values as strings)
        event_dict = event.model_dump(mode="json")
        assert isinstance(event_dict, dict)

        # Verify data (enums are strings due to use_enum_values)
        assert event_dict["trace_id"] == "trace-123"
        assert event_dict["event_type"] == "tool"  # string value
        assert event_dict["name"] == "search"
        assert event_dict["duration_ms"] == 150.5
        assert event_dict["tokens_in"] == 50

        # Reconstruct from dict: convert string enums back to enum objects
        event_dict["event_type"] = EventType(event_dict["event_type"])
        event_dict["status"] = EventStatus(event_dict.get("status", "ok"))

        # Convert timestamp string to datetime
        ts = event_dict.get("timestamp")
        if isinstance(ts, str):
            event_dict["timestamp"] = datetime.fromisoformat(ts.replace("Z", "+00:00"))

        # Reconstruct from dict
        reconstructed = AgentEvent.model_validate(event_dict)
        assert reconstructed == event

    def test_event_json_serialization_with_string_enums(self):
        """Test event JSON serialization when enums are strings."""
        event = AgentEvent(
            trace_id="trace-123",
            span_id="span-123",
            session_id="session-123",
            agent_id="test-agent",
            event_type=EventType.TOOL,
            name="search",
            input={"query": "test"},
            output={"result": "ok"},
            duration_ms=150.5,
            tokens_in=50,
            tokens_out=100,
        )

        # Use model_dump_json for strict JSON
        json_str = event.model_dump_json()
        assert isinstance(json_str, str)

        # Parse JSON
        data = json.loads(json_str)

        # Note: When use_enum_values=True, enums in JSON are strings
        # To reconstruct, we need to convert them back to enum values
        # This is what a real application would do
        data["event_type"] = EventType(data["event_type"])
        data["status"] = EventStatus(data["status"])

        # Convert timestamp string back to datetime
        data["timestamp"] = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

        # Reconstruct from dict
        reconstructed = AgentEvent.model_validate(data)
        assert reconstructed == event

    def test_event_timestamp_default(self):
        """Test timestamp defaults to current time."""
        before = datetime.now(UTC)
        event = AgentEvent(
            trace_id="trace-123",
            span_id="span-123",
            session_id="session-123",
            agent_id="test-agent",
            event_type=EventType.TOOL,
            name="search",
        )
        after = datetime.now(UTC)

        assert before <= event.timestamp <= after
        assert event.timestamp.tzinfo is not None

    def test_event_immutable(self):
        """Test event is immutable (frozen)."""
        event = AgentEvent(
            trace_id="trace-123",
            span_id="span-123",
            session_id="session-123",
            agent_id="test-agent",
            event_type=EventType.TOOL,
            name="search",
        )
        with pytest.raises(ValidationError):
            event.name = "other"

    def test_event_with_duration(self):
        """Test event with duration."""
        event = AgentEvent(
            trace_id="trace-123",
            span_id="span-123",
            session_id="session-123",
            agent_id="test-agent",
            event_type=EventType.TOOL,
            name="search",
            duration_ms=123.45,
        )
        assert event.duration_ms == 123.45

    def test_event_auto_generated_event_id(self):
        """Test event_id is auto-generated if not provided."""
        event = AgentEvent(
            trace_id="trace-123",
            span_id="span-123",
            session_id="session-123",
            agent_id="test-agent",
            event_type=EventType.TOOL,
            name="search",
        )
        assert event.event_id is not None
        assert len(event.event_id) > 0
