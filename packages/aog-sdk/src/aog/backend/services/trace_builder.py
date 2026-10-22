"""Trace service for constructing complete trace execution graphs."""

from sqlalchemy.ext.asyncio import AsyncSession

from aog.backend.models.schemas import TraceGraphResponse
from aog.backend.repositories.sessions import SessionRepository
from aog.backend.repositories.spans import SpanRepository
from aog.backend.services.graph_builder import GraphBuilder


class TraceService:
    """Reconstructs session execution graphs."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.spans_repo = SpanRepository(db)
        self.sessions_repo = SessionRepository(db)

    async def get_session_trace(self, session_id: str) -> TraceGraphResponse:
        spans = await self.spans_repo.list_by_session(session_id)
        session_summary = await self.sessions_repo.get_summary(session_id)
        nodes, edges = GraphBuilder.build_graph(spans)
        return TraceGraphResponse(session=session_summary, nodes=nodes, edges=edges)
