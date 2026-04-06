"""MCP tool definitions for Yandex.Direct."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ToolError:
    """Structured error returned by MCP tools."""

    code: str
    message: str
