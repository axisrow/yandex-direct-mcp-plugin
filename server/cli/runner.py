"""CLI subprocess runner for direct-cli."""

from __future__ import annotations

import subprocess


class DirectCliRunner:
    """Run direct-cli commands as subprocesses."""

    def __init__(self, cli_path: str = "direct") -> None:
        """Initialize the runner.

        Args:
            cli_path: Path or name of the direct-cli executable.
        """
        self._cli_path = cli_path

    def run(self, args: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
        """Execute a direct-cli command.

        Args:
            args: Command-line arguments to pass to direct-cli.
            timeout: Maximum execution time in seconds.

        Returns:
            CompletedProcess with stdout and stderr captured as strings.

        Raises:
            FileNotFoundError: If direct-cli is not found on PATH.
            subprocess.TimeoutExpired: If the command exceeds the timeout.
        """
        ...
