"""Unit tests for Span creation, lifecycle, and nesting."""

from collections.abc import Sequence

from aog.events.enums import EventStatus, EventType
from aog.events.models import AgentEvent
from aog.exporters.base import Exporter
from aog.tracing.lifecycle import SessionContextManager, SpanContextManager
from aog.tracing.span import Span
from aog.tracing.tracer import Tracer


class MemoryExporter(Exporter):
    def __init__(self) -> None:
        self.events: list[AgentEvent] = []

    def export(self, events: Sequence[AgentEvent]) -> None:
        self.events.extend(events)

    def shutdown(self) -> None:
        pass


class TestSpanLifecycle:
    def test_span_finish_computes_duration(self) -> None:
        span = Span(
            span_id="sp1",
            trace_id="tr1",
            session_id="ses1",
            agent_id="ag1",
            name="test_tool",
            event_type=EventType.TOOL,
        )
        span.set_input({"query": "hello"})
        span.set_output({"result": "world"})
        span.set_tokens(10, 20)
        span.set_model("gpt-4", "openai")
        span.set_cost(0.005)

        event = span.finish()
        assert event.span_id == "sp1"
        assert event.trace_id == "tr1"
        assert event.status == EventStatus.OK
        assert event.input == {"query": "hello"}
        assert event.output == {"result": "world"}
        assert event.tokens_in == 10
        assert event.tokens_out == 20
        assert event.model == "gpt-4"
        assert event.provider == "openai"
        assert event.cost_usd == 0.005
        assert event.duration_ms is not None
        assert event.duration_ms >= 0.0

    def test_span_record_error(self) -> None:
        span = Span(
            span_id="sp2",
            trace_id="tr1",
            session_id="ses1",
            agent_id="ag1",
            name="failing_tool",
        )
        try:
            raise ValueError("Something went wrong")
        except ValueError as exc:
            span.record_error(exc, retryable=False)

        event = span.finish()
        assert event.status == EventStatus.ERROR
        assert event.error is not None
        assert event.error.type == "ValueError"
        assert "Something went wrong" in event.error.message
        assert event.error.retryable is False

    def test_nested_spans_in_session(self) -> None:
        exporter = MemoryExporter()
        tracer = Tracer(exporter=exporter, default_agent_id="main_agent")

        with SessionContextManager(tracer=tracer, session_id="sess_123") as session:
            with SpanContextManager(tracer=tracer, name="llm_step", event_type=EventType.LLM) as s1:
                s1.set_tokens(50, 100)

            with (
                SpanContextManager(
                    tracer=tracer, name="tool_parent", event_type=EventType.TOOL
                ) as s2,
                SpanContextManager(
                    tracer=tracer, name="tool_child", event_type=EventType.TOOL
                ) as s3,
            ):
                s3.set_output({"status": "done"})

        # Spans finish in reverse order: s1, s3, s2, session
        assert len(exporter.events) == 4
        names = [e.name for e in exporter.events]
        assert names == ["llm_step", "tool_child", "tool_parent", "session:main_agent"]

        child_evt = next(e for e in exporter.events if e.name == "tool_child")
        parent_evt = next(e for e in exporter.events if e.name == "tool_parent")
        session_evt = next(e for e in exporter.events if e.name == "session:main_agent")

        assert child_evt.parent_span_id == parent_evt.span_id
        assert parent_evt.parent_span_id == session_evt.span_id
        assert session_evt.parent_span_id is None
