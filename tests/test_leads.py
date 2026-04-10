"""Tests for leads MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.leads import leads_list


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestLeadsList:
    """Tests for leads_list tool."""

    def test_leads_list_basic(self):
        """Test listing leads with campaign IDs."""
        mock_result = {"leads": [{"id": 1, "campaign_id": 12345}]}
        with patch(
            "server.tools.leads.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = leads_list(campaign_ids="12345")
            assert "leads" in result

    def test_leads_list_no_campaign_ids(self):
        """Test listing leads without campaign IDs (all campaigns)."""
        mock_result = {"leads": [{"id": 1, "campaign_id": 12345}]}
        with patch(
            "server.tools.leads.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = leads_list()
            assert "leads" in result

    def test_leads_list_batch_limit(self):
        """Test batch limit validation for leads_list."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = leads_list(campaign_ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_leads_list_passes_campaign_ids(self):
        """Verify CLI receives --campaign-ids flag."""
        runner = MagicMock()
        runner.run_json.return_value = {}
        with patch("server.tools.leads.get_runner", return_value=runner):
            leads_list(campaign_ids="123,456")
            call_args = runner.run_json.call_args[0][0]
            assert "--campaign-ids" in call_args
            assert "123,456" in call_args
