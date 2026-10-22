"""Unit tests for top-level AOG client interface."""

from collections.abc import Sequence

from aog.client import AOG
from aog.events.enums import EventStatus, EventType
from aog.events.models import AgentEvent
from aog.exporters.base import Exporter


class MemorySink(Exporter):
    def __init__(self) -> None:
        self.events: list[AgentEvent] = []

    def export(self, events: Sequence[AgentEvent]) -> None:
        self.events.extend(events)

    def shutdown(self) -> None:
        pass


class TestAOGClient:
    def test_client_session_and_nested_tools(self) -> None:
        sink = MemorySink()
        aog = AOG(exporter=sink, agent_id="research_bot")

        with aog.session() as session:
            with aog.llm(model="claude-3-7-sonnet", provider="anthropic") as llm_span:
                llm_span.set_tokens(tokens_in=100, tokens_out=50)
                llm_span.set_cost(0.001)

            with aog.tool("fetch_docs") as tool_span:
                tool_span.set_input({"query": "observability"})
                tool_span.set_output({"docs": ["doc1", "doc2"]})

        assert len(sink.events) == 3
        types = [e.event_type for e in sink.events]
        assert EventType.LLM in types
        assert EventType.TOOL in types
        assert EventType.SESSION in types

    def test_client_record_event(self) -> None:
        sink = MemorySink()
        aog = AOG(exporter=sink)

        event = aog.record(
            event_type=EventType.DECISION,
            name="plan_selection",
            input_data={"plan": "fast_search"},
            status=EventStatus.OK,
        )

        assert event.name == "plan_selection"
        assert event.event_type == EventType.DECISION
        assert len(sink.events) == 1
