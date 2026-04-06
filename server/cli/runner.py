import json
import shutil
import subprocess


class CliError(Exception):
    pass


class CliNotFoundError(CliError):
    pass


class CliTimeoutError(CliError):
    pass


class CliAuthError(CliError):
    pass


class DirectCliRunner:
    def __init__(self, token: str, *, timeout: int = 30):
        self._token = token
        self._timeout = timeout

    def run(self, args: list[str], *, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
        effective_timeout = timeout or self._timeout
        cmd = ["direct", "--token", self._token, *args]
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=effective_timeout)
        except subprocess.TimeoutExpired as e:
            raise CliTimeoutError(str(e)) from e
        except FileNotFoundError:
            raise CliNotFoundError("direct-cli not found")

    def is_available(self) -> bool:
        return shutil.which("direct") is not None

    def run_json(self, args: list[str], *, timeout: int | None = None) -> list[dict] | dict:
        result = self.run(args, timeout=timeout)
        if result.returncode != 0:
            if "401" in result.stderr or "Unauthorized" in result.stderr:
                raise CliAuthError("Auth error")
            raise CliError(f"CLI failed: {result.stderr}")
        if not result.stdout.strip():
            return []
        return json.loads(result.stdout.strip())
