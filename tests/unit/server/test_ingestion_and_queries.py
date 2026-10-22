"""End-to-end server test: ingestion, sessions listing, trace DAG API, analytics."""

import uuid

import pytest
from aog.backend.main import app
from aog.backend.models.db import init_db
from aog.events.enums import EventType
from aog.events.models import AgentEvent
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_ingest_and_query_flow() -> None:
    await init_db()
    session_id = f"trace_test_{uuid.uuid4().hex[:8]}"
    ev1_id = f"ev_root_{uuid.uuid4().hex[:8]}"
    ev2_id = f"ev_tool_{uuid.uuid4().hex[:8]}"

    span_root_id = f"span_root_{uuid.uuid4().hex[:8]}"
    span_tool_id = f"span_tool_{uuid.uuid4().hex[:8]}"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Ingest events
        e1 = AgentEvent(
            event_id=ev1_id,
            trace_id=session_id,
            span_id=span_root_id,
            session_id=session_id,
            agent_id="test_agent",
            event_type=EventType.SESSION,
            name="session:test_agent",
            duration_ms=30.0,
        )
        e2 = AgentEvent(
            event_id=ev2_id,
            trace_id=session_id,
            span_id=span_tool_id,
            parent_span_id=span_root_id,
            session_id=session_id,
            agent_id="test_agent",
            event_type=EventType.TOOL,
            name="calculator",
            input={"a": 2, "b": 3},
            output={"result": 5},
            duration_ms=15.0,
        )

        res = await client.post(
            "/v1/events",
            json={"events": [e1.model_dump(mode="json"), e2.model_dump(mode="json")]},
        )
        assert res.status_code == 200
        ingest_data = res.json()
        assert ingest_data["accepted"] == 2
        assert ingest_data["duplicates"] == 0

        # 2. Test Idempotency (re-posting should count as duplicates)
        res_dup = await client.post(
            "/v1/events",
            json={"events": [e1.model_dump(mode="json"), e2.model_dump(mode="json")]},
        )
        assert res_dup.status_code == 200
        assert res_dup.json()["duplicates"] == 2

        # 3. List sessions
        res_sessions = await client.get("/v1/sessions")
        assert res_sessions.status_code == 200
        sessions_data = res_sessions.json()
        assert sessions_data["total"] >= 1
        assert any(s["id"] == session_id for s in sessions_data["sessions"])
        session_data = next(s for s in sessions_data["sessions"] if s["id"] == session_id)
        assert session_data["status"] == "SUCCESS"

        # 4. Get Trace Graph
        res_trace = await client.get(f"/v1/sessions/{session_id}/trace")
        assert res_trace.status_code == 200
        trace_data = res_trace.json()
        assert len(trace_data["nodes"]) == 2
        assert len(trace_data["edges"]) == 1
        assert trace_data["edges"][0]["source"] == span_root_id
        assert trace_data["edges"][0]["target"] == span_tool_id

        # 5. Get Span detail
        res_span = await client.get(f"/v1/spans/{span_tool_id}")
        assert res_span.status_code == 200
        span_data = res_span.json()
        assert span_data["name"] == "calculator"
        assert span_data["input"] == {"a": 2, "b": 3}
        assert span_data["output"] == {"result": 5}

        # 6. Analytics Overview
        res_analytics = await client.get("/v1/analytics/overview")
        assert res_analytics.status_code == 200
        overview = res_analytics.json()
        assert overview["total_sessions"] >= 1
