"""Analytics endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from aog.backend.api.events import get_db
from aog.backend.models.schemas import (
    ErrorStat,
    ModelUsageStat,
    OverviewAnalytics,
    ToolUsageStat,
)
from aog.backend.services.analytics import AnalyticsService

router = APIRouter(prefix="/v1/analytics", tags=["Analytics"])


@router.get("/overview", response_model=OverviewAnalytics)
async def get_overview(db: AsyncSession = Depends(get_db)) -> OverviewAnalytics:
    service = AnalyticsService(db)
    return await service.get_overview()


@router.get("/tools", response_model=list[ToolUsageStat])
async def get_tools_analytics(db: AsyncSession = Depends(get_db)) -> list[ToolUsageStat]:
    service = AnalyticsService(db)
    return await service.get_tools_analytics()


@router.get("/models", response_model=list[ModelUsageStat])
async def get_models_analytics(db: AsyncSession = Depends(get_db)) -> list[ModelUsageStat]:
    service = AnalyticsService(db)
    return await service.get_models_analytics()


@router.get("/errors", response_model=list[ErrorStat])
async def get_errors_analytics(db: AsyncSession = Depends(get_db)) -> list[ErrorStat]:
    service = AnalyticsService(db)
    return await service.get_errors_analytics()
