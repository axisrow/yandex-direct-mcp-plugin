"""Tests for turbo pages MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.turbo_pages import turbo_pages_list, turbo_pages_add


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

    def test_turbo_pages_list_no_ids(self):
        """Test listing all turbo pages."""
        mock_result = {"turboPages": []}
        with patch(
            "server.tools.turbo_pages.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = turbo_pages_list()
            assert "turboPages" in result


class TestTurboPagesAdd:
    """Tests for turbo_pages_add tool."""

    def test_turbo_pages_add_basic(self):
        """Test adding a turbo page."""
        mock_result = {"id": 123, "name": "Test Page"}
        runner = MagicMock()
        runner.run_json.return_value = mock_result
        with patch(
            "server.tools.turbo_pages.get_runner",
            return_value=runner,
        ):
            result = turbo_pages_add(name="Test Page", url="https://example.com/page")
            assert result["id"] == 123
            call_args = runner.run_json.call_args[0][0]
            assert "--name" in call_args
            assert "--url" in call_args

    def test_turbo_pages_add_with_extra_json(self):
        """Test adding turbo page with extra JSON."""
        runner = MagicMock()
        runner.run_json.return_value = {"id": 124}
        with patch(
            "server.tools.turbo_pages.get_runner",
            return_value=runner,
        ):
            turbo_pages_add(
                name="Test",
                url="https://example.com/page",
                extra_json='{"Description":"test"}',
            )
            call_args = runner.run_json.call_args[0][0]
            assert "--json" in call_args
