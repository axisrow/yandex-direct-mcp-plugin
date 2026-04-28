#!/bin/bash
# Auto-install dependencies for yandex-direct plugin on session start
set -euo pipefail

DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data/yandex-direct}"
VENV="$DATA/venv"

_pip_user() {
    pip install --user --quiet --disable-pip-version-check "$@" 2>/dev/null || \
    pip install --break-system-packages --quiet --disable-pip-version-check "$@" 2>/dev/null || \
    true
}

_has_direct_cli_031() {
    "$1" -c "import direct_cli; raise SystemExit(tuple(map(int, direct_cli.__version__.split('.')[:3])) < (0, 3, 1))" 2>/dev/null
}

# Try plugin venv first (Debian/Docker friendly)
if [ ! -f "$VENV/bin/python3" ]; then
    python3 -m venv "$VENV" --quiet 2>/dev/null || true
fi

if [ -f "$VENV/bin/python3" ]; then
    # Venv available — install into it
    if ! _has_direct_cli_031 "$VENV/bin/python3"; then
        "$VENV/bin/pip" install --quiet --disable-pip-version-check 'direct-cli>=0.3.1' 2>/dev/null || true
    fi
    if ! "$VENV/bin/python3" -c "import mcp, httpx" 2>/dev/null; then
        "$VENV/bin/pip" install --quiet --disable-pip-version-check mcp "httpx>=0.27" python-dotenv 2>/dev/null || true
    fi
else
    # No venv — fallback to system install (macOS)
    if ! command -v direct &>/dev/null || ! _has_direct_cli_031 python3; then
        _pip_user 'direct-cli>=0.3.1'
    fi
    if ! python3 -c "import mcp, httpx" 2>/dev/null; then
        _pip_user mcp "httpx>=0.27" python-dotenv
    fi
fi
