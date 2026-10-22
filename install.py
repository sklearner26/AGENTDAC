#!/usr/bin/env python3
"""
AgentDAC — Python-based installer.

Supports:
  python install.py           # pip install into current env
  python install.py --venv    # create .venv and install
  python install.py --docker  # print docker run command

Usage as pip one-liner:
  pip install agentdac

Usage as direct installer:
  curl -fsSL https://raw.githubusercontent.com/sklearner26/agentdac/main/install.py | python3
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PACKAGE = "agentdac"
GITHUB = "https://github.com/sklearner26/agentdac"
MIN_PYTHON = (3, 12)
DOCKER_IMAGE = "sklearner26/agentdac:latest"

QUICKSTART = """
from agentdac import AgentDAC

aog = AgentDAC(agent_id="my-agent")  # backend auto-starts on port 8000

with aog.session(metadata={"task": "demo"}):
    with aog.tool("web_search") as span:
        span.set_input({"query": "AI observability"})
        span.set_output({"results": ["AgentDAC is live!"]})

# LangChain/LangGraph zero-code integration:
from aog.integrations.langchain import AgentDACCallbackHandler
handler = AgentDACCallbackHandler(aog)
chain.invoke(inputs, config={"callbacks": [handler]})

# Dashboard → http://localhost:8000
"""

DOCKER_CMD = f"""
# Run AgentDAC backend (standalone):
docker run -d \\
  --name agentdac \\
  -p 8000:8000 \\
  -v agentdac_data:/data \\
  -e AGENTDAC_CHAT_API_KEY=your_openai_key \\
  {DOCKER_IMAGE}

# SDK usage (from host / another container):
pip install agentdac
python -c "from agentdac import AgentDAC; AgentDAC(auto_start=False)"
"""


def check_python() -> None:
    if sys.version_info < MIN_PYTHON:
        print(f"[ERROR] Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required. Got {sys.version}")
        sys.exit(1)
    print(f"[OK]    Python {sys.version.split()[0]} detected")


def pip_install(pkg: str, pip_exe: list[str]) -> bool:
    try:
        subprocess.run(
            [*pip_exe, "install", "--quiet", "--upgrade", pkg],
            check=True, capture_output=True,
        )
    except subprocess.CalledProcessError:
        return False
    else:
        return True


def install_pip_env() -> None:
    pip_exe = [sys.executable, "-m", "pip"]
    print(f"[INFO]  Installing {PACKAGE} …")
    if pip_install(PACKAGE, pip_exe):
        print(f"[OK]    {PACKAGE} installed from PyPI")
        return
    print("[WARN]  PyPI failed, trying GitHub source …")
    if pip_install(f"git+{GITHUB}.git", pip_exe):
        print(f"[OK]    {PACKAGE} installed from GitHub")
        return
    pyproject = Path("pyproject.toml")
    if pyproject.exists():
        print("[INFO]  Installing from local source …")
        subprocess.run([*pip_exe, "install", "-e", "."], check=True)
        print(f"[OK]    {PACKAGE} installed from source")
        return
    print("[ERROR] All install methods failed.")
    sys.exit(1)


def install_venv() -> None:
    venv_dir = Path(".venv")
    if not venv_dir.exists():
        print("[INFO]  Creating .venv …")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    pip_path = venv_dir / "bin" / "pip"
    if not pip_path.exists():
        pip_path = venv_dir / "Scripts" / "pip.exe"
    pip_exe = [str(pip_path)]
    print(f"[INFO]  Installing {PACKAGE} into .venv …")
    if pip_install(PACKAGE, pip_exe):
        print(f"[OK]    {PACKAGE} installed in .venv")
    else:
        subprocess.run([str(pip_path), "install", "-e", "."], check=True)


def configure_claude_code() -> None:
    try:
        from integrations.claude_code.setup import configure_claude_hooks, detect_claude_cli
        installed, version = detect_claude_cli()
        if installed or (Path.home() / ".claude").exists():
            ok, msg = configure_claude_hooks()
            if ok:
                print("[OK]    Claude Code CLI hooks configured in ~/.claude/settings.json")
    except Exception:
        pass


def print_quickstart() -> None:
    print("\n" + "=" * 60)
    print("  AgentDAC installed! Quickstart:")
    print("=" * 60)
    print(QUICKSTART)
    print("\nEnvironment variables:")
    print("  AGENTDAC_PORT=8001          # backend port")
    print("  AGENTDAC_AGENT_ID=my-agent  # default agent id")
    print("  AGENTDAC_CHAT_API_KEY=sk-…  # AI chat in dashboard")
    print("\n  Dashboard → http://localhost:8000")
    print("  API docs  → http://localhost:8000/docs")
    print(f"  GitHub    → {GITHUB}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="AgentDAC installer")
    parser.add_argument("--venv", action="store_true", help="Install into .venv")
    parser.add_argument("--docker", action="store_true", help="Print Docker install command")
    args = parser.parse_args()

    print("\n  AgentDAC — Universal AI Observability SDK\n")
    check_python()

    if args.docker:
        print(DOCKER_CMD)
        return

    if args.venv:
        install_venv()
    else:
        install_pip_env()

    configure_claude_code()
    print_quickstart()


if __name__ == "__main__":
    main()
