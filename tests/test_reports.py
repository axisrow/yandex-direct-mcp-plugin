"""Tests for reports MCP tool."""

import json
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from server.tools.reports import (
    CUSTOM_REPORT_TIMEOUT_SECONDS,
    DEFAULT_REPORT_FIELDS,
    DEFAULT_REPORT_NAME,
    DEFAULT_REPORT_TYPE,
    reports_custom,
    reports_get,
    reports_list_types,
)

from tests.helpers import completed, mock_runner

SAMPLE_REPORTS = [
    {
        "CampaignName": "Sample campaign",
        "Impressions": 15420,
        "Clicks": 312,
        "Cost": 1000.00,
        "Conversions": 14,
    },
]


def test_reports_get():
    """Test 16: Statistics for date range."""
    runner = mock_runner(SAMPLE_REPORTS)
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
    runner = mock_runner(SAMPLE_REPORTS)
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
    runner = mock_runner(SAMPLE_REPORTS)
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
    runner = mock_runner(SAMPLE_REPORTS)
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
    runner = mock_runner(expected_types)
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_list_types()
        assert len(result) == 7
        assert "CAMPAIGN_PERFORMANCE_REPORT" in result
        runner.run_json.assert_called_once_with(["reports", "list-types"])


def test_reports_get_empty():
    """Test report with empty result."""
    with patch("server.tools.reports.get_runner", return_value=mock_runner([])):
        result = reports_get(date_from="2026-03-30", date_to="2026-04-06")
        assert result == []


def test_reports_get_auth_error():
    """Test auth error during report retrieval."""
    from server.cli.runner import CliAuthError

    runner = MagicMock()
    runner.run_json.side_effect = CliAuthError("Token expired")
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_get(date_from="2026-03-30", date_to="2026-04-06")
        assert result["error"] == "auth_expired"


def test_reports_get_invalid_date_format():
    result = reports_get(date_from="2026/03/30", date_to="2026-04-06")
    assert result["error"] == "invalid_date_format"
    assert "date_from" in result["message"]


# --- reports_custom -----------------------------------------------------


def _custom_args(call):
    """Extract the positional args list from runner.run_json mock call."""
    args, kwargs = call
    return args[0]


def test_reports_custom_month_with_goals():
    """User scenario: 2 years, by months, by goal IDs.

    `goal_ids` must thread to direct CLI's native `--goals` flag (added in
    direct-cli 0.3.2). The CLI emits it as top-level `ReportDefinition.Goals`,
    NOT as a `Filter[Goals:IN:...]` entry — Reports API rejects the latter
    with `error_code=8000`.
    """
    runner = mock_runner([{"Month": "2024-05", "Goals": "12345", "Conversions": 4}])
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
    i_from = args.index("--from")
    assert args[i_from + 1] == "2024-04-29"
    i_to = args.index("--to")
    assert args[i_to + 1] == "2026-04-29"
    i_fields = args.index("--fields")
    assert (
        args[i_fields + 1]
        == "Month,CampaignName,Impressions,Clicks,Cost,Goals,Conversions"
    )
    # goal_ids → native --goals, NOT --filter Goals:IN:...
    i_goals = args.index("--goals")
    assert args[i_goals + 1] == "12345,67890"
    assert not any(isinstance(a, str) and a.startswith("Goals:") for a in args), (
        "goal_ids must not produce a Filter entry; got args=" + repr(args)
    )
    i_order = args.index("--order-by")
    assert args[i_order + 1] == "Month:ASC"
    i_name = args.index("--name")
    assert args[i_name + 1].startswith("mcp_custom_")
    assert args[-2:] == ["--format", "json"]
    assert runner.run_json.call_args.kwargs["timeout"] == CUSTOM_REPORT_TIMEOUT_SECONDS


def test_reports_custom_goal_ids_only_no_filter_arg():
    """`goal_ids` without other filters must not introduce any --filter."""
    runner = mock_runner([])
    with patch("server.tools.reports.get_runner", return_value=runner):
        reports_custom(
            field_names="Date,Goals,Conversions",
            date_from="2026-01-01",
            date_to="2026-01-31",
            goal_ids="111",
        )
    args = _custom_args(runner.run_json.call_args)
    assert "--goals" in args
    assert args[args.index("--goals") + 1] == "111"
    assert "--filter" not in args


def test_reports_custom_goal_ids_with_other_filters_pass_through():
    """`goal_ids` and unrelated filters must coexist: --goals AND --filter both emit."""
    runner = mock_runner([])
    with patch("server.tools.reports.get_runner", return_value=runner):
        reports_custom(
            field_names="Date,Device,Goals,Conversions",
            date_from="2026-01-01",
            date_to="2026-01-31",
            goal_ids="111",
            filters=["Device:IN:DESKTOP"],
        )
    args = _custom_args(runner.run_json.call_args)
    assert args[args.index("--goals") + 1] == "111"
    assert args[args.index("--filter") + 1] == "Device:IN:DESKTOP"


def test_reports_custom_rejects_goals_filter_with_goal_ids():
    """Raw Goals filters must not combine with native goal_ids routing."""
    runner = mock_runner([])
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Goals,Conversions",
            date_from="2026-01-01",
            date_to="2026-01-31",
            goal_ids="111",
            filters=["Goals:IN:222"],
        )

    assert result["error"] == "invalid_goals_filter"
    assert "pass goal IDs via goal_ids instead" in result["message"]
    runner.run_json.assert_not_called()


def test_reports_custom_rejects_goals_filter_without_goal_ids():
    """Goal-based slicing must use goal_ids, not Reports API filters."""
    runner = mock_runner([])
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Goals,Conversions",
            date_from="2026-01-01",
            date_to="2026-01-31",
            filters=[" goals:IN:111"],
        )

    assert result["error"] == "invalid_goals_filter"
    assert "Goals filters are not supported" in result["message"]
    runner.run_json.assert_not_called()


def test_reports_custom_output_path(tmp_path):
    """output_path returns metadata, not the data array."""
    out = tmp_path / "report.json"
    runner = MagicMock()

    def fake_run(args, **kwargs):
        # Simulate direct-cli writing the file
        output_arg = args[args.index("--output") + 1]
        assert output_arg == str(out.resolve())
        out.write_text(json.dumps([{"x": 1}, {"x": 2}, {"x": 3}]))
        return completed()

    runner.run_checked.side_effect = fake_run
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            output_path=str(out),
            response_format="json",
        )

    args = _custom_args(runner.run_checked.call_args)
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
    runner = mock_runner([])
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            output_path="/etc/cron.d/direct-report.json",
        )

    assert result["error"] == "invalid_output_path"
    assert "output_path must be under one of" in result["message"]
    runner.run_json.assert_not_called()


def test_reports_custom_output_path_uncountable_file(tmp_path):
    """Existing files that cannot be counted return rows_written=None."""
    out = tmp_path / "report.json"
    runner = MagicMock()

    def fake_run(args, **kwargs):
        output_arg = args[args.index("--output") + 1]
        assert output_arg == str(out.resolve())
        out.write_text("not json")
        return completed()

    runner.run_checked.side_effect = fake_run
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

    def fake_run(args, **kwargs):
        output_arg = args[args.index("--output") + 1]
        assert output_arg == str(out.resolve())
        with out.open("w", encoding="utf-8") as f:
            f.write("[")
            for i in range(1000):
                if i:
                    f.write(",")
                f.write(json.dumps({"i": i, "nested": {"comma": "a,b"}}))
            f.write("]")
        return completed()

    runner.run_checked.side_effect = fake_run
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
    runner = mock_runner({"headers": {}, "body": fake_body})
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
    runner = mock_runner(raw)
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            dry_run=True,
        )
    assert result["request_body"] == raw


def test_reports_custom_dry_run_ignores_output_path(tmp_path):
    """dry_run=True must not pass --output to direct, otherwise the CLI writes
    the body to the file and stdout is empty, leaving request_body=[]."""
    fake_body = {"params": {"FieldNames": ["Date"]}}
    runner = mock_runner({"headers": {}, "body": fake_body})
    out = tmp_path / "ignored.json"
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            dry_run=True,
            output_path=str(out),
        )
    args = _custom_args(runner.run_json.call_args)
    assert "--output" not in args
    assert result["request_body"] == fake_body
    assert not out.exists()


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
    """date_range_type emits --date-range-type AND a concrete --from/--to pair.

    `direct reports get` keeps --from/--to required=True even with a preset
    --date-range-type, so the plugin must always supply a date pair (the API
    ignores it for non-CUSTOM_DATE ranges). See issue #170 finding #1.
    """
    runner = mock_runner([])
    with patch("server.tools.reports.get_runner", return_value=runner):
        reports_custom(
            field_names="Date,Cost",
            date_range_type="last_30_days",
        )

    args = _custom_args(runner.run_json.call_args)
    assert "--date-range-type" in args
    assert args[args.index("--date-range-type") + 1] == "last_30_days"
    # Both required CLI flags must be present so Click does not reject the call.
    assert "--from" in args and "--to" in args


def test_reports_custom_date_range_type_conflict():
    """date_range_type and explicit dates are mutually exclusive."""
    result = reports_custom(
        field_names="Date,Cost",
        date_from="2026-01-01",
        date_range_type="last_7_days",
    )
    assert result["error"] == "conflicting_date_inputs"
    assert "date_range_type OR explicit" in result["message"]


def test_reports_custom_requires_complete_explicit_date_range():
    """Custom reports reject partial explicit date ranges."""
    from_only = reports_custom(field_names="Date,Cost", date_from="2026-01-01")
    to_only = reports_custom(field_names="Date,Cost", date_to="2026-01-31")
    assert from_only["error"] == "missing_date_range"
    assert to_only["error"] == "missing_date_range"
    assert "Pass both date_from and date_to" in from_only["message"]


def test_reports_custom_rejects_invalid_response_format():
    result = reports_custom(
        field_names="Date,Cost",
        date_from="2026-01-01",
        date_to="2026-01-31",
        response_format="xml",
    )
    assert result["error"] == "invalid_response_format"


def test_reports_custom_rejects_invalid_date_format():
    result = reports_custom(
        field_names="Date,Cost",
        date_from="2026/01/01",
        date_to="2026-01-31",
    )
    assert result["error"] == "invalid_date_format"
    assert "date_from" in result["message"]


def test_reports_custom_override_report_type():
    """report_type override propagates to --type."""
    runner = mock_runner([])
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
    runner = mock_runner([])
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
    runner = mock_runner([])
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


# --- response_format / CLI 0.3.10 typed flags ---------------------------


def test_reports_custom_default_response_format_threads_json():
    """Default response_format=json must reach the CLI as --format json."""
    runner = mock_runner([{"x": 1}])
    with patch("server.tools.reports.get_runner", return_value=runner):
        reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
        )
    args = _custom_args(runner.run_json.call_args)
    assert args[-2:] == ["--format", "json"]


def test_reports_custom_response_format_tsv_in_memory():
    """response_format=tsv without output_path returns raw stdout payload."""
    runner = MagicMock()
    runner.run_checked.return_value = completed(stdout="Date\tCost\n2026-01-01\t12.5\n")
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            response_format="tsv",
        )
    args = _custom_args(runner.run_checked.call_args)
    assert args[-2:] == ["--format", "tsv"]
    assert result == {
        "format": "tsv",
        "report_type": "CUSTOM_REPORT",
        "content": "Date\tCost\n2026-01-01\t12.5\n",
    }
    runner.run_json.assert_not_called()


def test_reports_custom_response_format_csv_in_memory():
    runner = MagicMock()
    runner.run_checked.return_value = completed(stdout="Date,Cost\n2026-01-01,12.5\n")
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            response_format="csv",
        )
    args = _custom_args(runner.run_checked.call_args)
    assert args[-2:] == ["--format", "csv"]
    assert result["format"] == "csv"
    assert result["content"].startswith("Date,Cost")


def test_reports_custom_processing_mode_threads_through():
    runner = mock_runner([])
    with patch("server.tools.reports.get_runner", return_value=runner):
        reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            processing_mode="offline",
        )
    args = _custom_args(runner.run_json.call_args)
    idx = args.index("--processing-mode")
    assert args[idx + 1] == "offline"


def test_reports_custom_rejects_invalid_processing_mode():
    runner = mock_runner([])
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            processing_mode="async",
        )
    assert result["error"] == "invalid_processing_mode"
    runner.run_json.assert_not_called()
    runner.run_checked.assert_not_called()


def test_reports_custom_language_threads_through():
    runner = mock_runner([])
    with patch("server.tools.reports.get_runner", return_value=runner):
        reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            language="en",
        )
    args = _custom_args(runner.run_json.call_args)
    idx = args.index("--language")
    assert args[idx + 1] == "en"


def test_reports_custom_rejects_invalid_language():
    runner = mock_runner([])
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            language="fr",
        )
    assert result["error"] == "invalid_language"


def test_reports_custom_attribution_models_threads_through():
    runner = mock_runner([])
    with patch("server.tools.reports.get_runner", return_value=runner):
        reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            attribution_models="LSC,LYDCCD",
        )
    args = _custom_args(runner.run_json.call_args)
    idx = args.index("--attribution-models")
    assert args[idx + 1] == "LSC,LYDCCD"


def test_reports_custom_attribution_models_normalizes_whitespace():
    """Whitespace around tokens is stripped before forwarding to the CLI so
    `\"LSC, FC\"` becomes `\"LSC,FC\"` — matches what validation accepted."""
    runner = mock_runner([])
    with patch("server.tools.reports.get_runner", return_value=runner):
        reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            attribution_models="LSC, FC , LYDCCD",
        )
    args = _custom_args(runner.run_json.call_args)
    idx = args.index("--attribution-models")
    assert args[idx + 1] == "LSC,FC,LYDCCD"


def test_reports_custom_rejects_unknown_attribution_model():
    runner = mock_runner([])
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            attribution_models="LSC,MADE_UP",
        )
    assert result["error"] == "invalid_attribution_models"


def test_reports_custom_skip_flags_threaded():
    runner = mock_runner([])
    with patch("server.tools.reports.get_runner", return_value=runner):
        reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            skip_report_header=False,
            skip_column_header=True,
            skip_report_summary=False,
        )
    args = _custom_args(runner.run_json.call_args)
    assert "--no-skip-report-header" in args
    assert "--skip-column-header" in args
    assert "--no-skip-report-summary" in args
    assert "--skip-report-header" not in args
    assert "--skip-report-summary" not in args


def test_reports_custom_skip_flags_default_omits_them():
    """When skip_* are not set, the CLI defaults apply (no plugin override)."""
    runner = mock_runner([])
    with patch("server.tools.reports.get_runner", return_value=runner):
        reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
        )
    args = _custom_args(runner.run_json.call_args)
    assert "--skip-report-header" not in args
    assert "--no-skip-report-header" not in args
    assert "--skip-column-header" not in args
    assert "--skip-report-summary" not in args
    assert "--no-skip-report-summary" not in args


def test_reports_custom_output_path_with_tsv_format(tmp_path):
    """File output honors response_format=tsv (no implicit json override)."""
    out = tmp_path / "report.tsv"
    runner = MagicMock()

    def fake_run(args, **kwargs):
        out.write_text("Date\tCost\n2026-01-01\t12.5\n")
        return completed()

    runner.run_checked.side_effect = fake_run
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            output_path=str(out),
            response_format="tsv",
        )

    args = _custom_args(runner.run_checked.call_args)
    assert args[-2:] == ["--format", "tsv"]
    assert result["format"] == "tsv"
    assert result["output_path"] == str(out.resolve())


# --- non-zero exit code propagation (review #118 cycle 1) ---------------


def test_reports_custom_output_path_surfaces_cli_failure(tmp_path):
    """Non-zero CLI exit in the output_path branch must NOT silently
    produce a success-shaped dict. handle_cli_errors should convert the
    CliError raised by run_checked into a ToolError dict."""
    from server.cli.runner import CliError

    runner = MagicMock()
    runner.run_checked.side_effect = CliError(
        "direct failed (exit 1): boom", error_code=53, stderr="401 Unauthorized"
    )
    out = tmp_path / "report.json"
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-31",
            output_path=str(out),
        )
    assert "error" in result
    assert "output_path" not in result
    assert not out.exists()


def test_reports_custom_in_memory_tsv_surfaces_cli_failure():
    """Non-zero CLI exit in the in-memory TSV branch must NOT silently
    return {content: ""} as success."""
    from server.cli.runner import CliError

    runner = MagicMock()
    runner.run_checked.side_effect = CliError(
        "direct failed (exit 2): bad field", error_code=8000, stderr="error_code: 8000"
    )
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Bogus",
            date_from="2026-01-01",
            date_to="2026-01-31",
            response_format="tsv",
        )
    assert "error" in result
    assert "content" not in result


# --- _count_rows_written overhead given skip-flag state -----------------


def test_reports_custom_rows_written_default_skip_state(tmp_path):
    """Default CLI behaviour writes column header + N data rows; rows_written
    must equal N (overhead=1)."""
    out = tmp_path / "report.tsv"
    runner = MagicMock()

    def fake_run(args, **kwargs):
        # 1 header line + 3 data lines = 4 total
        out.write_text("Date\tCost\n2026-01-01\t1\n2026-01-02\t2\n2026-01-03\t3\n")
        return completed()

    runner.run_checked.side_effect = fake_run
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-03",
            output_path=str(out),
            response_format="tsv",
        )
    assert result["rows_written"] == 3


def test_reports_custom_rows_written_with_skip_column_header(tmp_path):
    """skip_column_header=True removes the header — overhead becomes 0."""
    out = tmp_path / "report.tsv"
    runner = MagicMock()

    def fake_run(args, **kwargs):
        # 3 data lines, no header
        out.write_text("2026-01-01\t1\n2026-01-02\t2\n2026-01-03\t3\n")
        return completed()

    runner.run_checked.side_effect = fake_run
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-03",
            output_path=str(out),
            response_format="tsv",
            skip_column_header=True,
        )
    assert result["rows_written"] == 3


def test_reports_custom_rows_written_with_summary_kept(tmp_path):
    """skip_report_summary=False adds a "Total rows: N" trailer — overhead 2."""
    out = tmp_path / "report.tsv"
    runner = MagicMock()

    def fake_run(args, **kwargs):
        # 1 col header + 3 data lines + 1 summary line = 5 total
        out.write_text(
            "Date\tCost\n2026-01-01\t1\n2026-01-02\t2\n2026-01-03\t3\nTotal rows: 3\n"
        )
        return completed()

    runner.run_checked.side_effect = fake_run
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-03",
            output_path=str(out),
            response_format="tsv",
            skip_report_summary=False,
        )
    assert result["rows_written"] == 3


def test_reports_custom_rows_written_with_report_header_kept(tmp_path):
    """skip_report_header=False adds the report title line — overhead 2."""
    out = tmp_path / "report.tsv"
    runner = MagicMock()

    def fake_run(args, **kwargs):
        # 1 report header + 1 col header + 3 data lines = 5 total
        out.write_text(
            '"X (2026-01-01 - 2026-01-03)"\n'
            "Date\tCost\n2026-01-01\t1\n2026-01-02\t2\n2026-01-03\t3\n"
        )
        return completed()

    runner.run_checked.side_effect = fake_run
    with patch("server.tools.reports.get_runner", return_value=runner):
        result = reports_custom(
            field_names="Date,Cost",
            date_from="2026-01-01",
            date_to="2026-01-03",
            output_path=str(out),
            response_format="tsv",
            skip_report_header=False,
        )
    assert result["rows_written"] == 3
