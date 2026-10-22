"""Unit tests for context propagation and isolation."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from aog.context import (
    TraceContext,
    get_current_context,
    set_current_context,
    with_context,
)


class TestContextPropagation:
    def test_default_context_is_none(self) -> None:
        assert get_current_context() is None

    def test_set_and_reset_context(self) -> None:
        ctx = TraceContext(
            trace_id="t1",
            session_id="s1",
            agent_id="a1",
            current_span_id="sp1",
        )
        with with_context(ctx):
            active = get_current_context()
            assert active is not None
            assert active.trace_id == "t1"
            assert active.current_span_id == "sp1"

        assert get_current_context() is None

    def test_child_context_inheritance(self) -> None:
        parent = TraceContext(
            trace_id="t1",
            session_id="s1",
            agent_id="a1",
            current_span_id="span-parent",
        )
        child = parent.child_context("span-child")
        assert child.trace_id == "t1"
        assert child.session_id == "s1"
        assert child.agent_id == "a1"
        assert child.current_span_id == "span-child"
        assert child.parent_span_id == "span-parent"

    def test_nested_context_managers(self) -> None:
        ctx1 = TraceContext(trace_id="t1", session_id="s1", agent_id="a1", current_span_id="sp1")
        ctx2 = ctx1.child_context("sp2")

        with with_context(ctx1):
            assert get_current_context() == ctx1
            with with_context(ctx2):
                active2 = get_current_context()
                assert active2 == ctx2
                assert active2 is not None and active2.parent_span_id == "sp1"
            assert get_current_context() == ctx1

        assert get_current_context() is None

    async def test_async_task_isolation(self) -> None:
        async def worker(task_id: str) -> list[str]:
            ctx = TraceContext(
                trace_id=f"trace-{task_id}",
                session_id=f"session-{task_id}",
                agent_id=f"agent-{task_id}",
                current_span_id=f"span-{task_id}",
            )
            set_current_context(ctx)
            await asyncio.sleep(0.01)
            current = get_current_context()
            assert current is not None
            return [current.trace_id, current.session_id]

        results = await asyncio.gather(*[worker(str(i)) for i in range(20)])
        for i, (trace_id, session_id) in enumerate(results):
            assert trace_id == f"trace-{i}"
            assert session_id == f"session-{i}"

    def test_thread_isolation(self) -> None:
        def thread_task(thread_id: int) -> str:
            ctx = TraceContext(
                trace_id=f"trace-{thread_id}",
                session_id=f"session-{thread_id}",
                agent_id="agent",
            )
            set_current_context(ctx)
            import time

            time.sleep(0.01)
            current = get_current_context()
            assert current is not None
            return current.trace_id

        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = [pool.submit(thread_task, i) for i in range(10)]
            for i, f in enumerate(futures):
                assert f.result() == f"trace-{i}"
