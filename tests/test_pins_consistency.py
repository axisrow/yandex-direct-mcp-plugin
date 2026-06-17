"""Guard that the runtime-pins.env single source of truth stays in lockstep.

#223 introduced exact-version pinning for `mcp` and `direct-cli` and a stamp-
file gate that skips bootstrap on hot starts. The wiring spans 5 files: the
pin file, its byte-identical Codex bundle copy, pyproject.toml, server/cli/
runner.py's MIN_DIRECT_VERSION, and the two bootstrap shell scripts. These
tests fail noisily if any of them drifts out of sync.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PIN_FILE_REPO = REPO_ROOT / "scripts" / "runtime-pins.env"
PIN_FILE_BUNDLE = REPO_ROOT / "plugins" / "yandex-direct" / "scripts" / "runtime-pins.env"
PYPROJECT = REPO_ROOT / "pyproject.toml"
RUNNER_PY = REPO_ROOT / "server" / "cli" / "runner.py"
SETUP_SH = REPO_ROOT / "hooks" / "setup.sh"
RUN_SERVER_SH = REPO_ROOT / "plugins" / "yandex-direct" / "run-server.sh"

REQUIRED_KEYS = ("PLUGIN_VERSION", "MCP_VERSION", "DIRECT_CLI_VERSION")
PEP440_LITE_RE = re.compile(r"^\d+\.\d+\.\d+(?:[.\-+a-zA-Z0-9]*)?$")


def _parse_pin_file(path: Path) -> dict[str, str]:
    """Return ``{KEY: VALUE}`` for KEY=VALUE lines, ignoring blanks and comments."""
    pins: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        assert "=" in line, f"{path}: malformed line {line!r}"
        key, value = line.split("=", 1)
        assert key not in pins, f"{path}: duplicate key {key!r}"
        pins[key] = value
    return pins


@pytest.fixture(scope="module")
def pins() -> dict[str, str]:
    return _parse_pin_file(PIN_FILE_REPO)


def test_pin_file_has_required_keys_only(pins: dict[str, str]) -> None:
    """#1 — pin file has exactly PLUGIN_VERSION, MCP_VERSION, DIRECT_CLI_VERSION."""
    assert set(pins) == set(REQUIRED_KEYS), (
        f"unexpected keys in {PIN_FILE_REPO}: {set(pins) ^ set(REQUIRED_KEYS)}"
    )


def test_pin_values_are_pep440_lite(pins: dict[str, str]) -> None:
    """#2 — every value matches PEP 440 lite (X.Y.Z with optional suffix)."""
    for key in REQUIRED_KEYS:
        assert PEP440_LITE_RE.match(pins[key]), (
            f"{key}={pins[key]!r} is not a valid PEP 440 version"
        )


def test_bundle_copy_is_byte_identical() -> None:
    """#1b — plugins/yandex-direct/scripts/runtime-pins.env mirrors the repo copy.

    The Codex bundle resolves ``$PLUGIN_ROOT/scripts/runtime-pins.env`` inside
    ``plugins/yandex-direct/``, so a separate copy lives there. It must match
    the repo source byte-for-byte; ``scripts/update-pins.sh`` and
    ``scripts/update-version.sh`` write both.
    """
    assert PIN_FILE_BUNDLE.read_bytes() == PIN_FILE_REPO.read_bytes(), (
        "scripts/runtime-pins.env and plugins/yandex-direct/scripts/runtime-pins.env "
        "have drifted; rerun scripts/update-pins.sh or scripts/update-version.sh"
    )


def test_pyproject_pins_match(pins: dict[str, str]) -> None:
    """#3 — pyproject.toml pins ``mcp`` and ``direct-cli`` to the same exact versions."""
    pyproject = tomllib.loads(PYPROJECT.read_text())
    deps = pyproject["project"]["dependencies"]
    expected = {f"mcp=={pins['MCP_VERSION']}", f"direct-cli=={pins['DIRECT_CLI_VERSION']}"}
    actual = set(deps)
    assert expected == actual, (
        f"pyproject.toml dependencies drifted from runtime-pins.env: "
        f"expected {expected}, got {actual}"
    )


def test_runner_min_direct_version_matches(pins: dict[str, str]) -> None:
    """#4 — ``MIN_DIRECT_VERSION`` in runner.py equals the (X, Y, Z) of the pin."""
    text = RUNNER_PY.read_text()
    match = re.search(
        r"^MIN_DIRECT_VERSION:\s*tuple\[int, int, int\]\s*=\s*\((\d+),\s*(\d+),\s*(\d+)\)",
        text,
        re.MULTILINE,
    )
    assert match, "MIN_DIRECT_VERSION not found in expected form in runner.py"
    actual = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    expected_parts = pins["DIRECT_CLI_VERSION"].split(".")[:3]
    expected = tuple(int(p) for p in expected_parts)
    assert actual == expected, (
        f"MIN_DIRECT_VERSION={actual} does not match "
        f"DIRECT_CLI_VERSION={pins['DIRECT_CLI_VERSION']!r}"
    )


def test_shell_scripts_source_pin_file() -> None:
    """#5 — both bootstrap scripts source runtime-pins.env."""
    setup_sh = SETUP_SH.read_text()
    run_server_sh = RUN_SERVER_SH.read_text()

    assert "/scripts/runtime-pins.env" in setup_sh, (
        "hooks/setup.sh does not reference scripts/runtime-pins.env"
    )
    assert ". \"$PIN_FILE\"" in setup_sh, (
        "hooks/setup.sh does not source the pin file"
    )

    assert "/scripts/runtime-pins.env" in run_server_sh, (
        "plugins/yandex-direct/run-server.sh does not reference runtime-pins.env"
    )
    assert ". \"$PIN_FILE\"" in run_server_sh, (
        "plugins/yandex-direct/run-server.sh does not source the pin file"
    )


def test_shell_scripts_use_pinned_literals() -> None:
    """#6 — both scripts install ``mcp==${MCP_VERSION}`` and ``direct-cli==${DIRECT_CLI_VERSION}``.

    Guards against someone hand-editing one channel to a different pin string
    (or back to a ``>=`` range) and forgetting the other.
    """
    for path in (SETUP_SH, RUN_SERVER_SH):
        text = path.read_text()
        assert "mcp==${MCP_VERSION}" in text, (
            f"{path}: install command does not use mcp==${{MCP_VERSION}}"
        )
        assert "direct-cli==${DIRECT_CLI_VERSION}" in text, (
            f"{path}: install command does not use direct-cli==${{DIRECT_CLI_VERSION}}"
        )


def test_plugin_version_matches_pyproject(pins: dict[str, str]) -> None:
    """#7 — PLUGIN_VERSION in the pin file equals pyproject.toml's version.

    ``scripts/update-version.sh`` writes both; this test catches any case where
    someone bumped pyproject.toml by hand without rerunning the script.
    """
    pyproject = tomllib.loads(PYPROJECT.read_text())
    assert pins["PLUGIN_VERSION"] == pyproject["project"]["version"], (
        f"PLUGIN_VERSION={pins['PLUGIN_VERSION']!r} does not match "
        f"pyproject.toml version={pyproject['project']['version']!r}"
    )
