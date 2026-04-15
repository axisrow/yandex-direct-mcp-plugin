"""Smoke test: MCP server registers all tools when started via __main__."""

import json
import os
import subprocess
import sys
from pathlib import Path

from server.contract import (
    CLI_HELPER_TOOL_NAMES,
    PLUGIN_ONLY_TOOL_NAMES,
    PUBLIC_TOOL_NAMES,
    REMOVED_LEGACY_PUBLIC_NAMES,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _read_response(proc: subprocess.Popen[str]) -> dict:
    """Read a single JSON-RPC response line from server stdout."""
    assert proc.stdout is not None
    line = proc.stdout.readline()
    assert line, "Server closed stdout unexpectedly"
    return json.loads(line)


def _start_server(env: dict[str, str] | None = None) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, str(PROJECT_ROOT / "server" / "main.py")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env,
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
        assert tool_names == PUBLIC_TOOL_NAMES, (
            f"Missing tools: {PUBLIC_TOOL_NAMES - tool_names}, "
            f"extra tools: {tool_names - PUBLIC_TOOL_NAMES}"
        )
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_mcp_server_keeps_helper_and_plugin_tools_separate():
    assert CLI_HELPER_TOOL_NAMES <= PUBLIC_TOOL_NAMES
    assert PLUGIN_ONLY_TOOL_NAMES <= PUBLIC_TOOL_NAMES
    assert CLI_HELPER_TOOL_NAMES.isdisjoint(PLUGIN_ONLY_TOOL_NAMES)


def test_mcp_server_does_not_expose_removed_legacy_aliases():
    proc = _start_server()
    try:
        _initialize(proc)
        assert proc.stdin is not None
        proc.stdin.write(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {},
                }
            )
            + "\n"
        )
        proc.stdin.flush()

        resp = _read_response(proc)
        assert resp["id"] == 2
        tool_names = {t["name"] for t in resp["result"]["tools"]}
        assert tool_names.isdisjoint(REMOVED_LEGACY_PUBLIC_NAMES)
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
                        "name": "campaigns_get",
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


def test_mcp_server_tools_call_campaigns_get_accepts_valid_state():
    proc = _start_server(env={**os.environ, "PATH": ""})
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
                        "name": "campaigns_get",
                        "arguments": {"state": "ON"},
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
        assert structured["error"] != "invalid_state"
    finally:
        proc.terminate()
        proc.wait(timeout=5)
