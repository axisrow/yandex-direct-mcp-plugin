"""Tests for ad group MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.adgroups import (
    adgroups_list,
    adgroups_add,
    adgroups_update,
    adgroups_delete,
)


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


SAMPLE_ADGROUPS = [
    {"Id": 1, "Name": "Ad Group 1", "CampaignId": 12345},
    {"Id": 2, "Name": "Ad Group 2", "CampaignId": 12345},
]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestAdgroupsList:
    """Tests for adgroups_list tool."""

    def test_adgroups_list_by_campaign(self):
        """Test listing ad groups by campaign."""
        with patch(
            "server.tools.adgroups.get_runner",
            return_value=_mock_runner(SAMPLE_ADGROUPS),
        ):
            result = adgroups_list(campaign_ids="12345")
            assert len(result) == 2
            assert result[0]["Id"] == 1

    def test_adgroups_list_empty(self):
        """Test empty ad groups list."""
        with patch(
            "server.tools.adgroups.get_runner",
            return_value=_mock_runner([]),
        ):
            result = adgroups_list(campaign_ids="12345")
            assert result == []

    def test_adgroups_list_batch_limit(self):
        """Test batch limit validation."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = adgroups_list(campaign_ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"


class TestAdgroupsAdd:
    """Tests for adgroups_add tool."""

    def test_adgroups_add_success(self):
        """Test adding an ad group successfully."""
        mock_result = {"Id": 123, "Name": "New Ad Group"}
        with patch(
            "server.tools.adgroups.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = adgroups_add(campaign_id="12345", name="New Ad Group")
            assert result["Id"] == 123

    def test_adgroups_add_with_type(self):
        """Test adding ad group with type parameter."""
        runner = MagicMock()
        runner.run_json.return_value = {"Id": 124}
        with patch(
            "server.tools.adgroups.get_runner",
            return_value=runner,
        ):
            adgroups_add(
                campaign_id="12345",
                name="Test",
                type="MOBILE_AD_GROUP",
            )
            call_args = runner.run_json.call_args[0][0]
            assert "--type" in call_args
            assert "MOBILE_AD_GROUP" in call_args


class TestAdgroupsUpdate:
    """Tests for adgroups_update tool."""

    def test_adgroups_update_name(self):
        """Test updating an ad group name."""
        mock_result = {"Id": 123, "Name": "Updated Name"}
        with patch(
            "server.tools.adgroups.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = adgroups_update(id="123", name="Updated Name")
            assert result["Id"] == 123

    def test_adgroups_update_requires_fields(self):
        """Test that updating with no fields returns error."""
        result = adgroups_update(id="123")
        assert "error" in result
        assert result["error"] == "missing_update_fields"

    def test_adgroups_update_with_status(self):
        """Test updating with status."""
        runner = MagicMock()
        runner.run_json.return_value = {"Id": 123}
        with patch(
            "server.tools.adgroups.get_runner",
            return_value=runner,
        ):
            adgroups_update(id="123", status="SUSPENDED")
            call_args = runner.run_json.call_args[0][0]
            assert "--status" in call_args
            assert "SUSPENDED" in call_args


class TestAdgroupsDelete:
    """Tests for adgroups_delete tool."""

    def test_adgroups_delete_success(self):
        """Test deleting ad groups successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.adgroups.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = adgroups_delete(ids="1")
            assert result["success"] is True

    def test_adgroups_delete_batch_limit(self):
        """Test batch limit validation."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = adgroups_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
