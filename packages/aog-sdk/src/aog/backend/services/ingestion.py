"""Ingestion service for batch event processing and persistence."""

from datetime import UTC, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from aog.backend.models.schemas import IngestResponse
from aog.backend.repositories.events import EventRepository
from aog.backend.repositories.sessions import SessionRepository
from aog.backend.repositories.spans import SpanRepository
from aog.events.models import AgentEvent


class IngestionService:
    """Processes incoming batches of AgentEvents idempotently."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.events_repo = EventRepository(db)
        self.sessions_repo = SessionRepository(db)
        self.spans_repo = SpanRepository(db)

    async def ingest_batch(self, events: list[AgentEvent]) -> IngestResponse:
        accepted = 0
        duplicates = 0
        rejected = 0

        seen_event_ids: set[str] = set()
        for ev in events:
            # 1. Idempotency check on raw event (batch and database)
            if ev.event_id in seen_event_ids:
                duplicates += 1
                continue
            seen_event_ids.add(ev.event_id)

            existing = await self.events_repo.get_by_id(ev.event_id)
            if existing is not None:
                duplicates += 1
                continue

            ts = ev.timestamp.replace(tzinfo=UTC) if ev.timestamp.tzinfo is None else ev.timestamp
            event_status = str(ev.status).upper()
            is_session_end = str(ev.event_type) == "session" and ev.duration_ms is not None
            session_status = (
                "ERROR"
                if event_status == "ERROR"
                else "SUCCESS"
                if is_session_end
                else "RUNNING"
            )
            session_timestamp = (
                ts + timedelta(milliseconds=ev.duration_ms or 0) if is_session_end else ts
            )

            # 2. Persist raw event
            await self.events_repo.create_event(
                event_id=ev.event_id,
                trace_id=ev.trace_id,
                span_id=ev.span_id,
                session_id=ev.session_id,
                agent_id=ev.agent_id,
                event_type=str(ev.event_type),
                name=ev.name,
                timestamp=ts,
                payload=ev.model_dump(mode="json"),
            )

            # 3. Upsert execution session
            await self.sessions_repo.upsert_session(
                session_id=ev.session_id,
                agent_id=ev.agent_id,
                timestamp=session_timestamp,
                status=session_status,
                metadata=ev.attributes,
            )

            # 4. Upsert span record
            await self.spans_repo.upsert_span(
                span_id=ev.span_id,
                trace_id=ev.trace_id,
                session_id=ev.session_id,
                parent_span_id=ev.parent_span_id,
                agent_id=ev.agent_id,
                event_type=str(ev.event_type),
                name=ev.name,
                timestamp=ts,
                status=event_status,
                input_data=ev.input,
                output_data=ev.output,
                attributes=ev.attributes,
                tokens_in=ev.tokens_in,
                tokens_out=ev.tokens_out,
                model=ev.model,
                provider=ev.provider,
                cost_usd=ev.cost_usd,
                error=ev.error.model_dump(mode="json") if ev.error else None,
                duration_ms=ev.duration_ms,
            )
            accepted += 1

        await self.db.commit()
        return IngestResponse(accepted=accepted, duplicates=duplicates, rejected=rejected)
