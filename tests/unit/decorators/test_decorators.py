"""Unit tests for observe, tool, agent, and llm decorators."""

from collections.abc import Sequence

import pytest
from aog.client import AOG
from aog.events.enums import EventType
from aog.events.models import AgentEvent
from aog.exporters.base import Exporter


class ListExporter(Exporter):
    def __init__(self) -> None:
        self.events: list[AgentEvent] = []

    def export(self, events: Sequence[AgentEvent]) -> None:
        self.events.extend(events)

    def shutdown(self) -> None:
        pass


class TestDecorators:
    def test_sync_function_decoration(self) -> None:
        exporter = ListExporter()
        aog = AOG(exporter=exporter)

        @aog.tool(name="calc_add")
        def add(a: int, b: int) -> int:
            return a + b

        result = add(2, 3)
        assert result == 5
        assert len(exporter.events) == 1
        event = exporter.events[0]
        assert event.name == "calc_add"
        assert event.event_type == EventType.TOOL
        assert event.output == {"data": 5}

    @pytest.mark.asyncio
    async def test_async_function_decoration(self) -> None:
        exporter = ListExporter()
        aog = AOG(exporter=exporter)

        @aog.observe(name="fetch_remote_data", event_type=EventType.RETRIEVAL)
        async def fetch(url: str) -> dict[str, str]:
            return {"url": url, "status": "ok"}

        res = await fetch("https://example.com")
        assert res["status"] == "ok"
        assert len(exporter.events) == 1
        event = exporter.events[0]
        assert event.name == "fetch_remote_data"
        assert event.event_type == EventType.RETRIEVAL

    def test_decorator_captures_exceptions(self) -> None:
        exporter = ListExporter()
        aog = AOG(exporter=exporter)

        @aog.tool(name="error_tool")
        def broken() -> None:
            raise KeyError("missing_key")

        with pytest.raises(KeyError):
            broken()

        assert len(exporter.events) == 1
        assert exporter.events[0].error is not None
        assert exporter.events[0].error.type == "KeyError"
