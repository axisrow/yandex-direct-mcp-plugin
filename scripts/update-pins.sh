#!/usr/bin/env bash
# Bump the two runtime dependency pins (mcp, direct-cli) across the canonical
# places that must stay in lockstep:
#
#   - scripts/runtime-pins.env                       (single source of truth)
#   - plugins/yandex-direct/scripts/runtime-pins.env (Codex bundle copy)
#   - pyproject.toml                                 (mcp==X.Y.Z, direct-cli==X.Y.Z)
#   - server/cli/runner.py                           (MIN_DIRECT_VERSION tuple)
#
# tests/test_pins_consistency.py guards that nothing drifted.
#
# This script does NOT touch the plugin version itself — bump that with
# scripts/update-version.sh, which also syncs PLUGIN_VERSION= in runtime-pins.env.
set -euo pipefail

PLUGIN_DIR="${PLUGIN_DIR:-${HOME}/Projects/yandex-direct-mcp-plugin}"

PIN_FILE_REPO="${PLUGIN_DIR}/scripts/runtime-pins.env"
PIN_FILE_BUNDLE="${PLUGIN_DIR}/plugins/yandex-direct/scripts/runtime-pins.env"
PYPROJECT="${PLUGIN_DIR}/pyproject.toml"
RUNNER_PY="${PLUGIN_DIR}/server/cli/runner.py"

usage() {
  cat >&2 <<EOF
Usage: $0 MCP_VERSION DIRECT_CLI_VERSION

Pin the runtime mcp and direct-cli versions across all canonical places.
Both versions must be PEP 440 X.Y.Z (optional [.-]suffix).
EOF
}

command -v perl >/dev/null || { echo "error: perl is required" >&2; exit 1; }
[[ $# -eq 2 ]] || { usage; exit 2; }
[[ -f "$PIN_FILE_REPO" ]] || { echo "error: $PIN_FILE_REPO not found" >&2; exit 1; }
[[ -f "$PIN_FILE_BUNDLE" ]] || { echo "error: $PIN_FILE_BUNDLE not found" >&2; exit 1; }
[[ -f "$PYPROJECT" ]] || { echo "error: $PYPROJECT not found" >&2; exit 1; }
[[ -f "$RUNNER_PY" ]] || { echo "error: $RUNNER_PY not found" >&2; exit 1; }

mcp_version="$1"
direct_cli_version="$2"

SEMVER_RE='^[0-9]+\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.-]+)?$'
if [[ ! "$mcp_version" =~ $SEMVER_RE ]]; then
  echo "error: invalid MCP_VERSION '$mcp_version'" >&2
  exit 1
fi
if [[ ! "$direct_cli_version" =~ $SEMVER_RE ]]; then
  echo "error: invalid DIRECT_CLI_VERSION '$direct_cli_version'" >&2
  exit 1
fi

# Derive the (X, Y, Z) tuple for MIN_DIRECT_VERSION from the leading triplet.
read -r dx dy dz <<< "$(echo "$direct_cli_version" | perl -ne '/^(\d+)\.(\d+)\.(\d+)/ && print "$1 $2 $3"')"
if [[ -z "${dx:-}" ]]; then
  echo "error: could not parse leading X.Y.Z from '$direct_cli_version'" >&2
  exit 1
fi

echo "Pinning mcp=${mcp_version}, direct-cli=${direct_cli_version}"

for pin_file in "$PIN_FILE_REPO" "$PIN_FILE_BUNDLE"; do
  perl -i -pe 's/^MCP_VERSION=.*$/MCP_VERSION='"$mcp_version"'/' "$pin_file"
  perl -i -pe 's/^DIRECT_CLI_VERSION=.*$/DIRECT_CLI_VERSION='"$direct_cli_version"'/' "$pin_file"
done

perl -i -pe 's/"mcp==[^"]+"/"mcp=='"$mcp_version"'"/' "$PYPROJECT"
perl -i -pe 's/"direct-cli==[^"]+"/"direct-cli=='"$direct_cli_version"'"/' "$PYPROJECT"

perl -i -pe 's/^MIN_DIRECT_VERSION: tuple\[int, int, int\] = \(\d+, \d+, \d+\)$/MIN_DIRECT_VERSION: tuple[int, int, int] = ('"$dx"', '"$dy"', '"$dz"')/' "$RUNNER_PY"

echo
echo "Changes:"
git -C "$PLUGIN_DIR" diff --stat -- \
  "$PIN_FILE_REPO" "$PIN_FILE_BUNDLE" "$PYPROJECT" "$RUNNER_PY"

echo
echo "Run by hand if needed:"
echo "  grep -nE 'direct-cli([>=]| )' README.md CLAUDE.md"
echo "  pytest -q tests/test_pins_consistency.py"
