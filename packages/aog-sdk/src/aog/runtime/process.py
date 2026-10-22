"""Cross-platform background process manager for AgentDAC backend."""

import contextlib
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger("agentdac.runtime")


class BackendProcess:
    """Manages the lifecycle of a locally spawned AgentDAC backend server subprocess."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        self.host = host
        self.port = port
        self.process: subprocess.Popen[Any] | None = None
        self._pid: int | None = None

        log_dir = Path(os.getenv("AGENTDAC_LOG_DIR", tempfile.gettempdir())) / ".agentdac"
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = log_dir / f"backend_{self.port}.log"

    def start(self) -> None:
        """Spawn the backend server subprocess without reload."""
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "aog.backend.main:app",
            "--host",
            self.host,
            "--port",
            str(self.port),
            "--log-level",
            "warning",
        ]

        logger.info(f"backend_starting host={self.host} port={self.port}")

        log_fp = self.log_file.open("a", encoding="utf-8")

        extra_kwargs: dict[str, Any] = {}
        if sys.platform == "win32":
            extra_kwargs["creationflags"] = (
                subprocess.CREATE_NEW_PROCESS_GROUP | getattr(subprocess, "DETACHED_PROCESS", 0)
            )
        else:
            extra_kwargs["start_new_session"] = True

        self.process = subprocess.Popen(
            cmd,
            stdout=log_fp,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            close_fds=True,
            **extra_kwargs,
        )
        self._pid = self.process.pid
        logger.info(f"backend_started pid={self._pid}")

    def is_alive(self) -> bool:
        """Check if the child process is still running."""
        if self.process is None:
            return False
        return self.process.poll() is None

    def stop(self) -> None:
        """Terminate the child backend process."""
        if self.process is not None:
            logger.info(f"backend_shutdown pid={self._pid}")
            try:
                self.process.terminate()
                self.process.wait(timeout=3.0)
            except Exception:
                with contextlib.suppress(Exception):
                    self.process.kill()
            finally:
                self.process = None
                self._pid = None
