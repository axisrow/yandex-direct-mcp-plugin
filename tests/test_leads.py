"""Tests for leads MCP tools (CLI 0.3.8 — --turbo-page-ids required)."""

from unittest.mock import patch

from server.tools.leads import leads_list

from tests.helpers import mock_runner


class TestLeadsList:
    """Tests for leads_list tool."""

    def test_leads_list_basic(self):
        mock_result = {"leads": [{"id": 1}]}
        runner = mock_runner(mock_result)
        with patch("server.tools.leads.get_runner", return_value=runner):
            result = leads_list(turbo_page_ids="42")
            assert "leads" in result
            runner.run_json.assert_called_once_with(
                ["leads", "get", "--format", "json", "--turbo-page-ids", "42"]
            )

    def test_leads_list_trims_ids(self):
        runner = mock_runner({"leads": []})
        with patch("server.tools.leads.get_runner", return_value=runner):
            leads_list(turbo_page_ids=" 1,2 ")
        runner.run_json.assert_called_once_with(
            ["leads", "get", "--format", "json", "--turbo-page-ids", "1,2"]
        )

    def test_leads_list_requires_turbo_page_ids(self):
        result = leads_list(turbo_page_ids="   ")
        assert result["error"] == "missing_turbo_page_ids"

    def test_leads_list_full_argv(self):
        runner = mock_runner({"leads": []})
        with patch("server.tools.leads.get_runner", return_value=runner):
            leads_list(
                turbo_page_ids="42",
                datetime_from="2026-01-01T00:00:00",
                datetime_to="2026-01-31T23:59:59",
                limit=100,
                fetch_all=True,
                fields="Id,Name",
            )
        argv = runner.run_json.call_args[0][0]
        assert "--datetime-from" in argv
        assert "--datetime-to" in argv
        assert "--limit" in argv and "100" in argv
        assert "--fetch-all" in argv
        assert "--fields" in argv
