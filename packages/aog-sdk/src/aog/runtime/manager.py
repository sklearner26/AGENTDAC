"""Runtime Manager for AgentDAC SDK and Backend lifecycle."""

import atexit
import logging
from urllib.parse import urlparse

from aog.config import AOGConfig
from aog.exceptions import AOGError
from aog.runtime.health import check_backend_health
from aog.runtime.lock import RuntimeLock
from aog.runtime.process import BackendProcess
from aog.runtime.readiness import wait_for_ready

logger = logging.getLogger("agentdac.runtime")

LOCAL_HOSTS = ("localhost", "127.0.0.1", "0.0.0.0")
DEFAULT_ENDPOINTS = ("http://localhost:8000", "http://127.0.0.1:8000")


class RuntimeManager:
    """Manages detection, automatic startup, readiness, and shutdown of the AgentDAC backend."""

    _instance: "RuntimeManager | None" = None

    def __init__(self) -> None:
        self._owned_process: BackendProcess | None = None
        self._lock = RuntimeLock()
        self._initialized = False
        self._active_endpoint: str | None = None
        self._registered_atexit = False

    @classmethod
    def get_instance(cls) -> "RuntimeManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _handle_external(self, target_endpoint: str, fail_open: bool) -> str:
        if check_backend_health(target_endpoint):
            logger.info(f"backend_detected external_endpoint={target_endpoint}")
        else:
            logger.warning(f"backend_unavailable external_endpoint={target_endpoint}")
            if not fail_open:
                raise AOGError(f"AgentDAC external backend unreachable at {target_endpoint}")
        self._active_endpoint = target_endpoint
        return target_endpoint

    def _start_local_backend(self, host: str, port: int, endpoint: str, fail_open: bool) -> str:
        start_error: Exception | None = None
        is_ready = False
        try:
            proc = BackendProcess(host=host, port=port)
            proc.start()
            self._owned_process = proc
            is_ready = wait_for_ready(endpoint, timeout=10.0, poll_interval=0.1)
        except Exception as e:
            start_error = e
            logger.warning(f"backend_start_failed endpoint={endpoint} error={e}")
            if self._owned_process:
                self._owned_process.stop()
                self._owned_process = None

        if is_ready:
            logger.info(f"backend_ready endpoint={endpoint}")
            self._active_endpoint = endpoint
            self._register_exit_hooks()
            return endpoint

        if start_error is None:
            logger.warning(
                f"backend_start_failed endpoint={endpoint} (timeout waiting for health)"
            )
            if self._owned_process:
                self._owned_process.stop()
                self._owned_process = None

        if not fail_open:
            if start_error is not None:
                raise AOGError(f"Failed to start AgentDAC backend: {start_error}") from start_error
            raise AOGError(f"AgentDAC backend failed to become ready at {endpoint}")

        self._active_endpoint = endpoint
        return endpoint

    def ensure_backend(self, config: AOGConfig) -> str:
        """Ensure a healthy AgentDAC backend is reachable, starting one locally if needed."""
        target_endpoint = config.endpoint.rstrip("/")
        parsed = urlparse(target_endpoint)
        host = parsed.hostname or config.host
        port = parsed.port or config.port

        # Mode B: External or Auto-start disabled
        if not config.auto_start or (
            host not in LOCAL_HOSTS and config.endpoint not in DEFAULT_ENDPOINTS
        ):
            return self._handle_external(target_endpoint, config.fail_open)

        # Mode A: Managed Local Mode
        local_endpoint = f"http://{host}:{port}"

        # Fast check if already running & healthy
        if check_backend_health(local_endpoint):
            logger.info(f"backend_reused endpoint={local_endpoint}")
            self._active_endpoint = local_endpoint
            return local_endpoint

        # Acquire lock for cross-process safe startup
        with self._lock:
            # Re-check health after acquiring lock
            if check_backend_health(local_endpoint):
                logger.info(f"backend_reused endpoint={local_endpoint}")
                self._active_endpoint = local_endpoint
                return local_endpoint

            return self._start_local_backend(host, port, local_endpoint, config.fail_open)

    def _register_exit_hooks(self) -> None:
        if not self._registered_atexit:
            atexit.register(self.shutdown)
            self._registered_atexit = True

    def shutdown(self, terminate_process: bool = True) -> None:
        """Gracefully release resources and terminate owned backend subprocess if requested."""
        if terminate_process and self._owned_process is not None:
            self._owned_process.stop()
            self._owned_process = None
            self._active_endpoint = None
