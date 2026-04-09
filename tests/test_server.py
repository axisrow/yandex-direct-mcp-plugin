"""Smoke test: MCP server registers all tools when started via __main__."""

import json
import subprocess
import sys
from pathlib import Path

EXPECTED_TOOLS = {
    # Ad Groups (4 tools)
    "adgroups_list",
    "adgroups_add",
    "adgroups_update",
    "adgroups_delete",
    # Campaigns (6 tools)
    "campaigns_list",
    "campaigns_update",
    "campaigns_add",
    "campaigns_delete",
    "campaigns_archive",
    "campaigns_unarchive",
    # Ads (7 tools)
    "ads_list",
    "ads_add",
    "ads_update",
    "ads_delete",
    "ads_moderate",
    "ads_suspend",
    "ads_resume",
    # Keywords (6 tools)
    "keywords_list",
    "keywords_update",
    "keywords_add",
    "keywords_delete",
    "keywords_suspend",
    "keywords_resume",
    # Reports
    "reports_get",
    # Bids (2 tools)
    "bids_list",
    "bids_set",
    # Bid Modifiers (4 tools)
    "bidmodifiers_list",
    "bidmodifiers_set",
    "bidmodifiers_toggle",
    "bidmodifiers_delete",
    # Sitelinks (3 tools)
    "sitelinks_list",
    "sitelinks_add",
    "sitelinks_delete",
    # VCards (3 tools)
    "vcards_list",
    "vcards_add",
    "vcards_delete",
    # Ad Images (3 tools)
    "adimages_list",
    "adimages_add",
    "adimages_delete",
    # Ad Extensions (3 tools)
    "adextensions_list",
    "adextensions_add",
    "adextensions_delete",
    # Audience Targets (5 tools)
    "audience_targets_list",
    "audience_targets_add",
    "audience_targets_delete",
    "audience_targets_suspend",
    "audience_targets_resume",
    # Retargeting (3 tools)
    "retargeting_list",
    "retargeting_add",
    "retargeting_delete",
    # Dynamic Targets (4 tools)
    "dynamic_targets_list",
    "dynamic_targets_add",
    "dynamic_targets_update",
    "dynamic_targets_delete",
    # Negative Keywords (4 tools)
    "negative_keywords_list",
    "negative_keywords_add",
    "negative_keywords_update",
    "negative_keywords_delete",
    # Negative Keyword Shared Sets (4 tools)
    "negative_keyword_shared_sets_list",
    "negative_keyword_shared_sets_add",
    "negative_keyword_shared_sets_update",
    "negative_keyword_shared_sets_delete",
    # Smart Targets (4 tools)
    "smart_targets_list",
    "smart_targets_add",
    "smart_targets_update",
    "smart_targets_delete",
    # Dictionaries (1 tool)
    "dictionaries_get",
    # Changes (3 tools)
    "changes_check",
    "changes_checkcamp",
    "changes_checkdict",
    # Clients (2 tools)
    "clients_get",
    "clients_update",
    # Agency (3 tools)
    "agency_clients_list",
    "agency_clients_add",
    "agency_clients_delete",
    # Research (2 tools)
    "keywords_has_volume",
    "keywords_deduplicate",
    # Leads (1 tool)
    "leads_list",
    # Feeds (4 tools)
    "feeds_list",
    "feeds_add",
    "feeds_update",
    "feeds_delete",
    # Creatives (1 tool)
    "creatives_list",
    # Turbo Pages (1 tool)
    "turbo_pages_list",
    # Auth (3 tools)
    "auth_status",
    "auth_setup",
    "auth_login",
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _read_response(proc: subprocess.Popen[str]) -> dict:
    """Read a single JSON-RPC response line from server stdout."""
    assert proc.stdout is not None
    line = proc.stdout.readline()
    assert line, "Server closed stdout unexpectedly"
    return json.loads(line)


def _start_server() -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, str(PROJECT_ROOT / "server" / "main.py")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(PROJECT_ROOT),
    )


def _initialize(proc: subprocess.Popen[str]) -> None:
    init_msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"},
        },
    }
    assert proc.stdin is not None
    proc.stdin.write(json.dumps(init_msg) + "\n")
    proc.stdin.flush()

    resp = _read_response(proc)
    assert resp["id"] == 1
    assert "tools" in resp["result"]["capabilities"]

    proc.stdin.write(
        json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"
    )
    proc.stdin.flush()


def test_mcp_server_registers_all_tools():
    proc = _start_server()
    try:
        _initialize(proc)

        # 3. tools/list
        tools_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }
        proc.stdin.write(json.dumps(tools_msg) + "\n")
        proc.stdin.flush()

        # Skip any non-JSON lines (e.g. INFO log lines on stderr)
        resp = _read_response(proc)
        assert resp["id"] == 2

        tool_names = {t["name"] for t in resp["result"]["tools"]}
        assert tool_names == EXPECTED_TOOLS, (
            f"Missing tools: {EXPECTED_TOOLS - tool_names}, "
            f"extra tools: {tool_names - EXPECTED_TOOLS}"
        )
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_mcp_server_tools_call_auth_status():
    proc = _start_server()
    try:
        _initialize(proc)
        assert proc.stdin is not None
        proc.stdin.write(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": "auth_status", "arguments": {}},
                }
            )
            + "\n"
        )
        proc.stdin.flush()

        resp = _read_response(proc)
        assert resp["id"] == 2
        assert resp["result"]["isError"] is False
        body = json.loads(resp["result"]["content"][0]["text"])
        assert body == {"valid": False}
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_mcp_server_tools_call_returns_structured_tool_error():
    proc = _start_server()
    try:
        _initialize(proc)
        assert proc.stdin is not None
        proc.stdin.write(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "campaigns_list",
                        "arguments": {"state": "BAD"},
                    },
                }
            )
            + "\n"
        )
        proc.stdin.flush()

        resp = _read_response(proc)
        assert resp["id"] == 2
        assert resp["result"]["isError"] is False
        structured = resp["result"]["structuredContent"]["result"]
        assert structured["error"] == "invalid_state"
        assert "got 'BAD'" in structured["message"]
    finally:
        proc.terminate()
        proc.wait(timeout=5)
