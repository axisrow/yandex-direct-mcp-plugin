"""Direct CLI runner — subprocess wrapper for the `direct` command."""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Protocol

_DIRECT_INSTALL_HINT = (
    "direct not found. Install package direct-cli and run `direct`: "
    "https://github.com/axisrow/direct-cli"
)

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_ERROR_CODE_RE = re.compile(r"\berror_code=(\d+)\b")
# Anchor on the literal program token ``direct`` (or its package alias
# ``direct-cli``) followed by ``version X.Y.Z``. Matches Click's standard
# ``version_option`` output ``"direct, version X.Y.Z"`` while rejecting
# unrelated banner lines like ``"Python version 3.12.0"`` that would
# otherwise be picked up by an unanchored regex and promote a stale
# wrapper to known-good.
_VERSION_RE = re.compile(
    r"\bdirect(?:-cli)?\b[,\s]+version\s+(\d+)\.(\d+)\.(\d+)",
    re.IGNORECASE,
)

MIN_DIRECT_VERSION: tuple[int, int, int] = (0, 3, 11)


def _strip_ansi(text: str) -> str:
    """Remove ANSI color/style escape sequences from CLI output."""
    return _ANSI_ESCAPE_RE.sub("", text)


def _probe_direct_version(executable: str) -> tuple[int, int, int] | None:
    """Return the (major, minor, patch) version of a `direct` binary, or None.

    Used to skip stale installs when PATH contains an older `direct` that
    would shadow a newer one in ``~/.local/bin``. ``None`` means the probe
    could not extract a version (binary missing, broken install, no
    ``--version`` support); callers in ``_find_direct`` defer these
    candidates as a last-resort fallback rather than rejecting them
    outright.
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
    """Ordered list of non-override `direct` binaries to consider.

    Order matches the historical search order, minus the
    ``YANDEX_DIRECT_CLI_PATH`` override (handled separately as the
    highest-priority candidate by ``_find_direct``):

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

    Search order (highest priority first):

    1. ``YANDEX_DIRECT_CLI_PATH`` env var (explicit override)
    2. ``CLAUDE_PLUGIN_DATA/venv/bin/direct`` (plugin-managed venv)
    3. System PATH (``shutil.which``)
    4. ``~/.local/bin/direct`` (``pip install --user``, macOS)

    Every candidate is probed with ``direct --version`` and classified
    three ways: known-good (>= ``MIN_DIRECT_VERSION``), known-stale
    (below the floor), unknown (probe failed / unparseable output).

    The override (step 1) is **strict**: if the user explicitly pinned a
    stale path, return ``None`` instead of silently falling back to a
    different binary. A broken/unprobable explicit path still defers to
    later known-good candidates (treated as unknown) so a fresh install
    can win when the override is misconfigured but not provably wrong.

    For steps 2-4, known-good wins on first match, known-stale is
    skipped, and unknown candidates are deferred — used only when no
    known-good candidate exists anywhere in the search order.

    The three-state classification fixes the PR #122 adversarial
    findings: (a) a broken PATH ``direct`` no longer shadows a freshly
    installed ``~/.local/bin/direct``; (b) ``YANDEX_DIRECT_CLI_PATH``
    can no longer pin the plugin to a stale CLI.
    """
    first_unknown: str | None = None

    explicit = os.environ.get("YANDEX_DIRECT_CLI_PATH")
    if explicit and Path(explicit).is_file():
        version = _probe_direct_version(explicit)
        if version is None:
            # Broken explicit override: defer but keep looking for a
            # known-good fallback. If nothing better turns up we still
            # return this path as a last resort.
            first_unknown = explicit
        elif version >= MIN_DIRECT_VERSION:
            return explicit
        else:
            # Stale explicit override: fail-fast. The user pinned this
            # path; silently swapping it for a different binary would
            # violate that contract.
            return None

    for candidate in _candidate_paths():
        version = _probe_direct_version(candidate)
        if version is None:
            if first_unknown is None:
                first_unknown = candidate
            continue
        if version >= MIN_DIRECT_VERSION:
            return candidate
        # Known-stale fallback candidate: keep searching for known-good.

    if first_unknown is not None:
        _warn_unverified_direct(first_unknown)
    return first_unknown


def _warn_unverified_direct(path: str) -> None:
    """Surface the fail-open fallback so users notice an unverified binary.

    Adversarial-review-round-4 finding 1 wanted hard fail-closed for
    unknown-version candidates. Pure fail-closed breaks legitimate edge
    cases (fresh installs whose ``--version`` momentarily errors, very
    old CLI binaries without ``--version`` support). The compromise is
    warn-and-use: pick the candidate so MCP tool calls keep working,
    but write a single diagnostic to stderr so the user sees that the
    floor could not be verified. The module-level cache makes this fire
    at most once per process.
    """
    sys.stderr.write(
        f"warning: direct binary at {path} could not be verified "
        f"as direct-cli >= {'.'.join(map(str, MIN_DIRECT_VERSION))}; "
        "using anyway — set YANDEX_DIRECT_CLI_PATH to override.\n"
    )


# Module-level cache: ``DirectCliRunner`` instances are constructed per
# request via ``get_runner()``, so an instance-level cache would still
# re-probe on every MCP tool call. A single resolution per process — with
# the version probe and ANSI-laden output costs amortised — keeps the
# steady-state cost negligible and the worst-case cost bounded.
_UNCACHED: object = object()
_RESOLVED_DIRECT: str | None | object = _UNCACHED


def _resolve_direct_cached() -> str | None:
    """Return the cached resolved binary path, computing it on first call."""
    global _RESOLVED_DIRECT
    if _RESOLVED_DIRECT is _UNCACHED:
        _RESOLVED_DIRECT = _find_direct()
    return _RESOLVED_DIRECT  # type: ignore[return-value]


def _reset_direct_cache() -> None:
    """Test helper: clear the cached resolution so the next call re-resolves."""
    global _RESOLVED_DIRECT
    _RESOLVED_DIRECT = _UNCACHED


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

    def __init__(self, *, timeout: int = 30) -> None:
        self._timeout = timeout

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

        direct_bin = _resolve_direct_cached()
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
        return _resolve_direct_cached() is not None

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
            parsed = json.loads(output)
        except json.JSONDecodeError as e:
            raise CliError(f"Failed to parse CLI output as JSON: {e}") from e

        if isinstance(parsed, (dict, list)):
            return parsed
        return {"result": parsed}


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
