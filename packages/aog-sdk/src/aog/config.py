"""Configuration management for AgentDAC / AOG SDK."""

import os
from dataclasses import dataclass, field
from typing import Any

from aog.redaction.rules import RedactionConfig


@dataclass
class AOGConfig:
    """Settings controlling AgentDAC SDK runtime, networking, and capture behavior."""

    endpoint: str = "http://127.0.0.1:8000"
    host: str = "127.0.0.1"
    port: int = 8000
    auto_start: bool = True
    api_key: str | None = None
    agent_id: str = "default-agent"
    environment: str = "development"

    fail_open: bool = True

    export_batch_size: int = 50
    export_flush_interval_ms: int = 500
    export_queue_size: int = 5000
    export_max_retries: int = 3
    export_timeout_s: float = 5.0

    redaction: RedactionConfig = field(default_factory=RedactionConfig)

    @classmethod
    def from_env(cls, **overrides: Any) -> "AOGConfig":
        """Load configuration from environment variables with optional parameter overrides."""
        host = str(
            overrides.get("host")
            or os.getenv("AGENTDAC_HOST")
            or os.getenv("AOG_HOST")
            or "127.0.0.1"
        )
        port_raw = (
            overrides.get("port") or os.getenv("AGENTDAC_PORT") or os.getenv("AOG_PORT") or "8000"
        )
        port = int(str(port_raw))

        default_endpoint = f"http://{host}:{port}"
        endpoint = str(
            overrides.get("endpoint")
            or os.getenv("AGENTDAC_BACKEND_URL")
            or os.getenv("AGENTDAC_ENDPOINT")
            or os.getenv("AOG_ENDPOINT")
            or default_endpoint
        )

        auto_start_raw = overrides.get("auto_start")
        if auto_start_raw is None:
            auto_start_raw = os.getenv("AGENTDAC_AUTO_START", os.getenv("AOG_AUTO_START", "true"))
        auto_start = str(auto_start_raw).lower() in ("true", "1", "yes", "on")

        api_key_val = (
            overrides.get("api_key") or os.getenv("AGENTDAC_API_KEY") or os.getenv("AOG_API_KEY")
        )
        api_key = str(api_key_val) if api_key_val is not None else None

        agent_id = str(
            overrides.get("agent_id")
            or os.getenv("AGENTDAC_AGENT_ID")
            or os.getenv("AOG_AGENT_ID")
            or "default-agent"
        )
        env = str(
            overrides.get("environment")
            or os.getenv("AGENTDAC_ENVIRONMENT")
            or os.getenv("AOG_ENVIRONMENT")
            or "development"
        )

        fail_open_raw = overrides.get("fail_open")
        if fail_open_raw is None:
            fail_open_raw = os.getenv("AGENTDAC_FAIL_OPEN", os.getenv("AOG_FAIL_OPEN", "true"))
        fail_open = str(fail_open_raw).lower() in ("true", "1", "yes", "on")

        batch_size_raw = overrides.get("export_batch_size") or os.getenv(
            "AGENTDAC_EXPORT_BATCH_SIZE", os.getenv("AOG_EXPORT_BATCH_SIZE", "50")
        )
        batch_size = int(str(batch_size_raw))

        flush_interval_raw = overrides.get("export_flush_interval_ms") or os.getenv(
            "AGENTDAC_EXPORT_FLUSH_INTERVAL_MS", os.getenv("AOG_EXPORT_FLUSH_INTERVAL_MS", "500")
        )
        flush_interval = int(str(flush_interval_raw))

        queue_size_raw = overrides.get("export_queue_size") or os.getenv(
            "AGENTDAC_EXPORT_QUEUE_SIZE", os.getenv("AOG_EXPORT_QUEUE_SIZE", "5000")
        )
        queue_size = int(str(queue_size_raw))

        capture_input = str(
            overrides.get("capture_input")
            or os.getenv("AGENTDAC_CAPTURE_INPUT", os.getenv("AOG_CAPTURE_INPUT", "true"))
        ).lower() in ("true", "1", "yes", "on")
        capture_output = str(
            overrides.get("capture_output")
            or os.getenv("AGENTDAC_CAPTURE_OUTPUT", os.getenv("AOG_CAPTURE_OUTPUT", "true"))
        ).lower() in ("true", "1", "yes", "on")
        capture_tool_args = str(
            overrides.get("capture_tool_args")
            or os.getenv("AGENTDAC_CAPTURE_TOOL_ARGS", os.getenv("AOG_CAPTURE_TOOL_ARGS", "true"))
        ).lower() in ("true", "1", "yes", "on")
        capture_tool_results = str(
            overrides.get("capture_tool_results")
            or os.getenv(
                "AGENTDAC_CAPTURE_TOOL_RESULTS", os.getenv("AOG_CAPTURE_TOOL_RESULTS", "true")
            )
        ).lower() in ("true", "1", "yes", "on")

        redaction = overrides.get("redaction") or RedactionConfig(
            capture_input=capture_input,
            capture_output=capture_output,
            capture_tool_args=capture_tool_args,
            capture_tool_results=capture_tool_results,
        )

        return cls(
            endpoint=endpoint,
            host=host,
            port=port,
            auto_start=auto_start,
            api_key=api_key,
            agent_id=agent_id,
            environment=env,
            fail_open=fail_open,
            export_batch_size=batch_size,
            export_flush_interval_ms=flush_interval,
            export_queue_size=queue_size,
            redaction=redaction,
        )


AgentDACConfig = AOGConfig
