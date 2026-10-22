"""AgentDAC Timeline Chatbot API.

Provides a single POST /v1/chat endpoint that accepts a natural-language
question and a session_id (optional). It fetches the raw timeline JSON
from the database, constructs a concise system prompt, and calls an LLM
via the OpenAI-compatible chat completion API.

The endpoint is zero-hallucination by design: the LLM receives only the
actual timeline data and is instructed to answer strictly from it.

Dependencies (optional - endpoint fails gracefully if missing):
    AGENTDAC_CHAT_API_KEY  - API key for the completion provider
    AGENTDAC_CHAT_MODEL    - model name (default: gpt-4o-mini)
    AGENTDAC_CHAT_BASE_URL - base URL (default: https://api.openai.com/v1)
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from aog.backend.api.events import get_db
from aog.backend.repositories.sessions import SessionRepository
from aog.backend.repositories.spans import SpanRepository

router = APIRouter(prefix="/v1", tags=["Chat"])


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None  # if None, uses latest session


class ChatResponse(BaseModel):
    answer: str
    session_id: str | None = None
    context_spans: int = 0


def _build_system_prompt(session_data: dict[str, Any], spans: list[dict[str, Any]]) -> str:
    return (
        "You are the AgentDAC observability assistant. "
        "You have access to the complete execution timeline of an AI agent session. "
        "Answer questions ONLY from the data provided. "
        "Be concise and precise. Never hallucinate. "
        "If information is not in the timeline, say so explicitly.\n\n"
        f"SESSION METADATA:\n{json.dumps(session_data, default=str, indent=2)}\n\n"
        f"EXECUTION TIMELINE ({len(spans)} spans):\n"
        + json.dumps(spans, default=str, indent=2)
    )


async def _call_llm(system: str, question: str) -> str:
    """Call the configured LLM with the timeline context. Fails gracefully."""
    api_key = os.getenv("AGENTDAC_CHAT_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return (
            "Chat requires AGENTDAC_CHAT_API_KEY (or OPENAI_API_KEY) env var. "
            "Set it and restart the AgentDAC backend."
        )

    try:
        model = os.getenv("AGENTDAC_CHAT_MODEL", "gpt-4o-mini")
        base_url = os.getenv("AGENTDAC_CHAT_BASE_URL", "https://api.openai.com/v1")

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": question},
            ],
            "temperature": 0.0,
            "max_tokens": 800,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return str(data["choices"][0]["message"]["content"])
    except Exception as exc:
        return f"LLM call failed: {exc}"


@router.post("/chat", response_model=ChatResponse)
async def chat_with_timeline(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Answer natural-language questions about a session's execution timeline."""
    session_repo = SessionRepository(db)
    span_repo = SpanRepository(db)

    # Resolve session
    if req.session_id:
        session = await session_repo.get_summary(req.session_id)
    else:
        session = await session_repo.get_latest_summary()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No session found. Run an instrumented agent first.",
        )

    # Load spans (truncate to 200 for LLM context budget)
    all_spans = await span_repo.list_by_session(session.id)
    spans_raw = all_spans[:200]
    spans_data = [
        {
            "id": s.id,
            "type": s.event_type,
            "name": s.name,
            "status": s.status,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            "tokens_in": s.tokens_in,
            "tokens_out": s.tokens_out,
            "model": s.model,
            "provider": s.provider,
            "cost_usd": s.cost_usd,
            "input": s.input_json,
            "output": s.output_json,
            "attributes": s.attributes_json,
            "error": s.error_json,
            "parent_span_id": s.parent_span_id,
        }
        for s in spans_raw
    ]

    session_data = session.model_dump(mode="json")
    system_prompt = _build_system_prompt(session_data, spans_data)
    answer = await _call_llm(system_prompt, req.question)

    return ChatResponse(
        answer=answer,
        session_id=session.id,
        context_spans=len(spans_data),
    )
