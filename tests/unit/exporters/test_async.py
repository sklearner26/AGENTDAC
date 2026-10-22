"""Unit tests for the asynchronous batching exporter."""

import threading

import pytest
from aog.exporters import AsyncExporter, Exporter

# Keep retry tests quick while still exercising real backoff sleeps.
FAST = {"backoff_base_s": 0.001}


class RecordingSink:
    """A sink that records the batches it is given."""

    def __init__(self) -> None:
        self.batches: list[list] = []
        self.shutdown_count = 0
        self._lock = threading.Lock()

    def export(self, events) -> None:
        with self._lock:
            self.batches.append(list(events))

    def shutdown(self) -> None:
        with self._lock:
            self.shutdown_count += 1

    @property
    def delivered(self) -> list:
        with self._lock:
            return [event for batch in self.batches for event in batch]


class GatedSink(RecordingSink):
    """A sink that blocks inside its first ``export`` until released.

    Lets a test know precisely when the worker has committed to a batch, which
    makes batching and overflow behaviour deterministic.
    """

    def __init__(self) -> None:
        super().__init__()
        self.entered = threading.Event()
        self.release = threading.Event()
        self._first = True

    def export(self, events) -> None:
        if self._first:
            self._first = False
            self.entered.set()
            self.release.wait(timeout=5)
        super().export(events)


class FlakySink(RecordingSink):
    """A sink that raises for its first ``fail_times`` attempts."""

    def __init__(self, fail_times: int) -> None:
        super().__init__()
        self.fail_times = fail_times
        self.attempts = 0

    def export(self, events) -> None:
        self.attempts += 1
        if self.attempts <= self.fail_times:
            raise RuntimeError("transport unavailable")
        super().export(events)


class TestAsyncExporterProtocol:
    """Tests that AsyncExporter honours the Exporter protocol."""

    def test_satisfies_exporter_protocol(self):
        """AsyncExporter is usable wherever an Exporter is expected."""
        sink = RecordingSink()
        exporter = AsyncExporter(sink)
        try:
            assert isinstance(exporter, Exporter)
        finally:
            exporter.shutdown()


class TestAsyncExporterDelivery:
    """Tests for successful delivery."""

    def test_submitted_events_reach_the_sink(self, make_event):
        """Every submitted event is delivered exactly once."""
        sink = RecordingSink()
        exporter = AsyncExporter(sink, flush_interval_ms=10)
        try:
            events = [make_event(name=f"event-{i}") for i in range(5)]
            for event in events:
                assert exporter.submit(event) is True

            exporter.flush(timeout=5)
        finally:
            exporter.shutdown()

        assert len(sink.delivered) == 5
        assert {event.name for event in sink.delivered} == {f"event-{i}" for i in range(5)}

    def test_export_accepts_a_batch(self, make_event):
        """The protocol method queues every event in the batch."""
        sink = RecordingSink()
        exporter = AsyncExporter(sink, flush_interval_ms=10)
        try:
            exporter.export([make_event(name="a"), make_event(name="b")])
            exporter.flush(timeout=5)
        finally:
            exporter.shutdown()

        assert len(sink.delivered) == 2

    def test_no_batch_exceeds_batch_size(self, make_event):
        """A batch never grows beyond the configured maximum."""
        sink = RecordingSink()
        exporter = AsyncExporter(sink, batch_size=2, flush_interval_ms=10)
        try:
            for i in range(5):
                exporter.submit(make_event(name=f"e{i}"))
            exporter.flush(timeout=5)
        finally:
            exporter.shutdown()

        assert len(sink.delivered) == 5
        assert max(len(batch) for batch in sink.batches) <= 2

    def test_queued_events_coalesce_into_one_batch(self, make_event):
        """Events waiting while a batch is in flight are drained together."""
        sink = GatedSink()
        exporter = AsyncExporter(sink, batch_size=10, flush_interval_ms=2000)
        try:
            assert exporter.submit(make_event(name="first")) is True
            # The worker has collected its first (single-event) batch and is
            # now parked inside export().
            assert sink.entered.wait(timeout=5)

            for i in range(4):
                exporter.submit(make_event(name=f"queued-{i}"))

            sink.release.set()
            exporter.flush(timeout=5)
        finally:
            sink.release.set()
            exporter.shutdown()

        assert [len(batch) for batch in sink.batches] == [1, 4]

    def test_flush_returns_when_the_queue_is_drained(self, make_event):
        """After flush, nothing is left pending."""
        sink = RecordingSink()
        exporter = AsyncExporter(sink, flush_interval_ms=10)
        try:
            exporter.submit(make_event())
            exporter.flush(timeout=5)

            assert exporter.pending_count == 0
        finally:
            exporter.shutdown()


class TestAsyncExporterOverflow:
    """Tests for bounded-queue behaviour."""

    def test_overflow_drops_instead_of_blocking(self, make_event):
        """A full queue rejects the event rather than blocking the producer."""
        sink = GatedSink()
        exporter = AsyncExporter(sink, queue_size=1, flush_interval_ms=2000)
        try:
            assert exporter.submit(make_event()) is True
            assert sink.entered.wait(timeout=5)  # worker holds one event

            assert exporter.submit(make_event()) is True  # fills the queue
            assert exporter.submit(make_event()) is False  # dropped

            assert exporter.dropped_count == 1
        finally:
            sink.release.set()
            exporter.shutdown()

    def test_submit_after_shutdown_is_dropped(self, make_event):
        """Events offered after shutdown are dropped, not buffered forever."""
        exporter = AsyncExporter(RecordingSink(), flush_interval_ms=10)
        exporter.shutdown()

        assert exporter.submit(make_event()) is False
        assert exporter.dropped_count == 1


class TestAsyncExporterRetry:
    """Tests for retry and backoff."""

    def test_transient_failure_is_retried_until_it_succeeds(self, make_event):
        """One failed attempt is followed by a successful retry."""
        sink = FlakySink(fail_times=1)
        exporter = AsyncExporter(sink, flush_interval_ms=10, max_retries=3, **FAST)
        try:
            exporter.submit(make_event(name="retried"))
            exporter.flush(timeout=5)
        finally:
            exporter.shutdown()

        assert sink.attempts == 2
        assert [event.name for event in sink.delivered] == ["retried"]
        assert exporter.failed_count == 0

    def test_gives_up_after_max_retries_and_counts_the_loss(self, make_event):
        """An unreachable sink exhausts retries and is counted, not raised."""
        sink = FlakySink(fail_times=99)
        exporter = AsyncExporter(sink, flush_interval_ms=10, max_retries=3, **FAST)
        try:
            exporter.submit(make_event())
            exporter.flush(timeout=5)
        finally:
            exporter.shutdown()

        assert sink.attempts == 4  # the initial attempt plus three retries
        assert exporter.failed_count == 1


class TestAsyncExporterFailOpen:
    """Tests that an unhealthy sink never breaks the caller."""

    def test_unavailable_sink_never_raises(self, make_event):
        """Submit, flush and shutdown all stay quiet when the sink is down."""
        sink = FlakySink(fail_times=99)
        exporter = AsyncExporter(sink, flush_interval_ms=10, max_retries=1, **FAST)

        assert exporter.submit(make_event()) is True
        exporter.flush(timeout=5)
        exporter.shutdown()

        assert exporter.failed_count == 1


class TestAsyncExporterShutdown:
    """Tests for graceful shutdown."""

    def test_shutdown_flushes_what_is_still_queued(self, make_event):
        """Events buffered when shutdown starts are still delivered."""
        sink = RecordingSink()
        exporter = AsyncExporter(sink, batch_size=10, flush_interval_ms=2000)

        exporter.export([make_event(name=f"e{i}") for i in range(3)])
        exporter.shutdown()

        assert len(sink.delivered) == 3

    def test_shutdown_closes_the_sink_once(self, make_event):
        """The sink is shut down exactly once, even with repeated calls."""
        sink = RecordingSink()
        exporter = AsyncExporter(sink, flush_interval_ms=10)

        exporter.submit(make_event())
        exporter.shutdown()
        exporter.shutdown()

        assert sink.shutdown_count == 1


class TestAsyncExporterConfiguration:
    """Tests for argument validation."""

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"queue_size": 0}, "queue_size"),
            ({"batch_size": 0}, "batch_size"),
            ({"max_retries": -1}, "max_retries"),
        ],
    )
    def test_invalid_configuration_is_rejected(self, kwargs, message):
        """Nonsensical limits fail loudly at construction time."""
        with pytest.raises(ValueError, match=message):
            AsyncExporter(RecordingSink(), **kwargs)
