"""Integration tests for Claude Code API endpoints."""

import pytest
from aog.backend.main import app
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_claude_code_integration_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Status endpoint
        res = await client.get("/v1/integrations/claude-code/status")
        assert res.status_code == 200
        data = res.json()
        assert data["integration"] == "claude-code"
        assert "status" in data
        assert "cli_installed" in data
        assert "hooks_configured" in data

        # 2. Toggle pause
        pause_res = await client.post("/v1/integrations/claude-code/toggle-pause")
        assert pause_res.status_code == 200
        first_state = pause_res.json()["paused"]

        unpause_res = await client.post("/v1/integrations/claude-code/toggle-pause")
        assert unpause_res.status_code == 200
        assert unpause_res.json()["paused"] != first_state

        # Ensure unpaused for subsequent tests
        if unpause_res.json()["paused"]:
            await client.post("/v1/integrations/claude-code/toggle-pause")

        # 3. Test event generation
        test_res = await client.post("/v1/integrations/claude-code/test-event")
        assert test_res.status_code == 200
        test_data = test_res.json()
        assert test_data["success"] is True
        session_id = test_data["session_id"]
        assert session_id.startswith("test-claude-")

        # 4. Verify session is queryable in sessions API
        sess_res = await client.get(f"/v1/sessions/{session_id}")
        assert sess_res.status_code == 200
        sess_data = sess_res.json()
        assert sess_data["agent_id"] == "claude-code"

        # 5. Verify DAG trace reconstruction
        trace_res = await client.get(f"/v1/sessions/{session_id}/trace")
        assert trace_res.status_code == 200
        trace_data = trace_res.json()
        assert len(trace_data["nodes"]) >= 3
        assert len(trace_data["edges"]) >= 2
