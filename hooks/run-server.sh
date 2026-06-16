#!/usr/bin/env bash
# Launch the yandex-direct MCP server with the interpreter that actually has the
# dependencies installed.
#
# hooks/setup.sh installs `mcp` and `direct-cli` into a per-user virtualenv
# ($CLAUDE_PLUGIN_DATA/venv), which is the Debian / PEP 668-friendly path: a plain
# `pip install --user` is blocked on externally-managed Pythons, so the venv is
# deliberate. But .mcp.json launches the server with a bare `python3`, and on
# Linux the system interpreter does not see the venv packages → `import mcp`
# fails and the server never starts (issue #165).
#
# .mcp.json cannot expand ${CLAUDE_PLUGIN_DATA}, so this wrapper resolves the venv
# the same way setup.sh does and prefers it, falling back to system `python3`
# (the macOS path, where deps land in user site-packages).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"

DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data/yandex-direct}"
VENV_PYTHON="$DATA/venv/bin/python3"

if [ -x "$VENV_PYTHON" ] && "$VENV_PYTHON" -c "import mcp" 2>/dev/null; then
    PYTHON="$VENV_PYTHON"
else
    PYTHON="python3"
fi

export PYTHONPATH="$PLUGIN_ROOT${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYTHON" "$PLUGIN_ROOT/server/main.py"
