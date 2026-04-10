"""Tests for smart_ad_targets MCP tools."""

from unittest.mock import patch, MagicMock

import pytest

import server.tools
from server.tools.smart_ad_targets import (
    smart_ad_targets_list,
    smart_ad_targets_add,
    smart_ad_targets_update,
    smart_ad_targets_delete,
)


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


SAMPLE_TARGETS = [
    {
        "Id": 100,
        "CampaignId": 300,
        "AdGroupId": 200,
        "Status": "ACCEPTED",
        "ServingStatus": "ELIGIBLE",
    },
]


def _mock_runner(return_value):
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def test_smart_ad_targets_list():
    with patch(
        "server.tools.smart_ad_targets.get_runner",
        return_value=_mock_runner(SAMPLE_TARGETS),
    ):
        result = smart_ad_targets_list(ad_group_ids="200")
        assert len(result) == 1


def test_smart_ad_targets_list_empty():
    with patch(
        "server.tools.smart_ad_targets.get_runner", return_value=_mock_runner([])
    ):
        result = smart_ad_targets_list(ad_group_ids="200")
        assert result == []


def test_smart_ad_targets_add():
    mock_result = {"Id": 400}
    with patch(
        "server.tools.smart_ad_targets.get_runner",
        return_value=_mock_runner(mock_result),
    ) as mock:
        result = smart_ad_targets_add(
            ad_group_id="200",
            target_type="RETARGETING",
            extra_json='{"Condition":"URL_CONTAINS"}',
        )
        assert result["Id"] == 400
        mock.return_value.run_json.assert_called_once_with(
            [
                "smartadtargets",
                "add",
                "--adgroup-id",
                "200",
                "--type",
                "RETARGETING",
                "--json",
                '{"Condition":"URL_CONTAINS"}',
            ]
        )


def test_smart_ad_targets_update():
    mock_result = {"success": True}
    with patch(
        "server.tools.smart_ad_targets.get_runner",
        return_value=_mock_runner(mock_result),
    ) as mock:
        result = smart_ad_targets_update(
            id="100",
            target_type="RETARGETING",
            extra_json='{"Condition":"URL_CONTAINS"}',
        )
        assert result["success"] is True
        mock.return_value.run_json.assert_called_once_with(
            [
                "smartadtargets",
                "update",
                "--id",
                "100",
                "--type",
                "RETARGETING",
                "--json",
                '{"Condition":"URL_CONTAINS"}',
            ]
        )


def test_smart_ad_targets_update_requires_changes():
    runner = _mock_runner({"success": True})
    with patch("server.tools.smart_ad_targets.get_runner", return_value=runner):
        result = smart_ad_targets_update(id="100")
        assert result["error"] == "missing_update_fields"
        runner.run_json.assert_not_called()


def test_smart_ad_targets_delete():
    mock_result = {"success": True}
    with patch(
        "server.tools.smart_ad_targets.get_runner",
        return_value=_mock_runner(mock_result),
    ) as mock:
        result = smart_ad_targets_delete(id="100")
        assert result["success"] is True
        mock.return_value.run_json.assert_called_once_with(
            ["smartadtargets", "delete", "--id", "100"]
        )
