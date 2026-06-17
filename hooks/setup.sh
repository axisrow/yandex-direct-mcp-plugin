#!/bin/bash
# Auto-install dependencies for yandex-direct plugin on session start.
#
# Fast path (almost always after first run): the pinned versions are already
# installed for this (plugin, mcp, direct-cli) triple — stamp file exists in
# $CLAUDE_PLUGIN_DATA — so we exit 0 immediately without touching pip or
# probing the venv. No network, no import cost.
#
# Slow path: stamp absent → ensure venv → pip install pinned versions → on
# success, stamp.  Soft-fail throughout (`|| true`-style) so a SessionStart
# never blocks Claude Code; if install fails, the next session retries.
#
# Versions come from scripts/runtime-pins.env (the single source of truth,
# also sourced by plugins/yandex-direct/run-server.sh in the Codex channel).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PIN_FILE="$PLUGIN_ROOT/scripts/runtime-pins.env"

if [ ! -f "$PIN_FILE" ]; then
    echo "yandex-direct: missing $PIN_FILE; aborting bootstrap." >&2
    exit 0
fi
# shellcheck source=/dev/null
. "$PIN_FILE"

DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data/yandex-direct}"
VENV="$DATA/venv"
STAMP="$DATA/.installed-${PLUGIN_VERSION}-${MCP_VERSION}-${DIRECT_CLI_VERSION}"

# Fast path: deps already pinned for this exact triple.
if [ -f "$STAMP" ]; then
    exit 0
fi

mkdir -p "$DATA"

_pip_user() {
    pip install --user --quiet --disable-pip-version-check "$@" 2>/dev/null || \
    pip install --break-system-packages --quiet --disable-pip-version-check "$@" 2>/dev/null || \
    return 1
}

PINNED_DEPS=("mcp==${MCP_VERSION}" "direct-cli==${DIRECT_CLI_VERSION}")

# Try plugin venv first (Debian/Docker friendly).
if [ ! -f "$VENV/bin/python3" ]; then
    python3 -m venv "$VENV" --quiet 2>/dev/null || true
fi

if [ -f "$VENV/bin/python3" ]; then
    if "$VENV/bin/pip" install --quiet --disable-pip-version-check \
        "${PINNED_DEPS[@]}" 2>/dev/null; then
        touch "$STAMP"
    fi
else
    if _pip_user "${PINNED_DEPS[@]}"; then
        touch "$STAMP"
    fi
fi

exit 0
