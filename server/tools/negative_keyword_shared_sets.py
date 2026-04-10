"""MCP tools for negative keyword shared sets management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors


@mcp.tool()
@handle_cli_errors
def negative_keyword_shared_sets_list(ids: str | None = None) -> list[dict] | dict:
    """List negative keyword shared sets.

    Args:
        ids: Comma-separated set IDs (optional).
    """
    args = ["negativekeywordsharedsets", "get", "--format", "json"]
    if ids:
        args.extend(["--ids", ids])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def negative_keyword_shared_sets_add(name: str, keywords: str) -> dict:
    """Add a negative keyword shared set.

    Args:
        name: Set name.
        keywords: Comma-separated negative keywords.
    """
    runner = get_runner()
    return runner.run_json(
        [
            "negativekeywordsharedsets",
            "add",
            "--name",
            name,
            "--keywords",
            keywords,
        ]
    )


@mcp.tool()
@handle_cli_errors
def negative_keyword_shared_sets_update(
    id: str,
    name: str | None = None,
    keywords: str | None = None,
    extra_json: str | None = None,
) -> dict:
    """Update a negative keyword shared set.

    Args:
        id: Set ID.
        name: New set name (optional).
        keywords: New comma-separated negative keywords (optional).
        extra_json: JSON string with additional parameters (optional).
    """
    if not any((name, keywords, extra_json)):
        return ToolError(
            error="missing_update_fields",
            message="Provide at least one of: name, keywords, extra_json",
        ).__dict__

    args = ["negativekeywordsharedsets", "update", "--id", id]
    if name is not None:
        args.extend(["--name", name])
    if keywords is not None:
        args.extend(["--keywords", keywords])
    if extra_json is not None:
        args.extend(["--json", extra_json])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def negative_keyword_shared_sets_delete(id: str) -> dict:
    """Delete a negative keyword shared set.

    Args:
        id: Set ID.
    """
    runner = get_runner()
    return runner.run_json(["negativekeywordsharedsets", "delete", "--id", id])
