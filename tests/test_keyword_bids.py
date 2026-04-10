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

    def test_keyword_bids_list_trims_filters(self):
        """Test keyword bid filters are normalized before argv construction."""
        runner = MagicMock()
        runner.run_json.return_value = []
        with patch("server.tools.keyword_bids.get_runner", return_value=runner):
            keyword_bids_list(
                campaign_ids=" 333 ",
                ad_group_ids=" 222 ",
                keyword_ids=" 111 ",
            )

        runner.run_json.assert_called_once_with(
            [
                "keywordbids",
                "get",
                "--format",
                "json",
                "--campaign-ids",
                "333",
                "--adgroup-ids",
                "222",
                "--keyword-ids",
                "111",
            ]
        )


class TestKeywordBidsSet:
    """Tests for keyword_bids_set tool."""

    def test_keyword_bids_set_search_bid(self):
        """Test setting keyword search bid."""
        mock_result = {"success": True}
        with patch(
            "server.tools.keyword_bids.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = keyword_bids_set(keyword_id="111", search_bid="10")
            assert result["success"] is True

    def test_keyword_bids_set_invalid_bid(self):
        """Test that non-integer bid is rejected."""
        result = keyword_bids_set(keyword_id="111", search_bid="abc")
        assert result["error"] == "invalid_value"

    def test_keyword_bids_set_negative_bid(self):
        """Test that negative bid is rejected."""
        result = keyword_bids_set(keyword_id="111", search_bid="-5")
        assert result["error"] == "invalid_value"

    def test_keyword_bids_set_zero_bid(self):
        """Test that zero bid is rejected."""
        result = keyword_bids_set(keyword_id="111", search_bid="0")
        assert result["error"] == "invalid_value"

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
            assert "--format" not in call_args

    def test_keyword_bids_set_with_json(self):
        """Test setting keyword bids with additional JSON."""
        mock_result = {"success": True}
        with patch(
            "server.tools.keyword_bids.get_runner",
            return_value=_mock_runner(mock_result),
        ) as mock:
            result = keyword_bids_set(
                keyword_id="111", extra_json='{"AutoBudget":"YES"}'
            )
            assert result["success"] is True
            call_args = mock.return_value.run_json.call_args[0][0]
            assert "--json" in call_args
            assert '{"AutoBudget":"YES"}' in call_args

    def test_keyword_bids_set_requires_changes(self):
        """Reject no-op updates before calling CLI."""
        runner = _mock_runner({"success": True})
        with patch("server.tools.keyword_bids.get_runner", return_value=runner):
            result = keyword_bids_set(keyword_id="111")
            assert result["error"] == "missing_update_fields"
            runner.run_json.assert_not_called()

    def test_keyword_bids_set_network_bid_invalid(self):
        """Test that non-integer network bid is rejected."""
        result = keyword_bids_set(keyword_id="111", network_bid="abc")
        assert result["error"] == "invalid_value"

    def test_keyword_bids_set_argv_with_search_bid(self):
        """Test argv composition for search bid."""
        runner = _mock_runner({"success": True})
        with patch("server.tools.keyword_bids.get_runner", return_value=runner):
            keyword_bids_set(keyword_id="111", search_bid="10")

        runner.run_json.assert_called_once_with(
            ["keywordbids", "set", "--keyword-id", "111", "--search-bid", "10"]
        )

    def test_keyword_bids_list_ignores_blank_filters(self):
        """Test blank filters behave like no filter."""
        runner = MagicMock()
        runner.run_json.return_value = SAMPLE_BIDS
        with patch("server.tools.keyword_bids.get_runner", return_value=runner):
            result = keyword_bids_list(
                campaign_ids="   ", ad_group_ids="   ", keyword_ids="   "
            )
            assert len(result) == 1
            call_args = runner.run_json.call_args[0][0]
            assert "--campaign-ids" not in call_args
            assert "--adgroup-ids" not in call_args
            assert "--keyword-ids" not in call_args
