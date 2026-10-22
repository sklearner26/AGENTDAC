"""LangChain / LangGraph auto-instrumentation callback handler for AgentDAC.

Usage (LangChain):
    from aog import AgentDAC
    from aog.integrations.langchain import AgentDACCallbackHandler

    aog = AgentDAC(agent_id="my-agent")
    handler = AgentDACCallbackHandler(aog)

    chain.invoke({"input": "..."}, config={"callbacks": [handler]})

Usage (LangGraph):
    from aog.integrations.langchain import AgentDACCallbackHandler

    handler = AgentDACCallbackHandler(aog)
    graph.invoke(state, config={"callbacks": [handler]})
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any
from uuid import UUID

from aog.context import TraceContext, get_current_context
from aog.events.enums import EventType

if TYPE_CHECKING:
    from langchain_core.outputs import LLMResult  # type: ignore[import-not-found]

    from aog.client import AOG


class AgentDACCallbackHandler:
    """LangChain-compatible callback that streams execution events to AgentDAC.

    Tracks:
    - LLM calls (prompt tokens, completion tokens, model name, latency)
    - Tool executions (name, input, output, latency, status)
    - Chain runs (name, inputs, outputs)
    - Agent actions & finishes
    - LangGraph node transitions (via on_chain_start with node name metadata)
    """

    def __init__(
        self,
        aog: AOG,
        agent_id: str | None = None,
        session_id: str | None = None,
    ) -> None:
        self._aog = aog
        self._agent_id = agent_id or getattr(aog.config, "agent_id", "langchain-agent")
        self._session_id = session_id
        # run_id → {span_ctx, start_time}
        self._pending: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _metadata(kwargs: dict[str, Any]) -> dict[str, Any]:
        """Keep callback metadata observable without capturing model reasoning."""
        metadata = kwargs.get("metadata") or {}
        tags = kwargs.get("tags") or []
        result = {"framework": "langchain", "tags": list(tags)}
        if isinstance(metadata, dict):
            result.update(metadata)
        for key in ("reason", "skill", "skill_name", "tool"):
            if key in kwargs and kwargs[key] is not None:
                result[key] = kwargs[key]
        return result

    def _parent_context(self, parent_run_id: UUID | None) -> TraceContext | None:
        """Rebuild the parent relationship when callbacks run in another task."""
        if parent_run_id is not None:
            parent = self._pending.get(str(parent_run_id))
            if parent and (span := getattr(parent["span_ctx"], "span", None)) is not None:
                return TraceContext(
                    trace_id=span.trace_id,
                    session_id=span.session_id,
                    agent_id=span.agent_id,
                    current_span_id=span.span_id,
                )
        return get_current_context()

    def _start(self, run_id: UUID, parent_run_id: UUID | None, span_ctx: Any, **state: Any) -> None:
        span_ctx.parent_context = self._parent_context(parent_run_id)
        span_ctx.__enter__()
        self._pending[str(run_id)] = {
            "span_ctx": span_ctx,
            "start": time.perf_counter(),
            "parent_run_id": str(parent_run_id) if parent_run_id else None,
            **state,
        }

    # ------------------------------------------------------------------ #
    # LLM callbacks                                                        #
    # ------------------------------------------------------------------ #

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        model = (
            serialized.get("kwargs", {}).get("model_name")
            or serialized.get("kwargs", {}).get("model")
            or "unknown-model"
        )
        provider = serialized.get("id", ["", ""])[2] if serialized.get("id") else None
        attrs = self._metadata(kwargs)
        attrs.update({"agent_id": self._agent_id, "run_id": str(run_id)})
        span_ctx = self._aog.llm(
            model=model,
            provider=provider,
            name=f"llm:{model}",
            attributes=attrs,
        )
        self._start(run_id, parent_run_id, span_ctx, model=model)

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> None:
        state = self._pending.pop(str(run_id), None)
        if state is None:
            return
        span_ctx = state["span_ctx"]
        # Extract token usage if available
        usage = {}
        if response.llm_output:
            usage = response.llm_output.get("token_usage", {})
        tokens_in = usage.get("prompt_tokens")
        tokens_out = usage.get("completion_tokens")
        # Set on the underlying span if accessible
        span = getattr(span_ctx, "span", None)
        if span is not None:
            if tokens_in:
                span.tokens_in = tokens_in
            if tokens_out:
                span.tokens_out = tokens_out
        span_ctx.__exit__(None, None, None)

    def on_llm_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        state = self._pending.pop(str(run_id), None)
        if state is None:
            return
        state["span_ctx"].__exit__(type(error), error, error.__traceback__)

    # ------------------------------------------------------------------ #
    # Tool callbacks                                                       #
    # ------------------------------------------------------------------ #

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        tool_name = serialized.get("name", "unknown_tool")
        attrs = self._metadata(kwargs)
        attrs.update({"agent_id": self._agent_id, "tool": tool_name, "run_id": str(run_id)})
        span_ctx = self._aog.tool(tool_name, attributes=attrs, input_data={"input": input_str})
        self._start(run_id, parent_run_id, span_ctx, tool=tool_name)

    def on_tool_end(self, output: str, *, run_id: UUID, **kwargs: Any) -> None:
        state = self._pending.pop(str(run_id), None)
        if state is None:
            return
        span = getattr(state["span_ctx"], "span", None)
        if span is not None:
            span.set_output({"output": output[:2000]})  # truncate large outputs
        state["span_ctx"].__exit__(None, None, None)

    def on_tool_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        state = self._pending.pop(str(run_id), None)
        if state is None:
            return
        state["span_ctx"].__exit__(type(error), error, error.__traceback__)

    # ------------------------------------------------------------------ #
    # Chain / LangGraph node callbacks                                     #
    # ------------------------------------------------------------------ #

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        name = (
            kwargs.get("name")
            or serialized.get("name")
            or serialized.get("id", ["unknown"])[-1]
            or "chain"
        )
        # LangGraph passes node name via kwargs["name"]
        attrs = self._metadata(kwargs)
        attrs.update({"agent_id": self._agent_id, "run_id": str(run_id)})
        span_ctx = self._aog.agent(name, attributes=attrs)
        self._start(run_id, parent_run_id, span_ctx, name=name)
        span = getattr(span_ctx, "span", None)
        if span is not None:
            span.set_input(inputs if isinstance(inputs, dict) else {"raw": str(inputs)[:500]})

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        state = self._pending.pop(str(run_id), None)
        if state is None:
            return
        span = getattr(state["span_ctx"], "span", None)
        if span is not None and isinstance(outputs, dict):
            span.set_output(outputs)
        state["span_ctx"].__exit__(None, None, None)

    def on_chain_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        state = self._pending.pop(str(run_id), None)
        if state is None:
            return
        state["span_ctx"].__exit__(type(error), error, error.__traceback__)

    # ------------------------------------------------------------------ #
    # Agent action callbacks                                               #
    # ------------------------------------------------------------------ #

    def on_agent_action(
        self, action: Any, *, run_id: UUID, parent_run_id: UUID | None = None, **kwargs: Any
    ) -> None:
        tool_name = getattr(action, "tool", "unknown")
        tool_input = getattr(action, "tool_input", {})
        self._aog.record(
            event_type=EventType.DECISION,
            name=f"agent_action:{tool_name}",
            input_data={"tool": tool_name, "input": tool_input},
            attributes={
                **self._metadata(kwargs),
                "agent_id": self._agent_id,
                "tool": tool_name,
                "run_id": str(run_id),
                "parent_run_id": str(parent_run_id) if parent_run_id else None,
            },
        )

    def on_agent_finish(
        self, finish: Any, *, run_id: UUID, parent_run_id: UUID | None = None, **kwargs: Any
    ) -> None:
        return_values = getattr(finish, "return_values", {})
        self._aog.record(
            event_type=EventType.OBSERVATION,
            name="agent_finish",
            output_data=return_values,
            attributes={
                **self._metadata(kwargs),
                "agent_id": self._agent_id,
                "run_id": str(run_id),
                "parent_run_id": str(parent_run_id) if parent_run_id else None,
            },
        )
