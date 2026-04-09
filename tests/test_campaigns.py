"""Tests for campaign MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.campaigns import (
    campaigns_list,
    campaigns_update,
    campaigns_add,
    campaigns_delete,
    campaigns_archive,
    campaigns_unarchive,
    campaigns_suspend,
    campaigns_resume,
)
from server.cli.runner import CliAuthError


@pytest.fixture(autouse=True)
def setup_token_getter():
    """Configure a mock token getter for all tests."""
    server.tools.set_token_getter(lambda: "test-token")


@pytest.fixture
def mock_campaigns():
    """Sample campaign data."""
    return [
        {"Id": 12345, "Name": "Campaign_1", "State": "ON", "DailyBudget": 5000},
        {"Id": 67890, "Name": "Campaign_2", "State": "OFF", "DailyBudget": 3000},
        {"Id": 11111, "Name": "Campaign_3", "State": "ON", "DailyBudget": 7000},
    ]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestCampaignsList:
    """Test scenarios 7-8."""

    def test_list_all_campaigns(self, mock_campaigns):
        """Test 7: List all campaigns."""
        with patch(
            "server.tools.campaigns.get_runner",
            return_value=_mock_runner(mock_campaigns),
        ):
            result = campaigns_list()
            assert len(result) == 3

    def test_list_active_campaigns(self, mock_campaigns):
        """Test 8: Filter by state=ON."""
        with patch(
            "server.tools.campaigns.get_runner",
            return_value=_mock_runner(mock_campaigns),
        ):
            result = campaigns_list(state="ON")
            assert len(result) == 2
            assert all(c["State"] == "ON" for c in result)

    def test_list_empty_result(self):
        """Empty response returns empty list."""
        with patch("server.tools.campaigns.get_runner", return_value=_mock_runner([])):
            result = campaigns_list()
            assert result == []


class TestCampaignsUpdate:
    """Test scenarios 9-10."""

    def test_enable_campaign(self):
        """Test 9: Enable a campaign."""
        with patch(
            "server.tools.campaigns.get_runner",
            return_value=_mock_runner({"Id": 67890, "State": "ON"}),
        ):
            result = campaigns_update(id="67890", state="ON")
            assert result["success"] is True
            assert result["state"] == "ON"

    def test_disable_campaign(self):
        """Test 9: Disable a campaign."""
        with patch(
            "server.tools.campaigns.get_runner",
            return_value=_mock_runner({"Id": 12345, "State": "OFF"}),
        ):
            result = campaigns_update(id="12345", state="OFF")
            assert result["success"] is True

    def test_invalid_state(self):
        """Test: Invalid state value."""
        result = campaigns_update(id="12345", state="INVALID")
        assert "error" in result
        assert result["error"] == "invalid_state"

    def test_not_found_campaign(self):
        """Test 10: Nonexistent campaign."""
        runner = MagicMock()
        runner.run_json.side_effect = Exception("Campaign 999 not found")
        with patch("server.tools.campaigns.get_runner", return_value=runner):
            result = campaigns_update(id="999", state="ON")
            assert "error" in result
            assert result["error"] == "not_found"

    def test_auth_error(self):
        """Test: Auth expired during update."""
        runner = MagicMock()
        runner.run_json.side_effect = CliAuthError("Token expired")
        with (
            patch("server.tools.campaigns.get_runner", return_value=runner),
            patch("server.tools._try_refresh_token", return_value=None),
        ):
            result = campaigns_update(id="12345", state="ON")
            assert result["error"] == "auth_expired"

    def test_auth_error_refresh_retries(self):
        """Test: Auth error triggers refresh, then retry succeeds."""
        expired_runner = MagicMock()
        expired_runner.run_json.side_effect = CliAuthError("Token expired")
        fresh_runner = MagicMock()
        fresh_runner.run_json.return_value = {"Id": 12345, "State": "ON"}
        with (
            patch(
                "server.tools.campaigns.get_runner",
                side_effect=[expired_runner, fresh_runner],
            ),
            patch("server.tools._try_refresh_token", return_value="new-token"),
        ):
            result = campaigns_update(id="12345", state="ON")
            assert result["success"] is True


class TestCampaignsCrudOperations:
    """Tests for campaign CRUD operations (add, delete, archive, unarchive)."""

    def test_campaigns_add(self):
        """Test adding a new campaign."""
        mock_result = {"Id": 99999, "Name": "New Campaign"}
        with patch(
            "server.tools.campaigns.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = campaigns_add(name="New Campaign", start_date="2026-01-01")
            assert result["Id"] == 99999

    def test_campaigns_delete_success(self):
        """Test deleting campaigns successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.campaigns.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = campaigns_delete(ids="12345,67890")
            assert result["success"] is True

    def test_campaigns_delete_batch_limit(self):
        """Test batch limit validation for delete."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = campaigns_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_campaigns_archive_success(self):
        """Test archiving campaigns successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.campaigns.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = campaigns_archive(ids="12345,67890")
            assert result["success"] is True

    def test_campaigns_archive_batch_limit(self):
        """Test batch limit validation for archive."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = campaigns_archive(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_campaigns_unarchive_success(self):
        """Test unarchiving campaigns successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.campaigns.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = campaigns_unarchive(ids="12345,67890")
            assert result["success"] is True

    def test_campaigns_unarchive_batch_limit(self):
        """Test batch limit validation for unarchive."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = campaigns_unarchive(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_campaigns_suspend_success(self):
        """Test suspending campaigns successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.campaigns.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = campaigns_suspend(ids="12345")
            assert result["success"] is True

    def test_campaigns_suspend_batch_limit(self):
        """Test batch limit validation for suspend."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = campaigns_suspend(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_campaigns_resume_success(self):
        """Test resuming campaigns successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.campaigns.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = campaigns_resume(ids="12345")
            assert result["success"] is True

    def test_campaigns_resume_batch_limit(self):
        """Test batch limit validation for resume."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = campaigns_resume(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
