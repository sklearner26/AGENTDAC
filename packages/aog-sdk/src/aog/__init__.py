"""AgentDAC / AOG — Universal Observability Plugin for AI Agents."""

from aog.client import AOG, AgentDAC
from aog.config import AgentDACConfig, AOGConfig
from aog.context import (
    TraceContext,
    get_current_context,
    set_current_context,
    with_context,
)
from aog.events.enums import EventStatus, EventType
from aog.events.models import AgentEvent, ErrorInfo
from aog.exceptions import (
    AOGConfigError,
    AOGContextError,
    AOGError,
    AOGExportError,
    AOGGraphIntegrityError,
    AOGTimeoutError,
    AOGValidationError,
)
from aog.exporters.async_exporter import AsyncExporter
from aog.exporters.base import Exporter
from aog.exporters.console import ConsoleExporter
from aog.exporters.http import HTTPExporter
from aog.redaction.rules import RedactionConfig
from aog.redaction.sanitizer import Sanitizer
from aog.runtime.manager import RuntimeManager
from aog.tracing.lifecycle import SessionContextManager, SpanContextManager
from aog.tracing.span import Span
from aog.tracing.tracer import Tracer

# Aliases for exceptions
AgentDACError = AOGError
AgentDACConfigError = AOGConfigError
AgentDACContextError = AOGContextError
AgentDACExportError = AOGExportError
AgentDACGraphIntegrityError = AOGGraphIntegrityError
AgentDACTimeoutError = AOGTimeoutError
AgentDACValidationError = AOGValidationError

__all__ = [
    "AOG",
    "AOGConfig",
    "AOGConfigError",
    "AOGContextError",
    "AOGError",
    "AOGExportError",
    "AOGGraphIntegrityError",
    "AOGTimeoutError",
    "AOGValidationError",
    "AgentDAC",
    "AgentDACConfig",
    "AgentDACConfigError",
    "AgentDACContextError",
    "AgentDACError",
    "AgentDACExportError",
    "AgentDACGraphIntegrityError",
    "AgentDACTimeoutError",
    "AgentDACValidationError",
    "AgentEvent",
    "AsyncExporter",
    "ConsoleExporter",
    "ErrorInfo",
    "EventStatus",
    "EventType",
    "Exporter",
    "HTTPExporter",
    "RedactionConfig",
    "RuntimeManager",
    "Sanitizer",
    "SessionContextManager",
    "Span",
    "SpanContextManager",
    "TraceContext",
    "Tracer",
    "get_current_context",
    "set_current_context",
    "with_context",
]
