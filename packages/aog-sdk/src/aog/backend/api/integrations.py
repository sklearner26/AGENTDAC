"""Integration management endpoints for Claude Code CLI."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from aog.backend.api.events import get_db
from aog.backend.repositories.sessions import SessionRepository
from aog.backend.services.ingestion import IngestionService
from integrations.claude_code.adapter import ClaudeCodeAdapter
from integrations.claude_code.setup import (
    configure_claude_hooks,
    get_integration_diagnostics,
    remove_claude_hooks,
)

ACTIVE_SESSION_THRESHOLD_SECONDS = 300

router = APIRouter(prefix="/v1/integrations", tags=["Integrations"])


@router.get("/claude-code/status")
async def get_claude_code_status(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve current connection status, statistics, and diagnostics for Claude Code CLI."""
    diag = get_integration_diagnostics()
    repo = SessionRepository(db)
    summaries, total = await repo.list_summaries(agent_id="claude-code", limit=1)

    latest_session = summaries[0] if summaries else None
    last_activity = latest_session.started_at if latest_session else None
    last_session_id = latest_session.id if latest_session else None

    # Calculate live status
    effective_status = diag["status"]
    if effective_status == "connected" and last_activity:
        activity_time = last_activity if last_activity.tzinfo else last_activity.replace(tzinfo=UTC)
        delta = (datetime.now(UTC) - activity_time).total_seconds()
        if (
            delta < ACTIVE_SESSION_THRESHOLD_SECONDS
            and latest_session
            and latest_session.status.upper() == "RUNNING"
        ):
            effective_status = "running"

    return {
        **diag,
        "status": effective_status,
        "observed_sessions_count": total,
        "last_activity": last_activity.isoformat() if last_activity else None,
        "last_session_id": last_session_id,
        "ingestion_endpoint": "http://localhost:8000/v1/events",
    }


@router.post("/claude-code/configure")
async def configure_integration() -> dict[str, Any]:
    """Configure Claude Code hooks in ~/.claude/settings.json."""
    ok, msg = configure_claude_hooks()
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=msg,
        )
    return {"success": True, "message": msg}


@router.post("/claude-code/disconnect")
async def disconnect_integration() -> dict[str, Any]:
    """Remove AgentDAC hooks from ~/.claude/settings.json."""
    ok, msg = remove_claude_hooks()
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=msg,
        )
    return {"success": True, "message": msg}


@router.post("/claude-code/toggle-pause")
async def toggle_pause() -> dict[str, Any]:
    """Toggle paused state for Claude Code event ingestion."""
    currently_paused = ClaudeCodeAdapter.is_paused()
    new_state = not currently_paused
    ClaudeCodeAdapter.set_paused(new_state)
    return {"paused": new_state}


@router.post("/claude-code/test-event")
async def send_test_event(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Inject a deterministic, realistic Claude Code session fixture for verification."""
    test_session_id = f"test-claude-{uuid4().hex[:8]}"
    tool_use_id = f"toolu_test_{uuid4().hex[:8]}"

    events = []
    # 1. Session start
    events.extend(
        ClaudeCodeAdapter.build_events_from_payload({
            "hook_event_name": "SessionStart",
            "session_id": test_session_id,
            "cwd": "C:/Users/Shreyansh Kesarwani/AGENTDAC",
            "transcript_path": "test/transcript.jsonl",
        })
    )

    # 2. User prompt submit
    events.extend(
        ClaudeCodeAdapter.build_events_from_payload({
            "hook_event_name": "UserPromptSubmit",
            "session_id": test_session_id,
            "prompt": "Inspect project structure and run verification tests",
            "cwd": "C:/Users/Shreyansh Kesarwani/AGENTDAC",
        })
    )

    # 3. Tool PreToolUse
    events.extend(
        ClaudeCodeAdapter.build_events_from_payload({
            "hook_event_name": "PreToolUse",
            "session_id": test_session_id,
            "tool_use_id": tool_use_id,
            "tool_name": "Read",
            "tool_input": {"file_path": "README.md", "limit": 50},
            "cwd": "C:/Users/Shreyansh Kesarwani/AGENTDAC",
        })
    )

    # 4. Tool PostToolUse
    events.extend(
        ClaudeCodeAdapter.build_events_from_payload({
            "hook_event_name": "PostToolUse",
            "session_id": test_session_id,
            "tool_use_id": tool_use_id,
            "tool_name": "Read",
            "tool_input": {"file_path": "README.md", "limit": 50},
            "tool_result": {"status": "success", "lines_read": 50},
            "duration_ms": 24.5,
            "cwd": "C:/Users/Shreyansh Kesarwani/AGENTDAC",
        })
    )

    # 5. Session Stop
    events.extend(
        ClaudeCodeAdapter.build_events_from_payload({
            "hook_event_name": "Stop",
            "session_id": test_session_id,
            "stop_reason": "turn_complete",
            "duration_ms": 1500.0,
            "cwd": "C:/Users/Shreyansh Kesarwani/AGENTDAC",
        })
    )

    service = IngestionService(db)
    result = await service.ingest_batch(events)

    return {
        "success": True,
        "session_id": test_session_id,
        "accepted": result.accepted,
        "duplicates": result.duplicates,
        "message": "Deterministic test Claude Code session generated successfully",
    }
