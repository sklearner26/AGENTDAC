"""Unit tests for payload redaction and secret sanitization."""

from aog.redaction.rules import REDACTED_PLACEHOLDER, RedactionConfig
from aog.redaction.sanitizer import Sanitizer


class TestSanitizer:
    def test_default_sensitive_keys_redacted(self) -> None:
        sanitizer = Sanitizer()
        data = {
            "api_key": "sk-secret12345",
            "Authorization": "Bearer abcde",
            "user": "alice",
            "nested": {
                "PASSWORD": "secretpassword",
                "token": "tok123",
                "safe_field": 42,
            },
        }

        result = sanitizer.sanitize(data)
        assert result["api_key"] == REDACTED_PLACEHOLDER
        assert result["Authorization"] == REDACTED_PLACEHOLDER
        assert result["user"] == "alice"
        assert result["nested"]["PASSWORD"] == REDACTED_PLACEHOLDER
        assert result["nested"]["token"] == REDACTED_PLACEHOLDER
        assert result["nested"]["safe_field"] == 42

    def test_string_truncation(self) -> None:
        cfg = RedactionConfig(max_string_length=10)
        sanitizer = Sanitizer(config=cfg)
        result = sanitizer.sanitize({"text": "abcdefghijklmnopqrstuvwxyz"})
        assert result["text"] == "abcdefghij...[TRUNCATED]"

    def test_payload_byte_limit(self) -> None:
        cfg = RedactionConfig(max_payload_bytes=50)
        sanitizer = Sanitizer(config=cfg)
        huge_dict = {f"key_{i}": "x" * 20 for i in range(10)}
        result = sanitizer.sanitize(huge_dict)
        assert result.get("_truncated") is True

    def test_custom_redactor(self) -> None:
        def custom(d: dict[str, str]) -> dict[str, str]:
            return {k: v.replace("SSN-1234", "[MASKED]") for k, v in d.items()}

        sanitizer = Sanitizer(custom_redactor=custom)
        result = sanitizer.sanitize({"info": "User SSN-1234 entered"})
        assert result["info"] == "User [MASKED] entered"
