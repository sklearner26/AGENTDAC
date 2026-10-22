"""Asynchronous, batching exporter.

Events are handed to a bounded in-memory queue and drained by a single
background daemon thread, which delivers them to a sink in batches. The
instrumented agent therefore never waits on the network.

The design is deliberately fail-open:

* :meth:`AsyncExporter.submit` never blocks and never raises. If the queue is
  full the event is dropped and counted.
* A sink that raises is retried with exponential backoff; once retries are
  exhausted the batch is abandoned and counted. Nothing propagates to the
  caller.
"""

import contextlib
import queue
import threading
import time
from collections.abc import Sequence

from aog.events.models import AgentEvent
from aog.exporters.base import Exporter

# Defaults from AOG_IMPLEMENTATION.md §14.
DEFAULT_QUEUE_SIZE = 5000
DEFAULT_BATCH_SIZE = 50
DEFAULT_FLUSH_INTERVAL_MS = 500
DEFAULT_MAX_RETRIES = 3

# Stop-signal for the worker loop.
_STOP = object()


class AsyncExporter:
    """Buffer events in a bounded queue and deliver them to a sink in batches.

    Args:
        sink: Destination for batches; any :class:`~aog.exporters.base.Exporter`.
        queue_size: Maximum number of buffered events. Once full, new events are
            dropped (and counted) rather than blocking the producer.
        batch_size: Maximum number of events handed to the sink per call.
        flush_interval_ms: How long the worker waits for a batch to fill before
            delivering what it has.
        max_retries: Retry attempts per batch after the first failure.
        backoff_base_s: Delay before the first retry; doubles each attempt.
        shutdown_timeout_s: How long :meth:`shutdown` waits for the worker.
    """

    def __init__(
        self,
        sink: Exporter,
        *,
        queue_size: int = DEFAULT_QUEUE_SIZE,
        batch_size: int = DEFAULT_BATCH_SIZE,
        flush_interval_ms: int = DEFAULT_FLUSH_INTERVAL_MS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base_s: float = 0.5,
        shutdown_timeout_s: float = 5.0,
    ) -> None:
        if queue_size < 1:
            raise ValueError("queue_size must be at least 1")
        if batch_size < 1:
            raise ValueError("batch_size must be at least 1")
        if max_retries < 0:
            raise ValueError("max_retries must not be negative")

        self._sink = sink
        self._batch_size = batch_size
        self._flush_interval_s = flush_interval_ms / 1000.0
        self._max_retries = max_retries
        self._backoff_base_s = backoff_base_s
        self._shutdown_timeout_s = shutdown_timeout_s

        self._queue: queue.Queue[AgentEvent | object] = queue.Queue(maxsize=queue_size)
        self._stop = threading.Event()
        self._stopped = False
        self._cond = threading.Condition()
        self._pending = 0
        self._dropped = 0
        self._failed = 0

        self._thread = threading.Thread(target=self._run, name="aog-exporter", daemon=True)
        self._thread.start()

    # -- public API ---------------------------------------------------------

    def submit(self, event: AgentEvent) -> bool:
        """Queue one event.

        Returns ``False`` if it was dropped, either because the queue is full or
        because the exporter has already been shut down.
        """
        with self._cond:
            if self._stopped:
                self._dropped += 1
                return False
            self._pending += 1
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            with self._cond:
                self._pending -= 1
                self._dropped += 1
            return False
        return True

    def export(self, events: Sequence[AgentEvent]) -> None:
        """Queue a batch of events; satisfies the :class:`Exporter` protocol."""
        for event in events:
            self.submit(event)

    def flush(self, timeout: float | None = None) -> None:
        """Block until every queued event has been handed to the sink.

        Returns when the timeout expires even if work remains; it never raises.
        """
        with self._cond:
            self._cond.wait_for(lambda: self._pending == 0, timeout=timeout)

    def shutdown(self, timeout: float | None = None) -> None:
        """Stop the worker, deliver what is still queued, and shut the sink down.

        Safe to call more than once.
        """
        with self._cond:
            if self._stopped:
                return
            self._stopped = True

        self._stop.set()
        self._wake_worker()
        self._thread.join(timeout if timeout is not None else self._shutdown_timeout_s)
        self._drain_remaining()
        self._sink.shutdown()

    @property
    def dropped_count(self) -> int:
        """Number of events discarded because the queue was full."""
        with self._cond:
            return self._dropped

    @property
    def failed_count(self) -> int:
        """Number of events abandoned after exhausting retries."""
        with self._cond:
            return self._failed

    @property
    def pending_count(self) -> int:
        """Number of events submitted but not yet delivered."""
        with self._cond:
            return self._pending

    # -- worker internals ---------------------------------------------------

    def _wake_worker(self) -> None:
        """Nudge the worker out of its blocking queue read, if we can."""
        with contextlib.suppress(queue.Full):
            self._queue.put_nowait(_STOP)

    def _run(self) -> None:
        while not self._stop.is_set():
            batch = self._collect_batch()
            if batch:
                self._deliver(batch)
                self._complete(len(batch))

    def _collect_batch(self) -> list[AgentEvent]:
        """Gather up to ``batch_size`` events, waiting at most one flush interval."""
        batch: list[AgentEvent] = []
        try:
            first = self._queue.get(timeout=self._flush_interval_s)
        except queue.Empty:
            return batch

        if not isinstance(first, AgentEvent):
            return batch

        batch.append(first)
        while len(batch) < self._batch_size:
            try:
                nxt = self._queue.get_nowait()
            except queue.Empty:
                break
            if not isinstance(nxt, AgentEvent):
                break
            batch.append(nxt)
        return batch

    def _deliver(self, batch: list[AgentEvent]) -> None:
        """Hand a batch to the sink, retrying with exponential backoff.

        Never raises: a batch that cannot be delivered is counted and dropped.
        """
        delay = self._backoff_base_s
        for attempt in range(self._max_retries + 1):
            try:
                self._sink.export(batch)
            except Exception:
                if attempt < self._max_retries:
                    time.sleep(delay)
                    delay *= 2
                continue
            return

        with self._cond:
            self._failed += len(batch)

    def _drain_remaining(self) -> None:
        """Deliver events left in the queue after the worker has stopped."""
        remaining: list[AgentEvent] = []
        while True:
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                break
            if isinstance(item, AgentEvent):
                remaining.append(item)

        for start in range(0, len(remaining), self._batch_size):
            chunk = remaining[start : start + self._batch_size]
            self._deliver(chunk)
        self._complete(len(remaining))

    def _complete(self, count: int) -> None:
        """Mark ``count`` events as processed and wake any waiters."""
        if count == 0:
            return
        with self._cond:
            self._pending -= count
            if self._pending <= 0:
                self._cond.notify_all()
