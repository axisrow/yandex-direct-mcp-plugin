"""MCP tools for negative keyword shared sets (legacy aliases).

These tools wrap the ``negativekeywords`` CLI subcommand, which is an alias
for ``negativekeywordsharedsets``.  Prefer the canonical wrappers in
``negative_keyword_shared_sets.py`` — the tools here are kept for
backward compatibility with existing skill/prompt references.
"""

from server.main import mcp
from server.tools import get_runner, handle_cli_errors

from server.tools.helpers import check_batch_limit


@mcp.tool()
@handle_cli_errors
def negative_keywords_list(ids: str | None = None) -> list[dict] | dict:
    """List negative keyword shared sets.

    Args:
        ids: Comma-separated set IDs (optional, max 10).
    """
    if ids is not None:
        batch_error = check_batch_limit(ids)
        if batch_error:
            return batch_error.__dict__

    args = ["negativekeywords", "get", "--format", "json"]
    if ids:
        args.extend(["--ids", ids])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def negative_keywords_add(name: str, keywords: str) -> dict:
    """Add a negative keyword shared set.

    Args:
        name: Set name.
        keywords: Comma-separated negative keywords.
    """
    runner = get_runner()
    return runner.run_json(
        [
            "negativekeywords",
            "add",
            "--name",
            name,
            "--keywords",
            keywords,
            "--format",
            "json",
        ]
    )


@mcp.tool()
@handle_cli_errors
def negative_keywords_update(
    id: str,
    name: str | None = None,
    keywords: str | None = None,
) -> dict:
    """Update a negative keyword shared set.

    Args:
        id: Set ID.
        name: New set name (optional).
        keywords: New comma-separated negative keywords (optional).
    """
    args = ["negativekeywords", "update", "--id", id]
    if name is not None:
        args.extend(["--name", name])
    if keywords is not None:
        args.extend(["--keywords", keywords])
    args.extend(["--format", "json"])
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool()
@handle_cli_errors
def negative_keywords_delete(ids: str) -> dict:
    """Delete negative keyword shared sets.

    Args:
        ids: Comma-separated set IDs (max 10).
    """
    batch_error = check_batch_limit(ids)
    if batch_error:
        return batch_error.__dict__

    runner = get_runner()
    result = runner.run_json(
        ["negativekeywords", "delete", "--id", ids, "--format", "json"]
    )
    return result
