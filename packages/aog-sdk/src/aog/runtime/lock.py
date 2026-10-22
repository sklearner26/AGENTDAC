"""Inter-process locking for AgentDAC runtime startup synchronization."""

import os
import tempfile
from pathlib import Path
from typing import Any

from filelock import FileLock, Timeout


class RuntimeLock:
    """Cross-platform inter-process file lock preventing duplicate backend startup."""

    def __init__(self, lock_path: str | Path | None = None, timeout: float = 15.0) -> None:
        if lock_path is None:
            lock_dir = Path(os.getenv("AGENTDAC_LOCK_DIR", tempfile.gettempdir())) / ".agentdac"
            lock_dir.mkdir(parents=True, exist_ok=True)
            self.lock_file = lock_dir / "agentdac_runtime.lock"
        else:
            self.lock_file = Path(lock_path)
            self.lock_file.parent.mkdir(parents=True, exist_ok=True)

        self.timeout = timeout
        self._lock = FileLock(str(self.lock_file), timeout=self.timeout)

    def acquire(self) -> bool:
        """Acquire the lock within the configured timeout."""
        try:
            self._lock.acquire(timeout=self.timeout)
        except Timeout:
            return False
        else:
            return True

    def release(self) -> None:
        """Release the lock if acquired."""
        try:
            if self._lock.is_locked:
                self._lock.release()
        except Exception:
            pass

    def __enter__(self) -> "RuntimeLock":
        self.acquire()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.release()
