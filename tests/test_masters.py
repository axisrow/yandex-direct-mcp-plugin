"""Tests for the read-only browser-backed Masters tools (#277)."""

from unittest.mock import patch

from server.tools.masters import (
    MASTERS_READ_TIMEOUT_SECONDS,
    masters_get,
    masters_targetactions_get,
)
from tests.helpers import mock_runner

SAMPLE_MASTER = {"CampaignId": 123, "Name": "Master", "Status": "ACTIVE"}
SAMPLE_TARGET_ACTIONS = {
    "CampaignId": 123,
    "Count": 1,
    "TargetActions": [{"GoalId": 42, "Price": "1000"}],
}


def test_masters_get_builds_read_only_cli_argv_and_trims_ids():
    runner = mock_runner(SAMPLE_MASTER)
    with patch("server.tools.masters.get_runner", return_value=runner):
        result = masters_get(" 123,456 ")

    assert result == SAMPLE_MASTER
    runner.run_json.assert_called_once_with(
        ["masters", "get", "123,456", "--format", "json"],
        timeout=MASTERS_READ_TIMEOUT_SECONDS,
    )


def test_masters_get_passes_moderation_statuses_flag():
    runner = mock_runner({**SAMPLE_MASTER, "RejectedCount": 0})
    with patch("server.tools.masters.get_runner", return_value=runner):
        masters_get("123", moderation_statuses=True)

    runner.run_json.assert_called_once_with(
        [
            "masters",
            "get",
            "123",
            "--moderation-statuses",
            "--format",
            "json",
        ],
        timeout=MASTERS_READ_TIMEOUT_SECONDS,
    )


def test_masters_get_rejects_blank_campaign_ids_without_running_cli():
    runner = mock_runner()
    with patch("server.tools.masters.get_runner", return_value=runner):
        result = masters_get("   ")

    assert result["error"] == "missing_campaign_ids"
    runner.run_json.assert_not_called()


def test_masters_targetactions_get_builds_nested_read_only_cli_argv():
    runner = mock_runner(SAMPLE_TARGET_ACTIONS)
    with patch("server.tools.masters.get_runner", return_value=runner):
        result = masters_targetactions_get(123)

    assert result == SAMPLE_TARGET_ACTIONS
    runner.run_json.assert_called_once_with(
        ["masters", "targetactions", "get", "123", "--format", "json"],
        timeout=MASTERS_READ_TIMEOUT_SECONDS,
    )
