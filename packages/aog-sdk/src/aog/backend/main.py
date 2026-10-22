"""Main entry point for AgentDAC FastAPI Backend Server."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aog.backend.api.analytics import router as analytics_router
from aog.backend.api.chat import router as chat_router
from aog.backend.api.events import router as events_router
from aog.backend.api.health import router as health_router
from aog.backend.api.integrations import router as integrations_router
from aog.backend.api.sessions import router as sessions_router
from aog.backend.api.traces import router as traces_router
from aog.backend.config import settings
from aog.backend.models.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager initializing database tables on startup."""
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AgentDAC Ingestion and Visualization API",
    lifespan=lifespan,
)

# CORS middleware for frontend React dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(events_router)
app.include_router(sessions_router)
app.include_router(traces_router)
app.include_router(analytics_router)
app.include_router(chat_router)
app.include_router(integrations_router)
