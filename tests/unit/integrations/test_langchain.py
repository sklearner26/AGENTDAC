"""Tests for callback metadata and explicit callback parent relationships."""

from collections.abc import Sequence
from uuid import uuid4

from aog.client import AOG
from aog.events.models import AgentEvent
from aog.exporters.base import Exporter
from aog.integrations.langchain import AgentDACCallbackHandler


class ListExporter(Exporter):
    def __init__(self) -> None:
        self.events: list[AgentEvent] = []

    def export(self, batch: Sequence[AgentEvent]) -> None:
        self.events.extend(batch)

    def shutdown(self) -> None:
        pass


def test_callback_preserves_parent_and_operational_metadata() -> None:
    exporter = ListExporter()
    callback = AgentDACCallbackHandler(AOG(agent_id="agent-1", exporter=exporter))
    chain_id, tool_id = uuid4(), uuid4()

    callback.on_chain_start(
        {"name": "graph_node"},
        {"query": "hello"},
        run_id=chain_id,
        tags=["production"],
        metadata={"reason": "answer user", "skill": "research"},
    )
    callback.on_tool_start(
        {"name": "search"},
        "hello",
        run_id=tool_id,
        parent_run_id=chain_id,
        metadata={"reason": "retrieve sources"},
    )
    callback.on_tool_end("result", run_id=tool_id)
    callback.on_chain_end({"answer": "done"}, run_id=chain_id)

    tool_event = next(event for event in exporter.events if event.name == "search")
    chain_event = next(event for event in exporter.events if event.name == "graph_node")
    assert tool_event.parent_span_id == chain_event.span_id
    assert tool_event.attributes["tool"] == "search"
    assert tool_event.attributes["reason"] == "retrieve sources"
    assert chain_event.attributes["skill"] == "research"
    assert chain_event.duration_ms is not None
