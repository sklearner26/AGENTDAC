"""Primary client interface for AgentDAC / AOG SDK."""

import atexit
from collections.abc import Callable
from typing import Any, TypeVar

from aog.config import AOGConfig
from aog.decorators.observe import create_observer
from aog.decorators.tool import agent_decorator, llm_decorator, tool_decorator
from aog.events.enums import EventStatus, EventType
from aog.events.models import AgentEvent, ErrorInfo
from aog.exporters.async_exporter import AsyncExporter
from aog.exporters.base import Exporter
from aog.exporters.console import ConsoleExporter
from aog.exporters.http import HTTPExporter
from aog.redaction.rules import RedactionConfig
from aog.redaction.sanitizer import RedactorFunc, Sanitizer
from aog.runtime.manager import RuntimeManager
from aog.tracing.lifecycle import SessionContextManager, SpanContextManager
from aog.tracing.tracer import Tracer

F = TypeVar("F", bound=Callable[..., Any])


class AgentDAC:
    """AgentDAC universal observability client for AI agents."""

    def __init__(
        self,
        endpoint: str | None = None,
        host: str | None = None,
        port: int | None = None,
        auto_start: bool | None = None,
        api_key: str | None = None,
        agent_id: str | None = None,
        fail_open: bool | None = None,
        exporter: Exporter | None = None,
        config: AOGConfig | None = None,
        redaction_config: RedactionConfig | None = None,
        redactor: RedactorFunc | None = None,
        use_console: bool = False,
    ) -> None:
        overrides: dict[str, Any] = {}
        if endpoint is not None:
            overrides["endpoint"] = endpoint
        if host is not None:
            overrides["host"] = host
        if port is not None:
            overrides["port"] = port
        if auto_start is not None:
            overrides["auto_start"] = auto_start
        if api_key is not None:
            overrides["api_key"] = api_key
        if agent_id is not None:
            overrides["agent_id"] = agent_id
        if fail_open is not None:
            overrides["fail_open"] = fail_open
        if redaction_config is not None:
            overrides["redaction"] = redaction_config

        self.config = config or AOGConfig.from_env(**overrides)
        self.sanitizer = Sanitizer(
            config=self.config.redaction,
            custom_redactor=redactor,
        )

        if exporter is not None:
            self.exporter = exporter
        elif use_console:
            self.exporter = AsyncExporter(
                sink=ConsoleExporter(),
                queue_size=self.config.export_queue_size,
                batch_size=self.config.export_batch_size,
                flush_interval_ms=self.config.export_flush_interval_ms,
                max_retries=self.config.export_max_retries,
            )
        else:
            # Managed / Connected HTTP Mode
            runtime_mgr = RuntimeManager.get_instance()
            active_endpoint = runtime_mgr.ensure_backend(self.config)
            self.config.endpoint = active_endpoint

            http_sink = HTTPExporter(
                endpoint=self.config.endpoint,
                api_key=self.config.api_key,
                timeout_s=self.config.export_timeout_s,
            )
            self.exporter = AsyncExporter(
                sink=http_sink,
                queue_size=self.config.export_queue_size,
                batch_size=self.config.export_batch_size,
                flush_interval_ms=self.config.export_flush_interval_ms,
                max_retries=self.config.export_max_retries,
            )

        self.tracer = Tracer(
            exporter=self.exporter,
            sanitizer=self.sanitizer,
            default_agent_id=self.config.agent_id,
            fail_open=self.config.fail_open,
        )

        # Register auto-flush on python exit
        atexit.register(self.flush)

    def session(
        self,
        agent_id: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SessionContextManager:
        """Create an execution session context manager."""
        return SessionContextManager(
            tracer=self.tracer,
            session_id=session_id,
            agent_id=agent_id or self.config.agent_id,
            metadata=metadata,
        )

    def span(
        self,
        name: str,
        event_type: EventType = EventType.TOOL,
        attributes: dict[str, Any] | None = None,
        input_data: Any = None,
    ) -> SpanContextManager:
        """Create a generic span context manager."""
        return SpanContextManager(
            tracer=self.tracer,
            name=name,
            event_type=event_type,
            attributes=attributes,
            input_data=input_data,
        )

    def tool(
        self,
        name_or_func: str | Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        attributes: dict[str, Any] | None = None,
        input_data: Any = None,
    ) -> Any:
        """Tool helper: usable as context manager or decorator."""
        if callable(name_or_func):
            return tool_decorator(lambda: self.tracer, name=name, attributes=attributes)(
                name_or_func
            )

        tool_name = str(name_or_func) if name_or_func is not None else (name or "unnamed_tool")
        return SpanContextManager(
            tracer=self.tracer,
            name=tool_name,
            event_type=EventType.TOOL,
            attributes=attributes,
            input_data=input_data,
        )

    def skill(
        self,
        name_or_func: str | Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        version: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Any:
        """Skill helper: usable as context manager or decorator."""
        attrs = dict(attributes or {})
        if version:
            attrs["version"] = version

        if callable(name_or_func):
            return create_observer(
                lambda: self.tracer,
                name=name,
                event_type=EventType.SKILL,
                attributes=attrs,
            )(name_or_func)

        skill_name = str(name_or_func) if name_or_func is not None else (name or "unnamed_skill")
        return SpanContextManager(
            tracer=self.tracer,
            name=skill_name,
            event_type=EventType.SKILL,
            attributes=attrs,
        )

    def agent(
        self,
        name_or_func: str | Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Any:
        """Agent helper: usable as context manager or decorator."""
        if callable(name_or_func):
            return agent_decorator(lambda: self.tracer, name=name, attributes=attributes)(
                name_or_func
            )

        agent_name = (
            str(name_or_func) if name_or_func is not None else (name or self.config.agent_id)
        )
        return SpanContextManager(
            tracer=self.tracer,
            name=agent_name,
            event_type=EventType.AGENT,
            attributes=attributes,
        )

    def llm(
        self,
        func: Callable[..., Any] | None = None,
        *,
        model: str = "default-model",
        provider: str | None = None,
        name: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Any:
        """LLM helper: usable as context manager or decorator."""
        attrs = dict(attributes or {})
        attrs["model"] = model
        if provider:
            attrs["provider"] = provider

        if callable(func):
            return llm_decorator(
                lambda: self.tracer,
                name=name,
                model=model,
                provider=provider,
                attributes=attrs,
            )(func)

        span_name = name or f"llm:{model}"
        return SpanContextManager(
            tracer=self.tracer,
            name=span_name,
            event_type=EventType.LLM,
            attributes=attrs,
        )

    def observe(
        self,
        func: F | None = None,
        *,
        name: str | None = None,
        event_type: EventType = EventType.TOOL,
        attributes: dict[str, Any] | None = None,
    ) -> Any:
        """Observe decorator for any function."""
        dec = create_observer(
            lambda: self.tracer,
            name=name,
            event_type=event_type,
            attributes=attributes,
        )
        if func is not None and callable(func):
            return dec(func)
        return dec

    def record(
        self,
        event_type: EventType | str = EventType.TOOL,
        name: str = "event",
        status: EventStatus | str = EventStatus.OK,
        input_data: Any = None,
        output_data: Any = None,
        attributes: dict[str, Any] | None = None,
        duration_ms: float | None = None,
        tokens_in: int | None = None,
        tokens_out: int | None = None,
        model: str | None = None,
        provider: str | None = None,
        cost_usd: float | None = None,
        error: ErrorInfo | None = None,
        event_id: str | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        parent_span_id: str | None = None,
        session_id: str | None = None,
        agent_id: str | None = None,
        timestamp: Any = None,
    ) -> AgentEvent:
        """Record an immediate one-off execution event."""
        typed_event_type = EventType(event_type) if isinstance(event_type, str) else event_type
        typed_status = EventStatus(status) if isinstance(status, str) else status
        return self.tracer.record_event(
            name=name,
            event_type=typed_event_type,
            status=typed_status,
            input_data=input_data,
            output_data=output_data,
            attributes=attributes,
            duration_ms=duration_ms,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            model=model,
            provider=provider,
            cost_usd=cost_usd,
            error=error,
            event_id=event_id,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            session_id=session_id,
            agent_id=agent_id,
            timestamp=timestamp,
        )

    def flush(self, timeout: float | None = None) -> None:
        """Flush any pending buffered events."""
        if hasattr(self.exporter, "flush"):
            self.exporter.flush(timeout=timeout)

    def shutdown(self, timeout: float | None = None) -> None:
        """Gracefully flush and close exporter background threads and connections."""
        self.exporter.shutdown()


# Alias for backward compatibility
AOG = AgentDAC
