"""Integration tests for AgentDAC Runtime lifecycle (Requirements §13, §14, §36, §37, §39, §40)."""

import concurrent.futures

import pytest
from agentdac import AgentDAC
from aog.runtime.manager import RuntimeManager


def test_multiple_sdk_instances_share_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies that multiple AgentDAC instances do not create duplicate backends."""
    monkeypatch.setattr("aog.runtime.manager.check_backend_health", lambda _url: True)

    a = AgentDAC()
    b = AgentDAC()
    c = AgentDAC()

    assert a.config.endpoint == b.config.endpoint == c.config.endpoint
    # Ensure all instances use the same runtime manager singleton
    mgr = RuntimeManager.get_instance()
    assert mgr._owned_process is None  # Reused healthy backend without spawning extra processes


def test_concurrent_startup_synchronization(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulates concurrent threads/processes attempting to initialize SDK simultaneously."""
    spawn_count = 0

    def mock_health(_url: str) -> bool:
        nonlocal spawn_count
        # Return False before spawn, True after first spawn
        return spawn_count > 0

    def mock_spawn(_self: object) -> None:
        nonlocal spawn_count
        spawn_count += 1

    monkeypatch.setattr("aog.runtime.manager.check_backend_health", mock_health)
    monkeypatch.setattr(
        "aog.runtime.manager.wait_for_ready", lambda _url, _timeout, _poll_interval: True
    )
    monkeypatch.setattr("aog.runtime.process.BackendProcess.start", mock_spawn)

    def init_client() -> AgentDAC:
        return AgentDAC()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(init_client) for _ in range(5)]
        clients = [f.result() for f in futures]

    assert len(clients) == 5
    # The lock must guarantee that spawn was called at most once
    assert spawn_count == 1
