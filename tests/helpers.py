"""Shared test helpers."""

import importlib
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from types import ModuleType
from unittest.mock import MagicMock, patch


def completed(
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
) -> subprocess.CompletedProcess:
    """Return a subprocess result matching DirectCliRunner expectations."""
    return subprocess.CompletedProcess(
        args=["direct"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def mock_runner(
    return_value=None,
    *,
    checked_return_value: subprocess.CompletedProcess | None = None,
) -> MagicMock:
    """Return a mock runner with configurable JSON and checked results."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    runner.run_checked.return_value = (
        checked_return_value if checked_return_value is not None else completed()
    )
    return runner


@contextmanager
def import_tool_module_without_registration(module_name: str) -> Iterator[ModuleType]:
    """Import a tool module without adding its decorators to the global MCP.

    Optional tool modules normally register on import. Tests need their plain Python
    callables without changing the default MCP surface for the rest of the suite.
    """

    from server.main import mcp

    parent_name, _, child_name = module_name.rpartition(".")
    parent = importlib.import_module(parent_name)
    previous_module = sys.modules.pop(module_name, None)
    previous_parent_attr = getattr(parent, child_name, None)
    had_parent_attr = hasattr(parent, child_name)
    registry = mcp._tool_manager._tools
    registered_before = set(registry)

    def passthrough_tool(*args, **kwargs):
        if len(args) == 1 and callable(args[0]) and not kwargs:
            return args[0]
        return lambda function: function

    with patch.object(mcp, "tool", new=passthrough_tool):
        try:
            yield importlib.import_module(module_name)
        finally:
            sys.modules.pop(module_name, None)
            for added_name in set(registry) - registered_before:
                registry.pop(added_name, None)
            if previous_module is not None:
                sys.modules[module_name] = previous_module
            if had_parent_attr:
                setattr(parent, child_name, previous_parent_attr)
            else:
                delattr(parent, child_name)
