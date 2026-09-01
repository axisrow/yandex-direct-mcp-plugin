"""Tests for the opt-in Playwright diagnostics MCP helper."""

from __future__ import annotations

import inspect
from collections.abc import Iterator
from types import ModuleType
from typing import Any, cast
from unittest.mock import MagicMock

import click
import pytest
from direct_cli.cli import cli  # type: ignore[import-not-found, import-untyped]

from tests.helpers import import_tool_module_without_registration

_WRAPPER_PARAMS = {"profile_dir", "chrome_profile", "output_format", "output"}


@pytest.fixture()
def playwright_module() -> Iterator[ModuleType]:
    with import_tool_module_without_registration("server.tools.playwright") as module:
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


def _published_doctor_or_skip() -> click.Command:
    group = cli.commands.get("playwright")
    if not isinstance(group, click.Group):
        pytest.skip("playwright group is not in published direct-cli 0.5.2")
    command = group.get_command(click.Context(group), "doctor")
    if command is None:
        pytest.skip("playwright doctor is not in published direct-cli 0.5.2")
    return command


def test_playwright_doctor_has_no_mcp_parameters(
    playwright_module: ModuleType,
) -> None:
    assert inspect.signature(playwright_module.playwright_doctor).parameters == {}


def test_playwright_doctor_returns_structured_lenient_json(
    playwright_module: ModuleType,
) -> None:
    result_data = {
        "ok": False,
        "checks": [
            {
                "name": "saved_session",
                "ok": False,
                "detail": "No saved session",
                "hint": "Run direct playwright login",
            }
        ],
    }
    runner = _runner_for(playwright_module, result_data)

    assert playwright_module.playwright_doctor() == result_data

    runner.run_json_lenient.assert_called_once_with(
        ["playwright", "doctor", "--format", "json"]
    )
    cast(Any, playwright_module).get_browser_runner.assert_called_once_with()


def test_playwright_doctor_forwards_profile_env_but_never_headful(
    playwright_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _runner_for(playwright_module, {"ok": True, "checks": []})
    monkeypatch.setenv("YANDEX_DIRECT_BROWSER_PROFILE_DIR", " /tmp/profile ")
    monkeypatch.setenv("YANDEX_DIRECT_BROWSER_CHROME_PROFILE", " Profile 4 ")
    monkeypatch.setenv("YANDEX_DIRECT_BROWSER_HEADFUL", "1")

    playwright_module.playwright_doctor()

    runner.run_json_lenient.assert_called_once_with(
        [
            "playwright",
            "doctor",
            "--profile-dir",
            "/tmp/profile",
            "--chrome-profile",
            "Profile 4",
            "--format",
            "json",
        ]
    )


def test_playwright_doctor_published_cli_params_are_wrapper_only(
    playwright_module: ModuleType,
) -> None:
    command = _published_doctor_or_skip()
    click_params = {parameter.name for parameter in command.params}

    assert click_params == _WRAPPER_PARAMS
    assert inspect.signature(playwright_module.playwright_doctor).parameters == {}
