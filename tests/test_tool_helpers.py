"""Tests for shared tool decorators and helper functions."""

from unittest.mock import patch

import pytest

import server.tools as tools
from server.auth.oauth import OAuthError
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


def test_try_refresh_token_returns_access_token() -> None:
    with patch("server.auth.oauth.OAuthManager") as mock_manager_cls:
        mock_manager = mock_manager_cls.return_value
        mock_manager.refresh_token.return_value = {"access_token": "fresh-token"}
        assert tools._try_refresh_token() == "fresh-token"


def test_try_refresh_token_reraises_oauth_error() -> None:
    with patch("server.auth.oauth.OAuthManager") as mock_manager_cls:
        mock_manager = mock_manager_cls.return_value
        mock_manager.refresh_token.side_effect = OAuthError("auth_expired", "expired")
        with pytest.raises(OAuthError):
            tools._try_refresh_token()


def test_try_refresh_token_returns_none_on_generic_error() -> None:
    with patch("server.auth.oauth.OAuthManager") as mock_manager_cls:
        mock_manager = mock_manager_cls.return_value
        mock_manager.refresh_token.side_effect = RuntimeError("boom")
        assert tools._try_refresh_token() is None


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


def test_handle_cli_errors_retries_once_after_refresh() -> None:
    state = {"calls": 0}

    @tools.handle_cli_errors
    def wrapped():
        state["calls"] += 1
        if state["calls"] == 1:
            raise CliAuthError("expired")
        return {"success": True}

    with patch("server.tools._try_refresh_token", return_value="fresh-token"):
        result = wrapped()

    assert result == {"success": True}
    assert state["calls"] == 2


def test_handle_cli_errors_returns_auth_expired_when_retry_still_fails() -> None:
    @tools.handle_cli_errors
    def wrapped():
        raise CliAuthError("expired")

    with patch("server.tools._try_refresh_token", return_value="fresh-token"):
        result = wrapped()

    assert result["error"] == "auth_expired"


def test_handle_cli_errors_returns_oauth_error_dict() -> None:
    @tools.handle_cli_errors
    def wrapped():
        raise OAuthError("auth_expired", "reauthorize", "https://oauth.example")

    result = wrapped()
    assert result["error"] == "auth_expired"
    assert result["auth_url"] == "https://oauth.example"


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


def test_handle_cli_errors_targeted_hint_8000_filter_falls_back_to_filter_hint() -> None:
    result = _wrap_cli_error(
        "boom",
        error_code=8000,
        stderr="error_code=8000, error_detail=Filter Field contains an invalid enumeration value",
    )()
    assert result["error"] == "invalid_request"
    assert "Operator must be one of" in result["hint"]


def test_handle_cli_errors_targeted_hint_8000_generic_when_no_detail_match() -> None:
    result = _wrap_cli_error("boom", error_code=8000, stderr=None)()
    assert result["error"] == "invalid_request"
    assert "dry_run=True" in result["hint"]


def test_handle_cli_errors_maps_error_code_53_to_auth_error_with_hint() -> None:
    result = _wrap_cli_error("boom", error_code=53, stderr="error_code=53")()
    assert result["error"] == "auth_error"
    assert "auth_login" in result["hint"]


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


def test_set_token_getter_and_get_runner() -> None:
    tools.set_token_getter(lambda: "test-token")
    runner = tools.get_runner()
    assert isinstance(runner, DirectCliRunner)
    assert runner._token == "test-token"


def test_get_runner_raises_without_token_getter() -> None:
    original = tools._token_getter
    tools._token_getter = None
    try:
        with pytest.raises(RuntimeError, match="Token getter not configured"):
            tools.get_runner()
    finally:
        tools._token_getter = original


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
