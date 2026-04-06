<<<<<<< HEAD
import json
import shutil
import subprocess


class DirectCliRunner:
=======
"""Direct CLI runner — subprocess wrapper for the `direct` command."""

import json
import shutil
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


class DirectCliRunner:
    """Executes direct-cli commands as subprocesses.

    The `direct` binary is installed via `pip install direct-cli`.
    It is invoked as: direct --token <token> <subcommand> [args] --format json
    """

>>>>>>> origin/main
    def __init__(self, token: str, *, timeout: int = 30) -> None:
        self._token = token
        self._timeout = timeout

    def run(self, args: list[str], *, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
<<<<<<< HEAD
        effective_timeout = timeout or self._timeout
        cmd = ["direct", "--token", self._token, *args]
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=effective_timeout)
        except subprocess.TimeoutExpired as e:
            raise CliTimeoutError(f"Timeout after {effective_timeout}s") from e
        except FileNotFoundError:
            raise CliNotFoundError("direct-cli not found")

    def run_json(self, args: list[str], *, timeout: int | None = None) -> list[dict] | dict:
        """Run CLI command and parse JSON output."""
        result = self.run(args, timeout=timeout)
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "401" in stderr or "Unauthorized" in stderr:
                raise CliAuthError(f"Authentication failed: {stderr}")
            raise CliError(f"CLI error (exit {result.returncode}): {stderr}")
        output = result.stdout.strip()
        if not output:
            return []
        data = json.loads(output)
        if isinstance(data, dict) and "error" in data:
            error_str = str(data["error"])
            if "401" in error_str or "Unauthorized" in error_str.lower():
                raise CliAuthError(f"Authentication failed: {error_str}")
            raise CliError(f"CLI returned error: {error_str}")
        return data

    def is_available(self) -> bool:
        return shutil.which("direct") is not None


class CliError(Exception):
=======
        """Run a direct-cli command.

        Args:
            args: CLI arguments (e.g., ["campaigns", "get", "--format", "json"]).
            timeout: Override default timeout in seconds.

        Returns:
            CompletedProcess with captured stdout/stderr.

        Raises:
            CliNotFoundError: If `direct` binary is not in PATH.
            CliTimeoutError: If the command exceeds the timeout.
        """
        effective_timeout = timeout if timeout is not None else self._timeout

        if not self.is_available():
            raise CliNotFoundError("direct-cli not found. Install: https://github.com/axisrow/direct-cli")

        cmd = ["direct", "--token", self._token, *args]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
            )
            return result
        except subprocess.TimeoutExpired as e:
            raise CliTimeoutError(f"direct-cli timed out after {effective_timeout}s") from e
        except FileNotFoundError:
            raise CliNotFoundError("direct-cli not found. Install: https://github.com/axisrow/direct-cli")

    def is_available(self) -> bool:
        """Check if the `direct` binary is available in PATH."""
        return shutil.which("direct") is not None

    def run_json(self, args: list[str], *, timeout: int | None = None) -> list[dict] | dict:
        """Run a command and parse JSON output.

        Returns:
            Parsed JSON response (list or dict).

        Raises:
            CliError: On CLI execution failures.
        """
        result = self.run(args, timeout=timeout)

        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "401" in stderr or "Unauthorized" in stderr:
                raise CliAuthError("Token expired or invalid")
            raise CliError(f"direct-cli failed (exit {result.returncode}): {stderr or result.stdout[:200]}")

        output = result.stdout.strip()
        if not output:
            return []

        try:
            return json.loads(output)
        except json.JSONDecodeError as e:
            raise CliError(f"Failed to parse CLI output as JSON: {e}") from e


class CliError(Exception):
    """Base error for CLI operations."""

>>>>>>> origin/main
    pass


class CliNotFoundError(CliError):
<<<<<<< HEAD
=======
    """The `direct` binary is not installed."""

>>>>>>> origin/main
    pass


class CliTimeoutError(CliError):
<<<<<<< HEAD
=======
    """The CLI command timed out."""

>>>>>>> origin/main
    pass


class CliAuthError(CliError):
<<<<<<< HEAD
=======
    """Authentication error (401)."""

>>>>>>> origin/main
    pass
