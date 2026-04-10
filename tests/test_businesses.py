"""Tests for businesses MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.businesses import businesses_list


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


SAMPLE_BUSINESSES = [
    {"Id": 100, "Name": "Test Business", "Url": "https://example.com"},
]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def test_businesses_list_success():
    with patch(
        "server.tools.businesses.get_runner",
        return_value=_mock_runner(SAMPLE_BUSINESSES),
    ):
        result = businesses_list()
        assert len(result) == 1
        assert result[0]["Id"] == 100


def test_businesses_list_with_ids():
    with patch(
        "server.tools.businesses.get_runner",
        return_value=_mock_runner(SAMPLE_BUSINESSES),
    ):
        result = businesses_list(ids="100")
        assert len(result) == 1


def test_businesses_list_trims_ids():
    runner = MagicMock()
    runner.run_json.return_value = SAMPLE_BUSINESSES
    with patch("server.tools.businesses.get_runner", return_value=runner):
        businesses_list(ids=" 100 ")

    runner.run_json.assert_called_once_with(
        ["businesses", "get", "--format", "json", "--ids", "100"]
    )


def test_businesses_list_empty():
    with patch(
        "server.tools.businesses.get_runner",
        return_value=_mock_runner([]),
    ):
        result = businesses_list()
        assert result == []
