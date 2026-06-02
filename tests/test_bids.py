"""Tests for bid MCP tools."""

from unittest.mock import patch

from server.tools.bids import bids_list, bids_set, bids_set_auto

from tests.helpers import mock_runner

SAMPLE_BIDS = [
    {"CampaignId": 12345, "Bid": 15000000},
]


class TestBidsList:
    """Tests for bids_list tool."""

    def test_bids_list_success(self):
        """Test listing bids for campaigns."""
        with patch(
            "server.tools.bids.get_runner",
            return_value=mock_runner(SAMPLE_BIDS),
        ):
            result = bids_list(campaign_ids="12345")
            assert len(result) == 1
            assert result[0]["CampaignId"] == 12345

    def test_bids_list_by_ad_group(self):
        """Test listing bids by ad group IDs."""
        runner = mock_runner([])
        with patch(
            "server.tools.bids.get_runner",
            return_value=runner,
        ):
            bids_list(ad_group_ids="67890")
            call_args = runner.run_json.call_args[0][0]
            assert "--adgroup-ids" in call_args

    def test_bids_list_by_keyword(self):
        """Test listing bids by keyword IDs."""
        runner = mock_runner([])
        with patch(
            "server.tools.bids.get_runner",
            return_value=runner,
        ):
            bids_list(keyword_ids="111,222")
            call_args = runner.run_json.call_args[0][0]
            assert "--keyword-ids" in call_args

    def test_bids_list_ignores_blank_filters(self):
        """Test blank filters behave like no filter."""
        runner = mock_runner(SAMPLE_BIDS)
        with patch("server.tools.bids.get_runner", return_value=runner):
            result = bids_list(
                campaign_ids="   ", ad_group_ids="   ", keyword_ids="   "
            )
            assert len(result) == 1
            call_args = runner.run_json.call_args[0][0]
            assert "--campaign-ids" not in call_args
            assert "--adgroup-ids" not in call_args
            assert "--keyword-ids" not in call_args

    def test_bids_list_batch_limit(self):
        """Test batch limit validation for bids_list."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = bids_list(campaign_ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"


class TestBidsSet:
    """Tests for bids_set tool (CLI 0.3.8: --keyword-id only)."""

    def test_bids_set_success(self):
        """Test setting bid for a keyword successfully."""
        mock_result = {"success": True}
        runner = mock_runner(mock_result)
        with patch("server.tools.bids.get_runner", return_value=runner):
            result = bids_set(keyword_id=99999, bid=15000000)
            assert result["success"] is True
            runner.run_json.assert_called_once_with(
                ["bids", "set", "--keyword-id", "99999", "--bid", "15000000"]
            )

    def test_bids_set_dry_run(self):
        runner = mock_runner({"_dry_run": True})
        with patch("server.tools.bids.get_runner", return_value=runner):
            bids_set(keyword_id=99999, bid=15000000, dry_run=True)
            assert "--dry-run" in runner.run_json.call_args[0][0]

    def test_bids_list_ad_group_batch_limit(self):
        """Test batch limit validation for ad_group_ids."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = bids_list(ad_group_ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_bids_list_keyword_batch_limit(self):
        """Test batch limit validation for keyword_ids."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = bids_list(keyword_ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"


class TestBidsSetAuto:
    """Tests for bids_set_auto tool."""

    def test_bids_set_auto_success(self):
        runner = mock_runner({"success": True})
        with patch("server.tools.bids.get_runner", return_value=runner):
            result = bids_set_auto(
                campaign_id=12345,
                max_bid=10500000,
                position="PREMIUM",
            )

        assert result["success"] is True
        runner.run_json.assert_called_once_with(
            [
                "bids",
                "set-auto",
                "--campaign-id",
                "12345",
                "--max-bid",
                "10500000",
                "--position",
                "PREMIUM",
            ]
        )

    def test_bids_set_auto_requires_scope(self):
        result = bids_set_auto(max_bid=10500000)
        assert result["error"] == "missing_target_scope"
