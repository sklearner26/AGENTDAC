"""Shared pytest fixtures for the AOG test suite."""

from typing import Any

import pytest
from aog.events.enums import EventType
from aog.events.models import AgentEvent


@pytest.fixture
def make_event():
    """Return a factory that builds a valid ``AgentEvent``.

    Call it with keyword overrides to change any field:

        event = make_event(name="search", event_type=EventType.LLM)
    """

    def _make_event(**overrides: Any) -> AgentEvent:
        data: dict[str, Any] = {
            "trace_id": "trace-123",
            "span_id": "span-123",
            "session_id": "session-123",
            "agent_id": "test-agent",
            "event_type": EventType.TOOL,
            "name": "test_event",
        }
        data.update(overrides)
        return AgentEvent(**data)

    return _make_event
