"""Tests for reports MCP tool."""

import json
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

import pytest

import server.tools
from server.tools.reports import (
    CUSTOM_REPORT_TIMEOUT_SECONDS,
    DEFAULT_REPORT_FIELDS,
    DEFAULT_REPORT_NAME,
    DEFAULT_REPORT_TYPE,
    reports_custom,
    reports_get,
    reports_list_types,
)


@pytest.fixture(autouse=True)
def setup():
    server.tools.set_token_getter(lambda: "test-token")


SAMPLE_REPORTS = [
    {
        "CampaignName": "Sample campaign",
        "Impressions": 15420,
        "Clicks": 312,
        "Cost": 1000.00,
        "Conversions": 14,
    },
]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def test_reports_get():
    """Test 16: Statistics for date range."""
    runner = _mock_runner(SAMPLE_REPORTS)
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_get(date_from="2026-03-30", date_to="2026-04-06")
        assert len(result) == 1
        assert result[0]["Impressions"] == 15420
        runner.run_json.assert_called_once_with(
            [
                "reports",
                "get",
                "--type",
                DEFAULT_REPORT_TYPE,
                "--from",
                "2026-03-30",
                "--to",
                "2026-04-06",
                "--name",
                DEFAULT_REPORT_NAME,
                "--fields",
                DEFAULT_REPORT_FIELDS,
                "--format",
                "json",
            ]
        )


def test_reports_no_dates():
    """Reports without date range."""
    runner = _mock_runner(SAMPLE_REPORTS)
    today = date.today()
    expected_from = (today - timedelta(days=8)).isoformat()
    expected_to = today.isoformat()
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_get()
        assert len(result) == 1
        runner.run_json.assert_called_once_with(
            [
                "reports",
                "get",
                "--type",
                DEFAULT_REPORT_TYPE,
                "--from",
                expected_from,
                "--to",
                expected_to,
                "--name",
                DEFAULT_REPORT_NAME,
                "--fields",
                DEFAULT_REPORT_FIELDS,
                "--format",
                "json",
            ]
        )


def test_reports_only_date_to():
    """Missing start date uses the same default 8-day window."""
    runner = _mock_runner(SAMPLE_REPORTS)
    with patch("server.tools.reports.get_runner", return_value=runner):
        reports_get(date_to="2026-04-08")
        runner.run_json.assert_called_once_with(
            [
                "reports",
                "get",
                "--type",
                DEFAULT_REPORT_TYPE,
                "--from",
                "2026-03-31",
                "--to",
                "2026-04-08",
                "--name",
                DEFAULT_REPORT_NAME,
                "--fields",
                DEFAULT_REPORT_FIELDS,
                "--format",
                "json",
            ]
        )


def test_reports_only_date_from():
    """Missing end date uses the same default 8-day window."""
    runner = _mock_runner(SAMPLE_REPORTS)
    with patch("server.tools.reports.get_runner", return_value=runner):
        reports_get(date_from="2026-03-30")
        runner.run_json.assert_called_once_with(
            [
                "reports",
                "get",
                "--type",
                DEFAULT_REPORT_TYPE,
                "--from",
                "2026-03-30",
                "--to",
                "2026-04-07",
                "--name",
                DEFAULT_REPORT_NAME,
                "--fields",
                DEFAULT_REPORT_FIELDS,
                "--format",
                "json",
            ]
        )


def test_reports_list_types():
    expected_types = [
        "CAMPAIGN_PERFORMANCE_REPORT",
        "ADGROUP_PERFORMANCE_REPORT",
        "AD_PERFORMANCE_REPORT",
        "CRITERIA_PERFORMANCE_REPORT",
        "CUSTOM_REPORT",
        "REACH_AND_FREQUENCY_CAMPAIGN_REPORT",
        "SEARCH_QUERY_PERFORMANCE_REPORT",
    ]
    runner = _mock_runner(expected_types)
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_list_types()
        assert len(result) == 7
        assert "CAMPAIGN_PERFORMANCE_REPORT" in result
        runner.run_json.assert_called_once_with(["reports", "list-types"])


def test_reports_get_empty():
    """Test report with empty result."""
    with patch("server.tools.reports.get_runner", return_value=_mock_runner([])):
        result = reports_get(date_from="2026-03-30", date_to="2026-04-06")
        assert result == []


def test_reports_get_auth_error():
    """Test auth error during report retrieval."""
    from server.cli.runner import CliAuthError

    runner = MagicMock()
    runner.run_json.side_effect = CliAuthError("Token expired")
    with (
        patch("server.tools.reports.get_runner", return_value=runner),
        patch("server.tools._try_refresh_token", return_value=None),
    ):
        result = reports_get(date_from="2026-03-30", date_to="2026-04-06")
        assert result["error"] == "auth_expired"


# --- reports_custom -----------------------------------------------------


def _custom_args(call):
    """Extract the positional args list from runner.run_json mock call."""
    args, kwargs = call
    return args[0]


def test_reports_custom_month_with_goals():
    """User scenario: 2 years, by months, filter by goal IDs."""
    runner = _mock_runner([{"Month": "2024-05", "Goals": "12345", "Conversions": 4}])
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Month,CampaignName,Impressions,Clicks,Cost,Goals,Conversions",
            date_from="2024-04-29",
            date_to="2026-04-29",
            goal_ids="12345,67890",
            order_by=["Month:ASC"],
        )

    assert isinstance(result, list)
    runner.run_json.assert_called_once()
    args = _custom_args(runner.run_json.call_args)
    assert args[:4] == ["reports", "get", "--type", "CUSTOM_REPORT"]
    # Date arguments
    i_from = args.index("--from")
    assert args[i_from + 1] == "2024-04-29"
    i_to = args.index("--to")
    assert args[i_to + 1] == "2026-04-29"
    # Fields
    i_fields = args.index("--fields")
    assert (
        args[i_fields + 1]
        == "Month,CampaignName,Impressions,Clicks,Cost,Goals,Conversions"
    )
    # Goal filter materialised
    assert "--filter" in args
    i_filter = args.index("--filter")
    assert args[i_filter + 1] == "Goals:IN:12345,67890"
    # Order-by passed through
    i_order = args.index("--order-by")
    assert args[i_order + 1] == "Month:ASC"
    # Auto-name with prefix
    i_name = args.index("--name")
    assert args[i_name + 1].startswith("mcp_custom_")
    # Default in-memory format
    assert args[-2:] == ["--format", "json"]
    # Higher timeout for long-period custom reports
    assert runner.run_json.call_args.kwargs["timeout"] == CUSTOM_REPORT_TIMEOUT_SECONDS


def test_reports_custom_conflicting_goal_filter():
    """Cannot pass both goal_ids and an explicit Goals: filter."""
    result = reports_custom(
        field_names="Month,Goals,Conversions",
        date_from="2024-01-01",
        date_to="2024-02-01",
        goal_ids="111",
        filters=["Goals:IN:222"],
    )
    assert result["error"] == "unknown"
    assert "conflicting goal filter" in result["message"]


def test_reports_custom_output_path(tmp_path):
    """output_path returns metadata, not the data array."""
    out = tmp_path / "report.json"
    runner = MagicMock()

    def fake_run_json(args, **kwargs):
        # Simulate direct-cli writing the file
        output_arg = args[args.index("--output") + 1]
        assert output_arg == str(out.resolve())
        out.write_text(json.dumps([{"x": 1}, {"x": 2}, {"x": 3}]))
        return {"status": "ok"}

    runner.run_json.side_effect = fake_run_json
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            output_path=str(out),
            response_format="json",
        )

    args = _custom_args(runner.run_json.call_args)
    assert "--output" in args and args[args.index("--output") + 1] == str(out.resolve())
    # response_format wins over the implicit JSON default
    assert args[-2:] == ["--format", "json"]
    # Result is metadata, not rows
    assert result == {
        "output_path": str(out.resolve()),
        "rows_written": 3,
        "report_type": "CUSTOM_REPORT",
        "format": "json",
    }


def test_reports_custom_output_path_rejects_unsafe_location():
    """output_path must stay under plugin data or temp roots."""
    runner = _mock_runner([])
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            output_path="/etc/cron.d/direct-report.json",
        )

    assert result["error"] == "unknown"
    assert "output_path must be under one of" in result["message"]
    runner.run_json.assert_not_called()


def test_reports_custom_output_path_uncountable_file(tmp_path):
    """Existing files that cannot be counted return rows_written=None."""
    out = tmp_path / "report.json"
    runner = MagicMock()

    def fake_run_json(args, **kwargs):
        output_arg = args[args.index("--output") + 1]
        assert output_arg == str(out.resolve())
        out.write_text("not json")
        return {"status": "ok"}

    runner.run_json.side_effect = fake_run_json
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            output_path=str(out),
            response_format="json",
        )

    assert result["rows_written"] is None


def test_reports_custom_output_path_counts_large_json_stream(tmp_path):
    """JSON rows are counted without materializing the whole output file."""
    out = tmp_path / "report.json"
    runner = MagicMock()

    def fake_run_json(args, **kwargs):
        output_arg = args[args.index("--output") + 1]
        assert output_arg == str(out.resolve())
        with out.open("w", encoding="utf-8") as f:
            f.write("[")
            for i in range(1000):
                if i:
                    f.write(",")
                f.write(json.dumps({"i": i, "nested": {"comma": "a,b"}}))
            f.write("]")
        return {"status": "ok"}

    runner.run_json.side_effect = fake_run_json
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            output_path=str(out),
            response_format="json",
        )

    assert result["rows_written"] == 1000


def test_reports_custom_dry_run():
    """dry_run threads --dry-run and returns the structured preview payload."""
    fake_body = {
        "params": {
            "SelectionCriteria": {"DateFrom": "2026-01-01", "DateTo": "2026-01-31"},
            "FieldNames": ["Date", "Cost"],
        }
    }
    runner = _mock_runner({"headers": {}, "body": fake_body})
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            dry_run=True,
        )

    args = _custom_args(runner.run_json.call_args)
    assert "--dry-run" in args
    assert result["dry_run"] is True
    assert result["command"][0] == "direct"
    assert "reports" in result["command"] and "get" in result["command"]
    assert result["request_body"] == fake_body


def test_reports_custom_dry_run_passthrough_when_no_body_key():
    """If runner returns a dict without 'body', it's passed through as request_body."""
    raw = {"unexpected": "shape"}
    runner = _mock_runner(raw)
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            dry_run=True,
        )
    assert result["request_body"] == raw


def test_reports_custom_invalid_request_hint():
    """error_code=8000 from CLI is surfaced with a helpful hint pointing to dry_run."""
    from server.cli.runner import CliError

    runner = MagicMock()
    runner.run_json.side_effect = CliError(
        "direct failed (exit 1): ✗ request_id=abc, error_code=8000, "
        "error_string=Invalid request, error_detail=Field contains an invalid enumeration value",
        error_code=8000,
        stderr="✗ request_id=abc, error_code=8000, error_string=Invalid request",
    )
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Month,GoalsIds",  # GoalsIds is a typo
            date_from="2026-04-01",
            date_to="2026-04-29",
        )

    assert result["error"] == "invalid_request"
    assert "error_code=8000" in result["message"]
    assert result["hint"] is not None
    assert "dry_run=True" in result["hint"]


def test_reports_custom_date_range_type():
    """date_range_type without explicit dates uses --date-range-type."""
    runner = _mock_runner([])
    with patch("server.tools.reports.get_runner", return_value=runner):
        reports_custom(
            field_names="Date,Cost",
            date_range_type="last_30_days",
        )

    args = _custom_args(runner.run_json.call_args)
    assert "--date-range-type" in args
    assert args[args.index("--date-range-type") + 1] == "last_30_days"
    assert "--from" not in args and "--to" not in args


def test_reports_custom_date_range_type_conflict():
    """date_range_type and explicit dates are mutually exclusive."""
    result = reports_custom(
        field_names="Date,Cost",
        date_from="2026-01-01",
        date_range_type="last_7_days",
    )
    assert result["error"] == "unknown"
    assert "date_range_type OR explicit" in result["message"]


def test_reports_custom_requires_complete_explicit_date_range():
    """Custom reports reject partial explicit date ranges."""
    assert (
        "pass both date_from and date_to"
        in reports_custom(field_names="Date,Cost", date_from="2026-01-01")["message"]
    )
    assert (
        "pass both date_from and date_to"
        in reports_custom(field_names="Date,Cost", date_to="2026-01-31")["message"]
    )


def test_reports_custom_override_report_type():
    """report_type override propagates to --type."""
    runner = _mock_runner([])
    with patch("server.tools.reports.get_runner", return_value=runner):
        reports_custom(
            field_names="CampaignName,Criterion,Cost",
            report_type="CRITERIA_PERFORMANCE_REPORT",
            date_from="2026-03-01",
            date_to="2026-03-31",
        )

    args = _custom_args(runner.run_json.call_args)
    assert args[args.index("--type") + 1] == "CRITERIA_PERFORMANCE_REPORT"


def test_reports_custom_unknown_report_type():
    """Unknown report_type is delegated to direct-cli validation."""
    from server.cli.runner import CliError

    runner = MagicMock()
    runner.run_json.side_effect = CliError("direct rejected report type")
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            report_type="MADE_UP_REPORT",
        )

    assert result["error"] == "unknown"
    assert "direct rejected report type" in result["message"]
    args = _custom_args(runner.run_json.call_args)
    assert args[args.index("--type") + 1] == "MADE_UP_REPORT"


def test_reports_custom_include_vat_false():
    """include_vat=False produces --no-include-vat."""
    runner = _mock_runner([])
    with patch("server.tools.reports.get_runner", return_value=runner):
        reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            include_vat=False,
            include_discount=False,
        )

    args = _custom_args(runner.run_json.call_args)
    assert "--no-include-vat" in args
    assert "--no-include-discount" in args
    assert "--include-vat" not in args


def test_reports_custom_multiple_order_by():
    """Each order_by element becomes a separate --order-by flag."""
    runner = _mock_runner([])
    with patch("server.tools.reports.get_runner", return_value=runner):
        reports_custom(
            field_names="Month,CampaignName,Cost",
            date_from="2024-01-01",
            date_to="2024-12-31",
            order_by=["Month:ASC", "Cost:DESC"],
        )

    args = _custom_args(runner.run_json.call_args)
    order_indices = [i for i, a in enumerate(args) if a == "--order-by"]
    assert len(order_indices) == 2
    assert args[order_indices[0] + 1] == "Month:ASC"
    assert args[order_indices[1] + 1] == "Cost:DESC"


def test_reports_custom_in_contract():
    """The new tool is registered in the public MCP contract."""
    from server.contract import (
        DIRECT_API_TOOL_NAMES,
        PUBLIC_TOOL_NAMES,
        REPORTS_SPEC_EXTRA_TOOLS,
    )

    assert "reports_custom" in PUBLIC_TOOL_NAMES
    assert "reports_custom" in DIRECT_API_TOOL_NAMES
    assert any(t.public_name == "reports_custom" for t in REPORTS_SPEC_EXTRA_TOOLS)
