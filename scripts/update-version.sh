#!/usr/bin/env bash
set -euo pipefail

PLUGIN_DIR="${PLUGIN_DIR:-${HOME}/Projects/yandex-direct-mcp-plugin}"
MARKETPLACE_DIR="${MARKETPLACE_DIR:-${HOME}/Projects/plugin-marketplace}"
PLUGIN_NAME="yandex-direct"

PYPROJECT="${PLUGIN_DIR}/pyproject.toml"
PLUGIN_JSON="${PLUGIN_DIR}/.claude-plugin/plugin.json"
LOCAL_MARKETPLACE_JSON="${PLUGIN_DIR}/.agents/plugins/marketplace.json"
BUNDLE_PLUGIN_JSON="${PLUGIN_DIR}/plugins/yandex-direct/.codex-plugin/plugin.json"
PIN_FILE_REPO="${PLUGIN_DIR}/scripts/runtime-pins.env"
PIN_FILE_BUNDLE="${PLUGIN_DIR}/plugins/yandex-direct/scripts/runtime-pins.env"
MARKETPLACE_JSON="${MARKETPLACE_DIR}/.claude-plugin/marketplace.json"

usage() {
  cat >&2 <<EOF
Usage: $0 VERSION

Update all local plugin version fields to VERSION, then sync the external
marketplace entry.
EOF
}

command -v jq >/dev/null || { echo "error: jq is required" >&2; exit 1; }
command -v perl >/dev/null || { echo "error: perl is required" >&2; exit 1; }
[[ $# -eq 1 ]] || { usage; exit 2; }
[[ -f "$PYPROJECT" ]] || { echo "error: $PYPROJECT not found" >&2; exit 1; }
[[ -f "$PLUGIN_JSON" ]] || { echo "error: $PLUGIN_JSON not found" >&2; exit 1; }
[[ -f "$LOCAL_MARKETPLACE_JSON" ]] || { echo "error: $LOCAL_MARKETPLACE_JSON not found" >&2; exit 1; }
[[ -f "$BUNDLE_PLUGIN_JSON" ]] || { echo "error: $BUNDLE_PLUGIN_JSON not found" >&2; exit 1; }
[[ -f "$PIN_FILE_REPO" ]] || { echo "error: $PIN_FILE_REPO not found" >&2; exit 1; }
[[ -f "$PIN_FILE_BUNDLE" ]] || { echo "error: $PIN_FILE_BUNDLE not found" >&2; exit 1; }
[[ -f "$MARKETPLACE_JSON" ]] || { echo "error: $MARKETPLACE_JSON not found" >&2; exit 1; }

new_version="$1"

if [[ ! "$new_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.-]+)?$ ]]; then
  echo "error: invalid version '$new_version'" >&2
  exit 1
fi

update_json_version() {
  local path="$1"
  local jq_filter="$2"
  local tmp

  tmp=$(mktemp)
  jq --arg name "$PLUGIN_NAME" --arg v "$new_version" "$jq_filter" "$path" > "$tmp"
  mv "$tmp" "$path"
}

echo "Syncing ${PLUGIN_NAME} version to ${new_version}"

perl -0pi -e 's/^version\s*=\s*"[^"]+"/version = "'"$new_version"'"/m' "$PYPROJECT"

perl -i -pe 's/^PLUGIN_VERSION=.*$/PLUGIN_VERSION='"$new_version"'/' "$PIN_FILE_REPO"
perl -i -pe 's/^PLUGIN_VERSION=.*$/PLUGIN_VERSION='"$new_version"'/' "$PIN_FILE_BUNDLE"

update_json_version "$PLUGIN_JSON" '.version = $v'
update_json_version "$BUNDLE_PLUGIN_JSON" '.version = $v'
update_json_version "$LOCAL_MARKETPLACE_JSON" \
  '(.plugins[] | select(.name == $name) | .version) = $v'

current_version=$(jq -r --arg name "$PLUGIN_NAME" \
  '.plugins[] | select(.name == $name) | .version' "$MARKETPLACE_JSON")

if [[ -z "$current_version" || "$current_version" == "null" ]]; then
  echo "error: plugin '$PLUGIN_NAME' not found in marketplace.json" >&2
  exit 1
fi

marketplace_dirty=false
if ! git -C "$MARKETPLACE_DIR" diff --quiet -- .claude-plugin/marketplace.json \
   || ! git -C "$MARKETPLACE_DIR" diff --cached --quiet -- .claude-plugin/marketplace.json; then
  marketplace_dirty=true
fi

if [[ "$current_version" == "$new_version" && "$marketplace_dirty" == false ]]; then
  echo "Marketplace already at ${new_version}"
  exit 0
fi

if [[ "$current_version" != "$new_version" ]]; then
  if [[ "$marketplace_dirty" == true ]]; then
    echo "error: marketplace.json has uncommitted changes; commit or stash them first" >&2
    exit 1
  fi

  git -C "$MARKETPLACE_DIR" pull --rebase origin main

  current_version=$(jq -r --arg name "$PLUGIN_NAME" \
    '.plugins[] | select(.name == $name) | .version' "$MARKETPLACE_JSON")

  echo "Bumping marketplace ${PLUGIN_NAME}: ${current_version} → ${new_version}"

  update_json_version "$MARKETPLACE_JSON" \
    '(.plugins[] | select(.name == $name) | .version) = $v'
else
  echo "Marketplace already edited to ${new_version}; committing pending change"
fi

git -C "$MARKETPLACE_DIR" add .claude-plugin/marketplace.json
git -C "$MARKETPLACE_DIR" commit -m "chore: bump ${PLUGIN_NAME} plugin to ${new_version}"
git -C "$MARKETPLACE_DIR" push origin main

echo "Done."
