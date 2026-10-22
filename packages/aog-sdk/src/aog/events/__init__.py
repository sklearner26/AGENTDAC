"""
AOG Events module.

Provides the universal event schema for agent observability.
"""

from aog.events.enums import EventStatus, EventType
from aog.events.models import AgentEvent, ErrorInfo
from aog.events.validation import (
    EventValidationError,
    validate_event_data,
    validate_event_status,
    validate_event_type,
    validate_payload_size,
    validate_required_fields,
)

__all__ = [
    "AgentEvent",
    "ErrorInfo",
    "EventStatus",
    "EventType",
    "EventValidationError",
    "validate_event_data",
    "validate_event_status",
    "validate_event_type",
    "validate_payload_size",
    "validate_required_fields",
]
