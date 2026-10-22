"""Seed realistic agent sessions into AOG database for demo and local development."""

import asyncio
import pathlib
import random
import sys
import uuid
from datetime import UTC, datetime, timedelta

# Add repository root to sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from aog.backend.models.db import async_session, init_db
from aog.backend.services.ingestion import IngestionService
from aog.events.enums import EventStatus, EventType
from aog.events.models import AgentEvent, ErrorInfo


async def seed_demo_data() -> None:
    await init_db()
    print("[*] Seeding AOG database with realistic agent sessions...")

    async with async_session() as db:
        service = IngestionService(db)

        agents = ["claude-code", "research-bot", "code-reviewer", "data-agent"]
        models = ["claude-3-7-sonnet", "claude-3-5-haiku", "gpt-4o"]
        tools = ["web_search", "view_file", "run_command", "git_commit", "grep_search", "read_url"]

        for i in range(8):
            agent = random.choice(agents)
            session_id = f"sess_{uuid.uuid4().hex[:10]}"
            start_time = datetime.now(UTC) - timedelta(minutes=random.randint(5, 120))
            is_error = i == 3  # Make one session have an error for demonstration

            events: list[AgentEvent] = []

            # 1. Root Session Event
            root_span_id = f"span_{uuid.uuid4().hex[:8]}"
            events.append(
                AgentEvent(
                    event_id=f"ev_{uuid.uuid4().hex[:8]}",
                    trace_id=session_id,
                    span_id=root_span_id,
                    session_id=session_id,
                    agent_id=agent,
                    event_type=EventType.SESSION,
                    name=f"session:{agent}",
                    timestamp=start_time,
                    status=EventStatus.ERROR if is_error else EventStatus.OK,
                    attributes={"environment": "production", "task_type": "autonomous_coding"},
                )
            )

            # 2. Initial LLM Step
            llm1_span = f"span_{uuid.uuid4().hex[:8]}"
            events.append(
                AgentEvent(
                    event_id=f"ev_{uuid.uuid4().hex[:8]}",
                    trace_id=session_id,
                    span_id=llm1_span,
                    parent_span_id=root_span_id,
                    session_id=session_id,
                    agent_id=agent,
                    event_type=EventType.LLM,
                    name="llm:reasoning",
                    timestamp=start_time + timedelta(seconds=1),
                    duration_ms=450.0,
                    tokens_in=random.randint(300, 1200),
                    tokens_out=random.randint(50, 250),
                    model=random.choice(models),
                    provider="anthropic",
                    cost_usd=round(random.uniform(0.001, 0.008), 4),
                )
            )

            # 3. Tool Calls
            tool_name = random.choice(tools)
            tool_span = f"span_{uuid.uuid4().hex[:8]}"
            if is_error:
                events.append(
                    AgentEvent(
                        event_id=f"ev_{uuid.uuid4().hex[:8]}",
                        trace_id=session_id,
                        span_id=tool_span,
                        parent_span_id=root_span_id,
                        session_id=session_id,
                        agent_id=agent,
                        event_type=EventType.TOOL,
                        name=tool_name,
                        timestamp=start_time + timedelta(seconds=2),
                        duration_ms=210.0,
                        status=EventStatus.ERROR,
                        input={"path": "/secure/system/config.json"},
                        error=ErrorInfo(
                            type="PermissionDeniedError",
                            message=(
                                "Access to path '/secure/system/config.json' "
                                "was denied by security policy"
                            ),
                            retryable=False,
                        ),
                    )
                )
            else:
                events.append(
                    AgentEvent(
                        event_id=f"ev_{uuid.uuid4().hex[:8]}",
                        trace_id=session_id,
                        span_id=tool_span,
                        parent_span_id=root_span_id,
                        session_id=session_id,
                        agent_id=agent,
                        event_type=EventType.TOOL,
                        name=tool_name,
                        timestamp=start_time + timedelta(seconds=2),
                        duration_ms=180.0,
                        status=EventStatus.OK,
                        input={"query": "AOG architecture specification"},
                        output={"matches": 4, "status": "success"},
                    )
                )

                # Child nested tool under the tool
                child_span = f"span_{uuid.uuid4().hex[:8]}"
                events.append(
                    AgentEvent(
                        event_id=f"ev_{uuid.uuid4().hex[:8]}",
                        trace_id=session_id,
                        span_id=child_span,
                        parent_span_id=tool_span,
                        session_id=session_id,
                        agent_id=agent,
                        event_type=EventType.RETRIEVAL,
                        name="fetch_document_chunks",
                        timestamp=start_time + timedelta(seconds=2.5),
                        duration_ms=90.0,
                        status=EventStatus.OK,
                        output={"chunks_retrieved": 3},
                    )
                )

            # 4. Final LLM Response Step
            llm2_span = f"span_{uuid.uuid4().hex[:8]}"
            events.append(
                AgentEvent(
                    event_id=f"ev_{uuid.uuid4().hex[:8]}",
                    trace_id=session_id,
                    span_id=llm2_span,
                    parent_span_id=root_span_id,
                    session_id=session_id,
                    agent_id=agent,
                    event_type=EventType.LLM,
                    name="llm:synthesis",
                    timestamp=start_time + timedelta(seconds=4),
                    duration_ms=620.0,
                    tokens_in=random.randint(500, 2000),
                    tokens_out=random.randint(100, 500),
                    model=random.choice(models),
                    provider="anthropic",
                    cost_usd=round(random.uniform(0.002, 0.015), 4),
                )
            )

            res = await service.ingest_batch(events)
            print(f"  [OK] Session {session_id} ({agent}) - {res.accepted} events ingested")

    print("[DONE] Demo seeding finished successfully!")


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
