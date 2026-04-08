"""Tests for changes MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.changes import (
    changes_check,
    changes_checkcamp,
    changes_checkdict,
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


class TestChangesCheck:
    """Test scenarios for changes_check."""

    def test_check_changes(self):
        """Test checking changes since timestamp."""
        mock_result = {
            "Campaigns": [{"Id": 12345, "Changes": "State"}],
            "Timestamp": "2026-01-01T00:00:00Z",
        }
        with patch(
            "server.tools.changes.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = changes_check(timestamp="2026-01-01T00:00:00Z")
            assert result == mock_result

    def test_check_empty_changes(self):
        """Test with no changes."""
        mock_result = {"Campaigns": []}
        with patch(
            "server.tools.changes.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = changes_check(timestamp="2026-01-01T00:00:00Z")
            assert result == mock_result


class TestChangesCheckCamp:
    """Test scenarios for changes_checkcamp."""

    def test_check_campaign_changes(self):
        """Test checking changes for specific campaigns."""
        mock_result = {
            "Campaigns": [{"Id": 12345, "Changes": "DailyBudget"}],
            "Timestamp": "2026-01-01T00:00:00Z",
        }
        with patch(
            "server.tools.changes.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = changes_checkcamp(
                campaign_ids="12345,67890", timestamp="2026-01-01T00:00:00Z"
            )
            assert result == mock_result

    def test_check_campaign_changes_single_id(self):
        """Test checking changes for single campaign."""
        mock_result = {
            "Campaigns": [{"Id": 12345, "Changes": "Name"}],
            "Timestamp": "2026-01-01T00:00:00Z",
        }
        with patch(
            "server.tools.changes.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = changes_checkcamp(
                campaign_ids="12345", timestamp="2026-01-01T00:00:00Z"
            )
            assert result == mock_result

    def test_check_campaign_changes_batch_limit(self):
        """Test batch limit validation."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = changes_checkcamp(campaign_ids=ids, timestamp="2026-01-01T00:00:00Z")
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_check_campaign_changes_max_ids(self):
        """Test with exactly 10 IDs (boundary case)."""
        mock_result = {"Campaigns": []}
        with patch(
            "server.tools.changes.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            ids = ",".join(str(i) for i in range(1, 11))  # 10 IDs
            result = changes_checkcamp(
                campaign_ids=ids, timestamp="2026-01-01T00:00:00Z"
            )
            assert result == mock_result


class TestChangesCheckDict:
    """Test scenarios for changes_checkdict."""

    def test_check_dictionary_changes(self):
        """Test checking dictionary changes."""
        mock_result = {
            "Dictionaries": ["GeographyRegions"],
            "Timestamp": "2026-01-01T00:00:00Z",
        }
        with patch(
            "server.tools.changes.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = changes_checkdict(timestamp="2026-01-01T00:00:00Z")
            assert result == mock_result

    def test_check_dictionary_changes_no_updates(self):
        """Test with no dictionary updates."""
        mock_result = {"Dictionaries": []}
        with patch(
            "server.tools.changes.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = changes_checkdict(timestamp="2026-01-01T00:00:00Z")
            assert result == mock_result
