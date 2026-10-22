# AgentDAC — Integrations Guide

AgentDAC provides plug-and-play adapters for popular AI agent frameworks and platforms, translating native framework executions into the standardized `AgentEvent` stream.

---

## Supported Frameworks & Ecosystem

| Integration | Type | Features | Status |
| :--- | :--- | :--- | :--- |
| **LangGraph** | Native Callback | StateGraph steps, node transitions, token tracking | ✅ Production Ready |
| **LangChain** | Native Callback | Chains, Tool calls, Chat models, Agents | ✅ Production Ready |
| **Claude Code** | CLI Hook Adapter | Real-time CLI tool execution, command steps | ✅ Production Ready |
| **Custom Python Agents** | Decorators / Context Managers | Multi-agent coordination, specialized skills, tools | ✅ Production Ready |
| **OpenAI Agents / CrewAI** | Generic Adapter | Extensible wrapper for custom agent loops | 🔵 Compatible |

---

## 1. LangGraph & LangChain Integration

AgentDAC includes a zero-boilerplate callback handler (`AgentDACCallbackHandler`) that maps LangChain and LangGraph executions into hierarchical execution graphs.

### Installation
```bash
pip install agentdac langchain langchain-openai langgraph
```

### LangGraph StateGraph Example
```python
from agentdac import AgentDAC
from aog.integrations.langchain import AgentDACCallbackHandler
from langgraph.graph import StateGraph, START, END

# 1. Initialize AgentDAC
aog = AgentDAC(agent_id="travel-concierge")

# 2. Instantiate the callback handler
handler = AgentDACCallbackHandler(aog, session_id="trip-session-42")

# 3. Attach handler to the compiled graph execution
graph = workflow.compile()
result = graph.invoke(
    {"query": "Book 5 days in Kyoto"},
    config={"callbacks": [handler]}
)
```

### What It Tracks Automatically
- `on_chain_start` / `on_chain_end` $\rightarrow$ Graph execution nodes and state mutations
- `on_llm_start` / `on_llm_end` $\rightarrow$ Model inference spans, prompt/completion tokens, and provider metadata
- `on_tool_start` / `on_tool_end` $\rightarrow$ Tool inputs, outputs, and execution duration
- `on_chain_error` / `on_tool_error` $\rightarrow$ Error classifications and stack traces

---

## 2. Claude Code CLI Hook Integration

AgentDAC integrates natively with Anthropic's Claude Code CLI. It receives observable hook events via stdin, capturing tool calls, bash executions, and operational metadata without ever accessing or recording private chain-of-thought tokens.

### Configuration

#### Automatic Configuration
```bash
python -m integrations.claude_code.setup
```
This automatically updates `~/.claude/settings.json` to route events to the AgentDAC hook handler.

#### Manual Configuration (`~/.claude/settings.json`)
```json
{
  "hooks": {
    "post_tool_use": "agentdac-claude-hook",
    "pre_tool_use": "agentdac-claude-hook"
  }
}
```

### Hook Protocol & Ingestion
Events are passed as JSON objects via stdin:
```bash
agentdac-claude-hook < event.json
```

**Captured Fields**:
- `session_id`: Correlates consecutive CLI actions into a unified trace
- `tool` / `name`: The executed command or tool (e.g. `bash`, `view_file`, `git_commit`)
- `input` / `output`: Arguments and sanitized responses
- `duration_ms`: Execution latency
- `status`: `ok` or `error`

---

## 3. Generic Custom Python Agent Integration

For custom agent frameworks or homegrown agentic loops, AgentDAC provides rich context managers and decorators.

### Using Context Managers
```python
from agentdac import AgentDAC

aog = AgentDAC(agent_id="research-assistant")

with aog.session(session_id="session-001", metadata={"goal": "tech_analysis"}):
    
    # 1. Agent Span
    with aog.agent("planner_agent", attributes={"role": "Task Decomposition"}) as agent:
        agent.set_input({"query": "Evaluate AgentDAC"})
        
        # 2. LLM Call
        with aog.llm(model="gpt-4o", provider="openai") as llm:
            llm.set_tokens(tokens_in=450, tokens_out=180)
            llm.set_cost(0.0035)
            
        # 3. Tool Call
        with aog.tool("github_search", input_data={"repo": "AGENTDAC"}) as tool:
            tool.set_output({"stars": 120, "forks": 15})
            
        # 4. Specialized Skill Execution
        with aog.skill("code_quality_scorer") as skill:
            skill.set_input({"test_coverage": "100%"})
            skill.set_output({"score": 98.5})
            
        agent.set_output({"status": "verified"})

aog.flush(timeout=3.0)
```

### Using Decorators
```python
from agentdac import AgentDAC

aog = AgentDAC()

@aog.agent(role="Researcher")
def conduct_research(topic: str) -> dict:
    return query_tools(topic)

@aog.tool(name="web_search")
def query_tools(query: str) -> list[str]:
    return ["result 1", "result 2"]

@aog.skill(name="summarization_skill")
def summarize(data: list[str]) -> str:
    return "Summary"
```

---

## 4. TripMate AI Case Study

For a comprehensive real-world walkthrough of a 5-agent LangGraph system instrumented with AgentDAC, see:
👉 **[TripMate AI Proof of Concept (POC) Case Study](poc-tripmate-case-study.md)**
