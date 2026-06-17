"""Tests for dynamic feed ad target MCP tools."""

from unittest.mock import patch

from server.tools.dynamic_feed_ad_targets import (
    dynamic_feed_ad_targets_add,
    dynamic_feed_ad_targets_delete,
    dynamic_feed_ad_targets_list,
    dynamic_feed_ad_targets_resume,
    dynamic_feed_ad_targets_set_bids,
    dynamic_feed_ad_targets_suspend,
)

from tests.helpers import mock_runner


class TestDynamicFeedAdTargetsList:
    """Tests for dynamic_feed_ad_targets_list."""

    def test_dynamic_feed_ad_targets_list(self):
        """Test listing dynamic feed ad targets."""
        mock_result = [
            {"Id": 10, "AdGroupId": 200, "Name": "Target A"},
            {"Id": 11, "AdGroupId": 200, "Name": "Target B"},
        ]
        runner = mock_runner(mock_result)
        with patch(
            "server.tools.dynamic_feed_ad_targets.get_runner",
            return_value=runner,
        ):
            result = dynamic_feed_ad_targets_list(campaign_ids="12345")
            assert len(result) == 2
            runner.run_json.assert_called_once_with(
                [
                    "dynamicfeedadtargets",
                    "get",
                    "--format",
                    "json",
                    "--campaign-ids",
                    "12345",
                ]
            )

    def test_dynamic_feed_ad_targets_list_forwards_many_ids_without_plugin_limit(self):
        """Plugin no longer caps the get array; CLI 0.4.3 (#555) owns the real
        per-method limit (campaign_ids ≤2 for this method). Plugin forwards (#201)."""
        ids = ",".join(str(i) for i in range(1, 12))
        runner = mock_runner([])
        with patch(
            "server.tools.dynamic_feed_ad_targets.get_runner", return_value=runner
        ):
            result = dynamic_feed_ad_targets_list(ids=ids)
        assert not (isinstance(result, dict) and result.get("error"))
        call_args = runner.run_json.call_args[0][0]
        assert "--ids" in call_args and ids in call_args


class TestDynamicFeedAdTargetsAdd:
    """Tests for dynamic_feed_ad_targets_add."""

    def test_dynamic_feed_ad_targets_add(self):
        """Test adding a dynamic feed ad target."""
        mock_result = {"Id": 20, "AdGroupId": 200, "Name": "Test"}
        runner = mock_runner(mock_result)
        with patch(
            "server.tools.dynamic_feed_ad_targets.get_runner",
            return_value=runner,
        ):
            result = dynamic_feed_ad_targets_add(
                ad_group_id=200,
                name="Test",
                bid=1500000,
            )
            assert result["Id"] == 20
            runner.run_json.assert_called_once_with(
                [
                    "dynamicfeedadtargets",
                    "add",
                    "--adgroup-id",
                    "200",
                    "--name",
                    "Test",
                    "--bid",
                    "1500000",
                ]
            )


class TestDynamicFeedAdTargetsDelete:
    """Tests for dynamic_feed_ad_targets_delete."""

    def test_dynamic_feed_ad_targets_delete(self):
        """Test deleting a dynamic feed ad target."""
        mock_result = {"success": True}
        with patch(
            "server.tools.dynamic_feed_ad_targets.get_runner",
            return_value=mock_runner(mock_result),
        ):
            result = dynamic_feed_ad_targets_delete(id=100)
            assert result["success"] is True


class TestDynamicFeedAdTargetsSuspend:
    """Tests for dynamic_feed_ad_targets_suspend."""

    def test_dynamic_feed_ad_targets_suspend(self):
        """Test batch suspending dynamic feed ad targets."""
        runner = mock_runner({"success": True})
        with patch(
            "server.tools.dynamic_feed_ad_targets.get_runner",
            return_value=runner,
        ):
            result = dynamic_feed_ad_targets_suspend(ids="100,101")
            assert result["success"] is True
            calls = runner.run_json.call_args_list
            assert len(calls) == 2
            assert calls[0][0][0] == ["dynamicfeedadtargets", "suspend", "--id", "100"]
            assert calls[1][0][0] == ["dynamicfeedadtargets", "suspend", "--id", "101"]


class TestDynamicFeedAdTargetsResume:
    """Tests for dynamic_feed_ad_targets_resume."""

    def test_dynamic_feed_ad_targets_resume(self):
        """Test batch resuming dynamic feed ad targets."""
        runner = mock_runner({"success": True})
        with patch(
            "server.tools.dynamic_feed_ad_targets.get_runner",
            return_value=runner,
        ):
            result = dynamic_feed_ad_targets_resume(ids="100,101")
            assert result["success"] is True
            calls = runner.run_json.call_args_list
            assert len(calls) == 2
            assert calls[0][0][0] == ["dynamicfeedadtargets", "resume", "--id", "100"]
            assert calls[1][0][0] == ["dynamicfeedadtargets", "resume", "--id", "101"]


class TestDynamicFeedAdTargetsSetBids:
    """Tests for dynamic_feed_ad_targets_set_bids."""

    def test_dynamic_feed_ad_targets_set_bids(self):
        """Test setting bids for a dynamic feed ad target."""
        runner = mock_runner({"success": True})
        with patch(
            "server.tools.dynamic_feed_ad_targets.get_runner",
            return_value=runner,
        ):
            result = dynamic_feed_ad_targets_set_bids(id=100, bid=2000000)
            assert result["success"] is True
            runner.run_json.assert_called_once_with(
                [
                    "dynamicfeedadtargets",
                    "set-bids",
                    "--id",
                    "100",
                    "--bid",
                    "2000000",
                ]
            )

    def test_dynamic_feed_ad_targets_set_bids_requires_scope(self):
        """Test that missing scope (id, ad_group_id, campaign_id) returns error."""
        result = dynamic_feed_ad_targets_set_bids(bid=2000000)
        assert result["error"] == "missing_target_scope"

    def test_dynamic_feed_ad_targets_set_bids_requires_update(self):
        """Test that missing update fields (bid, context_bid) returns error."""
        result = dynamic_feed_ad_targets_set_bids(id=100)
        assert result["error"] == "missing_update_fields"
