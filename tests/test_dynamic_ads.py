"""Tests for dynamic_ads MCP tools."""

from unittest.mock import patch, MagicMock

from server.tools.dynamic_ads import (
    dynamic_ads_list,
    dynamic_ads_add,
    dynamic_ads_delete,
    dynamic_ads_resume,
    dynamic_ads_set_bids,
    dynamic_ads_suspend,
)

from tests.helpers import mock_runner

SAMPLE_TARGETS = [
    {
        "Id": 100,
        "AdGroupId": 200,
        "Conditions": [
            {"Operand": "URL", "Operator": "CONTAINS", "Arguments": ["sale"]}
        ],
    },
]


def test_dynamic_ads_list():
    with patch(
        "server.tools.dynamic_ads.get_runner", return_value=mock_runner(SAMPLE_TARGETS)
    ):
        result = dynamic_ads_list(ad_group_ids="200")
        assert len(result) == 1


def test_dynamic_ads_list_trims_ids():
    runner = mock_runner(SAMPLE_TARGETS)
    with patch("server.tools.dynamic_ads.get_runner", return_value=runner):
        dynamic_ads_list(ad_group_ids=" 200 ")

    runner.run_json.assert_called_once_with(
        ["dynamicads", "get", "--format", "json", "--adgroup-ids", "200"]
    )


def test_dynamic_ads_list_no_filters():
    """Blank ad_group_ids behaves like no filter (CLI returns everything)."""
    runner = mock_runner(SAMPLE_TARGETS)
    with patch("server.tools.dynamic_ads.get_runner", return_value=runner):
        dynamic_ads_list(ad_group_ids="   ")
    argv = runner.run_json.call_args[0][0]
    assert "--adgroup-ids" not in argv


def test_dynamic_ads_list_empty():
    with patch("server.tools.dynamic_ads.get_runner", return_value=mock_runner([])):
        result = dynamic_ads_list(ad_group_ids="200")
        assert result == []


def test_dynamic_ads_add():
    mock_result = {"Id": 300}
    runner = mock_runner(mock_result)
    with patch("server.tools.dynamic_ads.get_runner", return_value=runner):
        result = dynamic_ads_add(
            ad_group_id=200,
            name="Sale page",
            condition="URL:CONTAINS:sale",
            bid=1500000,
            context_bid=1000000,
            priority="HIGH",
        )
        assert result["Id"] == 300
        runner.run_json.assert_called_once_with(
            [
                "dynamicads",
                "add",
                "--adgroup-id",
                "200",
                "--name",
                "Sale page",
                "--condition",
                "URL:CONTAINS:sale",
                "--bid",
                "1500000",
                "--context-bid",
                "1000000",
                "--priority",
                "HIGH",
            ]
        )


def test_dynamic_ads_add_dry_run():
    runner = mock_runner({"_dry_run": True})
    with patch("server.tools.dynamic_ads.get_runner", return_value=runner):
        dynamic_ads_add(ad_group_id=200, name="x", dry_run=True)
        assert "--dry-run" in runner.run_json.call_args[0][0]


def test_dynamic_ads_delete():
    runner = mock_runner({"success": True})
    with patch("server.tools.dynamic_ads.get_runner", return_value=runner):
        result = dynamic_ads_delete(id=100)
        assert result["success"] is True
        runner.run_json.assert_called_once_with(["dynamicads", "delete", "--id", "100"])


def test_dynamic_ads_suspend_batches_ids():
    runner = mock_runner({"success": True})
    with patch("server.tools.dynamic_ads.get_runner", return_value=runner):
        result = dynamic_ads_suspend(ids="100,101")

    assert result["success"] is True
    assert result["ids"] == ["100", "101"]


def test_dynamic_ads_resume_batches_ids():
    runner = mock_runner({"success": True})
    with patch("server.tools.dynamic_ads.get_runner", return_value=runner):
        result = dynamic_ads_resume(ids="100,101")

    assert result["success"] is True
    assert result["ids"] == ["100", "101"]


def test_dynamic_ads_set_bids():
    runner = mock_runner({"success": True})
    with patch("server.tools.dynamic_ads.get_runner", return_value=runner):
        result = dynamic_ads_set_bids(
            id=100,
            bid=1500000,
            context_bid=1200000,
            priority="HIGH",
        )

    assert result["success"] is True
    runner.run_json.assert_called_once_with(
        [
            "dynamicads",
            "set-bids",
            "--id",
            "100",
            "--bid",
            "1500000",
            "--context-bid",
            "1200000",
            "--priority",
            "HIGH",
        ]
    )


class TestDynamicAdsAuthErrors:
    """Auth error scenarios for dynamic ads."""

    def test_dynamic_ads_list_auth_error(self):
        """Test auth error during list."""
        from server.cli.runner import CliAuthError

        runner = MagicMock()
        runner.run_json.side_effect = CliAuthError("Token expired")
        with patch("server.tools.dynamic_ads.get_runner", return_value=runner):
            result = dynamic_ads_list(ad_group_ids="200")
            assert result["error"] == "auth_expired"

    def test_dynamic_ads_add_auth_error(self):
        """Test auth error during add."""
        from server.cli.runner import CliAuthError

        runner = MagicMock()
        runner.run_json.side_effect = CliAuthError("Token expired")
        with patch("server.tools.dynamic_ads.get_runner", return_value=runner):
            result = dynamic_ads_add(ad_group_id=200, name="x")
            assert result["error"] == "auth_expired"

    def test_dynamic_ads_delete_auth_error(self):
        """Test auth error during delete."""
        from server.cli.runner import CliAuthError

        runner = MagicMock()
        runner.run_json.side_effect = CliAuthError("Token expired")
        with patch("server.tools.dynamic_ads.get_runner", return_value=runner):
            result = dynamic_ads_delete(id=100)
            assert result["error"] == "auth_expired"
