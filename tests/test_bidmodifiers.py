"""Tests for bid modifier MCP tools."""

from unittest.mock import patch, MagicMock

import pytest

import server.tools
from server.tools.bidmodifiers import (
    bidmodifiers_list,
    bidmodifiers_set,
    bidmodifiers_toggle,
    bidmodifiers_delete,
)


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


SAMPLE_BIDMODIFIERS = [
    {"Id": 1, "CampaignId": 12345, "Type": "MULTIPLIER", "Value": 100},
]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestBidModifiersList:
    """Tests for bidmodifiers_list tool."""

    def test_bidmodifiers_list_success(self):
        """Test listing bid modifiers for campaigns."""
        with patch(
            "server.tools.bidmodifiers.get_runner", return_value=_mock_runner(SAMPLE_BIDMODIFIERS)
        ):
            result = bidmodifiers_list(campaign_ids="12345")
            assert len(result) == 1
            assert result[0]["CampaignId"] == 12345

    def test_bidmodifiers_list_batch_limit(self):
        """Test batch limit validation for bidmodifiers_list."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = bidmodifiers_list(campaign_ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"


class TestBidModifiersSet:
    """Tests for bidmodifiers_set tool."""

    def test_bidmodifiers_set_success(self):
        """Test setting bid modifier successfully."""
        mock_result = {"success": True}
        with patch("server.tools.bidmodifiers.get_runner", return_value=_mock_runner(mock_result)):
            result = bidmodifiers_set(campaign_id="12345", modifier_type="MULTIPLIER", value="100")
            assert result["success"] is True

    def test_bidmodifiers_set_invalid_type(self):
        """Test bidmodifiers_set with invalid modifier type."""
        result = bidmodifiers_set(campaign_id="12345", modifier_type="INVALID", value="100")
        assert "error" in result
        assert result["error"] == "invalid_state"

    def test_bidmodifiers_set_invalid_value_negative(self):
        """Test bidmodifiers_set with negative value."""
        result = bidmodifiers_set(campaign_id="12345", modifier_type="MULTIPLIER", value="-100")
        assert "error" in result
        assert result["error"] == "invalid_value"

    def test_bidmodifiers_set_invalid_value_zero(self):
        """Test bidmodifiers_set with zero value."""
        result = bidmodifiers_set(campaign_id="12345", modifier_type="MULTIPLIER", value="0")
        assert "error" in result
        assert result["error"] == "invalid_value"

    def test_bidmodifiers_set_invalid_value_non_numeric(self):
        """Test bidmodifiers_set with non-numeric value."""
        result = bidmodifiers_set(campaign_id="12345", modifier_type="MULTIPLIER", value="abc")
        assert "error" in result
        assert result["error"] == "invalid_value"


class TestBidModifiersToggle:
    """Tests for bidmodifiers_toggle tool."""

    def test_bidmodifiers_toggle_enable(self):
        """Test enabling a bid modifier."""
        mock_result = {"success": True}
        with patch("server.tools.bidmodifiers.get_runner", return_value=_mock_runner(mock_result)) as mock:
            result = bidmodifiers_toggle(id="1", enabled=True)
            assert result["success"] is True
            # Verify the CLI command uses lowercase true
            call_args = mock.return_value.run_json.call_args[0][0]
            assert "--enabled" in call_args
            assert "true" in call_args

    def test_bidmodifiers_toggle_disable(self):
        """Test disabling a bid modifier."""
        mock_result = {"success": True}
        with patch("server.tools.bidmodifiers.get_runner", return_value=_mock_runner(mock_result)) as mock:
            result = bidmodifiers_toggle(id="1", enabled=False)
            assert result["success"] is True
            # Verify the CLI command uses lowercase false
            call_args = mock.return_value.run_json.call_args[0][0]
            assert "--enabled" in call_args
            assert "false" in call_args


class TestBidModifiersDelete:
    """Tests for bidmodifiers_delete tool."""

    def test_bidmodifiers_delete_success(self):
        """Test deleting bid modifiers successfully."""
        mock_result = {"success": True}
        with patch("server.tools.bidmodifiers.get_runner", return_value=_mock_runner(mock_result)):
            result = bidmodifiers_delete(ids="1,2,3")
            assert result["success"] is True

    def test_bidmodifiers_delete_batch_limit(self):
        """Test batch limit validation for bidmodifiers_delete."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = bidmodifiers_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
