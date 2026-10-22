"""DAG Graph Builder: Reconstructs execution Directed Acyclic Graphs from SpanRecords."""

from datetime import UTC

from aog.backend.models.db import SpanRecord
from aog.backend.models.schemas import GraphEdge, GraphNode
from aog.exceptions import AOGGraphIntegrityError


class GraphBuilder:
    """Builds node and edge representations of trace execution and validates DAG acyclicity."""

    @staticmethod
    def build_graph(spans: list[SpanRecord]) -> tuple[list[GraphNode], list[GraphEdge]]:
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        span_ids = {s.id for s in spans}

        # Build adjacency graph for cycle validation
        adj: dict[str, list[str]] = {s.id: [] for s in spans}

        for s in spans:
            start_dt = (
                s.started_at.replace(tzinfo=UTC) if s.started_at.tzinfo is None else s.started_at
            )
            end_dt = (
                s.ended_at.replace(tzinfo=UTC)
                if s.ended_at and s.ended_at.tzinfo is None
                else s.ended_at
            )
            duration_ms = (end_dt - start_dt).total_seconds() * 1000.0 if end_dt else None

            node = GraphNode(
                id=s.id,
                type=s.event_type,
                label=s.name,
                status=s.status,
                started_at=s.started_at.isoformat(),
                ended_at=s.ended_at.isoformat() if s.ended_at else None,
                duration_ms=round(duration_ms, 2) if duration_ms is not None else None,
                tokens_in=s.tokens_in,
                tokens_out=s.tokens_out,
                cost_usd=s.cost_usd,
                model=s.model,
                provider=s.provider,
                metadata=s.attributes_json or {},
            )
            nodes.append(node)

            if s.parent_span_id and s.parent_span_id in span_ids:
                # Derive human-readable label from target span type
                type_label_map = {
                    "session": "starts session",
                    "agent": "spawns agent",
                    "llm": "invokes LLM",
                    "tool": "calls tool",
                    "skill": "uses skill",
                    "retrieval": "retrieves",
                    "memory": "reads memory",
                    "decision": "decides",
                    "handoff": "hands off to",
                    "state_change": "transitions state",
                    "observation": "observes",
                    "error": "raises error",
                }
                edge_label = type_label_map.get(s.event_type, f"→ {s.event_type}")
                # Include name for extra context
                edge_reason = s.name
                edge = GraphEdge(
                    id=f"e_{s.parent_span_id}_{s.id}",
                    source=s.parent_span_id,
                    target=s.id,
                    label=edge_label,
                    reason=edge_reason,
                )
                edges.append(edge)
                adj[s.parent_span_id].append(s.id)

        # Validate DAG acyclicity using DFS
        visited: dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited

        def has_cycle(u: str) -> bool:
            visited[u] = 1
            for v in adj.get(u, []):
                if visited.get(v, 0) == 1:
                    return True
                if visited.get(v, 0) == 0 and has_cycle(v):
                    return True
            visited[u] = 2
            return False

        for node_id in adj:
            if visited.get(node_id, 0) == 0 and has_cycle(node_id):
                raise AOGGraphIntegrityError(
                    f"Cycle detected in execution DAG involving span {node_id}"
                )

        return nodes, edges
