"""Repository for spans and trace hierarchy."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aog.backend.models.db import SpanRecord


class SpanRepository:
    """Manages SpanRecord persistence and trace queries."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, span_id: str) -> SpanRecord | None:
        result = await self.db.execute(select(SpanRecord).where(SpanRecord.id == span_id))
        return result.scalar_one_or_none()

    async def upsert_span(
        self,
        span_id: str,
        trace_id: str,
        session_id: str,
        parent_span_id: str | None,
        agent_id: str,
        event_type: str,
        name: str,
        timestamp: datetime,
        status: str = "OK",
        input_data: Any = None,
        output_data: Any = None,
        attributes: dict[str, Any] | None = None,
        tokens_in: int | None = None,
        tokens_out: int | None = None,
        model: str | None = None,
        provider: str | None = None,
        cost_usd: float | None = None,
        error: dict[str, Any] | None = None,
        duration_ms: float | None = None,
    ) -> SpanRecord:
        record = await self.get_by_id(span_id)
        if record is None:
            record = SpanRecord(
                id=span_id,
                trace_id=trace_id,
                session_id=session_id,
                parent_span_id=parent_span_id,
                agent_id=agent_id,
                event_type=event_type,
                name=name,
                started_at=timestamp,
                status=status,
                input_json=input_data
                if isinstance(input_data, dict)
                else ({"value": input_data} if input_data is not None else None),
                output_json=output_data
                if isinstance(output_data, dict)
                else ({"value": output_data} if output_data is not None else None),
                attributes_json=attributes or {},
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                model=model,
                provider=provider,
                cost_usd=cost_usd,
                error_json=error,
            )
            self.db.add(record)
        else:
            # Update existing span record
            record.status = status
            record.ended_at = timestamp
            if output_data is not None:
                record.output_json = (
                    output_data if isinstance(output_data, dict) else {"value": output_data}
                )
            if attributes:
                record.attributes_json.update(attributes)
            if tokens_in is not None:
                record.tokens_in = tokens_in
            if tokens_out is not None:
                record.tokens_out = tokens_out
            if model is not None:
                record.model = model
            if provider is not None:
                record.provider = provider
            if cost_usd is not None:
                record.cost_usd = cost_usd
            if error is not None:
                record.error_json = error

        return record

    async def list_by_session(self, session_id: str) -> list[SpanRecord]:
        query = (
            select(SpanRecord)
            .where(SpanRecord.session_id == session_id)
            .order_by(SpanRecord.started_at)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_trace(self, trace_id: str) -> list[SpanRecord]:
        query = (
            select(SpanRecord)
            .where(SpanRecord.trace_id == trace_id)
            .order_by(SpanRecord.started_at)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
