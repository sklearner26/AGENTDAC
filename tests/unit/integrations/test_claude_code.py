"""Unit tests for Claude Code integration."""

from collections.abc import Sequence

from aog.client import AOG
from aog.events.enums import EventType
from aog.events.models import AgentEvent
from aog.exporters.base import Exporter

from integrations.claude_code.adapter import ClaudeCodeAdapter
from integrations.claude_code.parser import ClaudeEventParser


class ListExporter(Exporter):
    def __init__(self) -> None:
        self.events: list[AgentEvent] = []

    def export(self, batch: Sequence[AgentEvent]) -> None:
        self.events.extend(batch)

    def shutdown(self) -> None:
        pass


def test_claude_code_adapter_lifecycle():
    exporter = ListExporter()
    client = AOG(agent_id="test-claude", exporter=exporter)
    adapter = ClaudeCodeAdapter(aog=client, session_id="claude-sess-1")

    adapter.start_session(metadata={"task": "refactor"})
    adapter.on_llm_call(model="claude-3-7-sonnet", tokens_in=500, tokens_out=100, cost_usd=0.002)

    with adapter.on_tool_start("view_file", {"path": "src/main.py"}) as span:
        span.set_output({"code": "print('hello')"})

    adapter.end_session()

    event_types = [e.event_type for e in exporter.events]
    assert EventType.SESSION in event_types
    assert EventType.LLM in event_types
    assert EventType.TOOL in event_types


def test_claude_event_parser():
    parsed_tool = ClaudeEventParser.parse_tool_call("grep_search", {"query": "def test"})
    assert parsed_tool["tool"] == "grep_search"
    assert parsed_tool["arguments"]["query"] == "def test"

    parsed_res = ClaudeEventParser.parse_tool_result({"status": "ok"})
    assert parsed_res == {"status": "ok"}

    tokens_in, tokens_out = ClaudeEventParser.extract_token_usage(
        {"input_tokens": 10, "output_tokens": 20}
    )
    assert tokens_in == 10
    assert tokens_out == 20


def test_claude_hook_parser_keeps_operational_metadata_only():
    parsed = ClaudeEventParser.parse_hook_event(
        {
            "type": "tool_result",
            "session_id": "session-1",
            "tool_name": "run_command",
            "metadata": {"reason": "inspect", "skill": "debug"},
            "usage": {"input_tokens": 3, "output_tokens": 4},
            "latency_ms": 12.5,
            "thinking": "private reasoning must not be exported",
        }
    )
    assert parsed["tool"] == "run_command"
    assert parsed["reason"] == "inspect"
    assert parsed["skill"] == "debug"
    assert parsed["tokens_in"] == 3
    assert parsed["duration_ms"] == 12.5
    assert "thinking" not in parsed


def test_claude_hook_event_is_recorded_with_metadata():
    exporter = ListExporter()
    client = AOG(agent_id="test-claude", exporter=exporter)
    adapter = ClaudeCodeAdapter(aog=client, session_id="claude-sess-2")
    adapter.start_session()
    adapter.on_hook_event(
        {
            "type": "tool_result",
            "tool_name": "grep_search",
            "reason": "find definition",
            "usage": {"input_tokens": 1, "output_tokens": 2},
        }
    )
    adapter.end_session()
    event = next(event for event in exporter.events if event.name == "claude:event")
    assert event.attributes["tool"] == "grep_search"
    assert event.attributes["reason"] == "find definition"
    assert event.tokens_in == 1


def test_claude_hook_payload_pre_and_post_tool_correlation():
    pre_payload = {
        "hook_event_name": "PreToolUse",
        "session_id": "sess-corr-1",
        "tool_use_id": "toolu_abc_123",
        "tool_name": "Bash",
        "tool_input": {"command": "npm test"},
    }
    pre_events = ClaudeCodeAdapter.build_events_from_payload(pre_payload)
    assert len(pre_events) == 2  # root_event + pre_event
    root_ev = pre_events[0]
    tool_ev = pre_events[1]

    assert root_ev.span_id == "session_root_sess-corr-1"
    assert tool_ev.span_id == "toolu_abc_123"
    assert tool_ev.parent_span_id == "session_root_sess-corr-1"
    assert tool_ev.input == {"command": "npm test"}

    post_payload = {
        "hook_event_name": "PostToolUse",
        "session_id": "sess-corr-1",
        "tool_use_id": "toolu_abc_123",
        "tool_name": "Bash",
        "tool_input": {"command": "npm test"},
        "tool_result": {"status": "passed"},
        "duration_ms": 120.0,
    }
    post_events = ClaudeCodeAdapter.build_events_from_payload(post_payload)
    post_tool_ev = post_events[1]

    # Exactly the same span_id for DAG updates
    assert post_tool_ev.span_id == "toolu_abc_123"
    assert post_tool_ev.duration_ms == 120.0
    assert post_tool_ev.output == {"status": "passed"}


def test_claude_hook_payload_redaction():
    payload = {
        "hook_event_name": "PreToolUse",
        "session_id": "sess-redact-1",
        "tool_use_id": "toolu_sec_1",
        "tool_name": "Bash",
        "tool_input": {"command": "curl", "api_key": "sk-secret-live-12345"},
    }
    events = ClaudeCodeAdapter.build_events_from_payload(payload)
    tool_ev = events[1]
    assert tool_ev.input["api_key"] == "[REDACTED]"
    assert tool_ev.input["command"] == "curl"


def test_claude_hook_pause_state(tmp_path, monkeypatch):
    test_pause_file = tmp_path / ".agentdac_paused"
    monkeypatch.setattr("integrations.claude_code.adapter.PAUSE_FILE", str(test_pause_file))

    assert not ClaudeCodeAdapter.is_paused()
    ClaudeCodeAdapter.set_paused(True)
    assert ClaudeCodeAdapter.is_paused()
    assert test_pause_file.exists()

    # handle_hook_payload returns False when paused without sending
    result = ClaudeCodeAdapter.handle_hook_payload({"hook_event_name": "PreToolUse"})
    assert result is False

    ClaudeCodeAdapter.set_paused(False)
    assert not ClaudeCodeAdapter.is_paused()

