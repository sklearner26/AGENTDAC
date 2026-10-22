"""Unit tests for HTTPExporter."""

from unittest.mock import MagicMock

import httpx
import pytest
from aog.events.enums import EventType
from aog.events.models import AgentEvent
from aog.exceptions import AOGExportError
from aog.exporters.http import HTTPExporter


def _sample_event() -> AgentEvent:
    return AgentEvent(
        event_id="ev1",
        trace_id="tr1",
        span_id="sp1",
        session_id="ses1",
        agent_id="ag1",
        event_type=EventType.TOOL,
        name="web_search",
    )


class TestHTTPExporter:
    def test_export_successful_post(self) -> None:
        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response

        exporter = HTTPExporter(
            endpoint="http://test-server:8000",
            api_key="secret-key",
            client=mock_client,
        )
        exporter.export([_sample_event()])

        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert args[0] == "http://test-server:8000/v1/events"
        assert kwargs["headers"]["authorization"] == "Bearer secret-key"
        exporter.shutdown()

    def test_export_raises_aog_export_error_on_failure(self) -> None:
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.post.side_effect = httpx.ConnectError("Connection refused")

        exporter = HTTPExporter(endpoint="http://offline-server:8000", client=mock_client)
        with pytest.raises(AOGExportError) as exc_info:
            exporter.export([_sample_event()])

        assert "Failed to export 1 event(s)" in str(exc_info.value)
        exporter.shutdown()
