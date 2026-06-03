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

_has_direct_cli_0402() {
    # Extract the leading X.Y.Z triplet so pre-release / dev suffixes
    # ("0.4.2rc1", "0.4.2.dev0") don't break int() parsing.
    "$1" -c "import re, direct_cli; m = re.match(r'^(\d+)\.(\d+)\.(\d+)', direct_cli.__version__); raise SystemExit(1 if not m else (tuple(map(int, m.groups())) < (0, 4, 2)))" 2>/dev/null
}

# Try plugin venv first (Debian/Docker friendly)
if [ ! -f "$VENV/bin/python3" ]; then
    python3 -m venv "$VENV" --quiet 2>/dev/null || true
fi

if [ -f "$VENV/bin/python3" ]; then
    # Venv available — install into it
    if ! _has_direct_cli_0402 "$VENV/bin/python3"; then
        "$VENV/bin/pip" install --quiet --disable-pip-version-check 'direct-cli>=0.4.2' 2>/dev/null || true
    fi
    if ! "$VENV/bin/python3" -c "import mcp" 2>/dev/null; then
        "$VENV/bin/pip" install --quiet --disable-pip-version-check mcp 2>/dev/null || true
    fi
else
    # No venv — fallback to system install (macOS)
    if ! command -v direct &>/dev/null || ! _has_direct_cli_0402 python3; then
        _pip_user 'direct-cli>=0.4.2'
    fi
    if ! python3 -c "import mcp" 2>/dev/null; then
        _pip_user mcp
    fi
fi
