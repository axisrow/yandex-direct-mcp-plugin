"""Read-only ``direct masters`` tools (issue #255).

Wraps ``direct masters get`` and ``direct masters targetactions get`` — the
read-only slice of the Playwright-based Masters campaign cluster. The full
mutation surface is deliberately excluded; the underlying browser automation
is fragile and mutations need a separate auth-model review.

Both tools override the default 30 s runner timeout to 60 s to match
direct-cli's internal timeouts for masters operations.
"""

from __future__ import annotations

from server.cli.runner import DirectCliRunner
from server.tools import handle_cli_errors


@handle_cli_errors
def masters_get(
    *,
    moderation_statuses: list[str] | None = None,
) -> dict:
    """List campaigns managed by the Masters interface.

    Read-only wrapper around ``direct masters get``. Masters campaigns are
    browser-only (no v5 API endpoint), so this tool uses direct-cli's Playwright
    automation.

    Args:
        moderation_statuses: Optional filter by moderation status. Omit to
            show all campaigns.

    Returns:
        dict: JSON output from direct-cli.
    """
    runner = DirectCliRunner()
    args: list[str] = ["masters", "get"]
    if moderation_statuses:
        for status in moderation_statuses:
            args.extend(["--moderation-statuses", status])
    return runner.run(args, timeout=60)


@handle_cli_errors
def masters_targetactions_get(
    *,
    moderation_statuses: list[str] | None = None,
) -> dict:
    """List target actions for Masters campaigns.

    Read-only wrapper around ``direct masters targetactions get``.

    Args:
        moderation_statuses: Optional filter by moderation status.

    Returns:
        dict: JSON output from direct-cli.
    """
    runner = DirectCliRunner()
    args: list[str] = ["masters", "targetactions", "get"]
    if moderation_statuses:
        for status in moderation_statuses:
            args.extend(["--moderation-statuses", status])
    return runner.run(args, timeout=60)
