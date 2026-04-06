"""MCP tool error types."""

from dataclasses import dataclass


@dataclass
class ToolError:
    """Structured error returned by MCP tools."""

    error: str
    message: str
    auth_url: str | None = None
