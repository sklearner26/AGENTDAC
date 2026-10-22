"""
AgentDAC — Minimal 5-Line Universal Quickstart.

Demonstrates the zero-configuration auto-managed backend lifecycle.
Instantiating AgentDAC automatically detects or launches the local
FastAPI + SQLite backend, records nested LLM and tool spans, and
flushes events asynchronously.

Run:
    uv run python examples/quickstart_basic.py
"""

from agentdac import AgentDAC


def main() -> None:
    # 1. Initialize AgentDAC (auto-manages local backend lifecycle)
    aog = AgentDAC(agent_id="quickstart-agent")

    print("[*] Recording agent session...")

    # 2. Context-managed session with child spans
    with aog.session(metadata={"task": "market_analysis"}):
        with aog.llm(model="claude-3-7-sonnet", provider="anthropic") as span:
            span.set_tokens(tokens_in=350, tokens_out=90)
            span.set_cost(0.0024)

        with aog.tool("web_search") as span:
            span.set_input({"query": "AI agent telemetry standards"})
            span.set_output({"results": ["AgentDAC universal observability standard"]})

        with aog.skill("data_synthesis") as span:
            span.set_input({"raw_records": 10})
            span.set_output({"verdict": "High correlation discovered"})

    aog.flush(timeout=2.0)
    print("[OK] Session recorded and flushed successfully!")

if __name__ == "__main__":
    main()
