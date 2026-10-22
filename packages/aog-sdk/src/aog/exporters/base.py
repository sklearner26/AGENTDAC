"""Exporter protocol for AOG.

An *exporter* is a sink: it receives a batch of already-validated events and
writes them somewhere (a console, an HTTP endpoint, a file, ...). Buffering,
batching and retry live one layer up in the async exporter, so a sink can stay
simple and synchronous.

Failure semantics: a sink should **raise** when it cannot deliver a batch. That
is the signal the async layer uses to retry with backoff and, once retries are
exhausted, to drop the batch. Fail-open behaviour is guaranteed one layer up by
:class:`~aog.exporters.async_exporter.AsyncExporter`, so an unhealthy
destination never takes the instrumented agent down with it.
"""

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from aog.events.models import AgentEvent


@runtime_checkable
class Exporter(Protocol):
    """A destination for batches of AOG events."""

    def export(self, events: Sequence[AgentEvent]) -> None:
        """Write a batch of events.

        Raises on delivery failure so the async layer can retry; see the
        failure-semantics note in this module's docstring.
        """
        ...

    def shutdown(self) -> None:
        """Release any resources held by the exporter.

        Must be safe to call more than once.
        """
        ...
