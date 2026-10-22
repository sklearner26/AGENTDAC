"""Tool, Agent, and LLM specialized decorators."""

from collections.abc import Callable
from typing import Any, TypeVar

from aog.decorators.observe import create_observer
from aog.events.enums import EventType
from aog.tracing.tracer import Tracer

F = TypeVar("F", bound=Callable[..., Any])


def tool_decorator(
    get_tracer: Callable[[], Tracer | None],
    name: str | None = None,
    attributes: dict[str, Any] | None = None,
) -> Callable[[F], F]:
    """Decorator to instrument tool execution."""
    return create_observer(
        get_tracer,
        name=name,
        event_type=EventType.TOOL,
        attributes=attributes,
    )


def agent_decorator(
    get_tracer: Callable[[], Tracer | None],
    name: str | None = None,
    attributes: dict[str, Any] | None = None,
) -> Callable[[F], F]:
    """Decorator to instrument agent execution."""
    return create_observer(
        get_tracer,
        name=name,
        event_type=EventType.AGENT,
        attributes=attributes,
    )


def llm_decorator(
    get_tracer: Callable[[], Tracer | None],
    name: str | None = None,
    model: str | None = None,
    provider: str | None = None,
    attributes: dict[str, Any] | None = None,
) -> Callable[[F], F]:
    """Decorator to instrument LLM calls."""
    attrs = dict(attributes or {})
    if model:
        attrs["model"] = model
    if provider:
        attrs["provider"] = provider

    return create_observer(
        get_tracer,
        name=name or f"llm:{model or 'model'}",
        event_type=EventType.LLM,
        attributes=attrs,
    )
