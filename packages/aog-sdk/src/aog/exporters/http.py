"""HTTP exporter: delivers batches to the AOG ingestion endpoint.

Raises :class:`~aog.exceptions.AOGExportError` when the batch could not be
delivered. That failure signal is what lets
:class:`~aog.exporters.async_exporter.AsyncExporter` retry with backoff and
ultimately fail open, so it must not be swallowed here.
"""

from collections.abc import Sequence

import httpx

from aog.events.models import AgentEvent
from aog.exceptions import AOGExportError

DEFAULT_INGEST_PATH = "/v1/events"
DEFAULT_TIMEOUT_S = 5.0


class HTTPExporter:
    """POST batches of events to ``{endpoint}/v1/events``.

    Args:
        endpoint: Base URL of the AOG server, e.g. ``http://localhost:8000``.
        api_key: Sent as a bearer token when provided.
        path: Ingestion path, relative to ``endpoint``.
        timeout_s: Per-request timeout.
        client: An ``httpx.Client`` to reuse. When omitted the exporter creates
            (and later closes) its own.
    """

    def __init__(
        self,
        endpoint: str,
        *,
        api_key: str | None = None,
        path: str = DEFAULT_INGEST_PATH,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        client: httpx.Client | None = None,
    ) -> None:
        self._url = endpoint.rstrip("/") + path
        self._headers = {"content-type": "application/json"}
        if api_key is not None:
            self._headers["authorization"] = f"Bearer {api_key}"
        self._owns_client = client is None
        self._client = client if client is not None else httpx.Client(timeout=timeout_s)

    def export(self, events: Sequence[AgentEvent]) -> None:
        """POST the batch. Raises :class:`AOGExportError` on any failure."""
        if not events:
            return

        payload = {"events": [event.model_dump(mode="json") for event in events]}
        try:
            response = self._client.post(self._url, json=payload, headers=self._headers)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AOGExportError(f"Failed to export {len(events)} event(s) to {self._url}") from exc

    def shutdown(self) -> None:
        """Close the underlying client if this exporter created it."""
        if self._owns_client:
            self._client.close()
