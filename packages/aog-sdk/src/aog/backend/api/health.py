"""Health check endpoint."""

from typing import Any

from fastapi import APIRouter

from aog.backend.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint for runtime manager, container orchestrators and readiness probes."""
    return {
        "status": "ok",
        "service": "agentdac",
        "version": settings.app_version,
    }
