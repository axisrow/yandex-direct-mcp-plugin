"""Tests for audience MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.audience import (
    audience_targets_add,
    audience_targets_delete,
    audience_targets_list,
    audience_targets_resume,
    audience_targets_suspend,
)
from server.cli.runner import CliAuthError


@pytest.fixture(autouse=True)
def setup_token_getter():
    """Configure a mock token getter for all tests."""
    server.tools.set_token_getter(lambda: "test-token")


@pytest.fixture
def mock_audience_targets():
    """Sample audience target data."""
    return [
        {
            "Id": 101,
            "CampaignId": 12345,
            "AdGroupId": 67890,
            "AudienceId": 555,
            "State": "ON",
        },
        {
            "Id": 102,
            "CampaignId": 12345,
            "AdGroupId": 67891,
            "AudienceId": 556,
            "State": "ON",
        },
    ]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestAudienceTargetsList:
    """Tests for audience_targets_list."""

    def test_list_audience_targets_success(self, mock_audience_targets):
        """Test listing audience targets successfully."""
        with patch(
            "server.tools.audience.get_runner",
            return_value=_mock_runner(mock_audience_targets),
        ):
            result = audience_targets_list(campaign_ids="12345,67890")
            assert len(result) == 2

    def test_list_audience_targets_empty(self):
        """Test listing audience targets with empty result."""
        with patch("server.tools.audience.get_runner", return_value=_mock_runner([])):
            result = audience_targets_list(campaign_ids="12345")
            assert result == []

    def test_list_audience_targets_batch_limit(self):
        """Test batch limit validation for list."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = audience_targets_list(campaign_ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"


class TestAudienceTargetsAdd:
    """Tests for audience_targets_add."""

    def test_add_audience_target_success(self):
        """Test adding an audience target successfully."""
        mock_result = {
            "Id": 103,
            "CampaignId": 12345,
            "AdGroupId": 67892,
            "AudienceId": 557,
            "State": "ON",
        }
        with patch(
            "server.tools.audience.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = audience_targets_add(
                campaign_id="12345", ad_group_id="67892", audience_id="557"
            )
            assert result["Id"] == 103
            assert result["CampaignId"] == 12345

    def test_add_audience_target_auth_error(self):
        """Test auth error during audience target add."""
        runner = MagicMock()
        runner.run_json.side_effect = CliAuthError("Token expired")
        with (
            patch("server.tools.audience.get_runner", return_value=runner),
            patch("server.tools._try_refresh_token", return_value=None),
        ):
            result = audience_targets_add(
                campaign_id="12345", ad_group_id="67892", audience_id="557"
            )
            assert result["error"] == "auth_expired"


class TestAudienceTargetsDelete:
    """Tests for audience_targets_delete."""

    def test_delete_audience_targets_success(self):
        """Test deleting audience targets successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.audience.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = audience_targets_delete(ids="101,102")
            assert result["success"] is True

    def test_delete_audience_targets_batch_limit(self):
        """Test batch limit validation for delete."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = audience_targets_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"


class TestAudienceTargetsSuspend:
    """Tests for audience_targets_suspend."""

    def test_suspend_audience_targets_success(self):
        """Test suspending audience targets successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.audience.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = audience_targets_suspend(ids="101,102")
            assert result["success"] is True

    def test_suspend_audience_targets_batch_limit(self):
        """Test batch limit validation for suspend."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = audience_targets_suspend(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"


class TestAudienceTargetsResume:
    """Tests for audience_targets_resume."""

    def test_resume_audience_targets_success(self):
        """Test resuming audience targets successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.audience.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = audience_targets_resume(ids="101,102")
            assert result["success"] is True

    def test_resume_audience_targets_batch_limit(self):
        """Test batch limit validation for resume."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = audience_targets_resume(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
