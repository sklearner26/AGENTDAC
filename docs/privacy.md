# AOG Privacy & Redaction

AOG is designed with privacy by default. Sensitive data is never automatically captured, and redaction is configurable.

## Privacy Principles

1. **Never capture secrets by default** - API keys, passwords, tokens are redacted
2. **Configurable capture** - Control what gets captured
3. **Redact recursively** - Redact nested structures
4. **Fail-safe** - Redaction failures don't break the application
5. **Provenance** - Redacted events still maintain traceability

## Default Redaction Rules

AOG automatically redacts fields matching these patterns:

```python
REDACT_KEY_PATTERNS = [
    "api_key",
    "authorization",
    "token",
    "password",
    "secret",
    "access_token",
    "refresh_token",
    "cookie",
    "session_id",  # can be configured
    "private_key",
    "credential",
]
```

## Configuration

### RedactionConfig

```python
from aog import AOG, RedactionConfig

aog = AOG(
    redactor=RedactionConfig(
        redact_keys=[
            "api_key",
            "authorization",
            "token",
            "password",
            "secret",
            "access_token",
            "refresh_token",
        ],
        max_payload_bytes=100000,
        redact_values=True,
    )
)
```

### Capture Controls

```python
from aog import AOGConfig

config = AOGConfig(
    capture_input=True,  # Capture event input
    capture_output=True,  # Capture event output
    capture_tool_args=True,  # Capture tool arguments
    capture_tool_results=True,  # Capture tool results
)
```

## Redaction Behavior

### Key Redaction

Keys are matched case-insensitively:

```python
# These are all redacted:
{"API_KEY": "secret123"}
{"Authorization": "Bearer token"}
{"auth_token": "abc123"}
```

### Value Redaction

String values are replaced with `[REDACTED]`:

```python
input = {"password": "supersecret"}
# Becomes:
{"password": "[REDACTED]"}
```

### Nested Structure Handling

Redaction is recursive:

```python
input = {"user": {"name": "John", "password": "secret123"}}
# Becomes:
{"user": {"name": "John", "password": "[REDACTED]"}}
```

### List Handling

Lists are also redacted:

```python
input = {"tokens": ["secret1", "secret2"]}
# Becomes:
{"tokens": ["[REDACTED]", "[REDACTED]"]}
```

## Custom Redactors

You can provide a custom redactor:

```python
def custom_redactor(data: dict, config: RedactionConfig) -> dict:
    """Custom redaction logic."""
    # Your redaction logic here
    return redacted_data


aog = AOG(redactor=custom_redactor)
```

Custom redactors should:
1. Accept `(data, config)` arguments
2. Return redacted data
3. Never raise exceptions (fail-safe)
4. Be idempotent

## Stack Trace Redaction

Stack traces can be redacted:

```python
aog.record(
    event_type=EventType.ERROR,
    name="error",
    error={
        "type": "ValueError",
        "message": "Invalid input",
        "stacktrace": "...",  # Can be configured for redaction
    },
)
```

## Compliance

AOG supports compliance requirements:

### GDPR

- Right to be forgotten
- Data minimization
- Purpose limitation

### CCPA

- Right to know
- Right to delete
- Right to opt-out

## Best Practices

1. **Never log sensitive data** - Use redaction rules
2. **Test redaction** - Verify your redaction rules work
3. **Monitor redaction** - Log redaction events for audit
4. **Update rules** - Keep redaction rules current with new secrets

## Testing Redaction

```python
def test_redaction():
    data = {"password": "secret123"}
    redacted = redact(data)
    assert redacted["password"] == "[REDACTED]"
    assert redacted["other"] == data["other"]


def test_nested_redaction():
    data = {"user": {"password": "secret"}}
    redacted = redact(data)
    assert redacted["user"]["password"] == "[REDACTED]"
```

## Debugging

To debug redaction issues:

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Or use the AOG debug mode
aog = AOG(debug=True)
```

## Security Checklist

- [ ] No secrets in events
- [ ] Redaction rules are tested
- [ ] Custom redactor is fail-safe
- [ ] Stack traces are redacted
- [ ] Audit logs capture redaction decisions
- [ ] Integration tests verify redaction