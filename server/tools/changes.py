"""MCP tools for checking changes in Yandex.Direct."""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def changes_check(timestamp: str) -> dict:
    """Check changes since timestamp.

    Args:
        timestamp: Timestamp to check changes from (e.g., "2026-01-01T00:00:00Z").
    """
    runner = get_runner()
    result = runner.run_json(
        ["changes", "check", "--timestamp", timestamp, "--format", "json"]
    )
    return result


@mcp.tool()
@handle_cli_errors
def changes_checkcamp(campaign_ids: str, timestamp: str) -> dict:
    """Check campaign changes since timestamp.

    Args:
        campaign_ids: Comma-separated campaign IDs (max 10).
        timestamp: Timestamp to check changes from (e.g., "2026-01-01T00:00:00Z").
    """
    from server.tools.helpers import check_batch_limit

    batch_error = check_batch_limit(campaign_ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(
        [
            "changes",
            "check-camp",
            "--campaign-ids",
            campaign_ids,
            "--timestamp",
            timestamp,
            "--format",
            "json",
        ]
    )
    return result


@mcp.tool()
@handle_cli_errors
def changes_checkdict(timestamp: str) -> dict:
    """Check dictionary changes since timestamp.

    Args:
        timestamp: Timestamp to check changes from (e.g., "2026-01-01T00:00:00Z").
    """
    runner = get_runner()
    result = runner.run_json(
        ["changes", "check-dict", "--timestamp", timestamp, "--format", "json"]
    )
    return result
