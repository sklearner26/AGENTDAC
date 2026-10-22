"""
Event-related enums for AOG.
"""

from enum import StrEnum


class EventType(StrEnum):
    """Type of agent event."""

    SESSION = "session"
    AGENT = "agent"
    LLM = "llm"
    TOOL = "tool"
    SKILL = "skill"
    RETRIEVAL = "retrieval"
    MEMORY = "memory"
    DECISION = "decision"
    HANDOFF = "handoff"
    STATE_CHANGE = "state_change"
    OBSERVATION = "observation"
    ERROR = "error"


class EventStatus(StrEnum):
    """Status of an event or span."""

    OK = "ok"
    ERROR = "error"
    CANCELLED = "cancelled"
