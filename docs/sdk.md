# AgentDAC — Python SDK Reference

The AgentDAC Python SDK allows you to instrument AI agents, tools, LLMs, and skills with minimal boilerplate, automatic backend lifecycle management, and built-in fail-open resilience.

---

## 1. Installation

```bash
pip install agentdac
# or with uv:
uv add agentdac
```

The canonical import is `agentdac`; the legacy alias `aog` is preserved for backward compatibility:
```python
from agentdac import AgentDAC, EventStatus, EventType
# or:
from aog import AOG
```

---

## 2. Client Initialization

```python
from agentdac import AgentDAC

# Managed Local Mode (Default: auto-starts local backend if not running)
aog = AgentDAC(agent_id="my-agent")

# Remote / External Backend Mode
aog = AgentDAC(
    agent_id="production-agent",
    endpoint="http://agentdac.internal:8000",
    auto_start=False,
    fail_open=True,  # Agent continues uninterrupted if telemetry is unavailable
)
```

### Configuration Options (`AgentDACConfig`)

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `agent_id` | `str` | `"default-agent"` | Identifier for the instrumented agent |
| `endpoint` | `str` | `"http://127.0.0.1:8000"` | AgentDAC backend API endpoint |
| `port` | `int` | `8000` | Port for local backend auto-management |
| `auto_start` | `bool` | `True` | Whether to automatically spawn local backend |
| `fail_open` | `bool` | `True` | Suppress exporter errors so agent never crashes |
| `queue_size` | `int` | `5000` | Max in-memory buffered spans |
| `batch_size` | `int` | `50` | Spans per export batch |
| `flush_interval_ms` | `int` | `500` | Export flush frequency in milliseconds |
| `max_payload_bytes`| `int` | `100000` | Truncation limit for inputs/outputs |

---

## 3. Context-Managed Tracing

AgentDAC uses Python `contextvars` to automatically link parent and child spans across nested operations.

### 3.1 Sessions
A session defines the root boundary of an execution workflow:
```python
with aog.session(session_id="session-123", metadata={"task": "market_research"}) as session:
    # All child spans automatically attach to this session root
    pass
```

### 3.2 Agents
Track distinct agent personas or sub-agents in a multi-agent choreography:
```python
with aog.agent("market_analyst", attributes={"role": "Trend Evaluator"}) as agent_span:
    agent_span.set_input({"query": "AI observability"})
    # child operations...
    agent_span.set_output({"verdict": "High growth sector"})
```

### 3.3 LLMs
Record model inference parameters, prompt/completion tokens, and financial cost:
```python
with aog.llm(model="claude-3-7-sonnet", provider="anthropic") as llm_span:
    llm_span.set_input({"prompt": "Analyze market trends..."})
    llm_span.set_tokens(tokens_in=450, tokens_out=180)
    llm_span.set_cost(0.0035)
    llm_span.set_output({"analysis": "..."})
```

### 3.4 Tools
Capture tool arguments, return values, and execution timing:
```python
with aog.tool("web_search", input_data={"query": "agent telemetry"}) as tool_span:
    results = perform_search("agent telemetry")
    tool_span.set_output({"results": results})
```

### 3.5 Skills
Track specialized procedural reasoning capabilities or scoring algorithms:
```python
with aog.skill("luxury_budget_scoring", attributes={"algorithm": "weighted"}) as skill_span:
    skill_span.set_input({"budget": 500, "stars": 4})
    skill_span.set_output({"confidence": 0.96})
```

---

## 4. Decorator-Based Instrumentation

For functional codebases, use decorators to instrument functions without modifying their call sites:

```python
from agentdac import AgentDAC

aog = AgentDAC()

@aog.agent(role="Data Extractor")
def run_extractor(url: str) -> dict:
    return fetch_content(url)

@aog.tool(name="fetch_url")
def fetch_content(url: str) -> dict:
    return {"html": "..."}

@aog.llm(model="gpt-4o", provider="openai")
def summarize(text: str) -> str:
    return "Summary text"

@aog.skill(name="entity_linker")
def link_entities(text: str) -> list[str]:
    return ["Entity A", "Entity B"]
```

---

## 5. Direct Event Recording

For custom integrations or low-level hooks, record raw events directly:

```python
aog.record(
    event_type="tool",
    name="custom_calculator",
    input={"expression": "40 * 1.05"},
    output={"result": 42},
    duration_ms=12.4,
)
```

---

## 6. Flushing & Teardown

Because AgentDAC processes and exports events asynchronously in the background, call `flush()` before process exit:

```python
# Flush all queued spans to the backend (blocking up to timeout seconds)
aog.flush(timeout=3.0)

# Optional complete shutdown
aog.shutdown()
```
