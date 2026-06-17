#!/usr/bin/env bash
# Launch the bundled yandex-direct MCP server with an interpreter that actually
# has the dependencies (`mcp`, `direct-cli`) importable.
#
# Why this exists (issue #197, same class as #165): the Codex plugin bundle has
# NO hooks/ directory and no setup.sh venv-bootstrap step, so the previous
# `.mcp.json` launched the server with a bare `python3`. On Linux the system
# interpreter is usually externally-managed (PEP 668) and does not see plugin
# deps, so `import mcp` fails and the server never starts. The Claude Code path
# was fixed in #186 by a venv-aware wrapper backed by hooks/setup.sh; the bundle
# has no setup.sh, so this wrapper is self-bootstrapping instead.
#
# Resolution order:
#   1. An existing per-user venv (created here on a previous run, or shared with
#      the Claude Code install) whose python can `import mcp`.
#   2. System `python3`, if it can already `import mcp` (the macOS / dev path
#      where deps live in user site-packages).
#   3. Otherwise create the venv and pip-install the deps into it, then use it.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$SCRIPT_DIR"

DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data/yandex-direct}"
VENV="$DATA/venv"
VENV_PYTHON="$VENV/bin/python3"

_can_import_mcp() { "$1" -c "import mcp" 2>/dev/null; }

if [ -x "$VENV_PYTHON" ] && _can_import_mcp "$VENV_PYTHON"; then
    PYTHON="$VENV_PYTHON"
elif command -v python3 >/dev/null 2>&1 && _can_import_mcp python3; then
    PYTHON="python3"
else
    # No usable interpreter — bootstrap a venv and install deps into it. Errors
    # are surfaced (no `|| true`) so a failed install does not silently fall
    # back to a python3 that cannot import mcp.
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install --quiet --disable-pip-version-check \
        "mcp>=1.23.3,<2" "direct-cli>=0.4.3"
    PYTHON="$VENV_PYTHON"
fi

export PYTHONPATH="$PLUGIN_ROOT${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYTHON" "$PLUGIN_ROOT/server/main.py"
