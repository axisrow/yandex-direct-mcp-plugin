"""Tests for campaign MCP tools."""

from unittest.mock import patch

import pytest

from server.tools.campaigns import campaigns_list, campaigns_update, set_token_getter
from server.cli.runner import CliAuthError


@pytest.fixture(autouse=True)
def setup_token_getter():
    """Configure a mock token getter for all tests."""
    set_token_getter(lambda: "test-token")


@pytest.fixture
def mock_campaigns():
    """Sample campaign data."""
    return [
        {"Id": 12345, "Name": "Campaign_1", "State": "ON", "DailyBudget": 5000},
        {"Id": 67890, "Name": "Campaign_2", "State": "OFF", "DailyBudget": 3000},
        {"Id": 11111, "Name": "Campaign_3", "State": "ON", "DailyBudget": 7000},
    ]


class TestCampaignsList:
    """Test scenarios 7-8."""

    def test_list_all_campaigns(self, mock_campaigns):
        """Test 7: List all campaigns."""
        with patch("server.tools.campaigns.DirectCliRunner") as MockRunner:
            instance = MockRunner.return_value
            instance.run_json.return_value = mock_campaigns
            result = campaigns_list()
            assert len(result) == 3

    def test_list_active_campaigns(self, mock_campaigns):
        """Test 8: Filter by state=ON."""
        with patch("server.tools.campaigns.DirectCliRunner") as MockRunner:
            instance = MockRunner.return_value
            instance.run_json.return_value = mock_campaigns
            result = campaigns_list(state="ON")
            assert len(result) == 2
            assert all(c["State"] == "ON" for c in result)

    def test_list_empty_result(self):
        """Empty response returns empty list."""
        with patch("server.tools.campaigns.DirectCliRunner") as MockRunner:
            instance = MockRunner.return_value
            instance.run_json.return_value = []
            result = campaigns_list()
            assert result == []


class TestCampaignsUpdate:
    """Test scenarios 9-10."""

    def test_enable_campaign(self):
        """Test 9: Enable a campaign."""
        with patch("server.tools.campaigns.DirectCliRunner") as MockRunner:
            instance = MockRunner.return_value
            instance.run_json.return_value = {"Id": 67890, "State": "ON"}
            result = campaigns_update(id="67890", state="ON")
            assert result["success"] is True
            assert result["state"] == "ON"

    def test_disable_campaign(self):
        """Test 9: Disable a campaign."""
        with patch("server.tools.campaigns.DirectCliRunner") as MockRunner:
            instance = MockRunner.return_value
            instance.run_json.return_value = {"Id": 12345, "State": "OFF"}
            result = campaigns_update(id="12345", state="OFF")
            assert result["success"] is True

    def test_invalid_state(self):
        """Test: Invalid state value."""
        result = campaigns_update(id="12345", state="INVALID")
        assert "error" in result
        assert result["error"] == "invalid_state"

    def test_not_found_campaign(self):
        """Test 10: Nonexistent campaign."""
        with patch("server.tools.campaigns.DirectCliRunner") as MockRunner:
            instance = MockRunner.return_value
            instance.run_json.side_effect = Exception("Campaign 999 not found")
            result = campaigns_update(id="999", state="ON")
            assert "error" in result
            assert result["error"] == "not_found"

    def test_auth_error(self):
        """Test: Auth expired during update."""
        with patch("server.tools.campaigns.DirectCliRunner") as MockRunner:
            instance = MockRunner.return_value
            instance.run_json.side_effect = CliAuthError("Token expired")
            result = campaigns_update(id="12345", state="ON")
            assert result["error"] == "auth_expired"
