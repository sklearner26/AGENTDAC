"""Unit tests for event enums."""

from aog.events.enums import EventStatus, EventType


class TestEventType:
    """Tests for EventType enum."""

    def test_all_event_types_present(self):
        """Verify all required event types are defined."""
        expected = {
            "session",
            "agent",
            "llm",
            "tool",
            "skill",
            "retrieval",
            "memory",
            "decision",
            "handoff",
            "state_change",
            "observation",
            "error",
        }
        actual = {et.value for et in EventType}
        assert actual == expected

    def test_event_type_values(self):
        """Verify specific event type values."""
        assert EventType.SESSION.value == "session"
        assert EventType.AGENT.value == "agent"
        assert EventType.LLM.value == "llm"
        assert EventType.TOOL.value == "tool"
        assert EventType.SKILL.value == "skill"
        assert EventType.RETRIEVAL.value == "retrieval"
        assert EventType.MEMORY.value == "memory"
        assert EventType.DECISION.value == "decision"
        assert EventType.HANDOFF.value == "handoff"
        assert EventType.STATE_CHANGE.value == "state_change"
        assert EventType.OBSERVATION.value == "observation"
        assert EventType.ERROR.value == "error"


class TestEventStatus:
    """Tests for EventStatus enum."""

    def test_all_statuses_present(self):
        """Verify all required statuses are defined."""
        expected = {"ok", "error", "cancelled"}
        actual = {es.value for es in EventStatus}
        assert actual == expected

    def test_status_values(self):
        """Verify specific status values."""
        assert EventStatus.OK.value == "ok"
        assert EventStatus.ERROR.value == "error"
        assert EventStatus.CANCELLED.value == "cancelled"
