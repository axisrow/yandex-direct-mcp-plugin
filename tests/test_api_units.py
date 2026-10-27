"""Tests for the api_units CLI-helper MCP tool (#318)."""

from unittest.mock import patch

from server.tools.api_units import api_units
from tests.helpers import mock_runner


def test_api_units_requests_json_from_units_command() -> None:
    result_data = {"Spent": 12345, "Rest": 98765, "Limit": 111110}
    runner = mock_runner(result_data)

    with patch("server.tools.api_units.get_runner", return_value=runner):
        assert api_units() == result_data

    runner.run_json.assert_called_once_with(["api", "units", "--format", "json"])
