"""Unit tests for execution DAG builder and cycle detection."""

from datetime import UTC, datetime

import pytest
from aog.backend.models.db import SpanRecord
from aog.backend.services.graph_builder import GraphBuilder
from aog.exceptions import AOGGraphIntegrityError


def _make_span(span_id: str, parent_id: str | None = None) -> SpanRecord:
    return SpanRecord(
        id=span_id,
        trace_id="tr1",
        session_id="ses1",
        parent_span_id=parent_id,
        agent_id="ag1",
        event_type="tool",
        name=f"step_{span_id}",
        started_at=datetime.now(UTC),
        status="OK",
    )


class TestGraphBuilder:
    def test_linear_trace(self) -> None:
        s1 = _make_span("1", None)
        s2 = _make_span("2", "1")
        s3 = _make_span("3", "2")

        nodes, edges = GraphBuilder.build_graph([s1, s2, s3])
        assert len(nodes) == 3
        assert len(edges) == 2
        assert edges[0].source == "1" and edges[0].target == "2"
        assert edges[1].source == "2" and edges[1].target == "3"

    def test_branching_trace(self) -> None:
        root = _make_span("root", None)
        c1 = _make_span("c1", "root")
        c2 = _make_span("c2", "root")

        nodes, edges = GraphBuilder.build_graph([root, c1, c2])
        assert len(nodes) == 3
        assert len(edges) == 2
        targets = {e.target for e in edges}
        assert targets == {"c1", "c2"}

    def test_cycle_detection_raises_integrity_error(self) -> None:
        s1 = _make_span("1", "2")
        s2 = _make_span("2", "1")

        with pytest.raises(AOGGraphIntegrityError):
            GraphBuilder.build_graph([s1, s2])
