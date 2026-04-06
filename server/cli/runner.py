"""CLI runner protocol for subprocess execution."""

import subprocess
from typing import Protocol


class CliRunner(Protocol):
    """Protocol for executing direct-cli commands as subprocesses."""

    def run(self, args: list[str], *, timeout: int = 30) -> subprocess.CompletedProcess[str]:
        """Run a direct-cli command with the given arguments."""
        ...

    def is_available(self) -> bool:
        """Check if the direct-cli binary is available in PATH."""
        ...
