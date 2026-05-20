"""Tests for turbo pages MCP tools."""

from unittest.mock import MagicMock, patch


from server.tools.turbo_pages import turbo_pages_list


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

    def test_turbo_pages_list_trims_ids(self):
        """Test turbo page IDs are normalized before argv construction."""
        runner = MagicMock()
        runner.run_json.return_value = {"turboPages": []}
        with patch("server.tools.turbo_pages.get_runner", return_value=runner):
            turbo_pages_list(ids=" 1 ")

        runner.run_json.assert_called_once_with(
            ["turbopages", "get", "--format", "json", "--ids", "1"]
        )

    def test_turbo_pages_list_full_argv(self):
        """Test all optional flags pass through to CLI."""
        runner = MagicMock()
        runner.run_json.return_value = {"turboPages": []}
        with patch("server.tools.turbo_pages.get_runner", return_value=runner):
            turbo_pages_list(
                ids="1",
                bound_with_hrefs="https://example.com",
                limit=50,
                fetch_all=True,
                fields="Id,Name",
                dry_run=True,
            )
        argv = runner.run_json.call_args[0][0]
        assert "--bound-with-hrefs" in argv
        assert "--limit" in argv and "50" in argv
        assert "--fetch-all" in argv
        assert "--fields" in argv and "Id,Name" in argv
        assert "--dry-run" in argv

    def test_turbo_pages_list_empty_result(self):
        """Test empty response returns empty dict."""
        with patch(
            "server.tools.turbo_pages.get_runner",
            return_value=_mock_runner({"turboPages": []}),
        ):
            result = turbo_pages_list()
            assert result == {"turboPages": []}

    def test_turbo_pages_list_ignores_blank_ids(self):
        """Test blank ids behave like no filter."""
        runner = MagicMock()
        runner.run_json.return_value = {"turboPages": []}
        with patch("server.tools.turbo_pages.get_runner", return_value=runner):
            turbo_pages_list(ids="   ")
            call_args = runner.run_json.call_args[0][0]
            assert "--ids" not in call_args
