# Agent Event Schema

## Overview

AOG uses a versioned universal event schema to capture agent execution. All events inherit from `AgentEvent` and contain common fields for trace and span identification.

## Core Event

```python
class AgentEvent(BaseModel):
    schema_version: str = "1.0"
    
    event_id: str
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    
    session_id: str
    agent_id: str
    
    event_type: EventType
    name: str
    
    timestamp: datetime
    status: EventStatus = EventStatus.OK
    
    input: dict | None = None
    output: dict | None = None
    attributes: dict = {}
    
    duration_ms: float | None = None
    
    tokens_in: int | None = None
    tokens_out: int | None = None
    
    model: str | None = None
    provider: str | None = None
    
    cost_usd: float | None = None
    
    error: ErrorInfo | None = None
```

## Event Types

| Event Type | Description |
|------------|-------------|
| `SESSION` | Session lifecycle (start, end) |
| `AGENT` | Agent execution |
| `LLM` | LLM model call |
| `TOOL` | Tool invocation |
| `RETRIEVAL` | Resource retrieval |
| `MEMORY` | Memory read/write |
| `DECISION` | Decision point |
| `HANDOFF` | Agent handoff |
| `STATE_CHANGE` | State mutation |
| `OBSERVATION` | Observation capture |
| `ERROR` | Error occurrence |

## Event Status

| Status | Description |
|--------|-------------|
| `OK` | Successfully completed |
| `ERROR` | Failed with error |
| `CANCELLED` | Cancelled by user/request |

## Error Information

```python
class ErrorInfo(BaseModel):
    type: str
    message: str
    stacktrace: str | None = None
    retryable: bool | None = None
```

## Event IDs

Events use UUIDs for `event_id`, `trace_id`, and `span_id`. Spans have parent-child relationships through `parent_span_id`.

## Attributes

Generic key-value pairs for custom metadata:

```python
attributes = {
    "tool_name": "search",
    "model": "claude-3-sonnet",
    "framework": "langchain",
    "cost": "0.05",
}
```

## Input/Output Redaction

Sensitive data can be redacted from input/output:

- `capture_input`: false to omit input from events
- `capture_output`: false to omit output from events
- Custom redaction rules for specific fields

## Timestamps

All events use ISO 8601 timestamps in UTC. `timestamp` is when the event occurred, `created_at` is when it was stored.

## Versioning

The `schema_version` field allows evolving the event schema over time. The backend validates events against the expected version.

## Example Event JSON

```json
{
  "schema_version": "1.0",
  "event_id": "evt_1234567890abcdef",
  "trace_id": "trace_1234567890abcdef",
  "span_id": "span_1234567890abcdef",
  "parent_span_id": "span_0987654321fedcba",
  "session_id": "session_1234567890abcdef",
  "agent_id": "research-agent",
  "event_type": "tool",
  "name": "web_search",
  "timestamp": "2024-01-15T10:30:00Z",
  "status": "ok",
  "input": {"query": "python tutorial"},
  "output": {"results": [...]},
  "attributes": {"provider": "tavily"},
  "duration_ms": 1250.5,
  "tokens_in": 150,
  "tokens_out": 800,
  "model": "claude-3-sonnet",
  "provider": "anthropic",
  "cost_usd": 0.075,
  "error": null
}
```