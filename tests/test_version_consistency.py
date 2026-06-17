"""Regression guard: the plugin version must be identical across all manifests.

The version lives in four committed files (plus the external marketplace repo,
which is out of this repo's reach). ``scripts/update-version.sh`` bumps all of
them at once, but nothing fails loudly if one drifts — e.g. a hand-edit to a
single ``plugin.json``. This test reads the version straight from each file and
asserts they agree, turning "forgot to sync one" from a silent release bug into
a red CI. Tracks #209.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Every committed file that pins the plugin version, with how to read it.
_PYPROJECT = REPO_ROOT / "pyproject.toml"
_PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"
_BUNDLE_PLUGIN_JSON = (
    REPO_ROOT / "plugins" / "yandex-direct" / ".codex-plugin" / "plugin.json"
)
_LOCAL_MARKETPLACE_JSON = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+([.-][0-9A-Za-z.-]+)?$")


def _pyproject_version() -> str:
    with _PYPROJECT.open("rb") as fh:
        return tomllib.load(fh)["project"]["version"]


def _json_version(path: Path) -> str:
    return json.loads(path.read_text())["version"]


def _marketplace_version(path: Path) -> str:
    data = json.loads(path.read_text())
    entries = [p for p in data["plugins"] if p.get("name") == "yandex-direct"]
    assert len(entries) == 1, (
        f"expected one yandex-direct entry in {path}, got {entries}"
    )
    return entries[0]["version"]


def _all_versions() -> dict[str, str]:
    return {
        "pyproject.toml": _pyproject_version(),
        ".claude-plugin/plugin.json": _json_version(_PLUGIN_JSON),
        "plugins/yandex-direct/.codex-plugin/plugin.json": _json_version(
            _BUNDLE_PLUGIN_JSON
        ),
        ".agents/plugins/marketplace.json": _marketplace_version(
            _LOCAL_MARKETPLACE_JSON
        ),
    }


def test_plugin_version_is_consistent_across_manifests() -> None:
    versions = _all_versions()
    distinct = set(versions.values())
    assert len(distinct) == 1, (
        "plugin version is out of sync across manifests "
        f"(bump all of them via scripts/update-version.sh): {versions}"
    )


def test_plugin_version_is_valid_semver() -> None:
    for source, version in _all_versions().items():
        assert _SEMVER_RE.match(version), (
            f"{source} has a non-semver version: {version!r}"
        )
