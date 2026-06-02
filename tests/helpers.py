"""Shared test helpers."""

import subprocess
from unittest.mock import MagicMock


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
