"""Tests for audience MCP tools."""

from unittest.mock import patch

import pytest

from server.tools.audience import (
    audience_targets_add,
    audience_targets_delete,
    audience_targets_list,
    audience_targets_resume,
    audience_targets_set_bids,
    audience_targets_suspend,
)

from tests.helpers import mock_runner


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


class TestAudienceTargetsList:
    """Tests for audience_targets_list."""

    def test_list_audience_targets_by_campaign(self, mock_audience_targets):
        """Test listing audience targets by campaign IDs."""
        with patch(
            "server.tools.audience.get_runner",
            return_value=mock_runner(mock_audience_targets),
        ):
            result = audience_targets_list(campaign_ids="12345")
            assert len(result) == 2

    def test_list_audience_targets_by_ad_group(self):
        """Test listing audience targets by ad group IDs."""
        runner = mock_runner([])
        with patch(
            "server.tools.audience.get_runner",
            return_value=runner,
        ):
            audience_targets_list(ad_group_ids="67890")
            call_args = runner.run_json.call_args[0][0]
            assert "--adgroup-ids" in call_args

    def test_list_audience_targets_by_ids(self):
        """Test listing audience targets by IDs."""
        runner = mock_runner([])
        with patch(
            "server.tools.audience.get_runner",
            return_value=runner,
        ):
            audience_targets_list(ids="101,102")
            call_args = runner.run_json.call_args[0][0]
            assert "--ids" in call_args

    def test_list_audience_targets_normalizes_blanks_with_real_filter(self):
        """Blank filters are dropped, but a real filter still goes through."""
        runner = mock_runner([])
        with patch("server.tools.audience.get_runner", return_value=runner):
            audience_targets_list(campaign_ids="12345", ad_group_ids="   ", ids="   ")
            call_args = runner.run_json.call_args[0][0]
            assert "--campaign-ids" in call_args
            assert "12345" in call_args
            assert "--adgroup-ids" not in call_args
            assert "--ids" not in call_args

    def test_list_audience_targets_states_satisfies_filter(self):
        """States alone is a typed filter (CLI counts it), so the call proceeds."""
        runner = mock_runner([])
        with patch("server.tools.audience.get_runner", return_value=runner):
            audience_targets_list(states="ON")
            call_args = runner.run_json.call_args[0][0]
            assert "--states" in call_args
            assert "ON" in call_args

    def test_list_audience_targets_requires_filter(self):
        """Filterless request is rejected up front (issue #167)."""
        result = audience_targets_list()
        assert result["error"] == "filter_required"

    def test_list_audience_targets_fetch_all_still_requires_filter(self):
        """fetch_all is not a filter — the exact repro from #167."""
        result = audience_targets_list(fetch_all=True)
        assert result["error"] == "filter_required"

    def test_list_audience_targets_blank_only_requires_filter(self):
        """Whitespace-only filters behave like no filter and are rejected."""
        result = audience_targets_list(
            campaign_ids="   ", ad_group_ids="   ", ids="   "
        )
        assert result["error"] == "filter_required"

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
        runner = mock_runner(mock_result)
        with patch(
            "server.tools.audience.get_runner",
            return_value=runner,
        ):
            result = audience_targets_add(
                ad_group_id=67892,
                retargeting_list_id=557,
            )
            assert result["Id"] == 103
            call_args = runner.run_json.call_args[0][0]
            assert "--adgroup-id" in call_args
            assert "--retargeting-list-id" in call_args

    def test_add_audience_target_with_bid(self):
        """Test adding with bid parameter."""
        runner = mock_runner({"Id": 104})
        with patch(
            "server.tools.audience.get_runner",
            return_value=runner,
        ):
            audience_targets_add(
                ad_group_id=67892,
                retargeting_list_id=557,
                bid=15500000,
            )
            call_args = runner.run_json.call_args[0][0]
            assert "--bid" in call_args
            assert "15500000" in call_args


class TestAudienceTargetsDelete:
    """Tests for audience_targets_delete."""

    def test_delete_audience_targets_success(self):
        """Test deleting audience targets successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.audience.get_runner",
            return_value=mock_runner(mock_result),
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
            return_value=mock_runner(mock_result),
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
            return_value=mock_runner(mock_result),
        ):
            result = audience_targets_resume(ids="101")
            assert result["success"] is True

    def test_resume_audience_targets_batch_limit(self):
        """Test batch limit validation for resume."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = audience_targets_resume(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"


class TestAudienceTargetsSetBids:
    """Tests for audience_targets_set_bids."""

    def test_set_bids_success(self):
        runner = mock_runner({"success": True})
        with patch("server.tools.audience.get_runner", return_value=runner):
            result = audience_targets_set_bids(
                id=101,
                context_bid=1500000,
                priority="HIGH",
            )

        assert result["success"] is True
        runner.run_json.assert_called_once_with(
            [
                "audiencetargets",
                "set-bids",
                "--id",
                "101",
                "--context-bid",
                "1500000",
                "--priority",
                "HIGH",
            ]
        )

    def test_set_bids_requires_scope(self):
        result = audience_targets_set_bids(context_bid=1500000)
        assert result["error"] == "missing_target_scope"
