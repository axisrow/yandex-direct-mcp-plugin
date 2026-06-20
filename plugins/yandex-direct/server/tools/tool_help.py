"""Meta-tool: on-demand detailed help for any MCP tool.

To keep the startup context small, every tool exposes only a short one-line
``description``. The full documentation (parameter reference, examples,
constraints) lives in each tool function's docstring and is served lazily
through ``tool_help`` instead of being loaded on every request.

``tool_help`` reaches into a few private FastMCP internals
(``mcp._tool_manager``, ``manager._tools``, ``tool.fn``) because the public
API does not expose a tool's underlying function/docstring. Those accesses are
wrapped defensively: if a future ``mcp`` upgrade renames or removes them,
``tool_help`` returns a graceful error dict instead of raising — important
because every other tool's description now points here for its parameters, so
a hard crash would cascade across the whole plugin. The ``mcp`` dependency is
also version-pinned in ``pyproject.toml`` to bound that risk.
"""

from server.main import mcp

_SHORT_DESCRIPTION = (
    "Get the full documentation for another tool: parameter reference, "
    "examples and constraints. Call this BEFORE using an unfamiliar tool — "
    "the tools themselves carry only a one-line summary. Pass the exact tool "
    "name (e.g. 'campaigns_add'); omit the name to list every available tool."
)

_INTERNAL_ERROR = {
    "error": "tool_manager_unavailable",
    "message": (
        "Could not read the MCP tool registry — the mcp library's internal "
        "API may have changed. Upgrade or reinstall the plugin."
    ),
}


def _list_tool_names() -> list[str] | None:
    """Return all registered tool names, or None if mcp internals changed."""
    try:
        return sorted(mcp._tool_manager._tools.keys())
    except AttributeError:
        return None


@mcp.tool(name="tool_help", description=_SHORT_DESCRIPTION)
def tool_help(name: str | None = None) -> dict:
    """Return the full documentation for any registered MCP tool.

    Every tool in this plugin exposes only a one-line summary so the startup
    context stays small; the full parameter reference, examples and
    constraints live in each tool's docstring and are served here on demand.

    Args:
        name: Exact tool name to document (e.g. 'campaigns_add'). Omit it to
            get the list of all available tool names instead.

    Returns:
        - With a valid name: {"tool", "documentation"} — the tool's full docs.
        - Without a name: {"available_tools", "count"} — every tool name.
        - Unknown name: {"error": "unknown_tool", "message", "available_tools"}.
    """
    available = _list_tool_names()
    if available is None:
        return dict(_INTERNAL_ERROR)

    if not name:
        return {"available_tools": available, "count": len(available)}

    requested = name.strip()
    try:
        tool = mcp._tool_manager.get_tool(requested)
        doc = (getattr(tool.fn, "__doc__", None) or "").strip() if tool else None
    except AttributeError:
        return dict(_INTERNAL_ERROR)

    if tool is None:
        return {
            "error": "unknown_tool",
            "message": f"No tool named {requested!r}.",
            "available_tools": available,
        }

    return {
        "tool": tool.name,
        "documentation": doc or "(no documentation available)",
    }
