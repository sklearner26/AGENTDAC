"""Generic agent helper utilities for manual instrumentation without frameworks."""

from typing import Any

from aog.client import AOG
from aog.events.enums import EventType


class GenericAgentInstrumentation:
    """Convenience wrapper for instrumenting custom agent loops."""

    def __init__(self, aog: AOG, agent_name: str = "custom_agent") -> None:
        self.aog = aog
        self.agent_name = agent_name

    def record_thought(self, content: str, attributes: dict[str, Any] | None = None) -> None:
        """Record an observable agent thought or decision event."""
        attrs = dict(attributes or {})
        self.aog.record(
            event_type=EventType.DECISION,
            name="agent_decision",
            input_data={"thought": content},
            attributes=attrs,
        )

    def record_state_change(
        self,
        previous_state: str,
        new_state: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record an agent state transition."""
        self.aog.record(
            event_type=EventType.STATE_CHANGE,
            name=f"state:{previous_state}->{new_state}",
            input_data={"from": previous_state, "to": new_state, "details": details or {}},
        )

    def record_handoff(
        self,
        target_agent: str,
        reason: str | None = None,
        context_data: dict[str, Any] | None = None,
    ) -> None:
        """Record a handoff to another agent."""
        self.aog.record(
            event_type=EventType.HANDOFF,
            name=f"handoff_to:{target_agent}",
            input_data={"target": target_agent, "reason": reason, "context": context_data or {}},
        )
