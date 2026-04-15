"""Tests for bid MCP tools."""

from unittest.mock import patch, MagicMock

import pytest

import server.tools
from server.tools.bids import bids_list, bids_set, bids_set_auto


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


SAMPLE_BIDS = [
    {"CampaignId": 12345, "Bid": 15000000},
]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestBidsList:
    """Tests for bids_list tool."""

    def test_bids_list_success(self):
        """Test listing bids for campaigns."""
        with patch(
            "server.tools.bids.get_runner",
            return_value=_mock_runner(SAMPLE_BIDS),
        ):
            result = bids_list(campaign_ids="12345")
            assert len(result) == 1
            assert result[0]["CampaignId"] == 12345

    def test_bids_list_by_ad_group(self):
        """Test listing bids by ad group IDs."""
        runner = MagicMock()
        runner.run_json.return_value = []
        with patch(
            "server.tools.bids.get_runner",
            return_value=runner,
        ):
            bids_list(ad_group_ids="67890")
            call_args = runner.run_json.call_args[0][0]
            assert "--adgroup-ids" in call_args

    def test_bids_list_by_keyword(self):
        """Test listing bids by keyword IDs."""
        runner = MagicMock()
        runner.run_json.return_value = []
        with patch(
            "server.tools.bids.get_runner",
            return_value=runner,
        ):
            bids_list(keyword_ids="111,222")
            call_args = runner.run_json.call_args[0][0]
            assert "--keyword-ids" in call_args

    def test_bids_list_ignores_blank_filters(self):
        """Test blank filters behave like no filter."""
        runner = MagicMock()
        runner.run_json.return_value = SAMPLE_BIDS
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
    """Tests for bids_set tool."""

    def test_bids_set_success(self):
        """Test setting bid successfully."""
        mock_result = {"success": True}
        runner = MagicMock()
        runner.run_json.return_value = mock_result
        with patch(
            "server.tools.bids.get_runner",
            return_value=runner,
        ):
            result = bids_set(campaign_id="12345", bid="15")
            assert result["success"] is True
            call_args = runner.run_json.call_args[0][0]
            assert "--bid" in call_args

    def test_bids_set_with_extra_json(self):
        """Test setting bid with extra JSON parameters."""
        runner = MagicMock()
        runner.run_json.return_value = {"success": True}
        with patch(
            "server.tools.bids.get_runner",
            return_value=runner,
        ):
            bids_set(
                campaign_id="12345",
                bid="15",
                extra_json='{"ContextBid":12000000}',
            )
            call_args = runner.run_json.call_args[0][0]
            assert "--json" in call_args

    def test_bids_set_requires_update_fields(self):
        """Test setting bid rejects empty updates before CLI call."""
        runner = MagicMock()
        with patch(
            "server.tools.bids.get_runner",
            return_value=runner,
        ):
            result = bids_set(campaign_id="12345")

        assert result["error"] == "missing_update_fields"
        runner.run_json.assert_not_called()

    def test_bids_set_only_extra_json(self):
        """Test setting bid with only extra_json (no bid)."""
        runner = MagicMock()
        runner.run_json.return_value = {"success": True}
        with patch(
            "server.tools.bids.get_runner",
            return_value=runner,
        ):
            result = bids_set(
                campaign_id="12345",
                extra_json='{"ContextBid":12000000}',
            )
            assert result["success"] is True
            call_args = runner.run_json.call_args[0][0]
            assert "--bid" not in call_args
            assert "--json" in call_args

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
        runner = MagicMock()
        runner.run_json.return_value = {"success": True}
        with patch("server.tools.bids.get_runner", return_value=runner):
            result = bids_set_auto(
                campaign_id="12345",
                max_bid="10.5",
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
                "10.5",
                "--position",
                "PREMIUM",
            ]
        )

    def test_bids_set_auto_requires_scope(self):
        result = bids_set_auto(max_bid="10.5")
        assert result["error"] == "missing_target_scope"
