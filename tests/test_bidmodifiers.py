"""Tests for bid modifier MCP tools."""

from unittest.mock import patch

from server.tools.bidmodifiers import (
    bidmodifiers_add,
    bidmodifiers_list,
    bidmodifiers_set,
    bidmodifiers_delete,
)

from tests.helpers import mock_runner

SAMPLE_BIDMODIFIERS = [
    {"Id": 1, "CampaignId": 12345, "Type": "DEMOGRAPHICS", "Value": 100},
]


class TestBidModifiersList:
    """Tests for bidmodifiers_list tool."""

    def test_bidmodifiers_list_by_campaign(self):
        """Test listing bid modifiers for campaigns."""
        with patch(
            "server.tools.bidmodifiers.get_runner",
            return_value=mock_runner(SAMPLE_BIDMODIFIERS),
        ):
            result = bidmodifiers_list(campaign_ids="12345")
            assert len(result) == 1
            assert result[0]["CampaignId"] == 12345

    def test_bidmodifiers_list_by_ad_group(self):
        """Test listing bid modifiers by ad group IDs."""
        runner = mock_runner([])
        with patch(
            "server.tools.bidmodifiers.get_runner",
            return_value=runner,
        ):
            bidmodifiers_list(ad_group_ids="67890")
            call_args = runner.run_json.call_args[0][0]
            assert "--adgroup-ids" in call_args

    def test_bidmodifiers_list_ignores_blank_ids(self):
        """Test blank filters behave like no filter."""
        runner = mock_runner(SAMPLE_BIDMODIFIERS)
        with patch("server.tools.bidmodifiers.get_runner", return_value=runner):
            result = bidmodifiers_list(campaign_ids="   ", ad_group_ids="   ")
            assert len(result) == 1
            call_args = runner.run_json.call_args[0][0]
            assert "--campaign-ids" not in call_args
            assert "--adgroup-ids" not in call_args

    def test_bidmodifiers_list_batch_limit(self):
        """Test batch limit validation for bidmodifiers_list."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = bidmodifiers_list(campaign_ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_bidmodifiers_list_with_levels(self):
        """Test listing bid modifiers with levels filter."""
        runner = mock_runner(SAMPLE_BIDMODIFIERS)
        with patch("server.tools.bidmodifiers.get_runner", return_value=runner):
            bidmodifiers_list(campaign_ids="12345", levels="CAMPAIGN")
            call_args = runner.run_json.call_args[0][0]
            assert "--levels" in call_args
            assert "CAMPAIGN" in call_args

    def test_bidmodifiers_list_rejects_invalid_levels(self):
        result = bidmodifiers_list(levels="campaign")
        assert result["error"] == "invalid_levels"


class TestBidModifiersSet:
    """Tests for bidmodifiers_set tool."""

    def test_bidmodifiers_set_success(self):
        """Test setting bid modifier successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.bidmodifiers.get_runner",
            return_value=mock_runner(mock_result),
        ):
            result = bidmodifiers_set(id=12345, value=150)
            assert result["success"] is True

    def test_bidmodifiers_set_dry_run(self):
        """dry_run=True appends --dry-run to argv."""
        runner = mock_runner({"_dry_run": True})
        with patch("server.tools.bidmodifiers.get_runner", return_value=runner):
            bidmodifiers_set(id=12345, value=150, dry_run=True)
            assert "--dry-run" in runner.run_json.call_args[0][0]

    def test_bidmodifiers_set_argv_composition(self):
        """Test set passes correct argv to CLI."""
        runner = mock_runner({"success": True})
        with patch("server.tools.bidmodifiers.get_runner", return_value=runner):
            bidmodifiers_set(id=67890, value=120)

        runner.run_json.assert_called_once_with(
            [
                "bidmodifiers",
                "set",
                "--id",
                "67890",
                "--value",
                "120",
            ]
        )


class TestBidModifiersAdd:
    """Tests for bidmodifiers_add tool."""

    def test_bidmodifiers_add_success(self):
        runner = mock_runner({"success": True})
        with patch("server.tools.bidmodifiers.get_runner", return_value=runner):
            result = bidmodifiers_add(
                campaign_id=12345,
                modifier_type="MOBILE_ADJUSTMENT",
                value=120,
                region_id=213,
            )

        assert result["success"] is True
        runner.run_json.assert_called_once_with(
            [
                "bidmodifiers",
                "add",
                "--type",
                "MOBILE_ADJUSTMENT",
                "--value",
                "120",
                "--campaign-id",
                "12345",
                "--region-id",
                "213",
            ]
        )

    def test_bidmodifiers_add_accepts_smart_tv_adjustment(self):
        """direct-cli 0.3.12 exposes SMART_TV_ADJUSTMENT."""
        runner = mock_runner({"success": True})
        with patch("server.tools.bidmodifiers.get_runner", return_value=runner):
            result = bidmodifiers_add(
                campaign_id=12345,
                modifier_type="SMART_TV_ADJUSTMENT",
                value=120,
            )

        assert result["success"] is True
        runner.run_json.assert_called_once_with(
            [
                "bidmodifiers",
                "add",
                "--type",
                "SMART_TV_ADJUSTMENT",
                "--value",
                "120",
                "--campaign-id",
                "12345",
            ]
        )

    def test_bidmodifiers_add_requires_scope(self):
        result = bidmodifiers_add(modifier_type="MOBILE_ADJUSTMENT", value=120)
        assert result["error"] == "missing_target_scope"


class TestBidModifiersDelete:
    """Tests for bidmodifiers_delete tool."""

    def test_bidmodifiers_delete_success(self):
        """Test deleting bid modifiers successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.bidmodifiers.get_runner",
            return_value=mock_runner(mock_result),
        ):
            result = bidmodifiers_delete(ids="1")
            assert result["success"] is True

    def test_bidmodifiers_delete_batch_limit(self):
        """Test batch limit validation for bidmodifiers_delete."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = bidmodifiers_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
