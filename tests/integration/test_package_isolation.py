"""Mandatory Package Isolation Test (Requirements §35 & §57).

Verifies that AgentDAC backend imports and runtime do not collide with
a host project that contains its own `server/app/main.py` or `backend/main.py`.
"""

import sys
import types

from aog.backend.main import app as aog_backend_app


def test_package_namespace_isolation() -> None:
    # 1. Simulate a host project with a conflicting `server.app.main` module
    fake_server = types.ModuleType("server")
    fake_server_app = types.ModuleType("server.app")
    fake_server_app_main = types.ModuleType("server.app.main")
    fake_server_app_main.app = "UNRELATED_HOST_APP_NOT_A_FASTAPI_APP"  # type: ignore[attr-defined]

    sys.modules["server"] = fake_server
    sys.modules["server.app"] = fake_server_app
    sys.modules["server.app.main"] = fake_server_app_main

    try:
        # Verify AgentDAC's backend is independent in `aog.backend` and accessible via `agentdac`
        import aog.backend.main as backend_module
        from agentdac import backend as agentdac_backend

        assert agentdac_backend.app is not None
        assert backend_module.app is not None
        assert backend_module.app.title == "AgentDAC Ingestion and Visualization API"
        assert agentdac_backend.app == aog_backend_app
        assert agentdac_backend.app != "UNRELATED_HOST_APP_NOT_A_FASTAPI_APP"
    finally:
        # Clean up simulated host modules
        sys.modules.pop("server.app.main", None)
        sys.modules.pop("server.app", None)
        sys.modules.pop("server", None)
