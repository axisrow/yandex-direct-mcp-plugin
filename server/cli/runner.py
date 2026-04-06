import json
import shutil
import subprocess


class DirectCliRunner:
    def __init__(self, token: str, *, timeout: int = 30) -> None:
        self._token = token
        self._timeout = timeout

    def run(self, args: list[str], *, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
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
    pass


class CliNotFoundError(CliError):
    pass


class CliTimeoutError(CliError):
    pass


class CliAuthError(CliError):
    pass
