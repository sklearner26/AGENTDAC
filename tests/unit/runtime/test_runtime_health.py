"""Tests for AgentDAC runtime health check verification."""

import pytest
from aog.runtime.health import check_backend_health


def test_health_check_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockResponse:
        status_code = 200

        def json(self) -> dict[str, str]:
            return {"status": "ok", "service": "agentdac"}

    class MockClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def __enter__(self) -> "MockClient":
            return self

        def __exit__(self, *args: object) -> None:
            pass

        def get(self, url: str) -> MockResponse:
            return MockResponse()

    monkeypatch.setattr("httpx.Client", MockClient)
    assert check_backend_health("http://127.0.0.1:8000") is True


def test_health_check_invalid_service(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockResponse:
        status_code = 200

        def json(self) -> dict[str, str]:
            return {"status": "ok", "service": "some-unrelated-app"}

    class MockClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def __enter__(self) -> "MockClient":
            return self

        def __exit__(self, *args: object) -> None:
            pass

        def get(self, url: str) -> MockResponse:
            return MockResponse()

    monkeypatch.setattr("httpx.Client", MockClient)
    assert check_backend_health("http://127.0.0.1:8000") is False


def test_health_check_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def __enter__(self) -> "MockClient":
            return self

        def __exit__(self, *args: object) -> None:
            pass

        def get(self, url: str) -> None:
            raise ConnectionRefusedError("Connection refused")

    monkeypatch.setattr("httpx.Client", MockClient)
    assert check_backend_health("http://127.0.0.1:8000") is False
