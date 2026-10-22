"""Recursive payload sanitization and secret redaction."""

import contextlib
import json
from collections.abc import Callable
from typing import Any

from aog.redaction.rules import REDACTED_PLACEHOLDER, RedactionConfig

RedactorFunc = Callable[[Any], Any]


class Sanitizer:
    """Sanitizes payload dictionaries and objects according to redaction rules."""

    def __init__(
        self,
        config: RedactionConfig | None = None,
        custom_redactor: RedactorFunc | None = None,
    ) -> None:
        self.config = config or RedactionConfig()
        self.custom_redactor = custom_redactor
        self._lower_keys = {k.lower() for k in self.config.redact_keys}

    def sanitize(self, data: Any) -> Any:
        """Sanitize an arbitrary data structure (dict, list, primitive)."""
        if data is None:
            return None

        if self.custom_redactor is not None:
            with contextlib.suppress(Exception):
                data = self.custom_redactor(data)

        return self._sanitize_value(data)

    def _sanitize_dict(self, val: dict[str, Any]) -> dict[str, Any]:
        sanitized_dict: dict[str, Any] = {}
        for k, v in val.items():
            str_k = str(k)
            if str_k.lower() in self._lower_keys:
                sanitized_dict[str_k] = REDACTED_PLACEHOLDER
            else:
                sanitized_dict[str_k] = self._sanitize_value(v)
        return self._enforce_size_limit(sanitized_dict)

    def _sanitize_string(self, text: str) -> str:
        if len(text) > self.config.max_string_length:
            return text[: self.config.max_string_length] + "...[TRUNCATED]"
        return text

    def _sanitize_value(self, val: Any) -> Any:
        if isinstance(val, dict):
            return self._sanitize_dict(val)
        if isinstance(val, list | tuple | set):
            return [self._sanitize_value(item) for item in val]
        if isinstance(val, str):
            return self._sanitize_string(val)
        if isinstance(val, int | float | bool):
            return val

        try:
            val_str = str(val)
        except Exception:
            return REDACTED_PLACEHOLDER
        else:
            return self._sanitize_string(val_str)

    def _enforce_size_limit(self, data: dict[str, Any]) -> dict[str, Any]:
        """Ensure serialized JSON does not exceed max_payload_bytes."""
        try:
            encoded = json.dumps(data, default=str)
            if len(encoded.encode("utf-8")) > self.config.max_payload_bytes:
                return {
                    "_warning": "Payload exceeded maximum allowed size",
                    "_truncated": True,
                }
        except Exception:
            pass
        return data
