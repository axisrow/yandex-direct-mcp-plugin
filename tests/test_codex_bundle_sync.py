"""Byte-for-byte sync guard for the Codex bundle (issue #236).

The marketplace packs ``plugins/yandex-direct/`` as a ``local`` source with no
build step (`.agents/plugins/marketplace.json`), so whatever is committed under
the bundle is exactly what ships. The bundle must therefore carry a *complete,
in-sync* copy of the repo's ``server/`` package — not a hand-maintained partial
``main.py``. Before #236 the bundle shipped only ``server/__init__.py`` +
``server/main.py`` (no ``server/tools/``, ``config.py``, ``contract.py``,
``cli/``), so a clean install died with ``ModuleNotFoundError: server.tools`` and
silently ignored the tool-surface config block.

``scripts/sync-codex-bundle.sh`` regenerates the mirror; this test fails if it
drifts (model: ``tests/test_version_consistency.py``).
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_SERVER = REPO_ROOT / "server"
BUNDLE_SERVER = REPO_ROOT / "plugins" / "yandex-direct" / "server"

_IGNORE_DIRS = {"__pycache__"}
_IGNORE_SUFFIXES = {".pyc", ".pyo"}


def _relevant_files(base: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(base)
        if any(part in _IGNORE_DIRS for part in rel.parts):
            continue
        if path.suffix in _IGNORE_SUFFIXES:
            continue
        files[rel.as_posix()] = path.read_bytes()
    return files


def test_codex_bundle_mirrors_repo_server_tree() -> None:
    root_files = _relevant_files(ROOT_SERVER)
    bundle_files = _relevant_files(BUNDLE_SERVER)

    hint = "run scripts/sync-codex-bundle.sh"

    missing = sorted(root_files.keys() - bundle_files.keys())
    assert not missing, (
        f"bundle is missing files present in server/: {missing} — {hint}"
    )

    extra = sorted(bundle_files.keys() - root_files.keys())
    assert not extra, f"bundle has stale files absent from server/: {extra} — {hint}"

    differing = sorted(
        rel for rel, data in root_files.items() if bundle_files[rel] != data
    )
    assert not differing, f"bundle is byte-divergent from server/: {differing} — {hint}"


def test_entrypoint_wires_tool_surface_config() -> None:
    """Guard the tool-surface config block (#207) in the *canonical* entrypoint.

    The byte-for-byte test above only proves the bundle mirrors the repo — not
    that the block exists at all. If the wiring were dropped from the canonical
    ``server/main.py``, the mirror would still be "in sync" yet *both* channels
    would silently ignore YANDEX_DIRECT_TOOL_PROFILE / *_GROUPS / *_TOOLS (the
    exact #236 Codex-channel failure mode). Asserting against the source closes
    that gap; the sync guard then propagates it to the bundle."""
    text = (ROOT_SERVER / "main.py").read_text()
    assert "apply_tool_surface" in text
    assert "config_from_env" in text
    assert "env_config_warnings" in text
