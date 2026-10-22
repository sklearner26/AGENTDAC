"""Parser for Claude Code events and execution structures."""

from typing import Any


class ClaudeEventParser:
    """Parses Claude Code tool calls, outputs, and lifecycle payloads."""

    @staticmethod
    def parse_tool_call(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Extract clean tool metadata and inputs safely."""
        return {
            "tool": tool_name,
            "arguments": tool_input,
        }

    @staticmethod
    def parse_tool_result(result: Any) -> dict[str, Any]:
        """Extract structured result data without private reasoning."""
        if isinstance(result, dict):
            return result
        return {"output": str(result)}

    @staticmethod
    def extract_token_usage(usage_dict: dict[str, Any] | None) -> tuple[int | None, int | None]:
        """Extract input and output tokens from usage metadata."""
        if not usage_dict:
            return None, None
        tokens_in = usage_dict.get("input_tokens") or usage_dict.get("prompt_tokens")
        tokens_out = usage_dict.get("output_tokens") or usage_dict.get("completion_tokens")
        return tokens_in, tokens_out

    @staticmethod
    def parse_hook_event(payload: dict[str, Any]) -> dict[str, Any]:
        """Normalize observable Claude hook fields without private reasoning."""
        usage = payload.get("usage")
        if not isinstance(usage, dict):
            usage = payload.get("token_usage")
        tokens_in, tokens_out = ClaudeEventParser.extract_token_usage(usage)
        raw_metadata = payload.get("metadata")
        metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}
        raw_event = payload.get("event")
        event: dict[str, Any] = raw_event if isinstance(raw_event, dict) else payload
        result: dict[str, Any] = {
            "event_type": event.get("event_type") or event.get("type") or "observation",
            "name": event.get("name") or event.get("hook_event") or "claude:event",
            "agent_id": event.get("agent_id") or payload.get("agent_id") or "claude-code",
            "session_id": event.get("session_id") or payload.get("session_id"),
            "parent_run_id": event.get("parent_run_id") or payload.get("parent_run_id"),
            "reason": event.get("reason") or metadata.get("reason"),
            "skill": event.get("skill") or metadata.get("skill") or metadata.get("skill_name"),
            "tool": event.get("tool") or event.get("tool_name"),
            "model": event.get("model"),
            "provider": event.get("provider") or "anthropic",
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": event.get("cost_usd") or event.get("cost"),
            "duration_ms": event.get("duration_ms") or event.get("latency_ms"),
            "input": event.get("input") or event.get("arguments"),
            "output": event.get("output") or event.get("result"),
        }
        result["attributes"] = {
            "framework": "claude-code",
            "hook_event": result["name"],
            **{k: v for k, v in metadata.items() if k not in {"reason", "skill", "skill_name"}},
        }
        return {key: value for key, value in result.items() if value is not None}

    parse_event = parse_hook_event
