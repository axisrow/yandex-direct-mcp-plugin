"""Tests for creatives MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.creatives import creatives_list


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestCreativesList:
    """Tests for creatives_list tool."""

    def test_creatives_list_basic(self):
        """Test listing creatives by IDs."""
        mock_result = {"creatives": [{"id": 1, "name": "Creative 1"}]}
        with patch(
            "server.tools.creatives.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = creatives_list(ids="1")
            assert "creatives" in result
