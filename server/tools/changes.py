"""MCP tools for checking changes in Yandex.Direct."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit


@mcp.tool()
@handle_cli_errors
def changes_check(
    campaign_ids: str,
    timestamp: str,
    fields: str | None = None,
) -> dict:
    """Check changes for specific campaigns since timestamp.

    Args:
        campaign_ids: Comma-separated campaign IDs (max 10).
        timestamp: Timestamp for changes check (YYYY-MM-DDTHH:MM:SS).
        fields: Comma-separated field names.
    """
    normalized = campaign_ids.strip()
    if not normalized:
        return ToolError(
            error="missing_campaign_ids",
            message="Provide at least one campaign ID.",
        ).__dict__
    batch_error = check_batch_limit(normalized)
    if batch_error:
        return batch_error.__dict__

    args = [
        "changes",
        "check",
        "--campaign-ids",
        normalized,
        "--timestamp",
        timestamp,
        "--format",
        "json",
    ]
    if fields is not None:
        args.extend(["--fields", fields])
    return get_runner().run_json(args)


@mcp.tool(name="changes_check_campaigns")
@handle_cli_errors
def changes_checkcamp(timestamp: str) -> dict:
    """Check account-wide campaign changes since timestamp.

    CLI 0.3.8 `changes check-campaigns` takes only `--timestamp`.

    Args:
        timestamp: Timestamp for changes check (YYYY-MM-DDTHH:MM:SS).
    """
    return get_runner().run_json(
        [
            "changes",
            "check-campaigns",
            "--timestamp",
            timestamp,
            "--format",
            "json",
        ]
    )


@mcp.tool(name="changes_check_dictionaries")
@handle_cli_errors
def changes_checkdict() -> dict:
    """Check dictionary changes.

    CLI 0.3.8 `changes check-dictionaries` takes no parameters.
    """
    return get_runner().run_json(["changes", "check-dictionaries", "--format", "json"])
