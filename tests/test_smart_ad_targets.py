"""Tests for smart_ad_targets MCP tools."""

from unittest.mock import patch

from server.tools.smart_ad_targets import (
    smart_ad_targets_list,
    smart_ad_targets_add,
    smart_ad_targets_update,
    smart_ad_targets_delete,
    smart_ad_targets_resume,
    smart_ad_targets_set_bids,
    smart_ad_targets_suspend,
)

from tests.helpers import mock_runner

SAMPLE_TARGETS = [
    {
        "Id": 100,
        "CampaignId": 300,
        "AdGroupId": 200,
        "Status": "ACCEPTED",
        "ServingStatus": "ELIGIBLE",
    },
]


def test_smart_ad_targets_list():
    with patch(
        "server.tools.smart_ad_targets.get_runner",
        return_value=mock_runner(SAMPLE_TARGETS),
    ):
        result = smart_ad_targets_list(ad_group_ids="200")
        assert len(result) == 1


def test_smart_ad_targets_list_trims_ids():
    runner = mock_runner(SAMPLE_TARGETS)
    with patch("server.tools.smart_ad_targets.get_runner", return_value=runner):
        smart_ad_targets_list(ad_group_ids=" 200 ")

    runner.run_json.assert_called_once_with(
        ["smartadtargets", "get", "--format", "json", "--adgroup-ids", "200"]
    )


def test_smart_ad_targets_list_no_filters():
    """Blank ad_group_ids behaves like no filter."""
    runner = mock_runner(SAMPLE_TARGETS)
    with patch("server.tools.smart_ad_targets.get_runner", return_value=runner):
        smart_ad_targets_list(ad_group_ids="   ")
    argv = runner.run_json.call_args[0][0]
    assert "--adgroup-ids" not in argv


def test_smart_ad_targets_list_empty():
    with patch(
        "server.tools.smart_ad_targets.get_runner", return_value=mock_runner([])
    ):
        result = smart_ad_targets_list(ad_group_ids="200")
        assert result == []


def test_smart_ad_targets_add():
    mock_result = {"Id": 400}
    runner = mock_runner(mock_result)
    with patch("server.tools.smart_ad_targets.get_runner", return_value=runner):
        result = smart_ad_targets_add(
            ad_group_id=200,
            name="Sale target",
            audience="VISITORS",
            condition="URL:CONTAINS:sale",
            average_cpc=2500000,
            priority="MEDIUM",
            available_items_only="YES",
        )
        assert result["Id"] == 400
        runner.run_json.assert_called_once_with(
            [
                "smartadtargets",
                "add",
                "--adgroup-id",
                "200",
                "--name",
                "Sale target",
                "--audience",
                "VISITORS",
                "--condition",
                "URL:CONTAINS:sale",
                "--average-cpc",
                "2500000",
                "--priority",
                "MEDIUM",
                "--available-items-only",
                "YES",
            ]
        )


def test_smart_ad_targets_update():
    mock_result = {"success": True}
    runner = mock_runner(mock_result)
    with patch("server.tools.smart_ad_targets.get_runner", return_value=runner):
        result = smart_ad_targets_update(
            id=100,
            name="New name",
            audience="VISITORS",
        )
        assert result["success"] is True
        runner.run_json.assert_called_once_with(
            [
                "smartadtargets",
                "update",
                "--id",
                "100",
                "--name",
                "New name",
                "--audience",
                "VISITORS",
            ]
        )


def test_smart_ad_targets_update_requires_changes():
    runner = mock_runner({"success": True})
    with patch("server.tools.smart_ad_targets.get_runner", return_value=runner):
        result = smart_ad_targets_update(id=100)
        assert result["error"] == "missing_update_fields"
        runner.run_json.assert_not_called()


def test_smart_ad_targets_update_accepts_zero_bid():
    """average_cpc=0 is a valid provided field; the missing-fields guard must
    not treat falsy 0 as "no update", and the CLI accepts a 0 bid (#170-22)."""
    runner = mock_runner({"success": True})
    with patch("server.tools.smart_ad_targets.get_runner", return_value=runner):
        result = smart_ad_targets_update(id=100, average_cpc=0)
    assert "error" not in result
    argv = runner.run_json.call_args[0][0]
    assert argv[argv.index("--average-cpc") + 1] == "0"


def test_smart_ad_targets_delete():
    mock_result = {"success": True}
    with patch(
        "server.tools.smart_ad_targets.get_runner",
        return_value=mock_runner(mock_result),
    ) as mock:
        result = smart_ad_targets_delete(id=100)
        assert result["success"] is True
        mock.return_value.run_json.assert_called_once_with(
            ["smartadtargets", "delete", "--id", "100"]
        )


def test_smart_ad_targets_suspend_batches_ids():
    runner = mock_runner({"success": True})
    with patch("server.tools.smart_ad_targets.get_runner", return_value=runner):
        result = smart_ad_targets_suspend(ids="100,101")

    assert result["success"] is True
    assert result["ids"] == ["100", "101"]


def test_smart_ad_targets_resume_batches_ids():
    runner = mock_runner({"success": True})
    with patch("server.tools.smart_ad_targets.get_runner", return_value=runner):
        result = smart_ad_targets_resume(ids="100,101")

    assert result["success"] is True
    assert result["ids"] == ["100", "101"]


def test_smart_ad_targets_set_bids():
    runner = mock_runner({"success": True})
    with patch("server.tools.smart_ad_targets.get_runner", return_value=runner):
        result = smart_ad_targets_set_bids(
            id=100,
            average_cpc=2500000,
            average_cpa=10000000,
            priority="MEDIUM",
        )

    assert result["success"] is True
    runner.run_json.assert_called_once_with(
        [
            "smartadtargets",
            "set-bids",
            "--id",
            "100",
            "--average-cpc",
            "2500000",
            "--average-cpa",
            "10000000",
            "--priority",
            "MEDIUM",
        ]
    )
