"""MCP tools for keyword management."""

import json

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors

MAX_BATCH_SIZE = 10


def _check_batch_limit(ids_str: str) -> ToolError | None:
    """Validate batch size of comma-separated IDs."""
    ids = [id.strip() for id in ids_str.split(",") if id.strip()]
    if len(ids) > MAX_BATCH_SIZE:
        return ToolError(
            error="batch_limit",
            message=f"Maximum {MAX_BATCH_SIZE} IDs per request. Got: {len(ids)}",
        )
    return None


@mcp.tool(name="keywords_get")
@handle_cli_errors
def keywords_list(campaign_ids: str) -> list[dict] | dict:
    """List keywords in specified campaigns.

    Args:
        campaign_ids: Comma-separated campaign IDs (max 10).
    """
    normalized_campaign_ids = campaign_ids.strip()
    if not normalized_campaign_ids:
        return ToolError(
            error="missing_campaign_ids",
            message="Provide at least one campaign ID.",
        ).__dict__
    batch_error = _check_batch_limit(normalized_campaign_ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    return runner.run_json(
        [
            "keywords",
            "get",
            "--campaign-ids",
            normalized_campaign_ids,
            "--format",
            "json",
        ]
    )


@mcp.tool()
@handle_cli_errors
def keywords_update(
    id: int,
    keyword: str | None = None,
    user_param_1: str | None = None,
    user_param_2: str | None = None,
    extra_json: str | dict | None = None,
) -> dict:
    """Update keyword text or user params.

    Note: bid changes go through `keyword_bids_set`, not this tool — CLI's
    `keywords update` does not accept `--bid` flags.

    Args:
        id: Keyword ID.
        keyword: Optional new keyword text.
        user_param_1: Optional user parameter 1.
        user_param_2: Optional user parameter 2.
        extra_json: Optional JSON string forwarded to direct-cli --json.
    """
    if not any((keyword, user_param_1, user_param_2, extra_json)):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: keyword, user_param_1, user_param_2, extra_json",
        ).__dict__

    runner = get_runner()
    args = ["keywords", "update", "--id", str(id)]
    if keyword is not None:
        args.extend(["--keyword", keyword])
    if user_param_1 is not None:
        args.extend(["--user-param-1", user_param_1])
    if user_param_2 is not None:
        args.extend(["--user-param-2", user_param_2])
    if extra_json:
        json_str = (
            json.dumps(extra_json) if isinstance(extra_json, dict) else extra_json
        )
        args.extend(["--json", json_str])
    runner.run_json(args)

    result: dict[str, object] = {"success": True, "id": id}
    if keyword is not None:
        result["keyword"] = keyword
    if user_param_1 is not None:
        result["user_param_1"] = user_param_1
    if user_param_2 is not None:
        result["user_param_2"] = user_param_2
    if extra_json:
        result["extra_json"] = extra_json
    return result


@mcp.tool()
@handle_cli_errors
def keywords_add(
    ad_group_id: int,
    keyword: str,
    bid: int | None = None,
    context_bid: int | None = None,
    user_param_1: str | None = None,
    user_param_2: str | None = None,
    extra_json: str | dict | None = None,
) -> dict:
    """Add a keyword to an ad group.

    Args:
        ad_group_id: Ad group ID to add the keyword to.
        keyword: Keyword text.
        bid: Optional search bid in micro-units (RUB × 1,000,000); CLI 0.2.10+
            rejects values 0 < x < 100_000 with a "did you mean × 1_000_000" hint.
        context_bid: Optional context bid in micro-units (same rules as `bid`).
        user_param_1: Optional user parameter 1.
        user_param_2: Optional user parameter 2.
        extra_json: Optional JSON string forwarded to direct-cli --json.
    """
    args = ["keywords", "add", "--adgroup-id", str(ad_group_id), "--keyword", keyword]
    if bid is not None:
        args.extend(["--bid", str(bid)])
    if context_bid is not None:
        args.extend(["--context-bid", str(context_bid)])
    if user_param_1 is not None:
        args.extend(["--user-param-1", user_param_1])
    if user_param_2 is not None:
        args.extend(["--user-param-2", user_param_2])
    if extra_json is not None:
        json_str = (
            json.dumps(extra_json) if isinstance(extra_json, dict) else extra_json
        )
        args.extend(["--json", json_str])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def keywords_delete(ids: str) -> dict:
    """Delete keywords.

    Args:
        ids: Comma-separated keyword IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "keywords", "delete", ids)


@mcp.tool()
@handle_cli_errors
def keywords_suspend(ids: str) -> dict:
    """Suspend keywords.

    Args:
        ids: Comma-separated keyword IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "keywords", "suspend", ids)


@mcp.tool()
@handle_cli_errors
def keywords_resume(ids: str) -> dict:
    """Resume suspended keywords.

    Args:
        ids: Comma-separated keyword IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "keywords", "resume", ids)


@mcp.tool()
@handle_cli_errors
def keywords_archive(ids: str) -> dict:
    """Archive keywords.

    Args:
        ids: Comma-separated keyword IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "keywords", "archive", ids)


@mcp.tool()
@handle_cli_errors
def keywords_unarchive(ids: str) -> dict:
    """Unarchive keywords.

    Args:
        ids: Comma-separated keyword IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(get_runner(), "keywords", "unarchive", ids)
