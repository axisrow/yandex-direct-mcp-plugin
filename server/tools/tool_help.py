"""Meta-tool: on-demand detailed help for any MCP tool.

To keep the startup context small, every tool exposes only a short one-line
``description``. The full documentation (parameter reference, examples,
constraints) lives in each tool function's docstring and is served lazily
through ``tool_help`` instead of being loaded on every request.
"""

from server.main import mcp

_SHORT_DESCRIPTION = (
    "Get the full documentation for another tool: parameter reference, "
    "examples and constraints. Call this BEFORE using an unfamiliar tool — "
    "the tools themselves carry only a one-line summary. Pass the exact tool "
    "name (e.g. 'campaigns_add'); omit the name to list every available tool."
)


@mcp.tool(name="tool_help", description=_SHORT_DESCRIPTION)
def tool_help(name: str | None = None) -> dict:
    # Full docstring intentionally omitted from the schema — the short
    # description above is what the model sees; this body is the help payload.
    manager = mcp._tool_manager
    available = sorted(manager._tools.keys())

    if not name:
        return {"available_tools": available, "count": len(available)}

    requested = name.strip()
    tool = manager.get_tool(requested)
    if tool is None:
        return {
            "error": "unknown_tool",
            "message": f"No tool named {requested!r}.",
            "available_tools": available,
        }

    doc = (getattr(tool.fn, "__doc__", None) or "").strip()
    return {
        "tool": tool.name,
        "documentation": doc or "(no documentation available)",
    }
