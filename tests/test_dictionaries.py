"""Tests for dictionaries MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.dictionaries import dictionaries_get


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
            result = dictionaries_get(dictionary_type="GeographyRegions")
            assert result == mock_result

    def test_get_time_zones(self):
        """Test getting TimeZones dictionary."""
        mock_result = {"TimeZones": [{"Id": "Europe/Moscow", "Name": "Moscow"}]}
        with patch(
            "server.tools.dictionaries.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = dictionaries_get(dictionary_type="TimeZones")
            assert result == mock_result

    def test_get_currencies(self):
        """Test getting Currencies dictionary."""
        mock_result = {"Currencies": [{"Currency": "RUB", "Name": "Russian Ruble"}]}
        with patch(
            "server.tools.dictionaries.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = dictionaries_get(dictionary_type="Currencies")
            assert result == mock_result

    def test_get_constants(self):
        """Test getting Constants dictionary."""
        mock_result = {"Constants": {"MaxAds": 50}}
        with patch(
            "server.tools.dictionaries.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = dictionaries_get(dictionary_type="Constants")
            assert result == mock_result

    def test_get_with_locale(self):
        """Test getting dictionary with locale parameter."""
        mock_result = {"Regions": [{"Id": 1, "Name": "Москва"}]}
        runner = MagicMock()
        runner.run_json.return_value = mock_result

        with patch("server.tools.dictionaries.get_runner", return_value=runner):
            dictionaries_get(dictionary_type="GeographyRegions", locale="ru")
            runner.run_json.assert_called_once()
            call_args = runner.run_json.call_args[0][0]
            assert "--locale" in call_args
            assert "ru" in call_args

    def test_invalid_dictionary_type(self):
        """Test with invalid dictionary type."""
        result = dictionaries_get(dictionary_type="InvalidType")
        assert "error" in result
        assert result["error"] == "invalid_type"

    def test_all_valid_dictionary_types(self):
        """Test all valid dictionary types are accepted."""
        valid_types = (
            "GeographyRegions",
            "TimeZones",
            "Currencies",
            "Constants",
            "AdCategories",
            "OperationSystemVersions",
            "MobileOperatingSystemVersions",
            "DeviceTypes",
            "AgeRanges",
            "Genders",
            "Interests",
        )

        for dict_type in valid_types:
            mock_result = {"Test": "data"}
            with patch(
                "server.tools.dictionaries.get_runner",
                return_value=_mock_runner(mock_result),
            ):
                result = dictionaries_get(dictionary_type=dict_type)
                assert result == mock_result
