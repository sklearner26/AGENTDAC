"""Integration tests for Fail-Open behavior (Requirements §3 & §38)."""

from agentdac import AgentDAC


def test_agent_continues_when_backend_unavailable() -> None:
    # Point to an unreachable port with fail_open=True
    aog = AgentDAC(endpoint="http://127.0.0.1:59999", auto_start=False, fail_open=True)

    executed = False
    with (
        aog.session(agent_id="resilient_agent"),
        aog.agent("planner"),
        aog.tool("unreachable_service"),
    ):
        executed = True

    assert executed is True
    # Flush should not raise an unhandled exception to the agent
    aog.flush(timeout=0.1)
    aog.shutdown()
