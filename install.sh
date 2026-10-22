#!/usr/bin/env bash
# =============================================================================
# AgentDAC — Universal Observability SDK Installer
# =============================================================================
# One-liner install:
#   curl -fsSL https://raw.githubusercontent.com/sklearner26/agentdac/main/install.sh | bash
# =============================================================================
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
RESET='\033[0m'

PACKAGE_NAME="agentdac"
GITHUB_REPO="https://github.com/sklearner26/agentdac"
MIN_PYTHON_MINOR=12
MAX_PYTHON_MINOR=14

banner() {
  echo ""
  echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════════════════╗${RESET}"
  echo -e "${CYAN}${BOLD}║        AgentDAC — Universal AI Observability SDK         ║${RESET}"
  echo -e "${CYAN}${BOLD}║   Every agent action, tool call & fact is a graph node   ║${RESET}"
  echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════════════════╝${RESET}"
  echo ""
}

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*"; exit 1; }

detect_python() {
  for cmd in python3.13 python3.12 python3 python; do
    if command -v "$cmd" &>/dev/null; then
       major=$("$cmd" -c "import sys; print(sys.version_info.major)")
       minor=$("$cmd" -c "import sys; print(sys.version_info.minor)")
       if [ "$major" -eq 3 ] && [ "$minor" -ge "$MIN_PYTHON_MINOR" ] && [ "$minor" -lt "$MAX_PYTHON_MINOR" ]; then
        echo "$cmd"
        return 0
      fi
    fi
  done
  return 1
}

banner

# ── Step 1: Find Python ──────────────────────────────────────────────────────
info "Detecting Python 3.12+ …"
PYTHON=$(detect_python) || error "Python 3.12 or 3.13 is required. Install from https://python.org"
PY_VERSION=$("$PYTHON" --version 2>&1)
success "Found $PY_VERSION at $(command -v "$PYTHON")"

# ── Step 2: Detect / create virtualenv ──────────────────────────────────────
VENV_DIR=".venv"
if [ -d "$VENV_DIR" ]; then
  info "Reusing existing virtualenv at $VENV_DIR"
else
  info "Creating virtualenv at $VENV_DIR …"
  "$PYTHON" -m venv "$VENV_DIR"
  success "Virtualenv created"
fi

# Activate
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate" 2>/dev/null || source "$VENV_DIR/Scripts/activate" 2>/dev/null || true
PIP="$VENV_DIR/bin/pip"
[ -f "$VENV_DIR/Scripts/pip.exe" ] && PIP="$VENV_DIR/Scripts/pip.exe"

# ── Step 3: Install agentdac ─────────────────────────────────────────────────
info "Installing ${BOLD}${PACKAGE_NAME}${RESET} from PyPI …"
if "$PIP" install --quiet --upgrade "$PACKAGE_NAME" 2>/dev/null; then
  success "$PACKAGE_NAME installed from PyPI"
elif "$PIP" install --quiet --upgrade "git+${GITHUB_REPO}.git" 2>/dev/null; then
  success "$PACKAGE_NAME installed from GitHub"
else
  warn "PyPI & GitHub installs failed. Trying source install …"
  if [ -f "pyproject.toml" ]; then
    "$PIP" install --quiet -e "." && success "$PACKAGE_NAME installed from source"
  else
    error "Could not install $PACKAGE_NAME. Check network connectivity."
  fi
fi

# ── Step 4: Configure Claude Code CLI Integration ────────────────────────────
info "Checking for Claude Code CLI …"
if command -v claude &>/dev/null || [ -d "$HOME/.claude" ]; then
  info "Configuring AgentDAC observability hooks in ~/.claude/settings.json …"
  if [ -f "integrations/claude_code/setup.py" ]; then
    "$PYTHON" -m integrations.claude_code.setup --install 2>/dev/null && success "Claude Code CLI hooks configured in ~/.claude/settings.json" || warn "Could not configure Claude Code hooks automatically"
  else
    "$PYTHON" -c '
import json, os
p = os.path.expanduser("~/.claude/settings.json")
os.makedirs(os.path.dirname(p), exist_ok=True)
s = {}
if os.path.exists(p):
    try:
        with open(p, "r", encoding="utf-8") as f: s = json.load(f)
    except: pass
hooks = s.get("hooks", {})
cmd = "python -m integrations.claude_code.hook"
entry = {"matcher": "", "hooks": [{"type": "command", "command": cmd}]}
for ev in ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Notification", "Stop"):
    hooks[ev] = [entry]
s["hooks"] = hooks
with open(p, "w", encoding="utf-8") as f: json.dump(s, f, indent=2)
' 2>/dev/null && success "Claude Code CLI hooks configured in ~/.claude/settings.json" || true
  fi
else
  info "Claude Code CLI not detected (can be connected anytime from the AgentDAC Dashboard)"
fi

# ── Step 5: Print quickstart ─────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}✔ AgentDAC installed successfully!${RESET}"
echo ""
echo -e "${BOLD}Quickstart (5 lines):${RESET}"
echo -e "${CYAN}"
cat <<'QUICKSTART'
from agentdac import AgentDAC

aog = AgentDAC(agent_id="my-agent")  # backend auto-starts

with aog.session(metadata={"task": "demo"}):
    with aog.tool("web_search") as span:
        span.set_input({"query": "AgentDAC"})
        span.set_output({"results": ["..."]})

# Open dashboard → http://localhost:8000/dashboard
QUICKSTART
echo -e "${RESET}"

echo -e "${BOLD}Environment variables (optional):${RESET}"
echo "  AGENTDAC_PORT=8001          # backend port (default: 8000)"
echo "  AGENTDAC_AGENT_ID=my-agent  # default agent id"
echo "  AGENTDAC_CHAT_API_KEY=sk-…  # enables AI chat in dashboard"
echo ""
echo -e "  ${CYAN}Dashboard:${RESET} http://localhost:8000"
echo -e "  ${CYAN}API docs:${RESET}  http://localhost:8000/docs"
echo -e "  ${CYAN}GitHub:${RESET}    ${GITHUB_REPO}"
echo ""
