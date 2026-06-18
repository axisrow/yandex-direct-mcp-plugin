#!/bin/bash
# Auto-install dependencies for yandex-direct plugin on session start.
#
# Fast path (almost always after first run): the pinned versions are already
# installed for this (plugin, mcp, direct-cli) triple — stamp file exists in
# $CLAUDE_PLUGIN_DATA — so we exit 0 immediately without touching pip or
# probing the venv. No network, no import cost.
#
# Slow path: stamp absent → create venv → pip install pinned versions → on
# success, stamp.  The stamp is the contract with hooks/run-server.sh: it
# refuses to launch the server unless both the stamp AND $VENV/bin/python3
# exist (#223 cycle 3). Stamping a non-venv install would create a sticky
# self-inflicted outage — every future SessionStart would fast-path on the
# stamp, and every launch would refuse to start.
#
# Soft-fail (exit 0) on missing prerequisites so SessionStart never blocks
# Claude Code; the user sees a clear error from the launcher the moment they
# try to use the MCP server.
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

PINNED_DEPS=("mcp==${MCP_VERSION}" "direct-cli==${DIRECT_CLI_VERSION}")

# Venv is the only supported install target — the launcher refuses to start
# without $VENV/bin/python3 (#223 cycle 3). On Debian/Ubuntu, `python3 -m venv`
# needs the `python3-venv` apt package; if it is missing, the user must install
# it. Stamping a user-site install would be sticky and unrecoverable.
if [ ! -f "$VENV/bin/python3" ] && ! python3 -m venv "$VENV" >/dev/null 2>&1; then
    echo "yandex-direct: could not create venv at $VENV." >&2
    echo "  On Debian/Ubuntu: sudo apt install python3-venv" >&2
    echo "  Then restart Claude Code." >&2
    exit 0
fi

if "$VENV/bin/pip" install --quiet --disable-pip-version-check \
    "${PINNED_DEPS[@]}" 2>/dev/null; then
    touch "$STAMP"
fi

exit 0
