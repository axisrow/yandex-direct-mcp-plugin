"""Direct CLI runner — subprocess wrapper for the `direct` command."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Protocol

_DIRECT_INSTALL_HINT = (
    "direct not found. Install package direct-cli and run `direct`: "
    "https://github.com/axisrow/direct-cli"
)

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_ERROR_CODE_RE = re.compile(r"\berror_code=(\d+)\b")
_VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")

MIN_DIRECT_VERSION: tuple[int, int, int] = (0, 3, 10)


def _strip_ansi(text: str) -> str:
    """Remove ANSI color/style escape sequences from CLI output."""
    return _ANSI_ESCAPE_RE.sub("", text)


def _probe_direct_version(executable: str) -> tuple[int, int, int] | None:
    """Return the (major, minor, patch) version of a `direct` binary, or None.

    Used to skip stale installs when PATH contains an older `direct` that
    would shadow a newer one in ``~/.local/bin``. ``None`` means the probe
    could not extract a version (binary missing, broken install, no
    ``--version`` support) — callers treat that as "accept and let runtime
    surface the real error", not as "fail-closed".
    """
    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            timeout=3,
            env=os.environ.copy(),
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    match = _VERSION_RE.search(result.stdout or result.stderr)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _candidate_paths() -> list[str]:
    """Ordered list of `direct` binaries to consider.

    Order matches the historical search order, minus the
    ``YANDEX_DIRECT_CLI_PATH`` override (handled separately because that
    override skips version probing entirely):

    1. ``CLAUDE_PLUGIN_DATA/venv/bin/direct`` (plugin-managed venv)
    2. ``shutil.which("direct")`` (system PATH)
    3. ``~/.local/bin/direct`` (``pip install --user``)
    """
    candidates: list[str] = []

    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA", "")
    if plugin_data:
        venv_direct = Path(plugin_data) / "venv" / "bin" / "direct"
        if venv_direct.is_file():
            candidates.append(str(venv_direct))

    if found := shutil.which("direct"):
        candidates.append(found)

    local_bin = Path.home() / ".local" / "bin" / "direct"
    if local_bin.is_file():
        candidates.append(str(local_bin))

    return candidates


def _find_direct() -> str | None:
    """Locate the `direct` binary across common install locations.

    Search order:

    1. ``YANDEX_DIRECT_CLI_PATH`` env var (explicit override — version
       check skipped, "trust the user")
    2. ``CLAUDE_PLUGIN_DATA/venv/bin/direct`` (plugin-managed venv)
    3. System PATH (``shutil.which``)
    4. ``~/.local/bin/direct`` (``pip install --user``, macOS)

    For options 2-4 each candidate is probed with ``direct --version``
    and classified three ways:

    - **known-good** (parsed version >= ``MIN_DIRECT_VERSION``) — preferred
    - **known-stale** (parsed version < ``MIN_DIRECT_VERSION``) — always skipped
    - **unknown** (probe failed, returncode != 0, or unparseable output) —
      only used as a last-resort fallback when no known-good candidate exists

    The three-state classification is the fix for the PR #122 adversarial
    finding: a broken PATH ``direct`` (e.g. wrapper that exits with
    ``ModuleNotFoundError``) used to be classified as "accept" by the
    fail-open helper, shadowing a freshly installed
    ``~/.local/bin/direct``. Now it can be deferred so a later known-good
    candidate wins.
    """
    if explicit := os.environ.get("YANDEX_DIRECT_CLI_PATH"):
        return explicit if Path(explicit).is_file() else None

    first_unknown: str | None = None
    for candidate in _candidate_paths():
        version = _probe_direct_version(candidate)
        if version is None:
            if first_unknown is None:
                first_unknown = candidate
            continue
        if version >= MIN_DIRECT_VERSION:
            return candidate
        # Known-stale: keep searching for a known-good candidate.

    return first_unknown


def _direct_env() -> dict[str, str]:
    """Build subprocess env for `direct`."""
    return os.environ.copy()


class CliRunner(Protocol):
    """Protocol for executing `direct` commands as subprocesses."""

    def run(
        self, args: list[str], *, timeout: int = 30, input: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        """Run a `direct` command with the given arguments."""
        ...

    def is_available(self) -> bool:
        """Check if the `direct` binary is available in PATH."""
        ...


class DirectCliRunner:
    """Executes `direct` commands as subprocesses.

    The `direct` binary is installed via `pip install direct-cli`.
    It is invoked as: direct <subcommand> [args] --format json.
    Authentication is resolved by `direct` from its active profile.
    """

    # Sentinel distinct from a real `_find_direct()` return value so the
    # cache can tell "not yet resolved" apart from "resolved to None".
    _UNCACHED: object = object()

    def __init__(self, *, timeout: int = 30) -> None:
        self._timeout = timeout
        self._direct_bin: str | None | object = DirectCliRunner._UNCACHED

    def _resolved_direct(self) -> str | None:
        """Cache the resolved `direct` binary across calls.

        ``_find_direct()`` now spawns up to three `direct --version` probes,
        each capped at a 3s timeout. Without caching, every MCP tool call
        would re-run those probes; in a degraded environment that adds up
        to ~9s of latency per call before the real CLI invocation even
        starts. Cache once per runner instance.
        """
        if self._direct_bin is DirectCliRunner._UNCACHED:
            self._direct_bin = _find_direct()
        return self._direct_bin  # type: ignore[return-value]

    def run(
        self,
        args: list[str],
        *,
        timeout: int | None = None,
        input: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Run a direct command.

        Args:
            args: CLI arguments (e.g., ["campaigns", "get", "--format", "json"]).
            timeout: Override default timeout in seconds.
            input: Optional stdin text. Pass an empty string to force EOF and
                prevent interactive commands from inheriting a parent TTY.

        Returns:
            CompletedProcess with captured stdout/stderr.

        Raises:
            CliNotFoundError: If `direct` binary is not in PATH.
            CliTimeoutError: If the command exceeds the timeout.
        """
        effective_timeout = timeout if timeout is not None else self._timeout

        direct_bin = self._resolved_direct()
        if not direct_bin:
            raise CliNotFoundError(_DIRECT_INSTALL_HINT)

        cmd = [direct_bin, *args]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                env=_direct_env(),
                input=input,
            )
            return result
        except subprocess.TimeoutExpired as e:
            raise CliTimeoutError(f"direct timed out after {effective_timeout}s") from e
        except FileNotFoundError:
            raise CliNotFoundError(_DIRECT_INSTALL_HINT)

    def is_available(self) -> bool:
        """Check if the `direct` binary is available."""
        return self._resolved_direct() is not None

    def run_checked(
        self, args: list[str], *, timeout: int | None = None
    ) -> subprocess.CompletedProcess[str]:
        """Run a command and raise CliError on non-zero exit.

        Mirrors run_json's failure handling (auth / registration / error_code
        detection) but leaves stdout parsing to the caller — useful when the
        CLI emits TSV/CSV/table or writes the payload directly to a file.

        Raises:
            CliError: On CLI execution failures.
        """
        result = self.run(args, timeout=timeout)
        _raise_for_status(result)
        return result

    def run_json(
        self, args: list[str], *, timeout: int | None = None
    ) -> list[dict] | dict:
        """Run a command and parse JSON output.

        Returns:
            Parsed JSON response (list or dict).

        Raises:
            CliError: On CLI execution failures.
        """
        result = self.run_checked(args, timeout=timeout)

        output = result.stdout.strip()
        if not output:
            return []

        try:
            return json.loads(output)
        except json.JSONDecodeError as e:
            raise CliError(f"Failed to parse CLI output as JSON: {e}") from e


def _raise_for_status(result: subprocess.CompletedProcess[str]) -> None:
    """Raise a structured CliError (or subclass) for a non-zero exit code."""
    if result.returncode == 0:
        return
    stderr = _strip_ansi(result.stderr).strip()
    error_code: int | None = None
    if match := _ERROR_CODE_RE.search(stderr):
        error_code = int(match.group(1))
    if "401" in stderr or "Unauthorized" in stderr or error_code == 53:
        raise CliAuthError("Token expired or invalid")
    if error_code == 58:
        raise CliRegistrationError(
            "Незаконченная регистрация. "
            "Вам нужно подать или переподать заявку на регистрацию приложения "
            "в Яндекс.Директ: https://direct.yandex.ru → Инструменты → API → Мои заявки."
        )
    raise CliError(
        f"direct failed (exit {result.returncode}): {stderr or _strip_ansi(result.stdout)[:200]}",
        error_code=error_code,
        stderr=stderr,
    )


class CliError(Exception):
    """Base error for CLI operations."""

    def __init__(
        self,
        message: str,
        *,
        error_code: int | None = None,
        stderr: str | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.stderr = stderr


class CliNotFoundError(CliError):
    """The `direct` binary is not installed."""

    pass


class CliTimeoutError(CliError):
    """The CLI command timed out."""

    pass


class CliAuthError(CliError):
    """Authentication error (401)."""

    pass


class CliRegistrationError(CliError):
    """Application not registered in Yandex.Direct (error 58)."""

    pass
