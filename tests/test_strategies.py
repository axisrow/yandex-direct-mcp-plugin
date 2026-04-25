"""Tests for strategy MCP tools."""

import json
from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.strategies import (
    strategies_add,
    strategies_archive,
    strategies_list,
    strategies_unarchive,
    strategies_update,
)


@pytest.fixture(autouse=True)
def setup_token_getter():
    """Configure a mock token getter for all tests."""
    server.tools.set_token_getter(lambda: "test-token")


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestStrategiesList:
    """Tests for strategies_get."""

    def test_strategies_list(self):
        """Basic list returns all strategies."""
        strategies = [
            {"Id": 1, "Name": "Strategy_A", "Type": "AverageCpc"},
            {"Id": 2, "Name": "Strategy_B", "Type": "MaxProfit"},
        ]
        with patch(
            "server.tools.strategies.get_runner",
            return_value=_mock_runner(strategies),
        ):
            result = strategies_list()
            assert len(result) == 2
            assert result[0]["Id"] == 1

    def test_strategies_list_with_types(self):
        """Filter by types passes --types to CLI."""
        runner = _mock_runner([{"Id": 1, "Type": "AverageCpc"}])
        with patch("server.tools.strategies.get_runner", return_value=runner):
            strategies_list(types="AverageCpc")
        runner.run_json.assert_called_once_with(
            ["strategies", "get", "--format", "json", "--types", "AverageCpc"]
        )

    def test_strategies_list_with_is_archived(self):
        """Filter by is_archived passes --is-archived to CLI."""
        runner = _mock_runner([{"Id": 1}])
        with patch("server.tools.strategies.get_runner", return_value=runner):
            strategies_list(is_archived="no")
        runner.run_json.assert_called_once_with(
            ["strategies", "get", "--format", "json", "--is-archived", "no"]
        )

    def test_strategies_list_batch_limit(self):
        """11 IDs triggers batch_limit error."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = strategies_list(ids=ids)
        assert result["error"] == "batch_limit"


class TestStrategiesAdd:
    """Tests for strategies_add."""

    def test_strategies_add(self):
        """Basic add with required fields."""
        runner = _mock_runner({"Id": 100, "Name": "MyStrategy"})
        with patch("server.tools.strategies.get_runner", return_value=runner):
            result = strategies_add(name="MyStrategy", type="AverageCpc")
        assert result["Id"] == 100
        runner.run_json.assert_called_once_with(
            ["strategies", "add", "--name", "MyStrategy", "--type", "AverageCpc"]
        )

    def test_strategies_add_with_params_dict(self):
        """Params as dict gets JSON-serialized before passing to CLI."""
        runner = _mock_runner({"Id": 101})
        params = {"AverageCpc": {"Cpc": 50000000}}
        with patch("server.tools.strategies.get_runner", return_value=runner):
            result = strategies_add(
                name="CpcStrategy", type="AverageCpc", params=params
            )
        assert result["Id"] == 101
        runner.run_json.assert_called_once_with(
            [
                "strategies",
                "add",
                "--name",
                "CpcStrategy",
                "--type",
                "AverageCpc",
                "--params",
                json.dumps(params),
            ]
        )


class TestStrategiesUpdate:
    """Tests for strategies_update."""

    def test_strategies_update(self):
        """Update passes id and changed fields to CLI."""
        runner = _mock_runner({"Id": 100, "Name": "Renamed"})
        with patch("server.tools.strategies.get_runner", return_value=runner):
            result = strategies_update(id=100, name="Renamed")
        assert result["Id"] == 100
        runner.run_json.assert_called_once_with(
            ["strategies", "update", "--id", "100", "--name", "Renamed"]
        )

    def test_strategies_update_requires_changes(self):
        """Update with no change fields returns missing_update_fields error."""
        runner = _mock_runner({"Id": 100})
        with patch("server.tools.strategies.get_runner", return_value=runner):
            result = strategies_update(id=100)
        assert result["error"] == "missing_update_fields"
        runner.run_json.assert_not_called()


class TestStrategiesArchive:
    """Tests for strategies_archive."""

    def test_strategies_archive(self):
        """Archive passes id to CLI."""
        runner = _mock_runner({"Id": 100})
        with patch("server.tools.strategies.get_runner", return_value=runner):
            result = strategies_archive(id=100)
        assert result["Id"] == 100
        runner.run_json.assert_called_once_with(
            ["strategies", "archive", "--id", "100"]
        )


class TestStrategiesUnarchive:
    """Tests for strategies_unarchive."""

    def test_strategies_unarchive(self):
        """Unarchive passes id to CLI."""
        runner = _mock_runner({"Id": 100})
        with patch("server.tools.strategies.get_runner", return_value=runner):
            result = strategies_unarchive(id=100)
        assert result["Id"] == 100
        runner.run_json.assert_called_once_with(
            ["strategies", "unarchive", "--id", "100"]
        )
