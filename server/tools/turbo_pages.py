"""MCP tools for turbo pages management."""

import json

from server.main import mcp
from server.tools import get_runner, handle_cli_errors


@mcp.tool(name="turbopages_get")
@handle_cli_errors
def turbo_pages_list(ids: str | None = None) -> dict:
    """List turbo pages.

    Args:
        ids: Comma-separated turbo page IDs (optional).
    """
    args = ["turbopages", "get", "--format", "json"]
    normalized_ids = ids.strip() if ids is not None else None
    if normalized_ids:
        args.extend(["--ids", normalized_ids])
    runner = get_runner()
    return runner.run_json(args)


@handle_cli_errors
def turbo_pages_add(name: str, url: str, extra_json: str | dict | None = None) -> dict:
    """Add a turbo page.

    Args:
        name: Page name.
        url: Page URL.
        extra_json: Optional JSON string with additional parameters.
    """
    args = ["turbopages", "add", "--name", name, "--url", url]
    if extra_json is not None:
        json_str = (
            json.dumps(extra_json) if isinstance(extra_json, dict) else extra_json
        )
        args.extend(["--json", json_str])
    runner = get_runner()
    return runner.run_json(args)
