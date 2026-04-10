"""Tests for dictionaries MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.dictionaries import dictionaries_get, dictionaries_list_names


@pytest.fixture(autouse=True)
def setup_token_getter():
    """Configure a mock token getter for all tests."""
    server.tools.set_token_getter(lambda: "test-token")


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestDictionariesGet:
    """Test scenarios for dictionaries_get."""

    def test_get_geography_regions(self):
        """Test getting GeographyRegions dictionary."""
        mock_result = {"Regions": [{"Id": 1, "Name": "Moscow"}]}
        with patch(
            "server.tools.dictionaries.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = dictionaries_get(names="GeoRegions")
            assert result == mock_result

    def test_get_time_zones(self):
        """Test getting TimeZones dictionary."""
        mock_result = {"TimeZones": [{"Id": "Europe/Moscow", "Name": "Moscow"}]}
        with patch(
            "server.tools.dictionaries.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = dictionaries_get(names="TimeZones")
            assert result == mock_result

    def test_get_currencies(self):
        """Test getting Currencies dictionary."""
        mock_result = {"Currencies": [{"Currency": "RUB", "Name": "Russian Ruble"}]}
        with patch(
            "server.tools.dictionaries.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = dictionaries_get(names="Currencies")
            assert result == mock_result

    def test_get_constants(self):
        """Test getting Constants dictionary."""
        mock_result = {"Constants": {"MaxAds": 50}}
        with patch(
            "server.tools.dictionaries.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = dictionaries_get(names="Constants")
            assert result == mock_result

    def test_get_multiple_dictionaries(self):
        """Test getting multiple dictionaries at once."""
        mock_result = {"Currencies": [], "GeoRegions": []}
        runner = MagicMock()
        runner.run_json.return_value = mock_result

        with patch("server.tools.dictionaries.get_runner", return_value=runner):
            result = dictionaries_get(names="Currencies,GeoRegions")
            assert result == mock_result
            call_args = runner.run_json.call_args[0][0]
            assert "--names" in call_args
            assert "Currencies,GeoRegions" in call_args

    def test_passes_names_flag(self):
        """Verify the CLI flag --names is used."""
        runner = MagicMock()
        runner.run_json.return_value = {}

        with patch("server.tools.dictionaries.get_runner", return_value=runner):
            dictionaries_get(names="Currencies")
            call_args = runner.run_json.call_args[0][0]
            assert "--names" in call_args
            assert "Currencies" in call_args


class TestDictionariesListNames:
    """Test scenarios for dictionaries_list_names."""

    def test_returns_list_of_names(self):
        result = dictionaries_list_names()
        assert isinstance(result, list)
        assert "Currencies" in result
        assert "GeoRegions" in result
        assert "TimeZones" in result
