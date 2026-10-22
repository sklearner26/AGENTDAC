"""Repository for sessions and session aggregation queries."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from aog.backend.models.db import AgentRecord, EventRecord, SessionRecord, SpanRecord
from aog.backend.models.schemas import SessionSummary


class SessionRepository:
    """Manages session records and queries."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, session_id: str) -> SessionRecord | None:
        result = await self.db.execute(select(SessionRecord).where(SessionRecord.id == session_id))
        return result.scalar_one_or_none()

    async def upsert_session(
        self,
        session_id: str,
        agent_id: str,
        timestamp: datetime,
        status: str = "RUNNING",
        metadata: dict[str, Any] | None = None,
    ) -> SessionRecord:
        record = await self.get_by_id(session_id)
        if record is None:
            # Ensure agent exists
            agent = await self.db.get(AgentRecord, agent_id)
            if agent is None:
                agent = AgentRecord(id=agent_id, name=agent_id)
                self.db.add(agent)

            record = SessionRecord(
                id=session_id,
                agent_id=agent_id,
                started_at=timestamp,
                status=status,
                metadata_json=metadata or {},
            )
            self.db.add(record)
        else:
            if status != "RUNNING":
                record.status = status
                record.ended_at = max(record.ended_at or timestamp, timestamp)
            if metadata:
                record.metadata_json.update(metadata)
        return record

    async def get_summary(self, session_id: str) -> SessionSummary | None:
        """Get summary for a single session."""
        session = await self.get_by_id(session_id)
        if not session:
            return None

        event_count_stmt = select(func.count(EventRecord.id)).where(
            EventRecord.session_id == session.id
        )
        ev_count = (await self.db.execute(event_count_stmt)).scalar() or 0

        tokens_expr = func.coalesce(SpanRecord.tokens_in, 0) + func.coalesce(
            SpanRecord.tokens_out, 0
        )
        tokens_stmt = select(
            func.sum(tokens_expr),
            func.sum(func.coalesce(SpanRecord.cost_usd, 0.0)),
        ).where(SpanRecord.session_id == session.id)
        token_res = (await self.db.execute(tokens_stmt)).first()
        tot_tokens = int(token_res[0] or 0) if token_res else 0
        tot_cost = float(token_res[1] or 0.0) if token_res else None

        started = (
            session.started_at.replace(tzinfo=UTC)
            if session.started_at.tzinfo is None
            else session.started_at
        )
        ended = (
            session.ended_at.replace(tzinfo=UTC)
            if session.ended_at and session.ended_at.tzinfo is None
            else session.ended_at
        )
        duration_s = (
            (ended - started).total_seconds()
            if ended
            else (datetime.now(UTC) - started).total_seconds()
        )

        return SessionSummary(
            id=session.id,
            agent_id=session.agent_id,
            started_at=session.started_at,
            ended_at=session.ended_at,
            duration_s=round(duration_s, 2),
            status=session.status,
            event_count=ev_count,
            total_tokens=tot_tokens,
            cost_usd=round(tot_cost, 4) if tot_cost else None,
            metadata=session.metadata_json,
        )

    async def get_latest_summary(self) -> SessionSummary | None:
        """Get summary for the most recently started session."""
        query = select(SessionRecord).order_by(desc(SessionRecord.started_at)).limit(1)
        res = await self.db.execute(query)
        session = res.scalar_one_or_none()
        if not session:
            return None
        return await self.get_summary(session.id)

    async def list_summaries(
        self,
        agent_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SessionSummary], int]:
        query = select(SessionRecord)
        if agent_id:
            query = query.where(SessionRecord.agent_id == agent_id)
        if status:
            query = query.where(SessionRecord.status == status)

        count_stmt = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        query = query.order_by(desc(SessionRecord.started_at)).limit(limit).offset(offset)
        sessions = (await self.db.execute(query)).scalars().all()

        summaries: list[SessionSummary] = []
        for s in sessions:
            event_count_stmt = select(func.count(EventRecord.id)).where(
                EventRecord.session_id == s.id
            )
            ev_count = (await self.db.execute(event_count_stmt)).scalar() or 0

            tokens_expr = func.coalesce(SpanRecord.tokens_in, 0) + func.coalesce(
                SpanRecord.tokens_out, 0
            )
            tokens_stmt = select(
                func.sum(tokens_expr),
                func.sum(func.coalesce(SpanRecord.cost_usd, 0.0)),
            ).where(SpanRecord.session_id == s.id)
            token_res = (await self.db.execute(tokens_stmt)).first()
            tot_tokens = int(token_res[0] or 0) if token_res else 0
            tot_cost = float(token_res[1] or 0.0) if token_res else None

            started = (
                s.started_at.replace(tzinfo=UTC) if s.started_at.tzinfo is None else s.started_at
            )
            ended = (
                s.ended_at.replace(tzinfo=UTC)
                if s.ended_at and s.ended_at.tzinfo is None
                else s.ended_at
            )
            duration_s = (
                (ended - started).total_seconds()
                if ended
                else (datetime.now(UTC) - started).total_seconds()
            )

            summaries.append(
                SessionSummary(
                    id=s.id,
                    agent_id=s.agent_id,
                    started_at=s.started_at,
                    ended_at=s.ended_at,
                    duration_s=round(duration_s, 2),
                    status=s.status,
                    event_count=ev_count,
                    total_tokens=tot_tokens,
                    cost_usd=round(tot_cost, 4) if tot_cost else None,
                    metadata=s.metadata_json,
                )
            )
        return summaries, total
