"""Unit tests for the console exporter."""

import io
import json

from aog.exporters import ConsoleExporter, Exporter


class TestConsoleExporterProtocol:
    """Tests that ConsoleExporter honours the Exporter protocol."""

    def test_satisfies_exporter_protocol(self):
        """ConsoleExporter is usable wherever an Exporter is expected."""
        assert isinstance(ConsoleExporter(), Exporter)


class TestConsoleExporterExport:
    """Tests for ConsoleExporter.export."""

    def test_writes_one_json_line_per_event(self, make_event):
        """Each event becomes exactly one line of JSON."""
        stream = io.StringIO()
        exporter = ConsoleExporter(stream)

        exporter.export([make_event(name="first"), make_event(name="second")])

        lines = stream.getvalue().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["name"] == "first"
        assert json.loads(lines[1])["name"] == "second"

    def test_line_is_valid_json_with_core_fields(self, make_event):
        """The emitted JSON carries the event's identifying fields."""
        stream = io.StringIO()
        event = make_event(name="search", trace_id="trace-abc")

        ConsoleExporter(stream).export([event])

        payload = json.loads(stream.getvalue())
        assert payload["trace_id"] == "trace-abc"
        assert payload["span_id"] == "span-123"
        assert payload["session_id"] == "session-123"
        assert payload["agent_id"] == "test-agent"
        assert payload["event_type"] == "tool"
        assert payload["name"] == "search"
        assert payload["status"] == "ok"

    def test_empty_batch_writes_nothing(self):
        """Exporting nothing produces no output and does not raise."""
        stream = io.StringIO()
        ConsoleExporter(stream).export([])

        assert stream.getvalue() == ""

    def test_pretty_mode_spans_multiple_lines(self, make_event):
        """Pretty output is indented rather than one line per event."""
        stream = io.StringIO()
        ConsoleExporter(stream, pretty=True).export([make_event()])

        output = stream.getvalue()
        assert len(output.splitlines()) > 1
        assert json.loads(output)["name"] == "test_event"

    def test_defaults_to_stdout(self, capsys, make_event):
        """With no stream given, output goes to stdout."""
        ConsoleExporter().export([make_event(name="to-stdout")])

        assert '"name":"to-stdout"' in capsys.readouterr().out


class TestConsoleExporterShutdown:
    """Tests for ConsoleExporter.shutdown."""

    def test_shutdown_is_idempotent(self):
        """Shutdown can be called more than once."""
        exporter = ConsoleExporter(io.StringIO())

        exporter.shutdown()
        exporter.shutdown()
