"""Tests for ads MCP tool."""

from unittest.mock import patch, MagicMock

import pytest

import server.tools
from server.tools.ads import ads_list, ads_add, ads_update, ads_delete, ads_moderate, ads_suspend, ads_resume


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
        with patch("server.tools.ads.get_runner", return_value=_mock_runner(mock_result)):
            result = ads_add(campaign_id="12345", ad_group_id="1", text="New ad text")
            assert result["Id"] == 999

    def test_ads_update(self):
        """Test updating an ad."""
        mock_result = {"Id": 111, "Text": "Updated ad text"}
        with patch("server.tools.ads.get_runner", return_value=_mock_runner(mock_result)):
            result = ads_update(id="111", text="Updated ad text")
            assert result["Id"] == 111

    def test_ads_update_argv_composition(self):
        """Test that update passes correct argv to CLI."""
        runner = _mock_runner({"Id": 111})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_update(id="111", text="New text")
            runner.run_json.assert_called_once_with(
                ["ads", "update", "--id", "111", "--text", "New text", "--format", "json"]
            )

    def test_ads_delete_success(self):
        """Test deleting ads successfully."""
        mock_result = {"success": True}
        with patch("server.tools.ads.get_runner", return_value=_mock_runner(mock_result)):
            result = ads_delete(ids="111,222")
            assert result["success"] is True

    def test_ads_delete_batch_limit(self):
        """Test batch limit validation for delete."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = ads_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_ads_moderate_success(self):
        """Test submitting ads for moderation."""
        mock_result = {"success": True}
        with patch("server.tools.ads.get_runner", return_value=_mock_runner(mock_result)):
            result = ads_moderate(ids="111,222")
            assert result["success"] is True

    def test_ads_moderate_batch_limit(self):
        """Test batch limit validation for moderate."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = ads_moderate(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_ads_suspend_success(self):
        """Test suspending ads."""
        mock_result = {"success": True}
        with patch("server.tools.ads.get_runner", return_value=_mock_runner(mock_result)):
            result = ads_suspend(ids="111,222")
            assert result["success"] is True

    def test_ads_suspend_batch_limit(self):
        """Test batch limit validation for suspend."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = ads_suspend(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_ads_resume_success(self):
        """Test resuming suspended ads."""
        mock_result = {"success": True}
        with patch("server.tools.ads.get_runner", return_value=_mock_runner(mock_result)):
            result = ads_resume(ids="111,222")
            assert result["success"] is True

    def test_ads_resume_batch_limit(self):
        """Test batch limit validation for resume."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = ads_resume(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
