"""Repository for raw event queries and insertions."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aog.backend.models.db import EventRecord


class EventRepository:
    """Manages raw EventRecord persistence and retrieval."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, event_id: str) -> EventRecord | None:
        result = await self.db.execute(select(EventRecord).where(EventRecord.id == event_id))
        return result.scalar_one_or_none()

    async def create_event(
        self,
        event_id: str,
        trace_id: str,
        span_id: str,
        session_id: str,
        agent_id: str,
        event_type: str,
        name: str,
        timestamp: datetime,
        payload: dict[str, Any],
    ) -> EventRecord:
        record = EventRecord(
            id=event_id,
            trace_id=trace_id,
            span_id=span_id,
            session_id=session_id,
            agent_id=agent_id,
            event_type=event_type,
            name=name,
            timestamp=timestamp,
            payload_json=payload,
        )
        self.db.add(record)
        return record

    async def list_by_session(
        self, session_id: str, limit: int = 500, offset: int = 0
    ) -> list[EventRecord]:
        query = (
            select(EventRecord)
            .where(EventRecord.session_id == session_id)
            .order_by(EventRecord.timestamp)
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_trace(self, trace_id: str) -> list[EventRecord]:
        query = (
            select(EventRecord)
            .where(EventRecord.trace_id == trace_id)
            .order_by(EventRecord.timestamp)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
