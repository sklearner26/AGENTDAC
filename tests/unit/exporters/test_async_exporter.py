"""Unit tests for AsyncExporter buffering, batching, retry, and fail-open."""

from collections.abc import Sequence

from aog.events.enums import EventType
from aog.events.models import AgentEvent
from aog.exporters.async_exporter import AsyncExporter
from aog.exporters.base import Exporter


def _make_event(name: str) -> AgentEvent:
    return AgentEvent(
        event_id=f"ev_{name}",
        trace_id="tr1",
        span_id=f"sp_{name}",
        session_id="ses1",
        agent_id="ag1",
        event_type=EventType.TOOL,
        name=name,
    )


class RecordingSink(Exporter):
    def __init__(self, fail_count: int = 0) -> None:
        self.fail_count = fail_count
        self.attempts = 0
        self.exported: list[AgentEvent] = []

    def export(self, events: Sequence[AgentEvent]) -> None:
        self.attempts += 1
        if self.attempts <= self.fail_count:
            raise ConnectionError("Simulated network outage")
        self.exported.extend(events)

    def shutdown(self) -> None:
        pass


class TestAsyncExporter:
    def test_batches_delivered_to_sink(self) -> None:
        sink = RecordingSink()
        exporter = AsyncExporter(
            sink=sink,
            batch_size=5,
            flush_interval_ms=50,
        )

        for i in range(12):
            exporter.submit(_make_event(f"e{i}"))

        exporter.flush(timeout=2.0)
        assert len(sink.exported) == 12
        exporter.shutdown()

    def test_retry_on_transient_failure(self) -> None:
        sink = RecordingSink(fail_count=2)
        exporter = AsyncExporter(
            sink=sink,
            batch_size=10,
            flush_interval_ms=20,
            max_retries=3,
            backoff_base_s=0.01,
        )

        for i in range(5):
            exporter.submit(_make_event(f"e{i}"))

        exporter.flush(timeout=2.0)
        assert len(sink.exported) == 5
        assert sink.attempts == 3  # 2 failures + 1 success
        exporter.shutdown()

    def test_queue_overflow_drops_events_fail_open(self) -> None:
        sink = RecordingSink()
        exporter = AsyncExporter(
            sink=sink,
            queue_size=3,
            batch_size=5,
            flush_interval_ms=500,  # worker won't drain immediately
        )

        submitted = [exporter.submit(_make_event(f"e{i}")) for i in range(10)]
        assert exporter.dropped_count > 0
        assert False in submitted
        exporter.shutdown(timeout=2.0)
