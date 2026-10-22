# Agent Observability Graph (AOG)
## Complete Product Planning & Implementation Specification for Claude Code

> **Purpose:** This document is the source-of-truth implementation plan for building a generalized, pluggable observability system for AI agents.
>
> **Primary MVP:** Any AI agent can emit standardized execution events; AOG reconstructs the session as an interactive execution DAG, exposes session/tool/LLM details, and provides analytics.
>
> **Future:** The same event stream evolves into a provenance-aware Knowledge Graph and agent memory substrate.

---

# 0. EXECUTION INSTRUCTIONS FOR CLAUDE CODE

You are implementing this repository, not merely explaining it.

## Rules

1. Read this entire file before making architectural changes.
2. Implement in the phases defined below, in order.
3. Do not jump to advanced phases before the current phase has:
   - working code,
   - tests,
   - type checking,
   - linting,
   - a runnable example,
   - updated documentation.
4. Prefer small modular files. Target **<300 LOC per source file** unless there is a strong reason otherwise.
5. Do not create unnecessary abstractions.
6. Do not introduce Kafka, Kubernetes, Neo4j, Qdrant, ClickHouse, or other distributed infrastructure during MVP.
7. PostgreSQL is the initial durable store.
8. The event model is the core abstraction.
9. The SDK must never require the application agent to know about the graph database.
10. Observability must be asynchronous/non-blocking whenever possible.
11. Never require collection of private model chain-of-thought. Capture observable execution state, tool calls, model metadata, state transitions, errors, outputs where configured, and provenance.
12. Never log secrets, API keys, authorization headers, passwords, raw credentials, or sensitive environment variables.
13. Make privacy/redaction configurable.
14. Preserve OpenTelemetry-compatible concepts:
    - trace
    - span
    - parent/child relationship
    - attributes
    - events
    - status
    - timestamps
15. Build the universal SDK first; framework-specific adapters come afterward.
16. Claude Code is the first real integration, but the core architecture must remain framework-independent.
17. Every implementation phase must leave the repository in a runnable state.
18. Do not silently change the event schema. If a schema change is necessary, update versioning and documentation.
19. Do not implement speculative features just because they appear in future roadmap sections.
20. When uncertain, choose the smallest implementation that preserves future extensibility.

---

# 1. PRODUCT VISION

## Product

**Agent Observability Graph (AOG)**

AOG is a generalized observability plugin/SDK that can be connected to AI agents and captures their observable execution as a structured event stream.

The event stream can be represented as:

1. execution traces,
2. hierarchical spans,
3. execution DAGs,
4. analytics,
5. provenance graphs,
6. eventually a semantic Knowledge Graph and memory system.

## Core statement

> Every agent action, model call, tool call, state transition, observation, and error becomes a structured event. Events are connected through trace and parent-child relationships so the complete agent execution can be inspected, queried, replayed, and eventually transformed into a Knowledge Graph.

## MVP user journey

```text
pip install agentdac
        |
        v
initialize AOG
        |
        v
run any instrumented agent
        |
        v
events emitted asynchronously
        |
        v
FastAPI ingestion service
        |
        v
PostgreSQL
        |
        v
execution graph API
        |
        v
React dashboard
        |
        v
interactive session DAG
```

The first successful demo must show:

```text
User Request
    |
    v
Agent
    |
    +----> LLM
    |
    +----> Tool
    |        |
    |        v
    |      Result
    |
    +----> LLM
    |
    v
Final Response
```

with:

- timing,
- status,
- model,
- tokens,
- estimated cost when available,
- tool name,
- input/output according to privacy configuration,
- errors,
- parent-child relationships,
- session metadata.

---

# 2. PRODUCT BOUNDARY

## In scope for MVP

- Python SDK
- universal event schema
- session/trace/span lifecycle
- context propagation
- decorators/context managers
- asynchronous HTTP exporter
- FastAPI ingestion API
- PostgreSQL persistence
- execution DAG reconstruction
- session API
- trace API
- basic analytics
- React/TypeScript dashboard
- interactive DAG
- timeline view
- node detail panel
- Claude Code integration
- generic manual instrumentation
- redaction/privacy controls
- tests
- Docker Compose
- local development documentation

## Explicitly deferred

- multi-language SDKs
- cloud SaaS
- multi-tenancy
- billing
- Kafka
- ClickHouse
- Kubernetes
- dedicated graph database
- advanced graph algorithms
- autonomous memory
- graph RAG
- marketplace
- natural-language-to-Cypher
- enterprise SSO
- distributed alerting
- advanced LLM evaluation

---

# 3. HIGH-LEVEL ARCHITECTURE

```text
                         USER AGENT
                             |
                +------------+-------------+
                |                          |
          AOG Python SDK             Claude Code Adapter
                |                          |
                +------------+-------------+
                             |
                      Universal Events
                             |
                   Async Event Exporter
                             |
                             v
                    FastAPI Ingestion
                             |
                  +----------+----------+
                  |                     |
                  v                     v
             PostgreSQL             Future Queue
                  |
         +--------+---------+
         |                  |
         v                  v
    Trace Service      Analytics Service
         |
         v
   Graph Builder
         |
         v
     REST API
         |
         v
 React Dashboard
         |
    +----+-----+
    |          |
    v          v
 Session DAG  Timeline
```

---

# 4. ARCHITECTURAL PRINCIPLES

## 4.1 Event-first architecture

The source of truth is the event stream.

Do not make the dashboard or graph database the source of truth.

```text
Agent
  |
  v
Events
  |
  +--> Trace
  +--> DAG
  +--> Analytics
  +--> Knowledge Graph later
  +--> Replay later
  +--> Memory later
```

## 4.2 Trace model

A trace represents one execution/session.

A span represents a logical operation.

Example:

```text
Trace: session-123

  agent.run
      |
      +--- llm.call
      |
      +--- tool.search
      |       |
      |       +--- tool.result
      |
      +--- llm.call
      |
      +--- response
```

## 4.3 Parent-child relationships

Every span has:

```text
span_id
trace_id
parent_span_id
```

This makes DAG/tree reconstruction possible.

## 4.4 Do not depend on chain-of-thought

AOG captures observable execution:

- selected tool,
- tool arguments where allowed,
- tool results where allowed,
- model call,
- model metadata,
- state changes,
- retrieval,
- memory access,
- retries,
- errors,
- handoffs,
- plan step identifiers where explicitly exposed by the agent.

Do not attempt to collect hidden/private reasoning.

## 4.5 Framework independence

The SDK core must not import LangChain, LangGraph, CrewAI, or Claude-specific modules.

Framework integrations live under:

```text
integrations/
```

---

# 5. REPOSITORY STRUCTURE

Use a monorepo:

```text
agent-observability/
|
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── SECURITY.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── uv.lock
|
├── docs/
│   ├── architecture.md
│   ├── event-schema.md
│   ├── sdk.md
│   ├── integrations.md
│   ├── privacy.md
│   └── roadmap.md
|
├── packages/
│   └── aog-sdk/
│       ├── pyproject.toml
│       └── src/
│           └── aog/
│               ├── __init__.py
│               ├── client.py
│               ├── config.py
│               ├── context.py
│               ├── exceptions.py
│               |
│               ├── events/
│               │   ├── models.py
│               │   ├── enums.py
│               │   └── validation.py
│               |
│               ├── tracing/
│               │   ├── tracer.py
│               │   ├── span.py
│               │   └── lifecycle.py
│               |
│               ├── decorators/
│               │   ├── observe.py
│               │   ├── agent.py
│               │   ├── tool.py
│               │   └── llm.py
│               |
│               ├── exporters/
│               │   ├── base.py
│               │   ├── http.py
│               │   └── console.py
│               |
│               ├── redaction/
│               │   ├── sanitizer.py
│               │   └── rules.py
│               |
│               └── integrations/
│                   └── generic.py
|
├── server/
│   ├── pyproject.toml
│   └── app/
│       ├── main.py
│       ├── config.py
│       |
│       ├── api/
│       │   ├── health.py
│       │   ├── events.py
│       │   ├── sessions.py
│       │   ├── traces.py
│       │   └── analytics.py
│       |
│       ├── models/
│       │   ├── db.py
│       │   └── schemas.py
│       |
│       ├── services/
│       │   ├── ingestion.py
│       │   ├── trace_builder.py
│       │   ├── graph_builder.py
│       │   └── analytics.py
│       |
│       ├── repositories/
│       │   ├── events.py
│       │   ├── sessions.py
│       │   └── spans.py
│       |
│       └── migrations/
|
├── dashboard/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       |
│       ├── api/
│       │   └── client.ts
│       |
│       ├── types/
│       │   └── graph.ts
│       |
│       ├── pages/
│       │   ├── SessionsPage.tsx
│       │   └── SessionPage.tsx
│       |
│       ├── components/
│       │   ├── SessionTable.tsx
│       │   ├── ExecutionGraph.tsx
│       │   ├── Timeline.tsx
│       │   ├── NodeInspector.tsx
│       │   └── StatsCards.tsx
│       |
│       └── hooks/
│           └── useSession.ts
|
├── integrations/
│   └── claude-code/
│       ├── README.md
│       ├── adapter.py
│       ├── parser.py
│       └── examples/
|
├── examples/
│   ├── basic_agent.py
│   ├── nested_tools.py
│   └── claude_code/
|
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
|
└── scripts/
    ├── dev.sh
    └── seed_demo.py
```

---

# 6. TECHNOLOGY STACK

## Backend

- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- asyncpg
- httpx
- pytest
- pytest-asyncio
- Ruff
- mypy
- uv

## SDK

- Python
- Pydantic
- contextvars
- httpx
- asyncio
- UUID/ULID-compatible IDs

## Frontend

- React
- TypeScript
- Vite
- React Flow
- TanStack Query
- lightweight component system
- CSS/Tailwind only if useful

## Infrastructure

- Docker
- Docker Compose
- PostgreSQL

## Observability compatibility

Design around OpenTelemetry concepts.

Do not implement a second incompatible tracing philosophy.

---

# 7. CORE EVENT MODEL

Create a versioned universal event schema.

## Event

```python
class AgentEvent(BaseModel):
    schema_version: str

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

## Event types

```python
class EventType(str, Enum):
    SESSION = "session"
    AGENT = "agent"
    LLM = "llm"
    TOOL = "tool"
    RETRIEVAL = "retrieval"
    MEMORY = "memory"
    DECISION = "decision"
    HANDOFF = "handoff"
    STATE_CHANGE = "state_change"
    OBSERVATION = "observation"
    ERROR = "error"
```

## Error

```python
class ErrorInfo(BaseModel):
    type: str
    message: str
    stacktrace: str | None = None
    retryable: bool | None = None
```

Stack traces must be redacted/configurable.

---

# 8. SPAN MODEL

A span represents one operation.

Required fields:

```text
span_id
trace_id
parent_span_id
name
type
start_time
end_time
status
attributes
```

Span lifecycle:

```text
start()
  |
  v
execute
  |
  +---- event()
  |
  v
finish()
```

If execution raises:

```text
finish(status=ERROR)
record_error(...)
raise
```

---

# 9. SESSION MODEL

A session is the top-level user/agent execution boundary.

```python
with aog.session(agent_id="research-agent", metadata={"environment": "development"}) as session:
    ...
```

The session automatically creates a root span.

Session states:

```text
RUNNING
SUCCESS
FAILED
CANCELLED
```

---

# 10. CONTEXT PROPAGATION

Use Python `contextvars`.

The active context must contain:

```python
trace_id
session_id
current_span_id
agent_id
```

Example:

```python
current_context = get_current_context()

with tracer.span("tool.search"):
    assert get_current_context().parent_span_id == previous_span_id
```

Nested calls automatically inherit context.

This is a critical requirement.

---

# 11. SDK API

The public API should be simple.

## Client

```python
from aog import AOG

aog = AOG(
    endpoint="http://localhost:8000",
    api_key="dev-key",
)
```

## Session

```python
with aog.session(agent_id="research-agent") as session:
    ...
```

## Agent

```python
with session.agent("researcher"):
    ...
```

## Tool

```python
with aog.tool("web_search", attributes={"provider": "tavily"}):
    result = search(query)
```

## LLM

```python
with aog.llm(model="claude-sonnet", provider="anthropic"):
    result = call_model(prompt)
```

## Generic span

```python
with aog.span(name="retrieve_documents", event_type="retrieval"):
    ...
```

---

# 12. DECORATORS

Support:

```python
@aog.observe
def function(): ...
```

and:

```python
@aog.tool()
def search(query): ...
```

and:

```python
@aog.agent()
def research_agent(query): ...
```

Decorator requirements:

- preserve function signature,
- preserve return value,
- capture duration,
- capture errors,
- propagate context,
- never break application execution because observability failed.

Observability must be fail-open by default.

---

# 13. FAIL-OPEN REQUIREMENT

If AOG server is down:

```text
Agent
  |
  +----> AOG export fails
  |
  +----> Agent continues
```

Never:

```text
AOG unavailable
      |
      v
agent crashes
```

SDK configuration:

```python
fail_open = True
```

Default: `True`.

Provide a strict mode for testing:

```python
fail_open = False
```

---

# 14. ASYNC EXPORTER

Do not synchronously send every event.

Architecture:

```text
Application
    |
    v
Event
    |
    v
In-memory queue
    |
    v
background exporter
    |
    v
HTTP batch
    |
    v
FastAPI
```

Requirements:

- bounded queue,
- batch size,
- flush interval,
- retry,
- exponential backoff,
- event IDs for idempotency,
- graceful shutdown,
- dropped-event counter.

Default example:

```text
batch_size = 50
flush_interval = 500ms
queue_size = 5000
max_retries = 3
```

These values must be configurable.

---

# 15. PRIVACY AND REDACTION

Never automatically capture secrets.

Implement:

```python
RedactionConfig(
    redact_keys=[
        "api_key",
        "authorization",
        "token",
        "password",
        "secret",
        "access_token",
        "refresh_token",
    ],
    max_payload_bytes=...,
)
```

Support:

```text
capture_input = true/false
capture_output = true/false
capture_tool_args = true/false
capture_tool_results = true/false
```

Support custom redactor:

```python
aog = AOG(redactor=my_redactor)
```

The SDK should redact recursively.

---

# 16. POSTGRESQL SCHEMA

Start with PostgreSQL.

## agents

```sql
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    framework TEXT,
    model TEXT,
    version TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## sessions

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(id),
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## spans

```sql
CREATE TABLE spans (
    id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    parent_span_id TEXT,
    agent_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    name TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    input JSONB,
    output JSONB,
    attributes JSONB NOT NULL DEFAULT '{}',
    tokens_in INTEGER,
    tokens_out INTEGER,
    model TEXT,
    provider TEXT,
    cost_usd DOUBLE PRECISION,
    error JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## events

```sql
CREATE TABLE events (
    id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    span_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    name TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Indexes:

```sql
CREATE INDEX idx_sessions_agent_time
ON sessions(agent_id, started_at DESC);

CREATE INDEX idx_spans_trace
ON spans(trace_id);

CREATE INDEX idx_spans_session
ON spans(session_id);

CREATE INDEX idx_spans_parent
ON spans(parent_span_id);

CREATE INDEX idx_spans_type
ON spans(event_type);

CREATE INDEX idx_events_trace
ON events(trace_id);

CREATE INDEX idx_events_session_time
ON events(session_id, timestamp);
```

---

# 17. IDEMPOTENCY

Event ingestion must be safe to retry.

Primary key:

```text
event_id
```

If an event arrives twice:

```text
first -> INSERT
second -> ignore/update safely
```

Do not duplicate spans/events.

---

# 18. FASTAPI API

Base path:

```text
/v1
```

## Health

```http
GET /health
```

## Ingest

```http
POST /v1/events
```

Request:

```json
{
  "events": []
}
```

Response:

```json
{
  "accepted": 50,
  "duplicates": 0,
  "rejected": 0
}
```

## Sessions

```http
GET /v1/sessions
GET /v1/sessions/{session_id}
```

Filters:

```text
agent_id
status
from
to
limit
cursor
```

## Trace

```http
GET /v1/sessions/{session_id}/trace
```

Response:

```json
{
  "session": {},
  "nodes": [],
  "edges": []
}
```

## Span

```http
GET /v1/spans/{span_id}
```

## Events

```http
GET /v1/sessions/{session_id}/events
```

## Analytics

```http
GET /v1/analytics/overview
GET /v1/analytics/tools
GET /v1/analytics/models
GET /v1/analytics/errors
```

---

# 19. GRAPH REPRESENTATION

The dashboard should consume:

```typescript
type GraphNode = {
  id: string;
  type: string;
  label: string;
  status: string;
  startedAt: string;
  endedAt?: string;
  durationMs?: number;
  metadata?: Record<string, unknown>;
};

type GraphEdge = {
  id: string;
  source: string;
  target: string;
  type: "parent";
};
```

The first graph is a **trace DAG/tree representation**.

Do not call it a semantic Knowledge Graph yet.

---

# 20. DAG BUILDING ALGORITHM

Input:

```text
spans[]
```

For every span:

```text
node = span
```

If:

```text
parent_span_id != null
```

create:

```text
edge(parent_span_id -> span_id)
```

Validate:

1. no missing parent references unless parent was intentionally omitted,
2. no self-parent,
3. no cycles,
4. every node belongs to the requested trace/session,
5. duplicate span IDs are rejected.

If a cycle is detected, return a graph integrity error.

---

# 21. GRAPH VIEW

Use React Flow.

Requirements:

- zoom
- pan
- fit view
- node selection
- edge visualization
- status indicator
- duration display
- model/tool labels
- error nodes visually distinct
- collapsible groups later
- search
- filtering

Do not overload the graph with huge payloads.

Fetch details on node selection.

---

# 22. SESSION PAGE

Layout:

```text
+------------------------------------------------------+
| Session abc                                          |
| Agent: researcher | Duration: 12.4s | Cost: $0.04  |
+------------------------------------------------------+

+---------------------------+--------------------------+
|                           |                          |
|     Execution Graph       |     Node Inspector       |
|                           |                          |
|       Agent               | Type: TOOL              |
|        / \                | Name: web_search        |
|      LLM Tool             | Duration: 1.2s          |
|          |                | Status: SUCCESS         |
|        Result             |                          |
|                           | Input: ...              |
|                           | Output: ...             |
+---------------------------+--------------------------+

+------------------------------------------------------+
| Timeline                                             |
+------------------------------------------------------+
```

---

# 23. SESSIONS PAGE

Columns:

```text
Session ID
Agent
Started
Duration
Events
Tokens
Cost
Status
```

Filters:

```text
Agent
Status
Date range
Model
Event type
```

---

# 24. NODE INSPECTOR

For a selected span show:

```text
Name
Type
Status
Start
End
Duration
Model
Provider
Tokens in
Tokens out
Estimated cost
Attributes
Input
Output
Error
Parent
Children
```

Support copy-to-JSON.

---

# 25. BASIC ANALYTICS

Implement first:

## Session count

```text
count(sessions)
```

## Error rate

```text
failed_sessions / total_sessions
```

## Tool frequency

```text
count(tool spans grouped by tool name)
```

## Tool latency

```text
avg
p50
p95
```

## Model usage

```text
calls by model
tokens by model
estimated cost by model
```

## Agent activity

```text
sessions per time period
```

---

# 26. COST CALCULATION

Do not hardcode one provider's prices into core logic.

Represent cost as:

```text
cost_usd
```

If an integration knows pricing, it can calculate it.

Otherwise:

```text
cost_usd = null
```

Never invent a cost.

Create a future pricing provider abstraction:

```python
class PricingProvider(Protocol):
    def calculate(
        self,
        provider: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
    ) -> float | None: ...
```

---

# 27. CLAUDE CODE INTEGRATION

Claude Code is the first concrete integration.

Do not put Claude Code-specific assumptions into the core event model.

Create an adapter:

```text
Claude Code
   |
   v
Claude Adapter
   |
   v
AgentEvent
```

The adapter should map available Claude Code lifecycle/tool/session information into:

```text
SESSION
AGENT
TOOL
STATE_CHANGE
OBSERVATION
ERROR
```

Where available.

## Integration requirements

- session start
- session end
- tool invocation
- tool completion
- errors
- timestamps
- parent relationships
- command/task metadata when available
- file/resource metadata when safely available

Do not capture secrets.

Do not capture hidden/private reasoning.

Do not make Claude Code the only integration architecture.

---

# 28. GENERIC INTEGRATION API

Provide a low-level adapter:

```python
aog.record(
    event_type="tool",
    name="search",
    input={"query": query},
    output=result,
)
```

and:

```python
with aog.span("search", event_type="tool"):
    ...
```

This means any custom agent can integrate even without an official adapter.

---

# 29. FUTURE FRAMEWORK ADAPTERS

After MVP:

```text
integrations/
├── claude-code/
├── langchain/
├── langgraph/
├── crewai/
├── autogen/
└── generic/
```

Every adapter outputs only the universal event schema.

---

# 30. KNOWLEDGE GRAPH PHASE

This is NOT part of MVP.

Once trace observability is stable, add semantic graph entities.

## Nodes

```text
Agent
Session
Span
Tool
Skill
Resource
Observation
Fact
MemoryEntity
```

## Relationships

```text
Agent -HAS_SESSION-> Session
Session -CONTAINS-> Span
Span -USES-> Tool
Span -ACCESSES-> Resource
Span -PRODUCES-> Observation
Fact -SOURCED_FROM-> Span
Agent -USES-> Skill
Agent -READS-> MemoryEntity
Agent -WRITES-> MemoryEntity
```

Every semantic fact must maintain provenance.

Example:

```text
Fact:
    User prefers Python

SOURCED_FROM
    |
    v
Span abc
    |
    v
Session xyz
```

Never create an unsupported fact without provenance.

---

# 31. GRAPH DATABASE MIGRATION STRATEGY

Do not migrate to Neo4j just because a Knowledge Graph exists.

First establish the domain model in PostgreSQL.

If graph traversal becomes a real bottleneck, introduce:

```text
Postgres = source of truth
Neo4j/Memgraph = graph projection
```

The graph projection must be rebuildable from PostgreSQL events.

Never make an unrecoverable graph projection the only source of truth.

---

# 32. MEMORY PHASE

After observability + semantic graph:

```text
Working Memory
Episodic Memory
Semantic Memory
Procedural Memory
```

Memory write:

```text
event
  |
  v
observation
  |
  v
entity/fact extraction
  |
  v
deduplication
  |
  v
provenance
  |
  v
graph
```

Memory read:

```text
query
  |
  +--> vector search
  |
  +--> graph traversal
  |
  +--> recency
  |
  +--> confidence
  |
  v
context bundle
```

This is a later product layer, not an MVP requirement.

---

# 33. MCP PHASE

After core observability is stable, expose the system through MCP.

Tools:

```text
get_session_trace
get_session_events
get_agent_stats
get_tool_usage
get_errors
search_observations
query_graph
```

Example:

```text
Agent
  |
  | MCP
  v
AOG
  |
  v
Observability Graph
```

MCP must be read-only by default.

Future write capabilities must require explicit authorization.

---

# 34. SECURITY MODEL

Minimum security requirements:

## API keys

Support:

```text
Authorization: Bearer <key>
```

Do not store plaintext API keys.

## Tenant preparation

Even though MVP is single-tenant/local, schema should leave room for:

```text
tenant_id
```

Do not implement complex multi-tenancy yet.

## Input validation

All external payloads use Pydantic validation.

## Payload size

Reject oversized events.

## Rate limiting

Not required for local MVP, but design API middleware so it can be added.

## Secrets

Never persist:

```text
API keys
passwords
OAuth tokens
authorization headers
private keys
.env contents
```

---

# 35. PERFORMANCE REQUIREMENTS

MVP target:

```text
SDK event creation: <1ms target
Export must be asynchronous
Agent must continue if server unavailable
Batch events
Use connection pooling
Use indexes for trace/session lookup
```

Do not optimize prematurely.

Measure first.

---

# 36. OBSERVABILITY OF AOG ITSELF

AOG should eventually observe itself.

At minimum, log:

```text
events_received
events_accepted
events_rejected
events_dropped
export_failures
ingestion_latency
database_latency
```

But do not create an infinite self-observability loop.

---

# 37. TEST STRATEGY

## Unit tests

Test:

- event validation
- event serialization
- span lifecycle
- context propagation
- nested spans
- decorators
- redaction
- cost calculation
- DAG construction
- cycle detection
- exporter retry
- fail-open behavior

## Integration tests

Test:

```text
SDK
  ↓
FastAPI
  ↓
Postgres
  ↓
trace API
```

## E2E test

Run:

```text
demo agent
  ↓
AOG SDK
  ↓
server
  ↓
database
  ↓
dashboard
```

Verify the UI can show the session.

---

# 38. REQUIRED TEST CASES

## Nested spans

```text
agent
  ├── llm
  └── tool
       └── nested span
```

## Error

```text
tool starts
tool fails
error recorded
agent continues
```

## Server unavailable

```text
agent executes successfully
AOG endpoint unavailable
events buffered/dropped according to policy
agent does not crash
```

## Duplicate events

```text
event sent twice
database contains one event
```

## Concurrent sessions

Run at least 20 concurrent sessions in tests.

Verify trace IDs remain isolated.

## Context isolation

Two concurrent tasks must never inherit each other's trace context.

---

# 39. DEMO AGENT

Create a deterministic demo agent.

Example:

```text
User:
"Find information about Python and summarize it."
```

Flow:

```text
Session
  |
  v
Agent
  |
  v
Planner
  |
  +----> Search Tool
  |          |
  |          v
  |        Result
  |
  v
LLM
  |
  v
Response
```

Use mock implementations by default so tests do not require external API keys.

---

# 40. LOCAL DEVELOPMENT

`docker-compose.yml` should initially contain:

```text
postgres
server
dashboard
```

Do not add Redis unless a concrete implementation requires it.

Commands:

```bash
make install
make dev
make test
make lint
make typecheck
```

Expected:

```text
API:
http://localhost:8000

Dashboard:
http://localhost:5173
```

---

# 41. ENVIRONMENT VARIABLES

Create `.env.example`:

```env
AOG_DATABASE_URL=postgresql+asyncpg://aog:aog@localhost:5432/aog
AOG_API_KEY=dev-key
AOG_LOG_LEVEL=INFO

AOG_CAPTURE_INPUT=true
AOG_CAPTURE_OUTPUT=true
AOG_CAPTURE_TOOL_ARGS=true
AOG_CAPTURE_TOOL_RESULTS=true

AOG_MAX_PAYLOAD_BYTES=100000
AOG_EXPORT_BATCH_SIZE=50
AOG_EXPORT_FLUSH_INTERVAL_MS=500
AOG_EXPORT_QUEUE_SIZE=5000
AOG_FAIL_OPEN=true
```

Never commit real `.env`.

---

# 42. CONFIGURATION MODEL

Use typed configuration.

```python
class AOGConfig(BaseSettings):
    endpoint: str
    api_key: str | None = None

    fail_open: bool = True

    capture_input: bool = True
    capture_output: bool = True

    export_batch_size: int = 50
    export_flush_interval_ms: int = 500

    queue_size: int = 5000
```

Validate all values.

---

# 43. LOGGING

Use structured logs.

Example:

```json
{
  "level": "INFO",
  "component": "exporter",
  "event": "batch_sent",
  "count": 50
}
```

Never log raw sensitive payloads.

---

# 44. ERROR HANDLING

Define custom errors:

```text
AOGError
AOGConfigError
AOGExportError
AOGValidationError
AOGContextError
AOGGraphIntegrityError
```

SDK errors should not break the application when `fail_open=True`.

---

# 45. DOCUMENTATION REQUIREMENTS

README must contain:

1. What AOG is.
2. Architecture diagram.
3. Installation.
4. 10-line quick start.
5. Generic instrumentation.
6. Running local dashboard.
7. Claude Code integration.
8. Privacy/redaction.
9. API overview.
10. Roadmap.

Create:

```text
docs/event-schema.md
```

with the complete event schema.

Create:

```text
docs/integrations.md
```

with integration rules.

Create:

```text
docs/privacy.md
```

with capture/redaction behavior.

---

# 46. PHASED IMPLEMENTATION ROADMAP

## Phase 0 — Bootstrap

Tasks:

- initialize repository
- configure uv
- configure Python
- configure Ruff
- configure mypy
- configure pytest
- create Docker Compose
- create README
- create `.env.example`

Acceptance:

```text
make test
make lint
make typecheck
```

all work.

---

## Phase 1 — Event Core

Implement:

- AgentEvent
- enums
- validation
- serialization
- IDs
- timestamps
- ErrorInfo

Acceptance:

- unit tests
- JSON round-trip
- invalid events rejected

---

## Phase 2 — Tracing

Implement:

- tracer
- span
- session
- contextvars
- nested span relationships
- lifecycle

Acceptance:

```text
session
  └── agent
       ├── llm
       └── tool
```

is correctly generated.

---

## Phase 3 — SDK Exporter

Implement:

- exporter protocol
- console exporter
- HTTP exporter
- async queue
- batching
- retry
- backoff
- graceful shutdown
- fail-open

Acceptance:

- events reach server
- agent doesn't crash if server is unavailable

---

## Phase 4 — Backend

Implement:

- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- ingestion endpoint
- sessions API
- trace API
- span API
- event API

Acceptance:

```text
SDK → API → DB → API
```

works end-to-end.

---

## Phase 5 — Graph Builder

Implement:

- graph nodes
- graph edges
- parent-child reconstruction
- cycle validation
- graph API

Acceptance:

Session trace is returned as:

```json
{
  "nodes": [],
  "edges": []
}
```

---

## Phase 6 — Dashboard

Implement:

- sessions page
- session detail
- React Flow graph
- timeline
- node inspector
- filters
- stats

Acceptance:

A developer can run one command and visually inspect an agent execution.

---

## Phase 7 — Analytics

Implement:

- sessions count
- error rate
- tool frequency
- latency
- model usage
- token totals
- cost when known

Acceptance:

Analytics match raw database calculations.

---

## Phase 8 — Claude Code

Implement:

- adapter
- event mapping
- lifecycle integration
- tool event capture
- session trace
- documentation

Acceptance:

A real Claude Code session appears in AOG as an execution graph.

Do not make unsupported assumptions about Claude Code internals. Inspect the currently available integration/hook mechanisms and adapt to them.

---

## Phase 9 — Generic Integration API

Implement:

```python
aog.record(...)
aog.span(...)
aog.tool(...)
aog.llm(...)
aog.agent(...)
```

Acceptance:

A custom Python agent can integrate without framework dependencies.

---

## Phase 10 — OpenTelemetry Compatibility

Implement mapping between AOG spans and OpenTelemetry concepts.

Do not duplicate OpenTelemetry unnecessarily.

Acceptance:

AOG can export or represent trace/span metadata in a standards-compatible way.

---

## Phase 11 — Semantic Knowledge Graph

Only after MVP is stable.

Implement:

- Tool nodes
- Agent nodes
- Resource nodes
- Observation nodes
- Fact nodes
- provenance
- relationships
- temporal metadata

Acceptance:

Every semantic fact can be traced back to an observation/span.

---

## Phase 12 — MCP

Implement:

- read-only MCP server
- trace query
- session query
- analytics query
- graph search

Acceptance:

An external MCP-compatible agent can query AOG.

---

## Phase 13 — Memory

Implement:

- working memory
- episodic memory
- semantic memory
- procedural memory
- graph + vector retrieval
- provenance
- temporal validity

Do not implement before the observability core is reliable.

---

# 47. DEFINITION OF DONE FOR MVP

MVP is complete only when all are true:

### SDK

- [ ] installable package
- [ ] session API
- [ ] span API
- [ ] tool API
- [ ] LLM API
- [ ] decorators
- [ ] context propagation
- [ ] async exporter
- [ ] retry
- [ ] fail-open
- [ ] redaction

### Backend

- [ ] FastAPI
- [ ] PostgreSQL
- [ ] migrations
- [ ] event ingestion
- [ ] session API
- [ ] trace API
- [ ] analytics API
- [ ] idempotency

### Graph

- [ ] DAG construction
- [ ] parent-child edges
- [ ] cycle detection
- [ ] graph API

### Dashboard

- [ ] sessions
- [ ] trace graph
- [ ] timeline
- [ ] node inspector
- [ ] filters
- [ ] basic metrics

### Claude Code

- [ ] integration
- [ ] session capture
- [ ] tool capture
- [ ] errors
- [ ] trace visualization

### Quality

- [ ] unit tests
- [ ] integration tests
- [ ] E2E test
- [ ] lint
- [ ] typecheck
- [ ] README
- [ ] architecture documentation
- [ ] privacy documentation

---

# 48. IMPLEMENTATION ORDER INSIDE CLAUDE CODE

Execute tasks in this exact sequence:

```text
1. Inspect repository
2. Bootstrap tooling
3. Implement event models
4. Implement tracing/context
5. Implement SDK API
6. Implement async exporter
7. Implement FastAPI
8. Implement PostgreSQL
9. Implement ingestion
10. Implement trace reconstruction
11. Implement graph API
12. Implement dashboard
13. Implement analytics
14. Add generic demo agent
15. Add Claude Code adapter
16. Add E2E tests
17. Harden privacy/security
18. Update docs
19. Run complete validation
```

After every major phase:

```bash
pytest
ruff check .
mypy ...
```

and fix failures before continuing.

---

# 49. CLAUDE CODE WORK STYLE

For every implementation task:

## Step 1

Inspect existing repository state.

## Step 2

Identify the smallest set of files required.

## Step 3

Implement.

## Step 4

Write tests immediately.

## Step 5

Run tests.

## Step 6

Run lint/typecheck.

## Step 7

Update documentation.

## Step 8

Only then move to the next phase.

Never create placeholder files for functionality that is not implemented unless explicitly marked as TODO.

---

# 50. FIRST CLAUDE CODE PROMPT

Use this as the first instruction after placing this file in the repository:

```text
Read IMPLEMENTATION.md completely.

You are implementing the Agent Observability Graph (AOG) described in this document.

Do not implement the entire roadmap at once.

Start with Phase 0 only.

First inspect the repository and report:
1. current files,
2. current tooling,
3. anything reusable,
4. conflicts with this specification.

Then implement Phase 0.

Do not start Phase 1 until Phase 0 is complete and validated.

After implementation:
- run tests,
- run lint,
- run typecheck,
- fix failures,
- update README if necessary.

Keep files modular and avoid unnecessary abstractions.
```

---

# 51. SECOND PROMPT AFTER PHASE 0

```text
Phase 0 is complete.

Now implement Phase 1 from IMPLEMENTATION.md: the universal AgentEvent schema.

Requirements:
- Pydantic v2
- versioned schema
- event IDs
- trace/session/span IDs
- parent span ID
- timestamps
- event types
- status
- input/output
- attributes
- token metadata
- model/provider
- cost
- error information
- strict validation
- JSON serialization

Write comprehensive unit tests.

Do not implement database, dashboard, graph, or Claude Code integration yet.

Run tests, lint, and typecheck before finishing.
```

---

# 52. THIRD PROMPT

```text
Phase 1 is complete.

Implement Phase 2: tracing and context propagation.

Implement:
- AOG client
- session lifecycle
- span lifecycle
- contextvars
- parent/child relationships
- nested spans
- exception handling
- decorators/context managers

Verify concurrent sessions cannot leak context.

Write tests for:
- simple span
- nested span
- error span
- concurrent sessions
- context isolation.

Do not implement backend or dashboard yet.
```

---

# 53. FOURTH PROMPT

```text
Implement Phase 3: asynchronous SDK exporting.

Implement:
- exporter interface
- console exporter
- HTTP exporter
- bounded async queue
- batching
- retry
- exponential backoff
- graceful shutdown
- fail-open behavior
- idempotent event IDs

Write tests for:
- successful export
- batching
- retry
- server unavailable
- queue overflow
- shutdown flush
- fail-open.

Do not implement dashboard yet.
```

---

# 54. FIFTH PROMPT

```text
Implement Phase 4: FastAPI + PostgreSQL backend.

Use:
- FastAPI
- SQLAlchemy async
- asyncpg
- Alembic
- PostgreSQL
- Pydantic schemas

Implement:
- health
- event ingestion
- sessions
- traces
- spans
- events
- idempotency

Add database indexes from IMPLEMENTATION.md.

Create integration tests using a disposable/test PostgreSQL environment.

Do not add Neo4j, Kafka, Redis, or ClickHouse.
```

---

# 55. SIXTH PROMPT

```text
Implement Phase 5: execution DAG reconstruction.

Build:
- trace graph service
- nodes
- parent-child edges
- validation
- cycle detection
- missing-parent handling
- graph endpoint

Return frontend-ready nodes and edges.

Add tests with:
- linear trace
- branching trace
- nested trace
- malformed trace
- cycle attempt
- concurrent traces.
```

---

# 56. SEVENTH PROMPT

```text
Implement Phase 6: React dashboard.

Use:
- React
- TypeScript
- Vite
- React Flow
- TanStack Query

Implement:
1. Sessions page
2. Session detail page
3. Execution graph
4. Timeline
5. Node inspector
6. Basic filters
7. Session statistics

The graph must fetch node details on selection rather than putting huge payloads into every graph node.

Make the interface clean and developer-focused.
```

---

# 57. EIGHTH PROMPT

```text
Implement Phase 7: analytics.

Add backend analytics for:
- session count
- error rate
- tool frequency
- tool latency
- model usage
- token usage
- cost where available

Add dashboard cards/tables.

Validate analytics against raw database queries.

Do not invent missing cost or token data.
```

---

# 58. NINTH PROMPT

```text
Implement Phase 8: Claude Code integration.

First inspect the currently available Claude Code integration/hook/event mechanisms rather than assuming an API.

Create a separate adapter that converts available Claude Code execution information into the universal AOG event schema.

Capture observable:
- sessions
- tool calls
- tool results where allowed
- errors
- timing
- parent-child relationships
- safe metadata

Do not capture hidden/private chain-of-thought.
Do not put Claude-specific fields into the core event model unless they are generic attributes.

Create an end-to-end example and documentation.
```

---

# 59. TENTH PROMPT

```text
The MVP should now be complete.

Run a complete validation.

Verify:
1. clean installation
2. Docker Compose startup
3. PostgreSQL migrations
4. FastAPI startup
5. dashboard startup
6. generic demo agent
7. SDK event export
8. trace reconstruction
9. dashboard graph
10. node inspector
11. analytics
12. Claude Code integration
13. privacy/redaction
14. fail-open behavior
15. concurrent session isolation

Run all tests, lint, and typecheck.

Fix all issues.

Then update README with exact local setup and a 10-minute quick-start tutorial.

Do not begin Knowledge Graph/memory implementation until the MVP passes this validation.
```

---

# 60. FUTURE KNOWLEDGE GRAPH DESIGN

Once MVP is stable, the graph should evolve:

```text
                 Agent
                /  |  \
               /   |   \
              v    v    v
          Session Tool Skill
             |
             v
            Span
          /  |  \
         /   |   \
        v    v    v
      LLM   Tool Observation
                    |
                    v
                   Fact
                 /     \
                v       v
             Entity   Entity
```

Every fact requires:

```text
source_span_id
confidence
created_at
valid_from
valid_until
```

This preserves provenance.

---

# 61. FUTURE MEMORY ARCHITECTURE

```text
                    Query
                      |
          +-----------+-----------+
          |                       |
          v                       v
     Vector Search          Graph Traversal
          |                       |
          +-----------+-----------+
                      |
                  Reranking
                      |
          +-----------+-----------+
          |           |           |
       recency    confidence   relevance
                      |
                      v
               Context Bundle
                      |
                      v
                    Agent
```

Memory must remain separate from raw observability events.

---

# 62. FUTURE SCALING ARCHITECTURE

Only when real load requires it:

```text
Agents
  |
  v
SDK
  |
  v
Load Balancer
  |
  v
Ingestion API
  |
  v
Kafka/NATS
  |
  +------------+-------------+
  |            |             |
  v            v             v
Postgres    ClickHouse    Graph DB
                              |
                              v
                           Vector DB
                              |
                              v
                         Query Layer
```

Do not implement this architecture during MVP.

---

# 63. FUTURE MULTI-TENANCY

Eventually every resource should support:

```text
tenant_id
project_id
agent_id
session_id
```

Authorization hierarchy:

```text
Organization
   |
   +-- Project
        |
        +-- Agent
             |
             +-- Session
```

Implement only after core product validation.

---

# 64. FUTURE DIFFERENTIATION

The long-term product can differentiate through:

1. universal agent event schema,
2. automatic instrumentation,
3. execution DAG,
4. provenance-aware Knowledge Graph,
5. graph-native memory,
6. session replay,
7. MCP access,
8. framework-independent architecture.

But do not attempt all differentiators simultaneously.

---

# 65. FINAL PRODUCT ARCHITECTURE

Eventually:

```text
                         AI AGENTS
        +------------------+------------------+
        |                  |                  |
    Claude Code        LangGraph          Custom
        |                  |                  |
        +------------------+------------------+
                           |
                    UNIVERSAL SDK
                           |
                    AgentEvent Stream
                           |
                    OpenTelemetry Model
                           |
                    Ingestion Layer
                           |
                +----------+----------+
                |                     |
           Event Store           Stream Bus
                |                     |
                +----------+----------+
                           |
                  Processing Pipeline
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
       Trace            Analytics       Semantic
        DAG                              Graph
          |                                |
          |                                v
          |                             Memory
          |                                |
          +---------------+----------------+
                          |
                     Query API
                          |
              +-----------+-----------+
              |                       |
              v                       v
          Dashboard                  MCP
```

---

# 66. MOST IMPORTANT IMPLEMENTATION RULE

Do not build the "Knowledge Graph product" first.

Build:

```text
UNIVERSAL EVENTS
       ↓
TRACE
       ↓
DAG
       ↓
OBSERVABILITY
```

Then:

```text
OBSERVABILITY
       ↓
PROVENANCE
       ↓
KNOWLEDGE GRAPH
       ↓
MEMORY
```

This keeps the project implementable while preserving the long-term architecture.

---

# 67. FIRST SUCCESS CRITERION

The first meaningful demo is:

```text
1. Start PostgreSQL
2. Start AOG server
3. Start dashboard
4. Run demo agent
5. Agent performs:
      LLM
      Tool
      Tool result
      LLM
6. Events are exported asynchronously
7. Session appears in dashboard
8. User clicks session
9. DAG appears
10. User clicks a tool node
11. Input/output/timing/status appears
12. Timeline shows execution order
13. Analytics show tool/model/token statistics
```

If this works, the core product exists.

Everything after this is expansion.

---

# 68. DEFINITION OF THE CORE ABSTRACTION

The project should always be explainable in one sentence:

> **AOG is a universal event-based observability layer for AI agents that turns agent execution into an inspectable trace/DAG and can later project the same provenance into a Knowledge Graph and memory system.**

Start with the event model. Build the trace system. Make the DAG beautiful and reliable. Then expand.
