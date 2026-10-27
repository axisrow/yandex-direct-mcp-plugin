"""Tests for default-on bundle registration and its env override (#312)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from server import optional_tools
from server.contract import (
    DEFAULT_TOOL_NAMES,
    IMPLEMENTED_BUNDLE_TOOL_NAMES,
    PUBLIC_CONTRACT,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TOOL_SURFACE_ENV = (
    optional_tools.ENV_OPTIONAL_TOOLS,
    "YANDEX_DIRECT_TOOL_PROFILE",
    "YANDEX_DIRECT_ENABLED_GROUPS",
    "YANDEX_DIRECT_DISABLED_GROUPS",
    "YANDEX_DIRECT_ENABLED_TOOLS",
    "YANDEX_DIRECT_DISABLED_TOOLS",
)


def _clean_env(extra_python_path: Path | None = None) -> dict[str, str]:
    env = os.environ.copy()
    for name in _TOOL_SURFACE_ENV:
        env.pop(name, None)
    python_path = [str(PROJECT_ROOT)]
    if extra_python_path is not None:
        python_path.insert(0, str(extra_python_path))
    if env.get("PYTHONPATH"):
        python_path.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(python_path)
    return env


def _run_python(
    source: str, *, env: dict[str, str], check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", source],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=check,
        timeout=30,
    )


def test_enabled_bundles_default_on_and_env_override() -> None:
    env_name = optional_tools.ENV_OPTIONAL_TOOLS
    # Default-on (#312): without the env every known bundle loads.
    assert optional_tools.enabled_bundles({}) == frozenset(
        optional_tools.OPTIONAL_BUNDLES
    )
    # A non-empty env is an explicit narrow-down override; "all" expands.
    assert optional_tools.enabled_bundles(
        {env_name: " browser, TRACKINGPARAMS, browser, unknown "}
    ) == frozenset({"browser", "trackingparams"})
    assert optional_tools.enabled_bundles({env_name: "all,unknown"}) == frozenset(
        optional_tools.OPTIONAL_BUNDLES
    )
    warnings = optional_tools.optional_tools_warnings(
        {env_name: "all, UNKNOWN, another"}
    )
    assert warnings == [
        (
            "unknown optional tool bundles ignored: ['another', 'unknown']; "
            "known: ['browser', 'trackingparams']"
        )
    ]


def test_optional_modules_preserve_bundle_order_and_deduplicate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        optional_tools,
        "OPTIONAL_BUNDLES",
        {
            "second": ("example.shared", "example.second"),
            "first": ("example.first", "example.shared"),
        },
    )
    env = {optional_tools.ENV_OPTIONAL_TOOLS: "first,second"}
    assert optional_tools.optional_modules(env) == (
        "example.shared",
        "example.second",
        "example.first",
    )


def test_optional_bundle_names_match_contract_metadata() -> None:
    contract_bundles = {
        tool.optional_bundle
        for tool in PUBLIC_CONTRACT
        if tool.optional_bundle is not None
    }
    assert set(optional_tools.OPTIONAL_BUNDLES) == contract_bundles
    assert optional_tools.optional_tool_names() == frozenset(
        tool.public_name for tool in PUBLIC_CONTRACT if tool.optional_bundle is not None
    )


def test_known_optional_module_import_failure_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        optional_tools,
        "OPTIONAL_BUNDLES",
        {"broken": ("module_that_does_not_exist_for_issue_293",)},
    )
    with pytest.raises(ModuleNotFoundError, match="module_that_does_not_exist"):
        optional_tools.import_optional_modules(
            {optional_tools.ENV_OPTIONAL_TOOLS: "broken"}
        )


def test_default_server_imports_every_bundle_module_and_registers_surface() -> None:
    source = """
import json
import sys

import server.main as main

assert "server.tools.masters" in sys.modules
assert "server.tools.history" in sys.modules
assert "server.tools.playwright" in sys.modules
assert "server.tools.trackingparams" in sys.modules
registry = main.mcp._tool_manager._tools
print(json.dumps({"tool_names": sorted(registry)}))
"""
    result = _run_python(source, env=_clean_env())
    payload = json.loads(result.stdout)
    assert set(payload["tool_names"]) == (
        DEFAULT_TOOL_NAMES | IMPLEMENTED_BUNDLE_TOOL_NAMES
    )


def test_default_start_degrades_softly_when_bundle_module_is_missing() -> None:
    """Default-on must not break startup when a bundle module is unavailable."""
    source = """
import json

import server.optional_tools as optional_tools

optional_tools.OPTIONAL_BUNDLES = {
    "browser": (
        "module_that_does_not_exist_for_default_on",
        "server.tools.history",
        "server.tools.playwright",
    ),
    "trackingparams": ("server.tools.trackingparams",),
}
import server.main as main

registry = main.mcp._tool_manager._tools
print(json.dumps({"tool_names": sorted(registry)}))
"""
    result = _run_python(source, env=_clean_env())
    payload = json.loads(result.stdout)
    assert set(payload["tool_names"]) == (
        DEFAULT_TOOL_NAMES | {"history_get", "playwright_doctor", "trackingparams_get"}
    )
    # Sibling bundles stay alive; only the broken module's tools are skipped.
    assert "module_that_does_not_exist_for_default_on" in result.stderr


def test_explicit_env_bundle_import_failure_still_fails_closed() -> None:
    source = """
import server.optional_tools as optional_tools

optional_tools.OPTIONAL_BUNDLES = {"browser": ("module_that_does_not_exist_x",)}
import server.main as main
"""
    env = _clean_env()
    env[optional_tools.ENV_OPTIONAL_TOOLS] = "browser"
    result = _run_python(source, env=env, check=False)
    assert result.returncode != 0
    assert "module_that_does_not_exist_x" in result.stderr


def test_trackingparams_bundle_registers_only_opt_in_contract_tool() -> None:
    source = """
import json
import os
import sys

from server.optional_tools import ENV_OPTIONAL_TOOLS

os.environ[ENV_OPTIONAL_TOOLS] = "trackingparams"
import server.main as main

print(json.dumps({
    "module_loaded": "server.tools.trackingparams" in sys.modules,
    "tool_names": sorted(main.mcp._tool_manager._tools),
}))
"""
    result = _run_python(source, env=_clean_env())
    payload = json.loads(result.stdout)
    assert payload["module_loaded"] is True
    assert set(payload["tool_names"]) == DEFAULT_TOOL_NAMES | {"trackingparams_get"}


def test_main_import_gate_registers_stub_before_surface_filter(tmp_path: Path) -> None:
    (tmp_path / "optional_stub.py").write_text(
        """from server.main import mcp

@mcp.tool(name="masters_get", description="Synthetic optional tool for #293")
def masters_get() -> dict[str, bool]:
    return {"stub": True}
"""
    )
    source = """
import json
import os
import sys

import server.optional_tools as optional_tools

optional_tools.OPTIONAL_BUNDLES = {"browser": ("optional_stub",)}
os.environ[optional_tools.ENV_OPTIONAL_TOOLS] = "browser"
import server.main as main

print(json.dumps({
    "stub_loaded": "optional_stub" in sys.modules,
    "tool_names": sorted(main.mcp._tool_manager._tools),
}))
"""
    result = _run_python(source, env=_clean_env(tmp_path))
    payload = json.loads(result.stdout)
    assert payload["stub_loaded"] is True
    assert set(payload["tool_names"]) == DEFAULT_TOOL_NAMES | {"masters_get"}


def test_tool_surface_filter_runs_after_optional_import(tmp_path: Path) -> None:
    (tmp_path / "optional_stub.py").write_text(
        """from server.main import mcp

@mcp.tool(name="masters_get", description="Synthetic optional tool for #293")
def masters_get() -> dict[str, bool]:
    return {"stub": True}
"""
    )
    source = """
import json
import os

import server.optional_tools as optional_tools

optional_tools.OPTIONAL_BUNDLES = {"browser": ("optional_stub",)}
os.environ[optional_tools.ENV_OPTIONAL_TOOLS] = "browser"
os.environ["YANDEX_DIRECT_DISABLED_TOOLS"] = "masters_get"
import server.main as main

print(json.dumps({"tool_names": sorted(main.mcp._tool_manager._tools)}))
"""
    result = _run_python(source, env=_clean_env(tmp_path))
    payload = json.loads(result.stdout)
    assert set(payload["tool_names"]) == DEFAULT_TOOL_NAMES
    assert "1 tool(s) disabled by config; 151 enabled" in result.stderr
