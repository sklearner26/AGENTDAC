"""Trace and Span inspection API endpoints."""

from datetime import UTC
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from aog.backend.api.events import get_db
from aog.backend.models.schemas import TraceGraphResponse
from aog.backend.repositories.sessions import SessionRepository
from aog.backend.repositories.spans import SpanRepository
from aog.backend.services.trace_builder import TraceService

router = APIRouter(prefix="/v1", tags=["Traces"])


@router.get("/sessions/{session_id}/trace", response_model=TraceGraphResponse)
async def get_session_trace(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> TraceGraphResponse:
    """Reconstruct execution DAG and return nodes & edges for graph visualization."""
    service = TraceService(db)
    target_id = session_id
    if session_id == "latest":
        repo = SessionRepository(db)
        latest = await repo.get_latest_summary()
        if not latest:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sessions found")
        target_id = latest.id
    return await service.get_session_trace(target_id)


@router.get("/spans/{span_id}")
async def get_span(
    span_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve full span payload, including inputs, outputs, errors, and attributes."""
    repo = SpanRepository(db)
    span = await repo.get_by_id(span_id)
    if span is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Span not found")

    start_dt = (
        span.started_at.replace(tzinfo=UTC) if span.started_at.tzinfo is None else span.started_at
    )
    end_dt = (
        span.ended_at.replace(tzinfo=UTC)
        if span.ended_at and span.ended_at.tzinfo is None
        else span.ended_at
    )
    duration_ms = (end_dt - start_dt).total_seconds() * 1000.0 if end_dt else None

    return {
        "id": span.id,
        "trace_id": span.trace_id,
        "session_id": span.session_id,
        "parent_span_id": span.parent_span_id,
        "agent_id": span.agent_id,
        "event_type": span.event_type,
        "name": span.name,
        "started_at": span.started_at.isoformat(),
        "ended_at": span.ended_at.isoformat() if span.ended_at else None,
        "duration_ms": round(duration_ms, 2) if duration_ms is not None else None,
        "status": span.status,
        "input": span.input_json,
        "output": span.output_json,
        "attributes": span.attributes_json,
        "tokens_in": span.tokens_in,
        "tokens_out": span.tokens_out,
        "model": span.model,
        "provider": span.provider,
        "cost_usd": span.cost_usd,
        "error": span.error_json,
    }
