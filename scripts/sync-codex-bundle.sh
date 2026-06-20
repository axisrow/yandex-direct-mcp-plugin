#!/usr/bin/env bash
# Sync the Codex bundle's server/ tree with the repo's canonical server/ (issue #236).
#
# The marketplace packs plugins/yandex-direct/ as a `local` source with no build
# step, so whatever is committed under the bundle is exactly what ships. The
# bundle therefore needs a *complete, byte-identical* copy of server/ — not a
# hand-maintained partial main.py. Run this after any change under server/ and
# commit the result; tests/test_codex_bundle_sync.py fails if the mirror drifts.
#
# Idempotent: re-running with no server/ changes leaves a clean working tree.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/server"
DEST="$REPO_ROOT/plugins/yandex-direct/server"

if [[ ! -d "$SRC" ]]; then
    echo "sync-codex-bundle: source $SRC not found" >&2
    exit 1
fi

mkdir -p "$DEST"

if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
        --exclude='__pycache__/' \
        --exclude='*.pyc' \
        --exclude='*.pyo' \
        "$SRC/" "$DEST/"
else
    # Portable fallback: wipe the mirror, then copy fresh, then strip caches.
    rm -rf "$DEST"
    mkdir -p "$DEST"
    cp -R "$SRC/." "$DEST/"
    find "$DEST" -type d -name '__pycache__' -prune -exec rm -rf {} +
    find "$DEST" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
fi

# As a pre-commit hook this must *block* the commit when it regenerated the
# mirror — otherwise the refreshed bundle files sit unstaged, the commit lands
# without them, and CI fails on test_codex_bundle_sync. Same convention as
# `ruff --fix`: modify files, exit non-zero, let the developer stage + recommit.
if [[ -z "${SYNC_CODEX_BUNDLE_NO_FAIL:-}" ]] &&
    [[ -n "$(git -C "$REPO_ROOT" status --porcelain -- "$DEST")" ]]; then
    echo "sync-codex-bundle: bundle was regenerated — stage and re-commit:" >&2
    echo "  git add plugins/yandex-direct/server/" >&2
    exit 1
fi

echo "sync-codex-bundle: mirrored server/ -> plugins/yandex-direct/server/ (up-to-date)"
