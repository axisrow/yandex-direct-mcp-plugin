"""Tests for creatives MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.creatives import creatives_list


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestCreativesList:
    """Tests for creatives_list tool."""

    def test_creatives_list_basic(self):
        """Test listing creatives by IDs."""
        mock_result = {"creatives": [{"id": 1, "name": "Creative 1"}]}
        with patch(
            "server.tools.creatives.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = creatives_list(ids="1")
            assert "creatives" in result

    def test_creatives_list_by_campaign(self):
        """Test listing creatives by campaign IDs."""
        runner = MagicMock()
        runner.run_json.return_value = []
        with patch(
            "server.tools.creatives.get_runner",
            return_value=runner,
        ):
            creatives_list(campaign_ids="12345")
            call_args = runner.run_json.call_args[0][0]
            assert "--campaign-ids" in call_args
            assert "12345" in call_args

    def test_creatives_list_trims_filters(self):
        """Test creative filters are normalized before argv construction."""
        runner = MagicMock()
        runner.run_json.return_value = []
        with patch("server.tools.creatives.get_runner", return_value=runner):
            creatives_list(ids=" 1 ", campaign_ids=" 12345 ")

        runner.run_json.assert_called_once_with(
            [
                "creatives",
                "get",
                "--format",
                "json",
                "--ids",
                "1",
                "--campaign-ids",
                "12345",
            ]
        )

    def test_creatives_list_empty_result(self):
        """Test empty response returns empty list."""
        with patch(
            "server.tools.creatives.get_runner",
            return_value=_mock_runner([]),
        ):
            result = creatives_list()
            assert result == []

    def test_creatives_list_ignores_blank_ids(self):
        """Test blank ids behave like no filter."""
        runner = MagicMock()
        runner.run_json.return_value = []
        with patch("server.tools.creatives.get_runner", return_value=runner):
            creatives_list(ids="   ", campaign_ids="   ")
            call_args = runner.run_json.call_args[0][0]
            assert "--ids" not in call_args
            assert "--campaign-ids" not in call_args
