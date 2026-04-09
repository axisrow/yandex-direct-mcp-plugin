"""Tests for keyword_bids MCP tools."""

from unittest.mock import patch, MagicMock

import pytest

import server.tools
from server.tools.keyword_bids import keyword_bids_list, keyword_bids_set


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


SAMPLE_BIDS = [
    {
        "KeywordId": 111,
        "AdGroupId": 222,
        "CampaignId": 333,
        "Bid": 1000000,
        "ContextBid": 500000,
    },
]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestKeywordBidsList:
    """Tests for keyword_bids_list tool."""

    def test_keyword_bids_list_by_campaign(self):
        """Test listing keyword bids by campaign."""
        with patch(
            "server.tools.keyword_bids.get_runner",
            return_value=_mock_runner(SAMPLE_BIDS),
        ):
            result = keyword_bids_list(campaign_ids="333")
            assert len(result) == 1
            assert result[0]["CampaignId"] == 333

    def test_keyword_bids_list_empty(self):
        """Test listing keyword bids with empty result."""
        with patch(
            "server.tools.keyword_bids.get_runner",
            return_value=_mock_runner([]),
        ):
            result = keyword_bids_list()
            assert result == []

    def test_keyword_bids_list_by_keyword(self):
        """Test listing keyword bids by keyword IDs."""
        with patch(
            "server.tools.keyword_bids.get_runner",
            return_value=_mock_runner(SAMPLE_BIDS),
        ) as mock:
            result = keyword_bids_list(keyword_ids="111")
            assert len(result) == 1
            call_args = mock.return_value.run_json.call_args[0][0]
            assert "--keyword-ids" in call_args
            assert "111" in call_args

    def test_keyword_bids_list_by_adgroup(self):
        """Test listing keyword bids by ad group IDs."""
        with patch(
            "server.tools.keyword_bids.get_runner",
            return_value=_mock_runner(SAMPLE_BIDS),
        ) as mock:
            result = keyword_bids_list(ad_group_ids="222")
            assert len(result) == 1
            call_args = mock.return_value.run_json.call_args[0][0]
            assert "--adgroup-ids" in call_args
            assert "222" in call_args


class TestKeywordBidsSet:
    """Tests for keyword_bids_set tool."""

    def test_keyword_bids_set_search_bid(self):
        """Test setting keyword search bid."""
        mock_result = {"success": True}
        with patch(
            "server.tools.keyword_bids.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = keyword_bids_set(keyword_id="111", search_bid="10.5")
            assert result["success"] is True

    def test_keyword_bids_set_both_bids(self):
        """Test setting both search and network bids."""
        mock_result = {"success": True}
        with patch(
            "server.tools.keyword_bids.get_runner",
            return_value=_mock_runner(mock_result),
        ) as mock:
            result = keyword_bids_set(
                keyword_id="111", search_bid="10", network_bid="5"
            )
            assert result["success"] is True
            call_args = mock.return_value.run_json.call_args[0][0]
            assert "--search-bid" in call_args
            assert "10" in call_args
            assert "--network-bid" in call_args
            assert "5" in call_args

    def test_keyword_bids_set_no_optional_bids(self):
        """Test setting keyword bid with no optional bids."""
        mock_result = {"success": True}
        with patch(
            "server.tools.keyword_bids.get_runner",
            return_value=_mock_runner(mock_result),
        ) as mock:
            result = keyword_bids_set(keyword_id="111")
            assert result["success"] is True
            call_args = mock.return_value.run_json.call_args[0][0]
            assert "--search-bid" not in call_args
            assert "--network-bid" not in call_args
