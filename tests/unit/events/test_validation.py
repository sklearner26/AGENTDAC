"""Unit tests for event validation."""

import pytest
from aog.events.validation import (
    EventValidationError,
    validate_event_data,
    validate_event_status,
    validate_event_type,
    validate_payload_size,
    validate_required_fields,
)


class TestValidateEventType:
    """Tests for event type validation."""

    def test_valid_event_types(self):
        """Test valid event types pass validation."""
        valid_types = [
            "session",
            "agent",
            "llm",
            "tool",
            "retrieval",
            "memory",
            "decision",
            "handoff",
            "state_change",
            "observation",
            "error",
        ]
        for et in valid_types:
            assert validate_event_type(et) is True

    def test_invalid_event_type(self):
        """Test invalid event type fails validation."""
        assert validate_event_type("invalid_type") is False
        assert validate_event_type("") is False
        assert validate_event_type("INVALID") is False


class TestValidateEventStatus:
    """Tests for event status validation."""

    def test_valid_statuses(self):
        """Test valid statuses pass validation."""
        valid_statuses = ["ok", "error", "cancelled"]
        for status in valid_statuses:
            assert validate_event_status(status) is True

    def test_invalid_status(self):
        """Test invalid status fails validation."""
        assert validate_event_status("invalid") is False
        assert validate_event_status("") is False
        assert validate_event_status("OK") is False


class TestValidateRequiredFields:
    """Tests for required fields validation."""

    def test_all_required_fields_present(self):
        """Test event with all required fields."""
        event = {
            "event_id": "evt-123",
            "trace_id": "trace-123",
            "span_id": "span-123",
            "session_id": "session-123",
            "agent_id": "agent-123",
            "event_type": "tool",
            "name": "search",
            "timestamp": "2024-01-01T00:00:00Z",
        }
        missing = validate_required_fields(event)
        assert missing == []

    def test_missing_fields_detected(self):
        """Test missing fields are detected."""
        event = {
            "trace_id": "trace-123",
            # missing: event_id, span_id, session_id, agent_id, event_type, name, timestamp
        }
        missing = validate_required_fields(event)
        expected_missing = [
            "event_id",
            "span_id",
            "session_id",
            "agent_id",
            "event_type",
            "name",
            "timestamp",
        ]
        assert sorted(missing) == sorted(expected_missing)

    def test_none_values_treated_as_missing(self):
        """Test None values are treated as missing."""
        event = {
            "event_id": None,
            "trace_id": "trace-123",
            "span_id": "span-123",
            "session_id": "session-123",
            "agent_id": "agent-123",
            "event_type": "tool",
            "name": "search",
            "timestamp": "2024-01-01T00:00:00Z",
        }
        missing = validate_required_fields(event)
        assert "event_id" in missing


class TestValidatePayloadSize:
    """Tests for payload size validation."""

    def test_small_payload(self):
        """Test small payload passes validation."""
        payload = {"key": "value"}
        assert validate_payload_size(payload) is True

    def test_large_payload(self):
        """Test large payload exceeds limit."""
        large_data = "a" * 200_000  # 200KB
        payload = {"data": large_data}
        assert validate_payload_size(payload, max_bytes=100_000) is False

    def test_payload_at_limit(self):
        """Test payload at exact limit passes."""
        # Create payload close to 100KB
        payload = {"data": "x" * 95_000}
        assert validate_payload_size(payload, max_bytes=100_000) is True

    def test_empty_payload(self):
        """Test empty payload passes validation."""
        assert validate_payload_size({}) is True


class TestValidateEventData:
    """Tests for complete event data validation."""

    def test_valid_event_passes(self):
        """Test valid event passes validation."""
        event = {
            "event_id": "evt-123",
            "trace_id": "trace-123",
            "span_id": "span-123",
            "session_id": "session-123",
            "agent_id": "agent-123",
            "event_type": "tool",
            "name": "search",
            "timestamp": "2024-01-01T00:00:00Z",
            "status": "ok",
            "input": {"query": "test"},
            "output": {"result": "ok"},
        }
        # Should not raise
        validate_event_data(event)

    def test_missing_required_fields_raises(self):
        """Test missing fields raises validation error."""
        event = {
            "trace_id": "trace-123",
            # missing required fields
        }
        with pytest.raises(EventValidationError) as exc_info:
            validate_event_data(event)
        assert "Missing required fields" in str(exc_info.value)

    def test_invalid_event_type_raises(self):
        """Test invalid event type raises validation error."""
        event = {
            "event_id": "evt-123",
            "trace_id": "trace-123",
            "span_id": "span-123",
            "session_id": "session-123",
            "agent_id": "agent-123",
            "event_type": "invalid_type",  # invalid
            "name": "search",
            "timestamp": "2024-01-01T00:00:00Z",
        }
        with pytest.raises(EventValidationError) as exc_info:
            validate_event_data(event)
        assert "Invalid event_type" in str(exc_info.value)

    def test_invalid_status_raises(self):
        """Test invalid status raises validation error."""
        event = {
            "event_id": "evt-123",
            "trace_id": "trace-123",
            "span_id": "span-123",
            "session_id": "session-123",
            "agent_id": "agent-123",
            "event_type": "tool",
            "name": "search",
            "timestamp": "2024-01-01T00:00:00Z",
            "status": "invalid_status",  # invalid
        }
        with pytest.raises(EventValidationError) as exc_info:
            validate_event_data(event)
        assert "Invalid status" in str(exc_info.value)

    def test_oversized_input_raises(self):
        """Test oversized input raises validation error."""
        event = {
            "event_id": "evt-123",
            "trace_id": "trace-123",
            "span_id": "span-123",
            "session_id": "session-123",
            "agent_id": "agent-123",
            "event_type": "tool",
            "name": "search",
            "timestamp": "2024-01-01T00:00:00Z",
            "input": {"data": "x" * 200_000},  # too large
        }
        with pytest.raises(EventValidationError) as exc_info:
            validate_event_data(event)
        assert "exceeds max size" in str(exc_info.value)

    def test_oversized_output_raises(self):
        """Test oversized output raises validation error."""
        event = {
            "event_id": "evt-123",
            "trace_id": "trace-123",
            "span_id": "span-123",
            "session_id": "session-123",
            "agent_id": "agent-123",
            "event_type": "tool",
            "name": "search",
            "timestamp": "2024-01-01T00:00:00Z",
            "output": {"data": "x" * 200_000},  # too large
        }
        with pytest.raises(EventValidationError) as exc_info:
            validate_event_data(event)
        assert "exceeds max size" in str(exc_info.value)

    def test_event_with_optional_status(self):
        """Test event without status passes validation."""
        event = {
            "event_id": "evt-123",
            "trace_id": "trace-123",
            "span_id": "span-123",
            "session_id": "session-123",
            "agent_id": "agent-123",
            "event_type": "tool",
            "name": "search",
            "timestamp": "2024-01-01T00:00:00Z",
            # status is optional
        }
        # Should not raise
        validate_event_data(event)
