"""MCP tool for Yandex.Direct browser-backed change history."""

import os

from server.main import mcp
from server.tools import get_browser_runner, handle_cli_errors
from server.tools.browser_helpers import browser_session_args
from server.tools.helpers import append_id_filters, normalize_optional_str


@mcp.tool(
    name="history_get",
    description="Read the account-wide Yandex.Direct change history with server-side filters and automatic pagination. Call tool_help('history_get') for parameters.",
)
@handle_cli_errors
def history_get(
    campaign_ids: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    logins: str | None = None,
    change_sources: str | None = None,
    categories: str | None = None,
    limit: int | None = None,
) -> list[dict] | dict:
    """Read the account's browser-backed «История изменений» journal.

    The command returns newest-first records for the browser session's logged-in
    account. Filters are applied by Yandex. Pagination is automatic, and direct
    de-duplicates overlapping pages by the server-owned ``Gtid``: the cursor has
    one-second granularity, so adjacent pages can repeat records from the same
    second. ``limit`` counts unique records after that de-duplication.

    A plain ``YYYY-MM-DD`` boundary is expanded by direct to the whole day:
    ``date_from`` gets ``T00:00:00`` and ``date_to`` gets ``T23:59:59``. A value
    already containing uppercase ``T`` passes through unchanged. If both dates
    are omitted, the web interface's own default period is preserved.

    ``categories`` has an intentional three-state contract. ``None`` omits the
    CLI flag and preserves the complete category list captured from the web UI
    (44 positions in the 2026-08-13 live check). An explicit empty string is
    forwarded as ``--categories ''`` and filters out every record. Do not
    collapse explicit empty ``categories`` to ``None``.

    Args:
        campaign_ids: Optional comma-separated campaign IDs.
        date_from: Optional start date or naive local datetime, in
            ``YYYY-MM-DD`` or ``YYYY-MM-DDTHH:MM:SS`` form.
        date_to: Optional end date or naive local datetime, in the same forms.
        logins: Optional comma-separated author logins.
        change_sources: Optional comma-separated UI source values such as
            ``WEB``, ``API``, or ``OTHER``.
        categories: Optional comma-separated UI change categories, for example
            ``CAMPAIGN_STRATEGY``. ``None`` and ``""`` differ as described above.
        limit: Optional maximum number of unique records. Must be positive;
            direct raises a UsageError for zero or negative values.

    Returns:
        A list of flattened records with ``Datetime``, ``Login``, ``Uid``,
        ``ChangeSource``, ``Category``, ``EventType``, ``CampaignId``,
        ``CampaignName``, ``Gtid``, and the event union passed through unchanged
        under ``Event``. Browser/auth failures are returned as structured errors.
    """
    args = ["history", "get"]

    append_id_filters(args, [(campaign_ids, "--campaign-ids")])

    for value, flag in (
        (date_from, "--date-from"),
        (date_to, "--date-to"),
        (logins, "--logins"),
        (change_sources, "--change-sources"),
    ):
        normalized = normalize_optional_str(value)
        if normalized is not None:
            args.extend([flag, normalized])

    # Unlike every other optional CSV above, an explicit empty categories value
    # is meaningful to direct-cli: it becomes [] and filters out every category.
    if categories is not None:
        args.extend(["--categories", categories.strip()])

    if limit is not None:
        args.extend(["--limit", str(limit)])

    args.extend(browser_session_args(os.environ))
    args.extend(["--format", "json"])
    return get_browser_runner().run_json_lenient(args)
