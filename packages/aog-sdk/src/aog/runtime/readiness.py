"""Readiness probe for waiting until AgentDAC backend is fully operational."""

import time

from aog.runtime.health import check_backend_health


def wait_for_ready(endpoint: str, timeout: float = 10.0, poll_interval: float = 0.1) -> bool:
    """Poll the backend health endpoint until it becomes ready or timeout occurs."""
    start_time = time.monotonic()
    while time.monotonic() - start_time < timeout:
        if check_backend_health(endpoint, timeout=min(poll_interval, 1.0)):
            return True
        time.sleep(poll_interval)
    return False
