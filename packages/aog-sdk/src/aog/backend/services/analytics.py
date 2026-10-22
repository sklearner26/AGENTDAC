"""Analytics service computing aggregated metrics across sessions, tools, and models."""

from datetime import UTC

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from aog.backend.models.db import SessionRecord, SpanRecord
from aog.backend.models.schemas import (
    ErrorStat,
    ModelUsageStat,
    OverviewAnalytics,
    ToolUsageStat,
)
from aog.backend.repositories.sessions import SessionRepository


class AnalyticsService:
    """Computes analytical overviews."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.sessions_repo = SessionRepository(db)

    async def get_overview(self) -> OverviewAnalytics:
        # Total sessions
        total_stmt = select(func.count(SessionRecord.id))
        total_sessions = (await self.db.execute(total_stmt)).scalar() or 0

        if total_sessions == 0:
            return OverviewAnalytics()

        # Success / Error counts
        err_stmt = select(func.count(SessionRecord.id)).where(SessionRecord.status == "ERROR")
        error_sessions = (await self.db.execute(err_stmt)).scalar() or 0
        success_sessions = total_sessions - error_sessions

        # Tokens and costs
        tokens_expr = func.coalesce(SpanRecord.tokens_in, 0) + func.coalesce(
            SpanRecord.tokens_out, 0
        )
        agg_stmt = select(
            func.sum(tokens_expr),
            func.sum(func.coalesce(SpanRecord.cost_usd, 0.0)),
        )
        agg_res = (await self.db.execute(agg_stmt)).first()
        total_tokens = int(agg_res[0] or 0) if agg_res else 0
        total_cost = float(agg_res[1] or 0.0) if agg_res else 0.0

        # Duration averages across all sessions
        summaries, _ = await self.sessions_repo.list_summaries(limit=total_sessions)
        avg_duration = (
            sum(s.duration_s or 0.0 for s in summaries) / len(summaries) if summaries else 0.0
        )

        return OverviewAnalytics(
            total_sessions=total_sessions,
            success_rate=round(success_sessions / total_sessions, 4),
            error_rate=round(error_sessions / total_sessions, 4),
            total_tokens=total_tokens,
            total_cost_usd=round(total_cost, 4),
            avg_session_duration_s=round(avg_duration, 2),
        )

    async def get_tools_analytics(self) -> list[ToolUsageStat]:
        stmt = select(SpanRecord).where(SpanRecord.event_type == "tool")
        spans = (await self.db.execute(stmt)).scalars().all()
        grouped: dict[str, list[SpanRecord]] = {}
        for span in spans:
            grouped.setdefault(span.name, []).append(span)

        tool_stats: list[ToolUsageStat] = []
        for name, tool_spans in sorted(
            grouped.items(), key=lambda item: len(item[1]), reverse=True
        ):
            durations: list[float] = []
            for span in tool_spans:
                duration = self._duration_ms(span)
                if duration is not None:
                    durations.append(duration)
            tool_stats.append(
                ToolUsageStat(
                    name=name,
                    count=len(tool_spans),
                    avg_duration_ms=round(sum(durations) / len(durations), 2) if durations else 0.0,
                    p95_duration_ms=(
                        round(self._percentile(durations, 0.95), 2) if durations else 0.0
                    ),
                    error_count=sum(span.status.upper() == "ERROR" for span in tool_spans),
                )
            )
        return tool_stats

    @staticmethod
    def _duration_ms(span: SpanRecord) -> float | None:
        if span.ended_at is None:
            return None
        started = (
            span.started_at.replace(tzinfo=UTC)
            if span.started_at.tzinfo is None
            else span.started_at
        )
        ended = (
            span.ended_at.replace(tzinfo=UTC)
            if span.ended_at.tzinfo is None
            else span.ended_at
        )
        return max(0.0, (ended - started).total_seconds() * 1000.0)

    @staticmethod
    def _percentile(values: list[float], percentile: float) -> float:
        ordered = sorted(values)
        index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile)))
        return ordered[index]

    async def get_models_analytics(self) -> list[ModelUsageStat]:
        stmt = (
            select(
                SpanRecord.model,
                func.count(SpanRecord.id).label("calls"),
                func.sum(func.coalesce(SpanRecord.tokens_in, 0)).label("tokens_in"),
                func.sum(func.coalesce(SpanRecord.tokens_out, 0)).label("tokens_out"),
                func.sum(func.coalesce(SpanRecord.cost_usd, 0.0)).label("cost"),
            )
            .where(SpanRecord.model.is_not(None))
            .group_by(SpanRecord.model)
            .order_by(desc("calls"))
        )
        results = (await self.db.execute(stmt)).all()

        model_stats: list[ModelUsageStat] = []
        for r in results:
            model_stats.append(
                ModelUsageStat(
                    model=r[0] or "unknown",
                    calls=r[1],
                    tokens_in=int(r[2] or 0),
                    tokens_out=int(r[3] or 0),
                    cost_usd=round(float(r[4] or 0.0), 4),
                )
            )
        return model_stats

    async def get_errors_analytics(self) -> list[ErrorStat]:
        stmt = (
            select(SpanRecord)
            .where(SpanRecord.error_json.is_not(None))
            .order_by(desc(SpanRecord.started_at))
            .limit(100)
        )
        spans = (await self.db.execute(stmt)).scalars().all()

        error_map: dict[str, ErrorStat] = {}
        for s in spans:
            err = s.error_json or {}
            err_type = err.get("type", "Error")
            msg = err.get("message", "Unknown error")
            key = f"{err_type}:{msg}"
            if key in error_map:
                error_map[key].count += 1
            else:
                error_map[key] = ErrorStat(
                    error_type=err_type,
                    message=msg,
                    count=1,
                    last_occurred=s.started_at,
                )
        return list(error_map.values())
