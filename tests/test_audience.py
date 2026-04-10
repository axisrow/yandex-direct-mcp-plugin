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
            "AdGroupId": 67890,
            "RetargetingListId": 555,
            "State": "ON",
        },
        {
            "Id": 102,
            "AdGroupId": 67891,
            "RetargetingListId": 556,
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

    def test_list_audience_targets_by_campaign(self, mock_audience_targets):
        """Test listing audience targets by campaign IDs."""
        with patch(
            "server.tools.audience.get_runner",
            return_value=_mock_runner(mock_audience_targets),
        ):
            result = audience_targets_list(campaign_ids="12345")
            assert len(result) == 2

    def test_list_audience_targets_by_ad_group(self):
        """Test listing audience targets by ad group IDs."""
        runner = MagicMock()
        runner.run_json.return_value = []
        with patch(
            "server.tools.audience.get_runner",
            return_value=runner,
        ):
            audience_targets_list(ad_group_ids="67890")
            call_args = runner.run_json.call_args[0][0]
            assert "--adgroup-ids" in call_args

    def test_list_audience_targets_by_ids(self):
        """Test listing audience targets by IDs."""
        runner = MagicMock()
        runner.run_json.return_value = []
        with patch(
            "server.tools.audience.get_runner",
            return_value=runner,
        ):
            audience_targets_list(ids="101,102")
            call_args = runner.run_json.call_args[0][0]
            assert "--ids" in call_args

    def test_list_audience_targets_ignores_blank_ids(self, mock_audience_targets):
        """Test blank filters behave like no filter."""
        runner = MagicMock()
        runner.run_json.return_value = mock_audience_targets
        with patch("server.tools.audience.get_runner", return_value=runner):
            result = audience_targets_list(
                campaign_ids="   ", ad_group_ids="   ", ids="   "
            )
            assert len(result) == 2
            call_args = runner.run_json.call_args[0][0]
            assert "--campaign-ids" not in call_args
            assert "--adgroup-ids" not in call_args
            assert "--ids" not in call_args

    def test_list_audience_targets_batch_limit(self):
        """Test batch limit validation for list."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = audience_targets_list(campaign_ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"


class TestAudienceTargetsAdd:
    """Tests for audience_targets_add."""

    def test_add_audience_target_success(self):
        """Test adding an audience target successfully."""
        mock_result = {
            "Id": 103,
            "AdGroupId": 67892,
            "RetargetingListId": 557,
            "State": "ON",
        }
        runner = MagicMock()
        runner.run_json.return_value = mock_result
        with patch(
            "server.tools.audience.get_runner",
            return_value=runner,
        ):
            result = audience_targets_add(
                ad_group_id="67892",
                retargeting_list_id="557",
            )
            assert result["Id"] == 103
            call_args = runner.run_json.call_args[0][0]
            assert "--adgroup-id" in call_args
            assert "--retargeting-list-id" in call_args

    def test_add_audience_target_with_bid(self):
        """Test adding with bid parameter."""
        runner = MagicMock()
        runner.run_json.return_value = {"Id": 104}
        with patch(
            "server.tools.audience.get_runner",
            return_value=runner,
        ):
            audience_targets_add(
                ad_group_id="67892",
                retargeting_list_id="557",
                bid="15.5",
            )
            call_args = runner.run_json.call_args[0][0]
            assert "--bid" in call_args
            assert "15.5" in call_args


class TestAudienceTargetsDelete:
    """Tests for audience_targets_delete."""

    def test_delete_audience_targets_success(self):
        """Test deleting audience targets successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.audience.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = audience_targets_delete(ids="101")
            assert result["success"] is True

    def test_delete_audience_targets_batch_limit(self):
        """Test batch limit validation for delete."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = audience_targets_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"


class TestAudienceTargetsSuspend:
    """Tests for audience_targets_suspend."""

    def test_suspend_audience_targets_success(self):
        """Test suspending audience targets successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.audience.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = audience_targets_suspend(ids="101")
            assert result["success"] is True

    def test_suspend_audience_targets_batch_limit(self):
        """Test batch limit validation for suspend."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = audience_targets_suspend(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"


class TestAudienceTargetsResume:
    """Tests for audience_targets_resume."""

    def test_resume_audience_targets_success(self):
        """Test resuming audience targets successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.audience.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = audience_targets_resume(ids="101")
            assert result["success"] is True

    def test_resume_audience_targets_batch_limit(self):
        """Test batch limit validation for resume."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = audience_targets_resume(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
