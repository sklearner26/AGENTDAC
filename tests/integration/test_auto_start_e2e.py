"""End-to-end Integration Test for Real Automatic Backend Startup (Requirement §56).

Tests full lifecycle:
Agent application starts -> AgentDAC SDK automatically spawns local backend ->
Agent executes & emits events -> Ingestion persists to DB ->
Reconstructed DAG and Session details are queryable via REST API ->
Graceful shutdown.
"""

import socket
import time

import httpx
import pytest
from agentdac import AgentDAC, EventType
from aog.runtime.manager import RuntimeManager


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.mark.slow
def test_real_backend_autostart_and_e2e_observability() -> None:
    port = _find_free_port()
    endpoint = f"http://127.0.0.1:{port}"

    # Initialize SDK with auto_start targeting this free port
    aog = AgentDAC(endpoint=endpoint, port=port, auto_start=True, agent_id="e2e_test_agent")

    try:
        # 1. Execute an instrumented agent workflow
        @aog.tool(name="fetch_data")
        def fetch_data(key: str) -> dict[str, str]:
            return {"key": key, "status": "retrieved"}

        with aog.session(session_id=f"e2e_ses_{port}", metadata={"env": "e2e_test"}):
            with aog.agent("orchestrator"):
                with aog.llm(model="mock-gpt4", provider="mock-ai") as llm_span:
                    llm_span.set_tokens(tokens_in=120, tokens_out=60)
                    llm_span.set_cost(0.0015)

                result = fetch_data("user_123")
                assert result["status"] == "retrieved"

            aog.record(
                event_type=EventType.DECISION, name="routing_choice", input_data={"route": "direct"}
            )

        # 2. Flush pending telemetry to the live backend
        aog.flush(timeout=5.0)

        # Allow brief moment for SQLite transaction to commit
        time.sleep(0.5)

        # 3. Query the live auto-started backend directly
        with httpx.Client(timeout=3.0) as client:
            # Health
            health_res = client.get(f"{endpoint}/health")
            assert health_res.status_code == 200
            assert health_res.json()["status"] == "ok"
            assert health_res.json()["service"] == "agentdac"

            # Latest Session
            latest_res = client.get(f"{endpoint}/v1/sessions/latest")
            assert latest_res.status_code == 200
            latest_data = latest_res.json()
            assert latest_data["agent_id"] == "e2e_test_agent"
            assert latest_data["total_tokens"] == 180

            # Trace DAG
            trace_res = client.get(f"{endpoint}/v1/sessions/{latest_data['id']}/trace")
            assert trace_res.status_code == 200
            trace_data = trace_res.json()
            assert len(trace_data["nodes"]) >= 3
            assert len(trace_data["edges"]) >= 2
    finally:
        aog.shutdown()
        RuntimeManager.get_instance().shutdown(terminate_process=True)
