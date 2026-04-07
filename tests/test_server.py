"""Smoke test: MCP server registers all tools when started via __main__."""

import json
import subprocess
import sys
from pathlib import Path

EXPECTED_TOOLS = {
    "campaigns_list",
    "campaigns_update",
    "ads_list",
    "keywords_list",
    "keywords_update",
    "reports_get",
    "auth_status",
    "auth_setup",
    "auth_login",
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _read_response(proc: subprocess.Popen) -> dict:
    """Read a single JSON-RPC response line from server stdout."""
    line = proc.stdout.readline()
    assert line, "Server closed stdout unexpectedly"
    return json.loads(line)


def test_mcp_server_registers_all_tools():
    proc = subprocess.Popen(
        [sys.executable, str(PROJECT_ROOT / "server" / "main.py")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    try:
        # 1. initialize
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
        proc.stdin.write(json.dumps(init_msg) + "\n")
        proc.stdin.flush()

        resp = _read_response(proc)
        assert resp["id"] == 1
        assert "tools" in resp["result"]["capabilities"]

        # 2. notifications/initialized
        proc.stdin.write(
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"
        )
        proc.stdin.flush()

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
