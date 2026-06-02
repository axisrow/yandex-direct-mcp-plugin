"""Tests for businesses MCP tools."""

from unittest.mock import patch

from server.tools.businesses import businesses_list

from tests.helpers import mock_runner

SAMPLE_BUSINESSES = [
    {"Id": 100, "Name": "Test Business", "Url": "https://example.com"},
]


def test_businesses_list_success():
    with patch(
        "server.tools.businesses.get_runner",
        return_value=mock_runner(SAMPLE_BUSINESSES),
    ):
        result = businesses_list()
        assert len(result) == 1
        assert result[0]["Id"] == 100


def test_businesses_list_with_ids():
    with patch(
        "server.tools.businesses.get_runner",
        return_value=mock_runner(SAMPLE_BUSINESSES),
    ):
        result = businesses_list(ids="100")
        assert len(result) == 1


def test_businesses_list_trims_ids():
    runner = mock_runner(SAMPLE_BUSINESSES)
    with patch("server.tools.businesses.get_runner", return_value=runner):
        businesses_list(ids=" 100 ")

    runner.run_json.assert_called_once_with(
        ["businesses", "get", "--format", "json", "--ids", "100"]
    )


def test_businesses_list_empty():
    with patch(
        "server.tools.businesses.get_runner",
        return_value=mock_runner([]),
    ):
        result = businesses_list()
        assert result == []


def test_businesses_list_ignores_blank_ids():
    """Test blank ids behave like no filter."""
    runner = mock_runner(SAMPLE_BUSINESSES)
    with patch("server.tools.businesses.get_runner", return_value=runner):
        result = businesses_list(ids="   ")
        assert len(result) == 1
        call_args = runner.run_json.call_args[0][0]
        assert "--ids" not in call_args


def test_businesses_list_empty_ids():
    """Test empty ids string treated like no filter."""
    runner = mock_runner([])
    with patch("server.tools.businesses.get_runner", return_value=runner):
        businesses_list(ids="")

    runner.run_json.assert_called_once_with(["businesses", "get", "--format", "json"])
