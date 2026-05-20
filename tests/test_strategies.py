"""Tests for strategy MCP tools."""

from unittest.mock import MagicMock, patch


from server.tools.strategies import (
    strategies_add,
    strategies_archive,
    strategies_list,
    strategies_unarchive,
    strategies_update,
)


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
            strategies_list(is_archived="NO")
        runner.run_json.assert_called_once_with(
            ["strategies", "get", "--format", "json", "--is-archived", "NO"]
        )

    def test_strategies_list_invalid_is_archived(self):
        """is_archived must be YES|NO."""
        result = strategies_list(is_archived="maybe")
        assert result["error"] == "invalid_is_archived"

    def test_strategies_list_batch_limit(self):
        """11 IDs triggers batch_limit error."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = strategies_list(ids=ids)
        assert result["error"] == "batch_limit"


class TestStrategiesAdd:
    """Tests for strategies_add (CLI 0.3.8 typed flags)."""

    def test_strategies_add(self):
        """Basic add with required fields."""
        runner = _mock_runner({"Id": 100, "Name": "MyStrategy"})
        with patch("server.tools.strategies.get_runner", return_value=runner):
            result = strategies_add(name="MyStrategy", type="AverageCpc")
        assert result["Id"] == 100
        runner.run_json.assert_called_once_with(
            ["strategies", "add", "--name", "MyStrategy", "--type", "AverageCpc"]
        )

    def test_strategies_add_typed_money_fields(self):
        """Money fields pass through as separate typed flags."""
        runner = _mock_runner({"Id": 101})
        with patch("server.tools.strategies.get_runner", return_value=runner):
            strategies_add(
                name="CpcStrategy",
                type="AverageCpc",
                average_cpc=50000000,
                weekly_spend_limit=200000000,
                bid_ceiling=70000000,
                counter_ids="11,22",
                attribution_model="LYDC",
            )
        argv = runner.run_json.call_args[0][0]
        assert "--average-cpc" in argv and "50000000" in argv
        assert "--weekly-spend-limit" in argv
        assert "--bid-ceiling" in argv
        assert "--counter-ids" in argv and "11,22" in argv
        assert "--attribution-model" in argv and "LYDC" in argv

    def test_strategies_add_priority_goals_repeats(self):
        """Each priority_goals item becomes a separate --priority-goal flag."""
        runner = _mock_runner({"Id": 102})
        with patch("server.tools.strategies.get_runner", return_value=runner):
            strategies_add(
                name="PayForConv",
                type="PayForConversion",
                priority_goals=["123:1000000", "456:2000000"],
            )
        argv = runner.run_json.call_args[0][0]
        assert argv.count("--priority-goal") == 2

    def test_strategies_add_dry_run(self):
        runner = _mock_runner({"_dry_run": True})
        with patch("server.tools.strategies.get_runner", return_value=runner):
            strategies_add(name="x", type="AverageCpc", dry_run=True)
            assert "--dry-run" in runner.run_json.call_args[0][0]


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

    def test_strategies_archive_dry_run(self):
        runner = _mock_runner({"_dry_run": True})
        with patch("server.tools.strategies.get_runner", return_value=runner):
            strategies_archive(id=100, dry_run=True)
            assert "--dry-run" in runner.run_json.call_args[0][0]


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

    def test_strategies_unarchive_dry_run(self):
        runner = _mock_runner({"_dry_run": True})
        with patch("server.tools.strategies.get_runner", return_value=runner):
            strategies_unarchive(id=100, dry_run=True)
            assert "--dry-run" in runner.run_json.call_args[0][0]
