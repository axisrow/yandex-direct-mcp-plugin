"""MCP tools for Yandex Direct v4 Live keyword-suggestion commands."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors


def _normalize_keywords(keywords: list[str] | None) -> list[str]:
    if not keywords:
        return []
    return [keyword.strip() for keyword in keywords if keyword.strip()]


@mcp.tool(name="v4keywords_get_suggestion")
@handle_cli_errors
def v4keywords_get_suggestion(keywords: list[str]) -> dict | list[dict]:
    """Get related keyword suggestions via v4 Live GetKeywordsSuggestion.

    Returns up to 20 suggested phrases per call. Spends API points
    (error_code=152 when the account runs out).

    Args:
        keywords: Source phrases to expand. At least one is required.
    """
    normalized = _normalize_keywords(keywords)
    if not normalized:
        return ToolError(
            error="missing_keywords",
            message="Provide at least one keyword.",
        ).__dict__

    args = ["v4keywords", "get-suggestion"]
    for keyword in normalized:
        args.extend(["--keyword", keyword])
    args.extend(["--format", "json"])

    return get_runner().run_json(args)
