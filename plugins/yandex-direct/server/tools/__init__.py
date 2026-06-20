import re
from dataclasses import asdict, dataclass
from functools import wraps

from server.cli.runner import (
    CliAuthError,
    CliError,
    CliNotFoundError,
    CliRegistrationError,
    CliTimeoutError,
)


_FILTER_TOKEN_RE = re.compile(r"\bfilter\b", re.IGNORECASE)

# Yandex error_detail for an invalid enum spells out the allowed values, e.g.
# "One of the following values is expected: Id, Name, State". Capture that list
# so the agent gets the right field names from the first response instead of
# guessing and re-calling. Stop at the first sentence break / end of string.
_EXPECTED_VALUES_RE = re.compile(
    r"following values?\s+(?:is|are)\s+expected:\s*(?P<values>[^.\n]+)",
    re.IGNORECASE,
)


def _extract_expected_values(stderr: str | None) -> str | None:
    """Pull the 'One of the following values is expected: ...' list from stderr."""
    if not stderr:
        return None
    match = _EXPECTED_VALUES_RE.search(stderr)
    if not match:
        return None
    values = match.group("values").strip().rstrip(",").strip()
    return values or None


@dataclass
class ToolError:
    error: str
    message: str
    auth_url: str | None = None
    hint: str | None = None


def tool_error_dict(error: ToolError) -> dict:
    """Return a stable dict representation for MCP error payloads.

    Canonical home is here (next to ``ToolError``) so ``handle_cli_errors`` can
    use it without importing ``helpers`` (which imports back from this module).
    ``helpers`` re-exports it for the tool modules.
    """
    return asdict(error)


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
    "A Filter entry has an invalid Field or Operator. Operators are usually "
    "one of EQUALS, NOT_EQUALS, IN, NOT_IN, LESS_THAN, GREATER_THAN, "
    "STARTS_WITH_IGNORE_CASE, DOES_NOT_START_WITH_IGNORE_CASE. "
    "For goal-based slicing use `goal_ids`, not a Filter."
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
    # 8300 / 8800 hints are intentionally NOT defined here: direct-cli >=0.4.3
    # emits them itself (direct_cli/output.py), and the whole CLI stderr flows
    # into the ToolError message, so a plugin-side hint would duplicate it (#219).
    # The machine-readable error_kind classification below (invalid_status /
    # not_found) is kept — it is structured data, not a text dup. 8301 / 9300 /
    # 1000 / 7001 / 8000 stay: the CLI does not emit hints for those.
    8301: (
        "Ad group cannot be removed because it still contains ads (error "
        "8301). Archive the ads first: call ads_get with ad_group_ids to list "
        "them, then ads_archive for those ads, then retry adgroups_delete. If "
        "ads_archive also fails with error 8300, the group can only be removed "
        "from the Direct web interface."
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
        base = _INVALID_REQUEST_HINT_FIELDNAMES
    elif "sortorder" in detail:
        base = _INVALID_REQUEST_HINT_SORTORDER
    elif _FILTER_TOKEN_RE.search(stderr):
        base = _INVALID_REQUEST_HINT_FILTER
    else:
        base = _INVALID_REQUEST_HINT_GENERIC

    # When Yandex enumerates the allowed values, surface them verbatim so the
    # agent picks correct fields on the first try instead of re-calling.
    expected = _extract_expected_values(stderr)
    if expected:
        return f"{base} Allowed values for this endpoint: {expected}."
    return base


def _hint_for_cli_error(error: CliError) -> str | None:
    """Return the best hint for a CliError, or None if nothing specific applies."""
    if error.error_code == 8000:
        return _build_invalid_request_hint(error.stderr)
    # 8800 (wrong Client-Login / object not found) is no longer hinted here:
    # direct-cli >=0.4.3 emits a Client-Login hint itself ("Check --login,
    # YANDEX_DIRECT_LOGIN, or the selected auth profile…"), which reaches the LLM
    # via the ToolError message. A plugin hint would duplicate it (#219).
    if error.error_code is not None and error.error_code in _HINTS_BY_ERROR_CODE:
        return _HINTS_BY_ERROR_CODE[error.error_code]
    return None


_INVALID_REQUEST_CODES = {8000, 4000, 4001, 4002, 4003, 4004, 4005, 4006}


def handle_cli_errors(func):
    """Decorator that catches CLI errors and returns ToolError dicts."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CliRegistrationError as e:
            return tool_error_dict(
                ToolError(error="incomplete_registration", message=str(e))
            )
        except CliAuthError as e:
            return tool_error_dict(
                ToolError(
                    error="auth_expired",
                    message=str(e) or "Token expired. Re-authorization required.",
                    hint="Run auth_status to check the active direct auth profile, then auth_login to re-authorize.",
                )
            )
        except CliNotFoundError as e:
            return tool_error_dict(ToolError(error="cli_not_found", message=str(e)))
        except CliTimeoutError as e:
            return tool_error_dict(ToolError(error="timeout", message=str(e)))
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
            elif e.error_code == 8300 or e.error_code == 8301:
                error_kind = "invalid_status"
            elif e.error_code == 9300 or e.error_code == 7001:
                error_kind = "limit_exceeded"
            else:
                error_kind = "unknown"
            return tool_error_dict(
                ToolError(error=error_kind, message=str(e), hint=hint)
            )
        except Exception as e:
            return tool_error_dict(ToolError(error="unknown", message=str(e)))

    return wrapper


def get_runner():
    """Create a DirectCliRunner using the active direct auth profile."""
    from server.cli.runner import DirectCliRunner

    return DirectCliRunner()
