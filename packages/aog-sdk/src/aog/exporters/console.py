"""Console exporter: writes events to a text stream, one JSON object per line.

Useful for local development and for verifying that events are being produced
before a backend exists.
"""

import sys
from collections.abc import Sequence
from typing import TextIO

from aog.events.models import AgentEvent


class ConsoleExporter:
    """Write each event as a single JSON line to a stream.

    Args:
        stream: Destination for the output. Defaults to ``sys.stdout``.
        pretty: When true, indent the JSON so it is readable by a human rather
            than one line per event.
    """

    def __init__(self, stream: TextIO | None = None, *, pretty: bool = False) -> None:
        self._stream = stream if stream is not None else sys.stdout
        self._pretty = pretty

    def export(self, events: Sequence[AgentEvent]) -> None:
        """Write every event in the batch to the stream."""
        indent = 2 if self._pretty else None
        for event in events:
            print(event.model_dump_json(indent=indent), file=self._stream)

    def shutdown(self) -> None:
        """Flush the stream. Safe to call repeatedly."""
        self._stream.flush()
