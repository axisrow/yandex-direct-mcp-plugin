"""Tests for turbo pages MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.turbo_pages import turbo_pages_list


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestTurboPagesList:
    """Tests for turbo_pages_list tool."""

    def test_turbo_pages_list_basic(self):
        """Test listing turbo pages by IDs."""
        mock_result = {"turboPages": [{"id": 1, "name": "Page 1"}]}
        with patch(
            "server.tools.turbo_pages.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = turbo_pages_list(ids="1")
            assert "turboPages" in result
