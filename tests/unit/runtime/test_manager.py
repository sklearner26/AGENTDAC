"""Tests for AgentDAC RuntimeManager lifecycle."""

from unittest.mock import MagicMock

import pytest
from aog.config import AOGConfig
from aog.exceptions import AOGError
from aog.runtime.manager import RuntimeManager


def test_runtime_manager_external_healthy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("aog.runtime.manager.check_backend_health", lambda _url: True)
    mgr = RuntimeManager()
    cfg = AOGConfig(endpoint="http://external-server:8000", auto_start=False)
    endpoint = mgr.ensure_backend(cfg)
    assert endpoint == "http://external-server:8000"


def test_runtime_manager_external_unhealthy_fail_open(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("aog.runtime.manager.check_backend_health", lambda _url: False)
    mgr = RuntimeManager()
    cfg = AOGConfig(endpoint="http://external-server:8000", auto_start=False, fail_open=True)
    endpoint = mgr.ensure_backend(cfg)
    assert endpoint == "http://external-server:8000"


def test_runtime_manager_external_unhealthy_strict(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("aog.runtime.manager.check_backend_health", lambda _url: False)
    mgr = RuntimeManager()
    cfg = AOGConfig(endpoint="http://external-server:8000", auto_start=False, fail_open=False)
    with pytest.raises(AOGError):
        mgr.ensure_backend(cfg)


def test_runtime_manager_reuse_existing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("aog.runtime.manager.check_backend_health", lambda _url: True)
    mgr = RuntimeManager()
    cfg = AOGConfig(auto_start=True)
    endpoint = mgr.ensure_backend(cfg)
    assert endpoint == "http://127.0.0.1:8000"
    assert mgr._owned_process is None


def test_runtime_manager_spawn_and_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    # First check: False, then wait_for_ready: True
    health_calls = []

    def mock_health(url: str) -> bool:
        health_calls.append(url)
        return False

    monkeypatch.setattr("aog.runtime.manager.check_backend_health", mock_health)
    monkeypatch.setattr(
        "aog.runtime.manager.wait_for_ready", lambda *_args, **_kwargs: True
    )

    mock_proc = MagicMock()
    monkeypatch.setattr("aog.runtime.manager.BackendProcess", lambda *_args, **_kwargs: mock_proc)

    mgr = RuntimeManager()
    cfg = AOGConfig(auto_start=True)
    endpoint = mgr.ensure_backend(cfg)

    assert endpoint == "http://127.0.0.1:8000"
    mock_proc.start.assert_called_once()
    assert mgr._owned_process == mock_proc

    mgr.shutdown()
    mock_proc.stop.assert_called_once()
