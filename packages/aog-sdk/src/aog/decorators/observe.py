"""Generic observation decorator for synchronous and asynchronous functions."""

import asyncio
import functools
from collections.abc import Callable
from typing import Any, TypeVar, cast

from aog.events.enums import EventType
from aog.tracing.lifecycle import SpanContextManager
from aog.tracing.tracer import Tracer

F = TypeVar("F", bound=Callable[..., Any])


def create_observer(
    get_tracer: Callable[[], Tracer | None],
    name: str | None = None,
    event_type: EventType = EventType.TOOL,
    attributes: dict[str, Any] | None = None,
) -> Callable[[F], F]:
    """Factory creating an observation decorator."""

    def decorator(func: F) -> F:
        span_name = name or func.__name__

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                tracer = get_tracer()
                if tracer is None:
                    return await func(*args, **kwargs)

                input_payload = {"args": args, "kwargs": kwargs}
                mgr = SpanContextManager(
                    tracer=tracer,
                    name=span_name,
                    event_type=event_type,
                    attributes=attributes,
                    input_data=input_payload,
                )
                async with mgr as span:
                    result = await func(*args, **kwargs)
                    span.set_output(result)
                    return result

            return cast(F, async_wrapper)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer()
            if tracer is None:
                return func(*args, **kwargs)

            input_payload = {"args": args, "kwargs": kwargs}
            mgr = SpanContextManager(
                tracer=tracer,
                name=span_name,
                event_type=event_type,
                attributes=attributes,
                input_data=input_payload,
            )
            with mgr as span:
                result = func(*args, **kwargs)
                span.set_output(result)
                return result

        return cast(F, sync_wrapper)

    return decorator
