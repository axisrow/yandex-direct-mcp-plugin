import json
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"
PLUGIN_ROOT = REPO_ROOT / "plugins" / "yandex-direct"
ROOT_PLUGIN_MANIFEST = REPO_ROOT / ".claude-plugin" / "plugin.json"
PLUGIN_MANIFEST = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
MARKETPLACE_MANIFEST = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
MCP_MANIFEST = PLUGIN_ROOT / ".mcp.json"
SERVER_ENTRYPOINT = PLUGIN_ROOT / "server" / "main.py"
SERVER_WRAPPER = PLUGIN_ROOT / "run-server.sh"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _load_pyproject() -> dict:
    return tomllib.loads(PYPROJECT.read_text())


def test_codex_plugin_bundle_exists() -> None:
    assert PLUGIN_ROOT.exists()
    assert PLUGIN_MANIFEST.exists()
    assert MARKETPLACE_MANIFEST.exists()
    assert MCP_MANIFEST.exists()
    assert SERVER_ENTRYPOINT.exists()


def test_marketplace_entry_points_to_plugin_bundle() -> None:
    root_plugin = _load_json(ROOT_PLUGIN_MANIFEST)
    pyproject = _load_pyproject()
    marketplace = _load_json(MARKETPLACE_MANIFEST)

    plugin_entry = next(
        item for item in marketplace["plugins"] if item["name"] == "yandex-direct"
    )

    assert pyproject["project"]["version"] == root_plugin["version"]
    assert plugin_entry["version"] == root_plugin["version"]
    assert plugin_entry["source"] == {
        "source": "local",
        "path": "./plugins/yandex-direct",
    }
    assert plugin_entry["policy"] == {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }
    assert plugin_entry["category"] == "Productivity"


def test_plugin_manifest_matches_bundle_layout() -> None:
    root_plugin = _load_json(ROOT_PLUGIN_MANIFEST)
    plugin = _load_json(PLUGIN_MANIFEST)
    mcp = _load_json(MCP_MANIFEST)

    assert plugin["name"] == "yandex-direct"
    assert plugin["version"] == root_plugin["version"]
    assert plugin["skills"] == "./skills/"
    assert plugin["mcpServers"] == "./.mcp.json"
    assert plugin["interface"]["displayName"] == "Yandex Direct"

    # The bundle launches via a venv-aware wrapper, NOT a bare interpreter, so a
    # Linux/PEP-668 install can still find `mcp`/`direct-cli` (issue #197).
    server = mcp["mcpServers"]["yandex-direct-mcp"]
    assert server["command"] == "bash"
    assert server["args"] == ["${CLAUDE_PLUGIN_ROOT}/run-server.sh"]


def test_bundle_does_not_launch_bare_interpreter() -> None:
    """Regression guard for #197: a marketplace/Codex install on Linux must not
    rely on a bare `python3` that cannot import the plugin deps."""
    mcp = _load_json(MCP_MANIFEST)
    server = mcp["mcpServers"]["yandex-direct-mcp"]
    assert server["command"] not in {"python", "python3"}, (
        "bundle .mcp.json must launch via the venv-aware wrapper, not a bare "
        f"interpreter (got {server['command']!r})"
    )
    assert SERVER_WRAPPER.exists(), "bundle run-server.sh wrapper is missing"
    text = SERVER_WRAPPER.read_text()
    # The wrapper must be self-sufficient (no hooks/setup.sh in the bundle): it
    # resolves/bootstraps a venv and ultimately execs the server entrypoint
    # with the pinned mcp install (no bare system-python bypass — #223).
    assert "server/main.py" in text
    assert "pip install" in text
    assert "mcp==${MCP_VERSION}" in text
    # Install-failure backoff (#214): a failed bootstrap must not silently
    # re-hammer pip on every cold start — it records a throttle marker.
    assert ".bootstrap-failed" in text
    # Negative anchors (#223): supply-chain pin is moot if the wrapper can
    # ever fall back to a bare system python that "happens to have mcp".
    assert "_can_import_mcp" not in text
    assert 'PYTHON="python3"' not in text


def test_plugin_entrypoint_imports_same_tools_as_repo_entrypoint() -> None:
    def tool_imports(path: Path) -> set[str]:
        return {
            line.strip()
            for line in path.read_text().splitlines()
            if line.startswith("import server.tools.")
        }

    assert tool_imports(SERVER_ENTRYPOINT) == tool_imports(
        REPO_ROOT / "server" / "main.py"
    )
