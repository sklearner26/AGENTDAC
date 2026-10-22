"""
Validation logic for AOG events.
"""

import json
from typing import Any

from aog.events.enums import EventStatus, EventType

# Allowed event types for validation
ALLOWED_EVENT_TYPES = {et.value for et in EventType}

# Allowed event statuses for validation
ALLOWED_STATUSES = {es.value for es in EventStatus}

# Maximum size for input/output payloads (in bytes)
DEFAULT_MAX_PAYLOAD_BYTES = 100_000  # 100KB


class EventValidationError(Exception):
    """Raised when event validation fails."""

    @classmethod
    def missing_fields(cls, missing: list[str]) -> "EventValidationError":
        """Build an error describing missing required fields."""
        return cls(f"Missing required fields: {', '.join(missing)}")

    @classmethod
    def invalid_event_type(cls, event_type: Any, allowed: set[str]) -> "EventValidationError":
        """Build an error describing an unrecognized event type."""
        return cls(f"Invalid event_type: {event_type}. Must be one of {sorted(allowed)}")

    @classmethod
    def invalid_status(cls, status: Any, allowed: set[str]) -> "EventValidationError":
        """Build an error describing an unrecognized event status."""
        return cls(f"Invalid status: {status}. Must be one of {sorted(allowed)}")

    @classmethod
    def payload_too_large(cls, which: str, max_bytes: int) -> "EventValidationError":
        """Build an error describing an oversized payload."""
        return cls(f"{which} payload exceeds max size of {max_bytes} bytes")


def validate_event_type(event_type: Any) -> bool:
    """Validate event type against allowed values.

    Accepts arbitrary input (these validators guard untrusted payloads),
    so the parameter is deliberately untyped.
    """
    return event_type in ALLOWED_EVENT_TYPES


def validate_event_status(status: Any) -> bool:
    """Validate event status against allowed values.

    Accepts arbitrary input (these validators guard untrusted payloads),
    so the parameter is deliberately untyped.
    """
    return status in ALLOWED_STATUSES


def validate_payload_size(
    payload: dict[str, Any],
    max_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES,
) -> bool:
    """Validate payload size does not exceed limit."""
    payload_bytes = len(json.dumps(payload, default=str).encode("utf-8"))
    return payload_bytes <= max_bytes


def validate_required_fields(event_dict: dict[str, Any]) -> list[str]:
    """Validate required fields are present.

    Returns list of missing field names.
    """
    required_fields = [
        "event_id",
        "trace_id",
        "span_id",
        "session_id",
        "agent_id",
        "event_type",
        "name",
        "timestamp",
    ]
    missing = []
    for field in required_fields:
        if field not in event_dict or event_dict[field] is None:
            missing.append(field)
    return missing


def validate_event_data(event_dict: dict[str, Any]) -> None:
    """Validate complete event data.

    Raises EventValidationError on failure.
    """
    # Check required fields
    missing = validate_required_fields(event_dict)
    if missing:
        raise EventValidationError.missing_fields(missing)

    # Validate event type
    event_type = event_dict.get("event_type")
    if isinstance(event_type, dict):
        event_type = event_type.get("value", event_type.get("type"))
    if not validate_event_type(event_type):
        raise EventValidationError.invalid_event_type(event_type, ALLOWED_EVENT_TYPES)

    # Validate event status if present
    status = event_dict.get("status")
    if status is not None:
        if isinstance(status, dict):
            status = status.get("value", status.get("type"))
        if not validate_event_status(status):
            raise EventValidationError.invalid_status(status, ALLOWED_STATUSES)

    # Validate payload sizes if input/output present
    max_bytes = event_dict.get("max_payload_bytes", DEFAULT_MAX_PAYLOAD_BYTES)
    if event_dict.get("input") is not None and not validate_payload_size(
        event_dict["input"], max_bytes
    ):
        raise EventValidationError.payload_too_large("Input", max_bytes)
    if event_dict.get("output") is not None and not validate_payload_size(
        event_dict["output"], max_bytes
    ):
        raise EventValidationError.payload_too_large("Output", max_bytes)
