"""Redaction configuration and default rules for AOG."""

from dataclasses import dataclass, field

DEFAULT_REDACT_KEYS: frozenset[str] = frozenset(
    {
        "api_key",
        "apikey",
        "authorization",
        "auth_token",
        "access_token",
        "refresh_token",
        "token",
        "password",
        "secret",
        "secret_key",
        "client_secret",
        "private_key",
        "ssh_key",
        "cookie",
        "set_cookie",
        "x-api-key",
    }
)

REDACTED_PLACEHOLDER = "[REDACTED]"


@dataclass(frozen=True)
class RedactionConfig:
    """Settings controlling payload redaction and data capture limits."""

    redact_keys: frozenset[str] = field(default=DEFAULT_REDACT_KEYS)
    max_payload_bytes: int = 100_000
    max_string_length: int = 10_000
    capture_input: bool = True
    capture_output: bool = True
    capture_tool_args: bool = True
    capture_tool_results: bool = True
    redact_stacktraces: bool = False
