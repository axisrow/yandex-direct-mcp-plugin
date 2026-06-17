#!/usr/bin/env bash
# Launch the bundled yandex-direct MCP server.
#
# Two paths, gated on the stamp file in $CLAUDE_PLUGIN_DATA:
#
#   Fast path  (almost always)        stamp present → pip is NEVER invoked.
#                                     We exec the server straight away.
#   Slow path  (first install / bump) stamp absent → ensure venv → pip install
#                                     pinned mcp + direct-cli → stamp on
#                                     success → exec.  Failures keep #214's
#                                     120s backoff via $DATA/.bootstrap-failed.
#
# Versions come from scripts/runtime-pins.env (single source of truth,
# also sourced by hooks/setup.sh in the Claude Code channel).
#
# Why this file is self-bootstrapping (issue #197): the Codex bundle has no
# SessionStart hook and no setup.sh. The launcher is the only place we get
# control before the server starts.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$SCRIPT_DIR"
PIN_FILE="$PLUGIN_ROOT/scripts/runtime-pins.env"

if [ ! -f "$PIN_FILE" ]; then
    echo "yandex-direct: missing $PIN_FILE; cannot determine pinned versions." >&2
    exit 1
fi
# shellcheck source=/dev/null
. "$PIN_FILE"

DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data/yandex-direct}"
VENV="$DATA/venv"
VENV_PYTHON="$VENV/bin/python3"
STAMP="$DATA/.installed-${PLUGIN_VERSION}-${MCP_VERSION}-${DIRECT_CLI_VERSION}"
FAIL_MARKER="$DATA/.bootstrap-failed"
BACKOFF_SECONDS=120

_can_import_mcp() { "$1" -c "import mcp" 2>/dev/null; }

# Fast path: stamp present ⇒ deps are pinned and installed. Pick the venv
# python (the only place pip wrote to) and exec without touching pip.
if [ -f "$STAMP" ] && [ -x "$VENV_PYTHON" ]; then
    PYTHON="$VENV_PYTHON"
# Dev path: system python can already import mcp (macOS user site-packages),
# stamp not required.
elif command -v python3 >/dev/null 2>&1 && _can_import_mcp python3; then
    PYTHON="python3"
else
    # Slow path: install pinned deps into the venv, then stamp.
    mkdir -p "$DATA"

    if [ -f "$FAIL_MARKER" ]; then
        last="$(cat "$FAIL_MARKER" 2>/dev/null || true)"
        case "$last" in '' | *[!0-9]*) last=0 ;; esac
        if [ "$(($(date +%s) - last))" -lt "$BACKOFF_SECONDS" ]; then
            echo "yandex-direct: dependency bootstrap failed <${BACKOFF_SECONDS}s ago; not retrying pip yet." >&2
            echo "  Fix network/pip, then: rm -f '$FAIL_MARKER' and restart (or wait ${BACKOFF_SECONDS}s)." >&2
            exit 1
        fi
    fi

    if python3 -m venv "$VENV" \
        && "$VENV/bin/pip" install --quiet --disable-pip-version-check \
            "mcp==${MCP_VERSION}" "direct-cli==${DIRECT_CLI_VERSION}"; then
        rm -f "$FAIL_MARKER"
        touch "$STAMP"
        PYTHON="$VENV_PYTHON"
    else
        date +%s >"$FAIL_MARKER"
        echo "yandex-direct: failed to install MCP server dependencies (mcp==${MCP_VERSION}, direct-cli==${DIRECT_CLI_VERSION})." >&2
        echo "  Check network/pip and restart; retries are throttled for ${BACKOFF_SECONDS}s." >&2
        exit 1
    fi
fi

export PYTHONPATH="$PLUGIN_ROOT${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYTHON" "$PLUGIN_ROOT/server/main.py"
