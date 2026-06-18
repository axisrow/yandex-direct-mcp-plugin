#!/usr/bin/env bash
# Launch the yandex-direct MCP server in the venv populated by hooks/setup.sh.
#
# Bootstrap split (Claude Code channel):
#   hooks/setup.sh        — SessionStart hook. Sources scripts/runtime-pins.env
#                           and installs the pinned `mcp` + `direct-cli` into
#                           $CLAUDE_PLUGIN_DATA/venv. Stamp-gated: 99% of starts
#                           exit in microseconds.
#   hooks/run-server.sh   — this file. The strict consumer of that work.
#                           No bootstrap, no version probing, no system-python
#                           fallback: if the stamp + venv pair is not there,
#                           we refuse to launch.
#
# Refusing-to-launch matters: silently falling back to a bare `python3` with
# whatever `mcp` happens to be in user site-packages defeats the supply-chain
# pin guarantee #223 introduces. Better an obvious error than a server running
# on the wrong dependencies.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"
PIN_FILE="$PLUGIN_ROOT/scripts/runtime-pins.env"

if [ ! -f "$PIN_FILE" ]; then
    echo "yandex-direct: missing $PIN_FILE; cannot determine pinned versions." >&2
    exit 1
fi
# shellcheck source=/dev/null
. "$PIN_FILE"

DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data/yandex-direct}"
VENV_PYTHON="$DATA/venv/bin/python3"
STAMP="$DATA/.installed-${PLUGIN_VERSION}-${MCP_VERSION}-${DIRECT_CLI_VERSION}"

if [ ! -f "$STAMP" ] || [ ! -x "$VENV_PYTHON" ]; then
    echo "yandex-direct: pinned dependencies not installed for this version triple." >&2
    echo "  Expected stamp: $STAMP" >&2
    echo "  Expected venv:  $VENV_PYTHON" >&2
    echo "  Restart Claude Code so the SessionStart hook (hooks/setup.sh) can install them." >&2
    exit 1
fi

export PYTHONPATH="$PLUGIN_ROOT${PYTHONPATH:+:$PYTHONPATH}"
exec "$VENV_PYTHON" "$PLUGIN_ROOT/server/main.py"
