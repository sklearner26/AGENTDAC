"""Integration test for AgentDAC public SDK interface."""

from collections.abc import Sequence

from agentdac import AgentDAC, AgentEvent, EventType
from aog.exporters.base import Exporter


class MemoryExporter(Exporter):
    def __init__(self) -> None:
        self.events: list[AgentEvent] = []

    def export(self, events: Sequence[AgentEvent]) -> None:
        self.events.extend(events)

    def shutdown(self) -> None:
        pass


def test_agentdac_full_instrumentation_flow() -> None:
    mem = MemoryExporter()
    aog = AgentDAC(exporter=mem, agent_id="demo_agent")

    @aog.tool(name="calc_add")
    def add(a: int, b: int) -> int:
        return a + b

    @aog.observe(name="custom_task")
    def do_task() -> str:
        return "done"

    with aog.session(session_id="ses_123", metadata={"env": "test"}):
        with aog.agent("planner"):
            with aog.llm(model="gpt-4o", provider="openai") as llm_span:
                llm_span.set_tokens(100, 50)
                llm_span.set_cost(0.001)

            res = add(10, 20)
            assert res == 30

            task_res = do_task()
            assert task_res == "done"

        # Record immediate one-off event
        aog.record(event_type=EventType.STATE_CHANGE, name="checkpoint", input_data={"step": 1})

    assert len(mem.events) >= 6
