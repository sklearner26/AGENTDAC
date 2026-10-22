"""Backend API routes package."""

from aog.backend.api.analytics import router as analytics_router
from aog.backend.api.events import router as events_router
from aog.backend.api.health import router as health_router
from aog.backend.api.sessions import router as sessions_router
from aog.backend.api.traces import router as traces_router

__all__ = [
    "analytics_router",
    "events_router",
    "health_router",
    "sessions_router",
    "traces_router",
]
