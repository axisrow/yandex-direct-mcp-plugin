"""Contract and argv tests for read-only Campaign Wizard tools."""

import asyncio
import importlib
import inspect
import json
import sys
from collections.abc import Iterator
from types import ModuleType
from typing import Any, cast
from unittest.mock import MagicMock, patch

import click
import pytest
from direct_cli.cli import cli  # type: ignore[import-not-found, import-untyped]
from mcp.server.fastmcp import FastMCP

import server.main as main_module
import server.tools as tools_package
from server.contract import PUBLIC_CONTRACT
from tests.helpers import import_tool_module_without_registration
from tests.measure_tool_tokens import _make_counter

TOOL_NAMES = (
    "masters_list",
    "masters_get",
    "masters_adimages_get",
    "masters_targetactions_get",
    "masters_counters_get",
    "masters_audience_get",
)
NESTED_TOOL_PATHS = {
    "masters_adimages_get": ("masters", "adimages", "get"),
    "masters_targetactions_get": ("masters", "targetactions", "get"),
    "masters_counters_get": ("masters", "counters", "get"),
    "masters_audience_get": ("masters", "audience", "get"),
}
IGNORED_CLI_PARAMS = {
    "headful",
    "profile_dir",
    "chrome_profile",
    "output_format",
    "output",
}


@pytest.fixture()
def masters_module() -> Iterator[ModuleType]:
    with import_tool_module_without_registration("server.tools.masters") as module:
        yield module


@pytest.fixture(autouse=True)
def clean_browser_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "YANDEX_DIRECT_BROWSER_PROFILE_DIR",
        "YANDEX_DIRECT_BROWSER_CHROME_PROFILE",
        "YANDEX_DIRECT_BROWSER_HEADFUL",
    ):
        monkeypatch.delenv(name, raising=False)


def _runner_for(module: ModuleType, result: object) -> MagicMock:
    runner = MagicMock()
    runner.run_json_lenient.return_value = result
    cast(Any, module).get_browser_runner = MagicMock(return_value=runner)
    return runner


def _click_command(path: tuple[str, ...]) -> click.Command:
    command: click.Command = cli
    for component in path:
        assert isinstance(command, click.Group), path
        child = command.get_command(click.Context(command), component)
        assert child is not None, path
        command = child
    return command


def test_masters_list_builds_default_read_command(masters_module: ModuleType) -> None:
    runner = _runner_for(masters_module, [{"id": 123}])

    result = masters_module.masters_list()

    assert result == [{"id": 123}]
    runner.run_json_lenient.assert_called_once_with(
        ["masters", "list", "--status", "not-archived", "--format", "json"]
    )
    cast(Any, masters_module).get_browser_runner.assert_called_once_with()


def test_masters_list_forwards_browser_env_after_command_options(
    masters_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _runner_for(masters_module, [])
    monkeypatch.setenv("YANDEX_DIRECT_BROWSER_PROFILE_DIR", "/tmp/profile")
    monkeypatch.setenv("YANDEX_DIRECT_BROWSER_CHROME_PROFILE", "Profile 4")
    monkeypatch.setenv("YANDEX_DIRECT_BROWSER_HEADFUL", "1")

    masters_module.masters_list(status="active")

    runner.run_json_lenient.assert_called_once_with(
        [
            "masters",
            "list",
            "--status",
            "active",
            "--profile-dir",
            "/tmp/profile",
            "--chrome-profile",
            "Profile 4",
            "--headful",
            "--format",
            "json",
        ]
    )


def test_masters_list_rejects_unknown_status(masters_module: ModuleType) -> None:
    runner = _runner_for(masters_module, [])

    result = masters_module.masters_list(status="paused")

    assert result["error"] == "invalid_status"
    runner.run_json_lenient.assert_not_called()


def test_masters_get_builds_exact_command(masters_module: ModuleType) -> None:
    runner = _runner_for(masters_module, [{"id": 101}, {"id": 202}])

    result = masters_module.masters_get(
        " 101, 202 ", moderation_statuses=True, tracking_params=True
    )

    assert result == [{"id": 101}, {"id": 202}]
    runner.run_json_lenient.assert_called_once_with(
        [
            "masters",
            "get",
            "101, 202",
            "--moderation-statuses",
            "--tracking-params",
            "--format",
            "json",
        ]
    )


def test_masters_get_rejects_blank_campaign_ids(masters_module: ModuleType) -> None:
    runner = _runner_for(masters_module, [])

    result = masters_module.masters_get("   ")

    assert result["error"] == "missing_campaign_ids"
    runner.run_json_lenient.assert_not_called()


def test_masters_get_preserves_single_campaign_object(
    masters_module: ModuleType,
) -> None:
    runner = _runner_for(masters_module, {"CampaignId": 101})

    result = masters_module.masters_get("101")

    assert result == {"CampaignId": 101}
    runner.run_json_lenient.assert_called_once_with(
        ["masters", "get", "101", "--format", "json"]
    )


@pytest.mark.parametrize("tool_name,path", NESTED_TOOL_PATHS.items())
def test_nested_read_tools_use_full_contract_path(
    masters_module: ModuleType,
    tool_name: str,
    path: tuple[str, ...],
) -> None:
    runner = _runner_for(masters_module, {"campaign_id": 456})

    result = getattr(masters_module, tool_name)("456")

    assert result == {"campaign_id": 456}
    runner.run_json_lenient.assert_called_once_with([*path, "456", "--format", "json"])


def test_adimages_path_is_not_flattened(masters_module: ModuleType) -> None:
    assert masters_module._command_path("masters_adimages_get") == [
        "masters",
        "adimages",
        "get",
    ]


def test_masters_signatures_match_click_except_env_and_output_options(
    masters_module: ModuleType,
) -> None:
    contract = {tool.public_name: tool for tool in PUBLIC_CONTRACT}

    for tool_name in TOOL_NAMES:
        tool = contract[tool_name]
        if tool.cli_subcommand_path is not None:
            path = tool.cli_subcommand_path
        else:
            assert tool.cli_service is not None
            assert tool.cli_subcommand is not None
            path = (tool.cli_service, tool.cli_subcommand)
        click_params = {
            parameter.name
            for parameter in _click_command(path).params
            if parameter.name not in IGNORED_CLI_PARAMS
        }
        mcp_params = set(
            inspect.signature(getattr(masters_module, tool_name)).parameters
        )
        assert mcp_params == click_params, tool_name


def test_masters_signature_defaults_and_cli_option_tables(
    masters_module: ModuleType,
) -> None:
    signatures = {
        name: inspect.signature(getattr(masters_module, name)) for name in TOOL_NAMES
    }

    assert signatures["masters_list"].parameters["status"].default == "not-archived"
    get_params = signatures["masters_get"].parameters
    assert get_params["campaign_ids"].default is inspect.Parameter.empty
    assert get_params["moderation_statuses"].default is False
    assert get_params["tracking_params"].default is False
    for tool_name in NESTED_TOOL_PATHS:
        parameter = signatures[tool_name].parameters["campaign_id"]
        assert parameter.default is inspect.Parameter.empty
        assert parameter.annotation is str

    assert [
        (option.name, option.flag, option.repeat, option.is_flag)
        for option in masters_module.MASTERS_LIST_OPTIONS
    ] == [("status", "--status", False, False)]
    assert [
        (option.name, option.flag, option.repeat, option.is_flag)
        for option in masters_module.MASTERS_GET_OPTIONS
    ] == [
        ("moderation_statuses", "--moderation-statuses", False, True),
        ("tracking_params", "--tracking-params", False, True),
    ]


def test_masters_status_choices_match_installed_click_command(
    masters_module: ModuleType,
) -> None:
    command = _click_command(("masters", "list"))
    status = next(
        parameter for parameter in command.params if parameter.name == "status"
    )

    assert isinstance(status.type, click.Choice)
    assert tuple(status.type.choices) == masters_module.MASTERS_STATUS_CHOICES
    assert masters_module.MASTERS_STATUS_CHOICES == (
        "not-archived",
        "active",
        "stopped",
        "archived",
        "all",
    )


@pytest.mark.parametrize("tool_name,path", NESTED_TOOL_PATHS.items())
def test_nested_click_integer_ids_are_safe_mcp_strings(
    masters_module: ModuleType,
    tool_name: str,
    path: tuple[str, ...],
) -> None:
    """Document the intentional ID-type divergence required by issue #256."""
    click_campaign_id = next(
        parameter
        for parameter in _click_command(path).params
        if parameter.name == "campaign_id"
    )
    mcp_campaign_id = inspect.signature(getattr(masters_module, tool_name)).parameters[
        "campaign_id"
    ]

    assert isinstance(click_campaign_id.type, click.types.IntParamType)
    assert mcp_campaign_id.annotation is str


def test_six_masters_tools_fit_token_budget() -> None:
    isolated_mcp = FastMCP("masters-token-test", json_response=True)
    module_name = "server.tools.masters"
    dynamic_tools_package = cast(Any, tools_package)
    previous_module = sys.modules.pop(module_name, None)
    had_parent_attr = hasattr(dynamic_tools_package, "masters")
    previous_parent_attr = dynamic_tools_package.masters if had_parent_attr else None
    with patch.object(main_module, "mcp", isolated_mcp):
        try:
            importlib.import_module(module_name)
            tools = asyncio.run(isolated_mcp.list_tools())
        finally:
            sys.modules.pop(module_name, None)
            if previous_module is not None:
                sys.modules[module_name] = previous_module
            if had_parent_attr:
                dynamic_tools_package.masters = previous_parent_attr
            else:
                del dynamic_tools_package.masters

    count, _ = _make_counter()
    total = 0
    for tool in tools:
        payload = json.dumps(
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema or {},
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        total += count(payload)

    assert {tool.name for tool in tools} == set(TOOL_NAMES)
    for tool in tools:
        if tool.name in NESTED_TOOL_PATHS:
            assert tool.inputSchema["properties"]["campaign_id"]["type"] == "string"
    assert total <= 500
