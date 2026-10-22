"""Event ingestion API endpoint."""

from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from aog.backend.models.db import async_session
from aog.backend.models.schemas import IngestRequest, IngestResponse
from aog.backend.services.ingestion import IngestionService

router = APIRouter(prefix="/v1", tags=["Events"])


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


@router.post("/events", response_model=IngestResponse, status_code=status.HTTP_200_OK)
async def ingest_events(
    payload: IngestRequest,
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    """Accept batches of AgentEvents from instrumented agents."""
    if not payload.events:
        return IngestResponse(accepted=0, duplicates=0, rejected=0)

    service = IngestionService(db)
    return await service.ingest_batch(payload.events)
