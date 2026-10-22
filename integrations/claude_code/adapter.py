"""Claude Code Adapter converting execution events into universal AOG events."""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import httpx
from aog.client import AOG
from aog.events.enums import EventStatus, EventType
from aog.events.models import AgentEvent
from aog.redaction.sanitizer import Sanitizer
from aog.tracing.lifecycle import SessionContextManager, SpanContextManager

from integrations.claude_code.parser import ClaudeEventParser

PAUSE_FILE = os.path.expanduser("~/.claude/.agentdac_paused")
DEFAULT_ENDPOINT = os.getenv("AGENTDAC_ENDPOINT", "http://localhost:8000")


class ClaudeCodeAdapter:
    """Instruments Claude Code sessions, tool executions, and file operations."""

    def __init__(self, aog: AOG | None = None, session_id: str | None = None) -> None:
        self.aog = aog or AOG(agent_id="claude-code")
        self.session_id = session_id
        self._session_mgr: SessionContextManager | None = None

    def start_session(self, metadata: dict[str, Any] | None = None) -> None:
        """Start a Claude Code session."""
        self._session_mgr = self.aog.session(
            agent_id="claude-code",
            session_id=self.session_id,
            metadata=metadata or {"tool": "claude-code", "framework": "anthropic"},
        )
        self._session_mgr.__enter__()

    def end_session(self, status: EventStatus = EventStatus.OK) -> None:
        """Finish the active session."""
        if self._session_mgr is not None:
            self._session_mgr.__exit__(None, None, None)
            self.aog.flush()

    def on_tool_start(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> SpanContextManager:
        """Context manager for a Claude Code tool invocation (e.g. view_file, run_command)."""
        return self.aog.span(
            name=f"claude:{tool_name}",
            event_type=EventType.TOOL,
            attributes={"tool": tool_name, "framework": "claude-code", **(metadata or {})},
            input_data=tool_input,
        )

    def on_llm_call(
        self,
        model: str = "claude-3-7-sonnet",
        tokens_in: int | None = None,
        tokens_out: int | None = None,
        cost_usd: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record an LLM call event."""
        self.aog.record(
            event_type=EventType.LLM,
            name=f"llm:{model}",
            model=model,
            provider="anthropic",
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost_usd,
            attributes={
                "framework": "claude-code",
                "agent_id": self.aog.config.agent_id,
                **(metadata or {}),
            },
        )

    def on_hook_event(self, payload: dict[str, Any]) -> None:
        """Record a structured observable hook event from Claude Code."""
        parsed = ClaudeEventParser.parse_hook_event(payload)
        event_type = parsed.pop("event_type", EventType.OBSERVATION)
        if event_type not in {item.value for item in EventType}:
            event_type = EventType.OBSERVATION
        attributes = parsed.pop("attributes", {})
        for key in ("agent_id", "reason", "skill", "tool", "parent_run_id"):
            if key in parsed:
                attributes[key] = parsed.pop(key)
        self.aog.record(
            event_type=event_type,
            name=parsed.pop("name", "claude:event"),
            input_data=parsed.pop("input", None),
            output_data=parsed.pop("output", None),
            duration_ms=parsed.pop("duration_ms", None),
            tokens_in=parsed.pop("tokens_in", None),
            tokens_out=parsed.pop("tokens_out", None),
            model=parsed.pop("model", None),
            provider=parsed.pop("provider", None),
            cost_usd=parsed.pop("cost_usd", None),
            attributes={**attributes, **parsed},
        )

    @staticmethod
    def is_paused() -> bool:
        """Check if Claude Code telemetry ingestion is paused."""
        return os.path.exists(PAUSE_FILE)

    @staticmethod
    def set_paused(paused: bool) -> None:
        """Pause or resume Claude Code telemetry ingestion."""
        if paused:
            os.makedirs(os.path.dirname(PAUSE_FILE), exist_ok=True)
            with open(PAUSE_FILE, "w", encoding="utf-8") as f:
                f.write("paused\n")
        elif os.path.exists(PAUSE_FILE):
            os.remove(PAUSE_FILE)

    @classmethod
    def handle_hook_payload(
        cls,
        payload: dict[str, Any],
        endpoint: str = DEFAULT_ENDPOINT,
        timeout_s: float = 2.0,
    ) -> bool:
        """Process a raw JSON hook payload delivered by Claude Code CLI via stdin."""
        if cls.is_paused():
            return False
        events = cls.build_events_from_payload(payload)
        return cls._deliver_events(events, endpoint=endpoint, timeout_s=timeout_s)

    @classmethod
    def build_events_from_payload(cls, payload: dict[str, Any]) -> list[AgentEvent]:
        """Convert a Claude Code hook payload into normalized AgentEvent instances."""
        hook_event = (
            payload.get("hook_event_name")
            or payload.get("type")
            or payload.get("event")
            or "unknown"
        )
        session_id = payload.get("session_id") or "claude-session-default"
        root_span_id = f"session_root_{session_id}"
        cwd = payload.get("cwd") or os.getcwd()
        sanitizer = Sanitizer()

        events: list[AgentEvent] = []
        now = datetime.now(UTC)

        # 1. Guarantee root session node exists for DAG graph connectivity
        root_event = AgentEvent(
            event_id=f"root_{session_id}",
            trace_id=session_id,
            span_id=root_span_id,
            parent_span_id=None,
            session_id=session_id,
            agent_id="claude-code",
            event_type=EventType.SESSION,
            name="Claude Code Session",
            timestamp=now,
            status=EventStatus.OK,
            attributes={
                "framework": "claude-code",
                "cwd": cwd,
                "transcript_path": payload.get("transcript_path"),
            },
        )
        events.append(root_event)

        # 2. Translate specific lifecycle event
        if hook_event == "PreToolUse":
            tool_name = payload.get("tool_name", "unknown")
            tool_use_id = payload.get("tool_use_id") or str(uuid4())
            raw_input = payload.get("tool_input")
            sanitized_input = (
                sanitizer.sanitize(raw_input)
                if isinstance(raw_input, dict)
                else ({"value": sanitizer.sanitize(raw_input)} if raw_input is not None else None)
            )
            parent_span_id = payload.get("parent_tool_use_id") or root_span_id

            tool_event = AgentEvent(
                event_id=f"pre_{tool_use_id}",
                trace_id=session_id,
                span_id=tool_use_id,
                parent_span_id=parent_span_id,
                session_id=session_id,
                agent_id="claude-code",
                event_type=EventType.TOOL,
                name=f"claude:{tool_name}",
                timestamp=now,
                status=EventStatus.OK,
                input=sanitized_input,
                attributes={
                    "hook": "PreToolUse",
                    "tool": tool_name,
                    "framework": "claude-code",
                    "cwd": cwd,
                    "permission_mode": payload.get("permission_mode"),
                },
            )
            events.append(tool_event)

        elif hook_event == "PostToolUse":
            tool_name = payload.get("tool_name", "unknown")
            tool_use_id = payload.get("tool_use_id") or str(uuid4())
            raw_input = payload.get("tool_input")
            sanitized_input = (
                sanitizer.sanitize(raw_input)
                if isinstance(raw_input, dict)
                else ({"value": sanitizer.sanitize(raw_input)} if raw_input is not None else None)
            )

            raw_output = (
                payload.get("tool_result")
                or payload.get("output")
                or payload.get("tool_output")
            )
            sanitized_output = (
                sanitizer.sanitize(raw_output)
                if isinstance(raw_output, dict)
                else ({"value": sanitizer.sanitize(raw_output)} if raw_output is not None else None)
            )

            is_error = bool(payload.get("error") or payload.get("is_error"))
            status = EventStatus.ERROR if is_error else EventStatus.OK
            duration_ms = payload.get("duration_ms")
            parent_span_id = payload.get("parent_tool_use_id") or root_span_id

            tool_event = AgentEvent(
                event_id=f"post_{tool_use_id}",
                trace_id=session_id,
                span_id=tool_use_id,
                parent_span_id=parent_span_id,
                session_id=session_id,
                agent_id="claude-code",
                event_type=EventType.TOOL,
                name=f"claude:{tool_name}",
                timestamp=now,
                status=status,
                input=sanitized_input,
                output=sanitized_output,
                duration_ms=duration_ms,
                attributes={
                    "hook": "PostToolUse",
                    "tool": tool_name,
                    "framework": "claude-code",
                    "cwd": cwd,
                },
            )
            events.append(tool_event)

        elif hook_event == "UserPromptSubmit":
            prompt_text = payload.get("prompt") or payload.get("user_prompt") or ""
            prompt_id = str(uuid4())
            prompt_event = AgentEvent(
                event_id=f"prompt_{prompt_id}",
                trace_id=session_id,
                span_id=f"prompt_{prompt_id}",
                parent_span_id=root_span_id,
                session_id=session_id,
                agent_id="claude-code",
                event_type=EventType.OBSERVATION,
                name="claude:user_prompt",
                timestamp=now,
                status=EventStatus.OK,
                input={"prompt": sanitizer.sanitize(prompt_text)},
                attributes={"hook": "UserPromptSubmit", "framework": "claude-code"},
            )
            events.append(prompt_event)

        elif hook_event == "Notification":
            title = payload.get("title", "notification")
            message = payload.get("message", "")
            notif_id = str(uuid4())
            notif_event = AgentEvent(
                event_id=f"notif_{notif_id}",
                trace_id=session_id,
                span_id=f"notif_{notif_id}",
                parent_span_id=root_span_id,
                session_id=session_id,
                agent_id="claude-code",
                event_type=EventType.OBSERVATION,
                name=f"claude:notification:{title}",
                timestamp=now,
                status=EventStatus.OK,
                output={"message": sanitizer.sanitize(message)},
                attributes={
                    "hook": "Notification",
                    "notification_title": title,
                    "framework": "claude-code",
                },
            )
            events.append(notif_event)

        elif hook_event == "Stop":
            stop_event = AgentEvent(
                event_id=f"stop_{session_id}_{int(time.time())}",
                trace_id=session_id,
                span_id=root_span_id,
                parent_span_id=None,
                session_id=session_id,
                agent_id="claude-code",
                event_type=EventType.SESSION,
                name="Claude Code Session",
                timestamp=now,
                status=EventStatus.OK,
                duration_ms=payload.get("duration_ms"),
                attributes={
                    "hook": "Stop",
                    "stop_reason": payload.get("stop_reason"),
                    "framework": "claude-code",
                },
            )
            events.append(stop_event)

        return events

    @classmethod
    def _deliver_events(
        cls,
        events: list[AgentEvent],
        endpoint: str,
        timeout_s: float = 2.0,
    ) -> bool:
        """Send normalized events to AgentDAC backend fail-open."""
        if not events:
            return True

        url = endpoint.rstrip("/") + "/v1/events"
        payload = {"events": [ev.model_dump(mode="json") for ev in events]}

        try:
            with httpx.Client(timeout=timeout_s) as client:
                res = client.post(url, json=payload, headers={"content-type": "application/json"})
                return res.status_code == 200
        except Exception:
            # Observability failures must never disrupt developer workflow
            return False
