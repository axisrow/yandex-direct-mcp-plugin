"""MCP tools for negative keyword management.

NOTE: The direct-cli does not expose a ``negativekeywords`` subcommand.
The CLI only provides ``negativekeywordsharedsets`` (see
negative_keyword_shared_sets.py).  These tools are kept as placeholders
until the CLI adds support for campaign-level negative keywords.
"""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors

from server.tools.helpers import check_batch_limit


@mcp.tool()
@handle_cli_errors
def negative_keywords_list(campaign_ids: str) -> list[dict] | dict:
    """List negative keywords in specified campaigns.

    Args:
        campaign_ids: Comma-separated campaign IDs (max 10).
    """
    batch_error = check_batch_limit(campaign_ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    return runner.run_json(
        ["negativekeywords", "get", "--campaign-ids", campaign_ids, "--format", "json"]
    )


@mcp.tool()
@handle_cli_errors
def negative_keywords_add(campaign_id: str, keywords: str) -> dict:
    """Add negative keywords to a campaign.

    Args:
        campaign_id: Campaign ID.
        keywords: Comma-separated keyword list to add as negative keywords.
    """
    runner = get_runner()
    result = runner.run_json(
        [
            "negativekeywords",
            "add",
            "--campaign-id",
            campaign_id,
            "--keywords",
            keywords,
            "--format",
            "json",
        ]
    )
    return result


@mcp.tool()
@handle_cli_errors
def negative_keywords_update(id: str, keywords: str) -> dict:
    """Update negative keyword set.

    Args:
        id: Negative keyword set ID.
        keywords: Comma-separated keyword list to set as negative keywords.
    """
    runner = get_runner()
    result = runner.run_json(
        [
            "negativekeywords",
            "update",
            "--id",
            id,
            "--keywords",
            keywords,
            "--format",
            "json",
        ]
    )
    return result


@mcp.tool()
@handle_cli_errors
def negative_keywords_delete(ids: str) -> dict:
    """Delete negative keyword sets.

    Args:
        ids: Comma-separated negative keyword set IDs (max 10).
    """
    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(
        ["negativekeywords", "delete", "--ids", ids, "--format", "json"]
    )
    return result
