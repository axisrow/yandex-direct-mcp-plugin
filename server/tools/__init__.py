import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps

from server.cli.runner import (
    CliAuthError,
    CliError,
    CliNotFoundError,
    CliRegistrationError,
    CliTimeoutError,
)


_FILTER_TOKEN_RE = re.compile(r"\bfilter\b", re.IGNORECASE)


@dataclass
class ToolError:
    error: str
    message: str
    auth_url: str | None = None
    hint: str | None = None


_INVALID_REQUEST_HINT_GENERIC = (
    "Yandex rejected the request. For reports tools, re-run with dry_run=True "
    "to inspect the request body. Common causes: typo in field_names "
    "(case-sensitive enum), unsupported Filter operator, or a field/filter "
    "not allowed for this report_type. "
    "Spec: https://yandex.com/dev/direct/doc/reports/spec.html"
)

_INVALID_REQUEST_HINT_FIELDNAMES = (
    "FieldNames contains a value not in the enum for this report_type. "
    "FieldNames are case-sensitive (e.g. CampaignName, not campaign_name). "
    "Run reports_list_types() for valid types and pass dry_run=True to see "
    "the exact request body."
)

_INVALID_REQUEST_HINT_SORTORDER = (
    "order_by entries must be FIELD or FIELD:ASC / FIELD:DESC (uppercase). "
    "Lowercase 'asc'/'desc' or other values are rejected as invalid enums."
)

_INVALID_REQUEST_HINT_FILTER = (
    "A Filter entry has an invalid Field or Operator. Operator must be one "
    "of EQUALS, NOT_EQUALS, IN, NOT_IN, LESS_THAN, GREATER_THAN, "
    "STARTS_WITH_IGNORE_CASE, DOES_NOT_START_WITH_IGNORE_CASE. "
    "Note: Goals filter is only valid for some report_types — pass dry_run=True "
    "to confirm the body shape."
)

# Targeted hints by error_code, per Yandex.Direct API errors-list reference.
# https://yandex.ru/dev/direct/doc/en/concepts/errors-list
_HINTS_BY_ERROR_CODE: dict[int, str] = {
    53: (
        "OAuth token rejected as invalid. Run auth_status to check, then "
        "auth_login to refresh it."
    ),
    54: (
        "No rights for this operation. If you manage multiple clients, the "
        "active login may be wrong — check clients_get and confirm the "
        "object belongs to the current account."
    ),
    152: (
        "Account is out of money. Top up the Yandex.Direct balance — this is "
        "an account state, not a parameter problem."
    ),
    506: (
        "Yandex throttled the connection (too many parallel requests). "
        "Retry with a small delay; consider serializing batch calls."
    ),
    1000: (
        "Yandex side temporary error. Retry after a few seconds; if it "
        "persists, the API itself is degraded."
    ),
    7001: (
        "Per-account object limit reached (campaigns / ads / keywords). "
        "Archive or delete unused objects first."
    ),
    8800: (
        "Object not found. Either the ID is wrong or it belongs to a "
        "different client. For ads_*, the plugin already pre-checks foreign "
        "campaign IDs — for other tools, verify with a *_get call."
    ),
    9300: (
        "Too many objects in one request. Yandex API caps batch size at "
        "10 IDs per call — split the input and retry."
    ),
}


def _build_invalid_request_hint(stderr: str | None) -> str:
    """Pick the most specific hint for an error_code=8000 response.

    Inspects error_detail in stderr to detect FieldNames / SortOrder / Filter
    issues and returns a targeted hint; falls back to a generic one.
    """
    if not stderr:
        return _INVALID_REQUEST_HINT_GENERIC
    detail = stderr.lower()
    if "fieldnames" in detail:
        return _INVALID_REQUEST_HINT_FIELDNAMES
    if "sortorder" in detail:
        return _INVALID_REQUEST_HINT_SORTORDER
    if _FILTER_TOKEN_RE.search(stderr):
        return _INVALID_REQUEST_HINT_FILTER
    return _INVALID_REQUEST_HINT_GENERIC


def _hint_for_cli_error(error: CliError) -> str | None:
    """Return the best hint for a CliError, or None if nothing specific applies."""
    if error.error_code == 8000:
        return _build_invalid_request_hint(error.stderr)
    if error.error_code is not None and error.error_code in _HINTS_BY_ERROR_CODE:
        return _HINTS_BY_ERROR_CODE[error.error_code]
    return None


_INVALID_REQUEST_CODES = {8000, 4000, 4001, 4002, 4003, 4004, 4005, 4006}


def _try_refresh_token() -> str | None:
    """Force-refresh the OAuth token. Returns new access token or None."""
    try:
        from server.auth.oauth import OAuthError, OAuthManager

        manager = OAuthManager()
        data = manager.refresh_token()
        return data["access_token"]
    except OAuthError:
        raise
    except Exception:
        return None


def handle_cli_errors(func):
    """Decorator that catches CLI errors and returns ToolError dicts.

    On 401, refreshes token and retries once."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CliRegistrationError as e:
            return ToolError(error="incomplete_registration", message=str(e)).__dict__
        except CliAuthError:
            from server.auth.oauth import OAuthError

            try:
                new_token = _try_refresh_token()
            except OAuthError as e:
                return e.to_dict()
            if new_token is not None:
                try:
                    return func(*args, **kwargs)
                except CliAuthError:
                    pass
                except OAuthError as e:
                    return e.to_dict()
            return ToolError(
                error="auth_expired",
                message="Token expired. Re-authorization required.",
            ).__dict__
        except CliNotFoundError as e:
            return ToolError(error="cli_not_found", message=str(e)).__dict__
        except CliTimeoutError as e:
            return ToolError(error="timeout", message=str(e)).__dict__
        except CliError as e:
            hint = _hint_for_cli_error(e)
            if e.error_code in _INVALID_REQUEST_CODES:
                error_kind = "invalid_request"
            elif e.error_code == 53:
                error_kind = "auth_error"
            elif e.error_code == 54:
                error_kind = "no_rights"
            elif e.error_code == 152:
                error_kind = "insufficient_funds"
            elif e.error_code == 506 or e.error_code == 1000:
                error_kind = "transient"
            elif e.error_code == 8800:
                error_kind = "not_found"
            elif e.error_code == 9300 or e.error_code == 7001:
                error_kind = "limit_exceeded"
            else:
                error_kind = "unknown"
            return ToolError(
                error=error_kind, message=str(e), hint=hint
            ).__dict__
        except Exception as e:
            from server.auth.oauth import OAuthError as _OAuthError

            if isinstance(e, _OAuthError):
                return e.to_dict()
            return ToolError(error="unknown", message=str(e)).__dict__

    return wrapper


_token_getter: Callable[[], str] | None = None


def set_token_getter(getter: Callable[[], str]) -> None:
    global _token_getter
    _token_getter = getter


def get_runner():
    """Create a DirectCliRunner using the configured token getter."""
    from server.cli.runner import DirectCliRunner

    if _token_getter is None:
        raise RuntimeError("Token getter not configured")
    return DirectCliRunner(token=_token_getter())
