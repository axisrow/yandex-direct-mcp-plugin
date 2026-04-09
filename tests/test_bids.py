"""Tests for bid MCP tools."""

from unittest.mock import patch, MagicMock

import pytest

import server.tools
from server.tools.bids import bids_list, bids_set


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
            "server.tools.bids.get_runner", return_value=_mock_runner(SAMPLE_BIDS)
        ):
            result = bids_list(campaign_ids="12345")
            assert len(result) == 1
            assert result[0]["CampaignId"] == 12345

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
        with patch(
            "server.tools.bids.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = bids_set(campaign_id="12345", bid="15000000")
            assert result["success"] is True

    def test_bids_set_with_context_bid(self):
        """Test setting bid with context bid."""
        mock_result = {"success": True}
        with patch(
            "server.tools.bids.get_runner", return_value=_mock_runner(mock_result)
        ) as mock:
            result = bids_set(
                campaign_id="12345", bid="15000000", context_bid="12000000"
            )
            assert result["success"] is True
            # Verify the CLI command includes context bid
            call_args = mock.return_value.run_json.call_args[0][0]
            assert "--context-bid" in call_args
            assert "12000000" in call_args

    def test_bids_set_invalid_bid_negative(self):
        """Test bids_set with negative bid."""
        result = bids_set(campaign_id="12345", bid="-100")
        assert "error" in result
        assert result["error"] == "invalid_value"

    def test_bids_set_invalid_bid_zero(self):
        """Test bids_set with zero bid."""
        result = bids_set(campaign_id="12345", bid="0")
        assert "error" in result
        assert result["error"] == "invalid_value"

    def test_bids_set_invalid_bid_non_numeric(self):
        """Test bids_set with non-numeric bid."""
        result = bids_set(campaign_id="12345", bid="abc")
        assert "error" in result
        assert result["error"] == "invalid_value"

    def test_bids_set_invalid_context_bid(self):
        """Test bids_set with invalid context bid."""
        result = bids_set(campaign_id="12345", bid="15000000", context_bid="invalid")
        assert "error" in result
        assert result["error"] == "invalid_value"
