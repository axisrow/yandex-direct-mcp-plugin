"""Smoke test: MCP server registers all tools when started via __main__."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from server.contract import (
    BROWSER_TOOL_NAMES,
    CLI_HELPER_TOOL_NAMES,
    DEFAULT_TOOL_NAMES,
    PLUGIN_ONLY_TOOL_NAMES,
    PUBLIC_TOOL_NAMES,
    REMOVED_LEGACY_PUBLIC_NAMES,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_OPTIONAL_TOOLS = "YANDEX_DIRECT_OPTIONAL_TOOLS"
_TOOL_SURFACE_ENV = (
    ENV_OPTIONAL_TOOLS,
    "YANDEX_DIRECT_TOOL_PROFILE",
    "YANDEX_DIRECT_ENABLED_GROUPS",
    "YANDEX_DIRECT_DISABLED_GROUPS",
    "YANDEX_DIRECT_ENABLED_TOOLS",
    "YANDEX_DIRECT_DISABLED_TOOLS",
)
_BROWSER_MODULE_FILES = tuple(
    PROJECT_ROOT / "server" / "tools" / f"{name}.py"
    for name in ("masters", "history", "playwright")
)
_ALL_OPTIONAL_MODULE_FILES = _BROWSER_MODULE_FILES + (
    PROJECT_ROOT / "server" / "tools" / "trackingparams.py",
)


def _read_response(proc: subprocess.Popen[str]) -> dict:
    """Read a single JSON-RPC response line from server stdout."""
    assert proc.stdout is not None
    line = proc.stdout.readline()
    assert line, "Server closed stdout unexpectedly"
    return json.loads(line)


def _start_server(env: dict[str, str] | None = None) -> subprocess.Popen[str]:
    proc_env = os.environ.copy()
    proc_env["HOME"] = "/tmp/yandex-direct-mcp-plugin-test-home"
    proc_env.pop("YANDEX_DIRECT_TOKEN", None)
    proc_env.pop("YANDEX_DIRECT_LOGIN", None)
    for name in _TOOL_SURFACE_ENV:
        proc_env.pop(name, None)
    if env:
        proc_env.update(env)
    return subprocess.Popen(
        [sys.executable, str(PROJECT_ROOT / "server" / "main.py")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/tmp",
        env=proc_env,
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
        assert tool_names == DEFAULT_TOOL_NAMES, (
            f"Missing tools: {DEFAULT_TOOL_NAMES - tool_names}, "
            f"extra tools: {tool_names - DEFAULT_TOOL_NAMES}"
        )
    finally:
        proc.terminate()
        proc.wait(timeout=5)


@pytest.mark.skipif(
    not all(path.exists() for path in _ALL_OPTIONAL_MODULE_FILES),
    reason="full optional tool implementations land in later #290 work items",
)
def test_mcp_server_registers_full_surface():
    proc = _start_server(env={ENV_OPTIONAL_TOOLS: "all"})
    try:
        _initialize(proc)
        assert _list_tool_names(proc) == PUBLIC_TOOL_NAMES
    finally:
        proc.terminate()
        proc.wait(timeout=5)


@pytest.mark.skipif(
    not all(path.exists() for path in _BROWSER_MODULE_FILES),
    reason="browser tool implementations land in later #290 work items",
)
def test_mcp_server_registers_only_browser_optional_bundle():
    proc = _start_server(env={ENV_OPTIONAL_TOOLS: "browser"})
    try:
        _initialize(proc)
        expected = DEFAULT_TOOL_NAMES | (BROWSER_TOOL_NAMES - {"trackingparams_get"})
        assert _list_tool_names(proc) == expected
    finally:
        proc.terminate()
        proc.wait(timeout=5)


@pytest.mark.skipif(
    not all(path.exists() for path in _ALL_OPTIONAL_MODULE_FILES),
    reason="full optional tool implementations land in later #290 work items",
)
def test_disabled_browser_group_removes_loaded_optional_surface():
    proc = _start_server(
        env={
            ENV_OPTIONAL_TOOLS: "all",
            "YANDEX_DIRECT_DISABLED_GROUPS": "browser",
        }
    )
    try:
        _initialize(proc)
        assert _list_tool_names(proc) == DEFAULT_TOOL_NAMES
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def _list_tool_names(proc: subprocess.Popen[str]) -> set[str]:
    assert proc.stdin is not None
    proc.stdin.write(
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        + "\n"
    )
    proc.stdin.flush()
    resp = _read_response(proc)
    assert resp["id"] == 2
    return {t["name"] for t in resp["result"]["tools"]}


def test_unregistered_optional_tool_allowlist_fails_closed():
    """A browser tool allowlist cannot fail open to all default tools (#304)."""
    proc = _start_server(env={"YANDEX_DIRECT_ENABLED_TOOLS": "masters_get"})
    try:
        _initialize(proc)
        assert _list_tool_names(proc) == set()
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_mcp_server_respects_disabled_tool_groups():
    """YANDEX_DIRECT_DISABLED_GROUPS removes a group from tools/list (#190).

    destructive=delete only; archive is the separate lifecycle group (#205-A),
    so disabling destructive drops campaigns_delete but keeps ads_archive.
    """
    proc = _start_server(env={"YANDEX_DIRECT_DISABLED_GROUPS": "destructive,lifecycle"})
    try:
        _initialize(proc)
        names = _list_tool_names(proc)
        assert "campaigns_delete" not in names  # destructive
        assert "ads_archive" not in names  # lifecycle
        assert "campaigns_get" in names
        assert names < DEFAULT_TOOL_NAMES
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_mcp_server_allowlist_profile_via_enabled_groups():
    """YANDEX_DIRECT_ENABLED_GROUPS switches to allow-list mode (#190)."""
    proc = _start_server(env={"YANDEX_DIRECT_ENABLED_GROUPS": "analytics"})
    try:
        _initialize(proc)
        names = _list_tool_names(proc)
        assert "reports_get" in names
        assert "campaigns_add" not in names
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_mcp_server_warns_and_ignores_unknown_optional_bundle():
    proc = _start_server(env={ENV_OPTIONAL_TOOLS: "unknown-bundle"})
    try:
        _initialize(proc)
        assert _list_tool_names(proc) == DEFAULT_TOOL_NAMES
    finally:
        proc.terminate()
        proc.wait(timeout=5)
    assert proc.stderr is not None
    assert (
        "unknown optional tool bundles ignored: ['unknown-bundle']"
        in proc.stderr.read()
    )


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
        assert body == {
            "valid": False,
            "reason": "not_authenticated",
            "profile": "default",
        }
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


def test_mcp_server_tools_call_rejects_removed_campaigns_list_alias():
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
                        "arguments": {"state": "ON"},
                    },
                }
            )
            + "\n"
        )
        proc.stdin.flush()

        resp = _read_response(proc)
        assert resp["id"] == 2
        assert resp["result"]["isError"] is True
        assert "campaigns_list" in resp["result"]["content"][0]["text"]
    finally:
        proc.terminate()
        proc.wait(timeout=5)
