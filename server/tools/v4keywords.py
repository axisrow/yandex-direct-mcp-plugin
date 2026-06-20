"""MCP tools for Yandex Direct v4 Live keyword-suggestion commands."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import require_non_empty_list, tool_error_dict


@mcp.tool(
    name="v4keywords_get_suggestion",
    description="Get related keyword suggestions via v4 Live GetKeywordsSuggestion (up to 20 phrases; spends API points). Call tool_help('v4keywords_get_suggestion') for parameters.",
)
@handle_cli_errors
def v4keywords_get_suggestion(keywords: list[str]) -> dict | list[dict]:
    """Get related keyword suggestions via v4 Live GetKeywordsSuggestion.

    Returns up to 20 suggested phrases per call. Spends API points
    (error_code=152 when the account runs out).

    Args:
        keywords: Source phrases to expand. At least one is required.
    """
    normalized = require_non_empty_list(
        keywords, error="missing_keywords", noun="keyword"
    )
    if isinstance(normalized, ToolError):
        return tool_error_dict(normalized)

    args = ["v4keywords", "get-suggestion"]
    for keyword in normalized:
        args.extend(["--keyword", keyword])
    args.extend(["--format", "json"])

    return get_runner().run_json(args)
