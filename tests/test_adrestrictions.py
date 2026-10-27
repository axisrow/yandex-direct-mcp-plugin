"""Contract and argv tests for the browser-backed ``adrestrictions_get`` tool."""

import inspect
from collections.abc import Iterator
from types import ModuleType
from typing import Any, cast
from unittest.mock import MagicMock

import click
import pytest
from direct_cli.cli import cli  # type: ignore[import-not-found, import-untyped]

from server.cli.runner import CliBrowserAuthError
from server.contract import PUBLIC_CONTRACT
from tests.helpers import import_tool_module_without_registration

SAMPLE_RESTRICTIONS = {
    "campaign_id": 77593206,
    "ads": [
        {
            "ad_id": 1,
            "headlines": ["Пример заголовка"],
            "warnings": [
                {
                    "kind": "moderation",
                    "text": "Добавлено предупреждение: Медицина и фармацевтика",
                }
            ],
        }
    ],
}
IGNORED_CLI_PARAMS = {
    "headful",
    "profile_dir",
    "chrome_profile",
    "output_format",
    "output",
}


@pytest.fixture()
def adrestrictions_module() -> Iterator[ModuleType]:
    with import_tool_module_without_registration(
        "server.tools.adrestrictions"
    ) as module:
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


def _click_command() -> click.Command:
    command: click.Command = cli
    for component in ("adrestrictions",):
        assert isinstance(command, click.Group)
        child = command.get_command(click.Context(command), component)
        assert child is not None
        command = child
    return command


def test_adrestrictions_get_forwards_positional_id_and_group_ids(
    adrestrictions_module: ModuleType,
) -> None:
    runner = _runner_for(adrestrictions_module, SAMPLE_RESTRICTIONS)

    result = adrestrictions_module.adrestrictions_get("77593206", group_ids=" 12,34 ")

    assert result == SAMPLE_RESTRICTIONS
    runner.run_json_lenient.assert_called_once_with(
        ["adrestrictions", "77593206", "--group-ids", "12,34", "--format", "json"]
    )
    runner.run_json.assert_not_called()


def test_adrestrictions_get_omits_unset_and_blank_group_ids(
    adrestrictions_module: ModuleType,
) -> None:
    unset_runner = _runner_for(adrestrictions_module, SAMPLE_RESTRICTIONS)
    adrestrictions_module.adrestrictions_get("77593206")

    blank_runner = _runner_for(adrestrictions_module, SAMPLE_RESTRICTIONS)
    adrestrictions_module.adrestrictions_get("77593206", group_ids="   ")

    assert "--group-ids" not in unset_runner.run_json_lenient.call_args.args[0]
    blank_runner.run_json_lenient.assert_called_once_with(
        ["adrestrictions", "77593206", "--format", "json"]
    )


def test_adrestrictions_get_forwards_browser_session_environment(
    adrestrictions_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _runner_for(adrestrictions_module, SAMPLE_RESTRICTIONS)
    monkeypatch.setenv("YANDEX_DIRECT_BROWSER_PROFILE_DIR", "/tmp/direct-profile")
    monkeypatch.setenv("YANDEX_DIRECT_BROWSER_CHROME_PROFILE", "Profile 3")
    monkeypatch.setenv("YANDEX_DIRECT_BROWSER_HEADFUL", "1")

    adrestrictions_module.adrestrictions_get("77593206")

    runner.run_json_lenient.assert_called_once_with(
        [
            "adrestrictions",
            "77593206",
            "--profile-dir",
            "/tmp/direct-profile",
            "--chrome-profile",
            "Profile 3",
            "--headful",
            "--format",
            "json",
        ]
    )


def test_adrestrictions_get_maps_browser_auth_failures(
    adrestrictions_module: ModuleType,
) -> None:
    runner = _runner_for(adrestrictions_module, SAMPLE_RESTRICTIONS)
    runner.run_json_lenient.side_effect = CliBrowserAuthError("browser login required")

    result = adrestrictions_module.adrestrictions_get("77593206")

    assert result["error"] == "browser_auth_required"
    assert "direct playwright login" in result["hint"]


def test_adrestrictions_get_uses_contract_leaf_path(
    adrestrictions_module: ModuleType,
) -> None:
    contract = {tool.public_name: tool for tool in PUBLIC_CONTRACT}
    tool = contract["adrestrictions_get"]

    assert tool.cli_subcommand == "get"
    assert tool.cli_subcommand_path == ("adrestrictions",)
    assert tool.optional_bundle == "browser"


def test_adrestrictions_signature_matches_installed_click_command(
    adrestrictions_module: ModuleType,
) -> None:
    click_params = {
        parameter.name
        for parameter in _click_command().params
        if parameter.name not in IGNORED_CLI_PARAMS
    }
    mcp_params = set(
        inspect.signature(adrestrictions_module.adrestrictions_get).parameters
    )

    assert mcp_params == click_params
    positional = inspect.signature(adrestrictions_module.adrestrictions_get).parameters
    assert positional["campaign_id"].default is inspect.Parameter.empty
    assert positional["campaign_id"].annotation is str
    assert positional["group_ids"].default is None
