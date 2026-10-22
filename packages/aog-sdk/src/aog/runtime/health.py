"""Health check client for verifying AgentDAC backend availability."""

import logging
from typing import Any

import httpx

logger = logging.getLogger("agentdac.runtime")

HTTP_OK = 200

VALID_SERVICES = {
    "agentdac",
    "aog-server",
    "agent-observability-graph",
    "AgentDAC Ingestion and Visualization API",
    "Agent Observability Graph (AOG) API",
}


def check_backend_health(endpoint: str, timeout: float = 1.0) -> bool:
    """Verify that an AgentDAC backend is responsive and returns a valid health payload."""
    url = f"{endpoint.rstrip('/')}/health"
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url)
            if response.status_code == HTTP_OK:
                data: dict[str, Any] = response.json()
                status_val = data.get("status")
                service_val = data.get("service")
                if status_val == "ok" and (
                    service_val is None
                    or service_val in VALID_SERVICES
                    or "agentdac" in str(service_val).lower()
                    or "aog" in str(service_val).lower()
                ):
                    return True
            return False
    except Exception:
        return False
