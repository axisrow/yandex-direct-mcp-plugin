"""Tests for dictionaries MCP tools."""

from unittest.mock import patch

from server.tools.dictionaries import (
    dictionaries_get,
    dictionaries_get_geo_regions,
    dictionaries_list_names,
)

from tests.helpers import mock_runner


class TestDictionariesGet:
    """Test scenarios for dictionaries_get."""

    def test_get_geography_regions(self):
        """Test getting GeographyRegions dictionary."""
        mock_result = {"Regions": [{"Id": 1, "Name": "Moscow"}]}
        with patch(
            "server.tools.dictionaries.get_runner",
            return_value=mock_runner(mock_result),
        ):
            result = dictionaries_get(names="GeoRegions")
            assert result == mock_result

    def test_get_time_zones(self):
        """Test getting TimeZones dictionary."""
        mock_result = {"TimeZones": [{"Id": "Europe/Moscow", "Name": "Moscow"}]}
        with patch(
            "server.tools.dictionaries.get_runner",
            return_value=mock_runner(mock_result),
        ):
            result = dictionaries_get(names="TimeZones")
            assert result == mock_result

    def test_get_currencies(self):
        """Test getting Currencies dictionary."""
        mock_result = {"Currencies": [{"Currency": "RUB", "Name": "Russian Ruble"}]}
        with patch(
            "server.tools.dictionaries.get_runner",
            return_value=mock_runner(mock_result),
        ):
            result = dictionaries_get(names="Currencies")
            assert result == mock_result

    def test_get_constants(self):
        """Test getting Constants dictionary."""
        mock_result = {"Constants": {"MaxAds": 50}}
        with patch(
            "server.tools.dictionaries.get_runner",
            return_value=mock_runner(mock_result),
        ):
            result = dictionaries_get(names="Constants")
            assert result == mock_result

    def test_get_multiple_dictionaries(self):
        """Test getting multiple dictionaries at once."""
        mock_result = {"Currencies": [], "GeoRegions": []}
        runner = mock_runner(mock_result)

        with patch("server.tools.dictionaries.get_runner", return_value=runner):
            result = dictionaries_get(names="Currencies,GeoRegions")
            assert result == mock_result
            call_args = runner.run_json.call_args[0][0]
            assert "--names" in call_args
            assert "Currencies,GeoRegions" in call_args

    def test_passes_names_flag(self):
        """Verify the CLI flag --names is used."""
        runner = mock_runner({})

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

    def test_lists_audience_and_schema_dictionaries(self):
        """dictionaries_get accepts these v5 names, so list_names must too (#169)."""
        result = dictionaries_list_names()
        for name in (
            "GeoRegionNames",
            "AudienceInterests",
            "AudienceCriteriaTypes",
            "AudienceDemographicProfiles",
            "FilterSchemas",
        ):
            assert name in result
        assert len(result) == 15
        assert len(set(result)) == len(result)


class TestDictionariesGetGeoRegions:
    """Test scenarios for dictionaries_get_geo_regions."""

    def test_passes_geo_region_args(self):
        runner = mock_runner({"GeoRegions": []})
        with patch("server.tools.dictionaries.get_runner", return_value=runner):
            result = dictionaries_get_geo_regions(
                fields="Id,Name",
                name="Москва",
                region_ids="213",
                exact_names="Москва",
            )

        assert result == {"GeoRegions": []}
        runner.run_json.assert_called_once_with(
            [
                "dictionaries",
                "get-geo-regions",
                "--fields",
                "Id,Name",
                "--format",
                "json",
                "--name",
                "Москва",
                "--region-ids",
                "213",
                "--exact-names",
                "Москва",
            ]
        )
