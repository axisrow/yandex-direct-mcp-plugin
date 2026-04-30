"""Tests for shared tool decorators and helper functions."""

import server.tools as tools
from server.cli.runner import (
    CliAuthError,
    CliNotFoundError,
    CliRegistrationError,
    CliTimeoutError,
    DirectCliRunner,
)
from server.tools.ads import _check_batch_limit as ads_check_batch_limit
from server.tools.ads import _get_foreign_campaign_id, _parse_ids
from server.tools.auth_tools import _human_readable_time
from server.tools.keywords import _check_batch_limit as keywords_check_batch_limit


def test_human_readable_time_formats_expected_ranges() -> None:
    assert _human_readable_time(0) == "истёк"
    assert _human_readable_time(59) == "59 сек."
    assert _human_readable_time(90) == "1 мин. 30 сек."
    assert _human_readable_time(3660) == "1 ч. 1 мин."


def test_handle_cli_errors_maps_registration_error() -> None:
    @tools.handle_cli_errors
    def wrapped():
        raise CliRegistrationError("registration incomplete")

    result = wrapped()
    assert result["error"] == "incomplete_registration"


def test_handle_cli_errors_maps_cli_not_found() -> None:
    @tools.handle_cli_errors
    def wrapped():
        raise CliNotFoundError("cli missing")

    result = wrapped()
    assert result["error"] == "cli_not_found"


def test_handle_cli_errors_maps_timeout() -> None:
    @tools.handle_cli_errors
    def wrapped():
        raise CliTimeoutError("timed out")

    result = wrapped()
    assert result["error"] == "timeout"


def test_handle_cli_errors_returns_auth_expired_without_plugin_refresh() -> None:
    state = {"calls": 0}

    @tools.handle_cli_errors
    def wrapped():
        state["calls"] += 1
        raise CliAuthError("expired")

    result = wrapped()
    assert result["error"] == "auth_expired"
    assert "auth_login" in result["hint"]
    assert state["calls"] == 1


def test_handle_cli_errors_returns_unknown_for_unexpected_exception() -> None:
    @tools.handle_cli_errors
    def wrapped():
        raise RuntimeError("boom")

    result = wrapped()
    assert result["error"] == "unknown"
    assert result["message"] == "boom"


def _wrap_cli_error(message: str, *, error_code: int | None, stderr: str | None = None):
    """Helper: build a wrapped function that raises a CliError when called."""
    from server.cli.runner import CliError

    @tools.handle_cli_errors
    def wrapped():
        raise CliError(message, error_code=error_code, stderr=stderr)

    return wrapped


def test_handle_cli_errors_targeted_hint_8000_fieldnames() -> None:
    result = _wrap_cli_error(
        "boom",
        error_code=8000,
        stderr="error_code=8000, error_detail=Element of array FieldNames contains an invalid enumeration value",
    )()
    assert result["error"] == "invalid_request"
    assert "FieldNames are case-sensitive" in result["hint"]


def test_handle_cli_errors_targeted_hint_8000_sortorder() -> None:
    result = _wrap_cli_error(
        "boom",
        error_code=8000,
        stderr="error_code=8000, error_detail=SortOrder contains an invalid enumeration value",
    )()
    assert result["error"] == "invalid_request"
    assert "FIELD:ASC" in result["hint"]


def test_handle_cli_errors_targeted_hint_8000_filter_falls_back_to_filter_hint() -> (
    None
):
    result = _wrap_cli_error(
        "boom",
        error_code=8000,
        stderr="error_code=8000, error_detail=Filter Field contains an invalid enumeration value",
    )()
    assert result["error"] == "invalid_request"
    assert "Operators are usually one of" in result["hint"]


def test_handle_cli_errors_filter_hint_matches_only_whole_word() -> None:
    """A substring like 'filterable' or 'unfiltered' must NOT trigger the
    Filter hint — only the standalone word 'filter' does."""
    result = _wrap_cli_error(
        "boom",
        error_code=8000,
        stderr="error_code=8000, error_detail=value 'filterable' is not allowed",
    )()
    assert result["error"] == "invalid_request"
    # No real Filter token → falls back to the generic hint, not the Filter one.
    assert "Operator must be one of" not in result["hint"]
    assert "dry_run=True" in result["hint"]


def test_handle_cli_errors_targeted_hint_8000_generic_when_no_detail_match() -> None:
    result = _wrap_cli_error("boom", error_code=8000, stderr=None)()
    assert result["error"] == "invalid_request"
    assert "dry_run=True" in result["hint"]


def test_handle_cli_errors_maps_error_code_53_to_auth_error_with_hint() -> None:
    result = _wrap_cli_error("boom", error_code=53, stderr="error_code=53")()
    assert result["error"] == "auth_error"
    assert "auth_login" in result["hint"]


def test_handle_cli_errors_error_code_8800_client_login_hint() -> None:
    result = _wrap_cli_error(
        "boom",
        error_code=8800,
        stderr="error_code=8800, error_detail=The HTTP Client-Login header contains a nonexistent username",
    )()
    assert result["error"] == "not_found"
    assert "direct-cli profile" in result["hint"]


def test_handle_cli_errors_maps_error_code_152_to_insufficient_funds() -> None:
    result = _wrap_cli_error("boom", error_code=152)()
    assert result["error"] == "insufficient_funds"
    assert "balance" in result["hint"].lower()


def test_handle_cli_errors_maps_error_code_9300_to_limit_exceeded() -> None:
    result = _wrap_cli_error("boom", error_code=9300)()
    assert result["error"] == "limit_exceeded"
    assert "10 IDs" in result["hint"]


def test_handle_cli_errors_unknown_code_keeps_unknown_and_no_hint() -> None:
    result = _wrap_cli_error("boom", error_code=99999)()
    assert result["error"] == "unknown"
    assert result["hint"] is None


def test_handle_cli_errors_no_code_keeps_unknown_and_no_hint() -> None:
    """Plain CliError without an error_code (e.g. parse failure) stays unknown."""
    result = _wrap_cli_error("boom", error_code=None)()
    assert result["error"] == "unknown"
    assert result["hint"] is None


def test_get_runner_returns_profile_based_runner() -> None:
    runner = tools.get_runner()
    assert isinstance(runner, DirectCliRunner)


def test_parse_ids_strips_whitespace_and_empty_values() -> None:
    assert _parse_ids(" 1, 2 ,,3 , ") == ["1", "2", "3"]


def test_ads_batch_limit_allows_ten_ids_and_rejects_eleven() -> None:
    assert ads_check_batch_limit(",".join(str(i) for i in range(10))) is None
    result = ads_check_batch_limit(",".join(str(i) for i in range(11)))
    assert result is not None
    assert result.error == "batch_limit"


def test_get_foreign_campaign_id_detects_only_foreign_range() -> None:
    assert _get_foreign_campaign_id("abc,72999999,73000000,5") == "73000000"
    assert _get_foreign_campaign_id("100,200,abc") is None


def test_keywords_batch_limit_allows_ten_ids_and_rejects_eleven() -> None:
    assert keywords_check_batch_limit(",".join(str(i) for i in range(10))) is None
    result = keywords_check_batch_limit(",".join(str(i) for i in range(11)))
    assert result is not None
    assert result.error == "batch_limit"
