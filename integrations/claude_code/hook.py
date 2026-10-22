"""AgentDAC hook for Claude Code CLI.

Receives JSON payloads from Claude Code hooks via stdin,
normalizes them using ClaudeCodeAdapter, and forwards them
to the AgentDAC backend.

Guaranteed fail-open: any error in observability will never
interrupt or alter Claude Code developer execution.
"""

from __future__ import annotations

import json
import os
import sys

# Resolve project root so modules are importable
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SDK_SRC = os.path.join(_PROJECT_ROOT, "packages", "aog-sdk", "src")
if _SDK_SRC not in sys.path:
    sys.path.insert(0, _SDK_SRC)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from integrations.claude_code.adapter import ClaudeCodeAdapter


def main() -> None:
    """Entry point: read JSON from stdin and dispatch to adapter."""
    try:
        raw = sys.stdin.read()
        if not raw or not raw.strip():
            return

        payload = json.loads(raw)
        if isinstance(payload, dict):
            ClaudeCodeAdapter.handle_hook_payload(payload)
    except Exception:
        # Zero blockage to developer workflow on any error
        pass


if __name__ == "__main__":
    main()
