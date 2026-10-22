"""Pydantic schemas for API request validation and response models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from aog.events.models import AgentEvent


class IngestRequest(BaseModel):
    events: list[AgentEvent] = Field(default_factory=list)


class IngestResponse(BaseModel):
    accepted: int = 0
    duplicates: int = 0
    rejected: int = 0


class SessionSummary(BaseModel):
    id: str
    agent_id: str
    started_at: datetime
    ended_at: datetime | None = None
    duration_s: float | None = None
    status: str
    event_count: int = 0
    total_tokens: int = 0
    cost_usd: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionListResponse(BaseModel):
    sessions: list[SessionSummary]
    total: int


class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    status: str
    started_at: str
    ended_at: str | None = None
    duration_ms: float | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    cost_usd: float | None = None
    model: str | None = None
    provider: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str = "parent"
    label: str | None = None
    reason: str | None = None


class TraceGraphResponse(BaseModel):
    session: SessionSummary | None = None
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


class OverviewAnalytics(BaseModel):
    total_sessions: int = 0
    success_rate: float = 0.0
    error_rate: float = 0.0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_session_duration_s: float = 0.0


class ToolUsageStat(BaseModel):
    name: str
    count: int
    avg_duration_ms: float
    p95_duration_ms: float
    error_count: int


class ModelUsageStat(BaseModel):
    model: str
    calls: int
    tokens_in: int
    tokens_out: int
    cost_usd: float


class ErrorStat(BaseModel):
    error_type: str
    message: str
    count: int
    last_occurred: datetime
