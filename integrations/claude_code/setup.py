"""Claude Code Setup and Configuration Helper for AgentDAC.

Manages detection, hook configuration, diagnostics, and disconnection
for Claude Code CLI integration in ~/.claude/settings.json.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from integrations.claude_code.adapter import PAUSE_FILE


def get_claude_settings_path() -> Path:
    """Get the path to ~/.claude/settings.json."""
    return Path.home() / ".claude" / "settings.json"


def get_hook_script_path() -> Path:
    """Get the absolute path to hook.py."""
    return Path(__file__).resolve().parent / "hook.py"


def detect_claude_cli() -> tuple[bool, str | None]:
    """Check if 'claude' CLI is installed and return its version."""
    claude_bin = shutil.which("claude")
    if not claude_bin:
        return False, None

    try:
        res = subprocess.run(
            [claude_bin, "--version"],
            capture_output=True,
            text=True,
            timeout=3.0,
            check=False,
        )
        version = res.stdout.strip() if res.returncode == 0 else "Installed"
        return True, version
    except Exception:
        return True, "Installed"


def read_claude_settings() -> dict[str, Any]:
    """Read ~/.claude/settings.json safely."""
    path = get_claude_settings_path()
    if not path.exists():
        return {}

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def is_hooks_configured() -> bool:
    """Check if AgentDAC hooks are configured in ~/.claude/settings.json."""
    settings = read_claude_settings()
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return False

    # Check if any hook references our hook.py
    for event_name in ("PreToolUse", "PostToolUse", "Notification", "Stop"):
        entries = hooks.get(event_name, [])
        if isinstance(entries, list):
            for entry in entries:
                if isinstance(entry, dict):
                    # Check nested hooks array (Claude Code 2.1.x matcher format)
                    inner_hooks = entry.get("hooks", [])
                    for h in inner_hooks:
                        cmd = h.get("command", "").replace("\\", "/")
                        if "integrations/claude_code/hook.py" in cmd:
                            return True
                    # Check direct command format
                    cmd = entry.get("command", "").replace("\\", "/")
                    if "integrations/claude_code/hook.py" in cmd:
                        return True
    return False


def build_hook_command() -> str:
    """Construct command to execute hook.py."""
    hook_path = str(get_hook_script_path()).replace("\\", "/")
    # Use python if available
    return f'python "{hook_path}"'


def configure_claude_hooks() -> tuple[bool, str]:
    """Safely install AgentDAC hooks into ~/.claude/settings.json."""
    settings_path = get_claude_settings_path()
    settings_dir = settings_path.parent
    settings_dir.mkdir(parents=True, exist_ok=True)

    settings = read_claude_settings()
    cmd = build_hook_command()

    # Target Claude Code 2.1.x matcher + hooks format
    standard_entry = {
        "matcher": "",
        "hooks": [
            {
                "type": "command",
                "command": cmd,
            }
        ],
    }

    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}

    target_events = (
        "SessionStart",
        "UserPromptSubmit",
        "PreToolUse",
        "PostToolUse",
        "Notification",
        "Stop",
    )
    for event in target_events:
        existing_list = hooks.get(event, [])
        if not isinstance(existing_list, list):
            existing_list = []

        # Remove any previous hook.py entries to avoid duplication
        cleaned = []
        for item in existing_list:
            if isinstance(item, dict):
                inner = item.get("hooks", [])
                has_agentdac = any(
                    "integrations/claude_code/hook.py" in h.get("command", "").replace("\\", "/")
                    for h in inner
                )
                direct_has = (
                    "integrations/claude_code/hook.py"
                    in item.get("command", "").replace("\\", "/")
                )
                if not (has_agentdac or direct_has):
                    cleaned.append(item)
            else:
                cleaned.append(item)

        cleaned.append(standard_entry)
        hooks[event] = cleaned

    settings["hooks"] = hooks

    try:
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        return True, f"Configured AgentDAC hooks in {settings_path}"
    except Exception as e:
        return False, f"Failed to write {settings_path}: {e}"


def remove_claude_hooks() -> tuple[bool, str]:
    """Safely remove only AgentDAC hooks from ~/.claude/settings.json."""
    settings_path = get_claude_settings_path()
    if not settings_path.exists():
        return True, "No settings file found to modify."

    settings = read_claude_settings()
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return True, "No hooks configured."

    new_hooks = {}
    for event, entries in hooks.items():
        if isinstance(entries, list):
            cleaned = []
            for item in entries:
                if isinstance(item, dict):
                    inner = item.get("hooks", [])
                    has_agentdac = any(
                        "integrations/claude_code/hook.py"
                        in h.get("command", "").replace("\\", "/")
                        for h in inner
                    )
                    direct_has = (
                        "integrations/claude_code/hook.py"
                        in item.get("command", "").replace("\\", "/")
                    )
                    if not (has_agentdac or direct_has):
                        cleaned.append(item)
                else:
                    cleaned.append(item)
            if cleaned:
                new_hooks[event] = cleaned
        else:
            new_hooks[event] = entries

    if not new_hooks:
        del settings["hooks"]
    else:
        settings["hooks"] = new_hooks

    try:
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        return True, f"Removed AgentDAC hooks from {settings_path}"
    except Exception as e:
        return False, f"Failed to update {settings_path}: {e}"


def get_integration_diagnostics() -> dict[str, Any]:
    """Return complete diagnostics for Claude Code CLI integration."""
    installed, version = detect_claude_cli()
    configured = is_hooks_configured()
    paused = os.path.exists(PAUSE_FILE)
    hook_path = get_hook_script_path()
    settings_path = get_claude_settings_path()

    status = "connected"
    if not configured:
        status = "setup_required" if installed else "not_connected"
    elif paused:
        status = "paused"

    return {
        "integration": "claude-code",
        "name": "Claude Code CLI",
        "status": status,
        "cli_installed": installed,
        "cli_version": version,
        "hooks_configured": configured,
        "paused": paused,
        "hook_script_path": str(hook_path),
        "hook_script_exists": hook_path.exists(),
        "settings_path": str(settings_path),
        "settings_exists": settings_path.exists(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="AgentDAC Claude Code Integration Helper")
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install AgentDAC hooks into Claude Code settings",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove AgentDAC hooks from Claude Code settings",
    )
    parser.add_argument("--status", action="store_true", help="Print integration status JSON")
    args = parser.parse_args()

    if args.install:
        ok, msg = configure_claude_hooks()
        print(f"[{'OK' if ok else 'ERROR'}] {msg}")
        sys.exit(0 if ok else 1)
    elif args.uninstall:
        ok, msg = remove_claude_hooks()
        print(f"[{'OK' if ok else 'ERROR'}] {msg}")
        sys.exit(0 if ok else 1)
    else:
        diag = get_integration_diagnostics()
        print(json.dumps(diag, indent=2))


if __name__ == "__main__":
    main()
