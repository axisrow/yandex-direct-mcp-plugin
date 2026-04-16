import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "yandex-direct"
PLUGIN_MANIFEST = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
MARKETPLACE_MANIFEST = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
MCP_MANIFEST = PLUGIN_ROOT / ".mcp.json"
ROOT_MCP_MANIFEST = REPO_ROOT / ".mcp.json"
SERVER_ENTRYPOINT = PLUGIN_ROOT / "server" / "main.py"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def test_codex_plugin_bundle_exists() -> None:
    assert PLUGIN_ROOT.exists()
    assert PLUGIN_MANIFEST.exists()
    assert MARKETPLACE_MANIFEST.exists()
    assert MCP_MANIFEST.exists()
    assert ROOT_MCP_MANIFEST.exists()
    assert SERVER_ENTRYPOINT.exists()


def test_marketplace_entry_points_to_plugin_bundle() -> None:
    marketplace = _load_json(MARKETPLACE_MANIFEST)

    plugin_entry = next(
        item for item in marketplace["plugins"] if item["name"] == "yandex-direct"
    )

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
    plugin = _load_json(PLUGIN_MANIFEST)
    mcp = _load_json(MCP_MANIFEST)

    assert plugin["name"] == "yandex-direct"
    assert plugin["skills"] == "./skills/"
    assert plugin["mcpServers"] == "./.mcp.json"
    assert plugin["interface"]["displayName"] == "Yandex Direct"

    server = mcp["yandex-direct-mcp"]
    assert server["command"] == "python3"
    assert server["args"] == ["${CLAUDE_PLUGIN_ROOT}/server/main.py"]


def test_root_mcp_manifest_uses_flat_server_mapping() -> None:
    mcp = _load_json(ROOT_MCP_MANIFEST)

    assert "mcpServers" not in mcp
    server = mcp["yandex-direct-mcp"]
    assert server["command"] == "python3"
    assert server["args"] == ["${CLAUDE_PLUGIN_ROOT}/server/main.py"]
