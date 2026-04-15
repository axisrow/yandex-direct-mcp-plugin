"""Tests for ads MCP tool."""

from unittest.mock import MagicMock, call, patch

import pytest

import server.tools
from server.tools.ads import (
    ads_list,
    ads_add,
    ads_update,
    ads_delete,
    ads_moderate,
    ads_suspend,
    ads_resume,
    ads_archive,
    ads_unarchive,
)


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


SAMPLE_ADS = [
    {
        "Id": 111,
        "Title": "Ad title placeholder",
        "Title2": "Ad title2 placeholder",
        "State": "ON",
    },
    {"Id": 222, "Title": "Ad title placeholder 2", "State": "OFF"},
]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def test_ads_list_success():
    """Test 11: List ads in a campaign."""
    with patch("server.tools.ads.get_runner", return_value=_mock_runner(SAMPLE_ADS)):
        result = ads_list(campaign_ids="12345")
        assert len(result) == 2


def test_ads_list_ignores_blank_filters():
    """Test blank filters behave like no filter."""
    runner = MagicMock()
    runner.run_json.return_value = SAMPLE_ADS
    with patch("server.tools.ads.get_runner", return_value=runner):
        result = ads_list(campaign_ids="   ", ad_group_ids="   ", ids="   ")
        assert len(result) == 2
        call_args = runner.run_json.call_args[0][0]
        assert "--campaign-ids" not in call_args
        assert "--adgroup-ids" not in call_args
        assert "--ids" not in call_args


def test_ads_foreign_campaign():
    """Test 12: Campaign belongs to second account (73-77M range)."""
    result = ads_list(campaign_ids="75000001")
    assert "error" in result
    assert result["error"] == "foreign_campaign"


def test_ads_batch_limit():
    """Test 13: Too many IDs."""
    ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
    result = ads_list(campaign_ids=ids)
    assert "error" in result
    assert result["error"] == "batch_limit"


def test_ads_empty():
    """Empty result."""
    with patch("server.tools.ads.get_runner", return_value=_mock_runner([])):
        result = ads_list(campaign_ids="12345")
        assert result == []


class TestAdsCrudOperations:
    """Tests for ad CRUD operations (add, update, delete, moderate, suspend, resume)."""

    def test_ads_add(self):
        """Test adding a new ad."""
        mock_result = {"Id": 999, "Text": "New ad text"}
        runner = _mock_runner(mock_result)
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_add(
                ad_group_id="1",
                ad_type="TEXT_AD",
                title="Title",
                text="New ad text",
                href="https://example.com",
            )
            assert result["Id"] == 999
            runner.run_json.assert_called_once_with(
                [
                    "ads",
                    "add",
                    "--adgroup-id",
                    "1",
                    "--type",
                    "TEXT_AD",
                    "--title",
                    "Title",
                    "--text",
                    "New ad text",
                    "--href",
                    "https://example.com",
                ]
            )

    def test_ads_update(self):
        """Test updating an ad."""
        mock_result = {"Id": 111, "Status": "SUSPENDED"}
        with patch(
            "server.tools.ads.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = ads_update(id="111", status="SUSPENDED")
            assert result["Id"] == 111

    def test_ads_update_argv_composition(self):
        """Test that update passes correct argv to CLI."""
        runner = _mock_runner({"Id": 111})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_update(
                id="111",
                status="SUSPENDED",
            )
            runner.run_json.assert_called_once_with(
                [
                    "ads",
                    "update",
                    "--id",
                    "111",
                    "--status",
                    "SUSPENDED",
                ]
            )

    def test_ads_update_requires_changes(self):
        """Test that empty updates are rejected before CLI call."""
        runner = _mock_runner({"Id": 111})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_update(id="111")
            assert result["error"] == "missing_update_fields"
            runner.run_json.assert_not_called()

    def test_ads_delete_success(self):
        """Test deleting ads successfully."""
        runner = _mock_runner({"success": True})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_delete(ids="111,222")
            assert result["success"] is True
            runner.run_json.assert_has_calls(
                [
                    call(["ads", "delete", "--id", "111"]),
                    call(["ads", "delete", "--id", "222"]),
                ]
            )

    def test_ads_delete_batch_limit(self):
        """Test batch limit validation for delete."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = ads_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_ads_moderate_success(self):
        """Test submitting ads for moderation."""
        runner = _mock_runner({"success": True})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_moderate(ids="111,222")
            assert result["success"] is True
            runner.run_json.assert_has_calls(
                [
                    call(["ads", "moderate", "--id", "111"]),
                    call(["ads", "moderate", "--id", "222"]),
                ]
            )

    def test_ads_moderate_batch_limit(self):
        """Test batch limit validation for moderate."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = ads_moderate(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_ads_suspend_success(self):
        """Test suspending ads."""
        runner = _mock_runner({"success": True})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_suspend(ids="111,222")
            assert result["success"] is True
            runner.run_json.assert_has_calls(
                [
                    call(["ads", "suspend", "--id", "111"]),
                    call(["ads", "suspend", "--id", "222"]),
                ]
            )

    def test_ads_suspend_batch_limit(self):
        """Test batch limit validation for suspend."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = ads_suspend(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_ads_resume_success(self):
        """Test resuming suspended ads."""
        runner = _mock_runner({"success": True})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_resume(ids="111,222")
            assert result["success"] is True
            runner.run_json.assert_has_calls(
                [
                    call(["ads", "resume", "--id", "111"]),
                    call(["ads", "resume", "--id", "222"]),
                ]
            )

    def test_ads_resume_batch_limit(self):
        """Test batch limit validation for resume."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = ads_resume(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_ads_archive_success(self):
        """Test archiving ads."""
        runner = _mock_runner({"success": True})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_archive(ids="111,222")
            assert result["success"] is True
            runner.run_json.assert_has_calls(
                [
                    call(["ads", "archive", "--id", "111"]),
                    call(["ads", "archive", "--id", "222"]),
                ]
            )

    def test_ads_archive_batch_limit(self):
        """Test batch limit validation for archive."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = ads_archive(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_ads_unarchive_success(self):
        """Test unarchiving ads."""
        runner = _mock_runner({"success": True})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_unarchive(ids="111,222")
            assert result["success"] is True
            runner.run_json.assert_has_calls(
                [
                    call(["ads", "unarchive", "--id", "111"]),
                    call(["ads", "unarchive", "--id", "222"]),
                ]
            )

    def test_ads_unarchive_batch_limit(self):
        """Test batch limit validation for unarchive."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = ads_unarchive(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
