"""Tests for v4 Live MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.contract import (
    PUBLIC_TOOL_NAMES,
    V4_LIVE_BLOCKED_METHOD_NAMES,
    V4_LIVE_TOOL_NAMES,
)
from server.tools.balance import balance_get
from server.tools.v4goals import (
    v4goals_get_retargeting_goals,
    v4goals_get_stat_goals,
)


@pytest.fixture(autouse=True)
def setup_token_getter():
    server.tools.set_token_getter(lambda: "test-token")


def _mock_runner(return_value):
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def test_balance_get_without_logins():
    runner = _mock_runner({"Accounts": []})
    with patch("server.tools.balance.get_runner", return_value=runner):
        result = balance_get()

    assert result == {"Accounts": []}
    runner.run_json.assert_called_once_with(["balance", "--format", "json"])


def test_balance_get_with_logins():
    runner = _mock_runner({"Accounts": []})
    with patch("server.tools.balance.get_runner", return_value=runner):
        result = balance_get(logins=" client-a,client-b ")

    assert result == {"Accounts": []}
    runner.run_json.assert_called_once_with(
        ["balance", "--format", "json", "--logins", "client-a,client-b"]
    )


def test_v4goals_get_stat_goals():
    runner = _mock_runner({"Goals": []})
    with patch("server.tools.v4goals.get_runner", return_value=runner):
        result = v4goals_get_stat_goals(campaign_ids=" 123,456 ")

    assert result == {"Goals": []}
    runner.run_json.assert_called_once_with(
        [
            "v4goals",
            "get-stat-goals",
            "--campaign-ids",
            "123,456",
            "--format",
            "json",
        ]
    )


def test_v4goals_get_retargeting_goals():
    runner = _mock_runner({"RetargetingGoals": []})
    with patch("server.tools.v4goals.get_runner", return_value=runner):
        result = v4goals_get_retargeting_goals(campaign_ids="123,456")

    assert result == {"RetargetingGoals": []}
    runner.run_json.assert_called_once_with(
        [
            "v4goals",
            "get-retargeting-goals",
            "--campaign-ids",
            "123,456",
            "--format",
            "json",
        ]
    )


def test_v4goals_requires_campaign_ids():
    result = v4goals_get_stat_goals(campaign_ids="   ")
    assert result["error"] == "missing_campaign_ids"


def test_v4_contract_exposes_only_cli_backed_tools():
    assert V4_LIVE_TOOL_NAMES == {
        "balance_get",
        "v4goals_get_stat_goals",
        "v4goals_get_retargeting_goals",
    }
    assert V4_LIVE_TOOL_NAMES <= PUBLIC_TOOL_NAMES
    assert {"GetClientsUnits", "PingAPI", "CreateNewForecast"} <= (
        V4_LIVE_BLOCKED_METHOD_NAMES
    )
    assert "v4finance_get_clients_units" not in PUBLIC_TOOL_NAMES
    assert "v4meta_ping_api" not in PUBLIC_TOOL_NAMES
