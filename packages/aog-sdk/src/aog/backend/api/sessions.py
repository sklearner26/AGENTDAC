"""Session query API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from aog.backend.api.events import get_db
from aog.backend.models.schemas import SessionListResponse, SessionSummary
from aog.backend.repositories.events import EventRepository
from aog.backend.repositories.sessions import SessionRepository

router = APIRouter(prefix="/v1", tags=["Sessions"])


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    agent_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> SessionListResponse:
    """List sessions with optional filters."""
    repo = SessionRepository(db)
    summaries, total = await repo.list_summaries(
        agent_id=agent_id, status=status_filter, limit=limit, offset=offset
    )
    return SessionListResponse(sessions=summaries, total=total)


@router.get("/sessions/latest", response_model=SessionSummary)
async def get_latest_session(
    db: AsyncSession = Depends(get_db),
) -> SessionSummary:
    """Retrieve the most recent execution session."""
    repo = SessionRepository(db)
    summary = await repo.get_latest_summary()
    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sessions found")
    return summary


@router.get("/sessions/{session_id}", response_model=SessionSummary)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> SessionSummary:
    """Retrieve details for a single execution session."""
    repo = SessionRepository(db)
    if session_id == "latest":
        summary = await repo.get_latest_summary()
    else:
        summary = await repo.get_summary(session_id)
    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return summary


@router.get("/sessions/{session_id}/events")
async def get_session_events(
    session_id: str,
    limit: int = Query(default=500, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Retrieve raw events emitted in a session."""
    repo = EventRepository(db)
    records = await repo.list_by_session(session_id, limit=limit, offset=offset)
    return [r.payload_json for r in records]
