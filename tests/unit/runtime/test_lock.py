"""Tests for AgentDAC cross-process file locking."""

import tempfile
from pathlib import Path

from aog.runtime.lock import RuntimeLock


def test_runtime_lock_acquire_and_release() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        lock_path = Path(tmp_dir) / "test.lock"
        lock1 = RuntimeLock(lock_path=lock_path, timeout=1.0)
        assert lock1.acquire() is True
        lock1.release()


def test_runtime_lock_context_manager() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        lock_path = Path(tmp_dir) / "test.lock"
        with RuntimeLock(lock_path=lock_path, timeout=1.0):
            pass


def test_runtime_lock_contention() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        lock_path = Path(tmp_dir) / "test.lock"
        lock1 = RuntimeLock(lock_path=lock_path, timeout=1.0)
        lock2 = RuntimeLock(lock_path=lock_path, timeout=0.1)

        assert lock1.acquire() is True
        # lock2 should fail to acquire within timeout
        assert lock2.acquire() is False

        lock1.release()
        # now lock2 should succeed
        assert lock2.acquire() is True
        lock2.release()
