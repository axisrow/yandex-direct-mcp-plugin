"""Audience CLI runner — subprocess wrapper for the `yac` command.

Second transport beside DirectCliRunner: MCP → yac (yandex-audience-cli) →
Yandex Audience API. The plugin never talks to the Audience API directly —
same transport-boundary rule as `direct` (#no-direct-api-bypass, applied to
Audience).

Differences from DirectCliRunner, all deliberate:

- No auth machinery: yac resolves its OAuth token itself
  (``--token`` > ``YANDEX_AUDIENCE_TOKEN`` env passthrough >
  ``~/.config/yandex-audience-cli/token`` file). The runner only makes sure
  the environment reaches the subprocess untouched.
- No version floor: yandex-audience-cli has no real PyPI release yet
  (0.0.1 stub as of 2026-11-04), so there is nothing to floor against and
  ``--version`` probing would be theater. A floor is added together with
  the first real release and the pins/bootstrap wiring.
- No JSON envelope tricks: yac prints the API response as plain JSON to
  stdout (`-o json`), errors go to stderr with exit 1. No notices, no
  per-action error codes, no browser fallback paths.

Error classes subclass the transport-neutral ``CliError`` taxonomy from
:mod:`server.cli.runner` so ``handle_cli_errors`` maps them without extra
plumbing: ``AudienceCliNotFoundError`` → ``cli_not_found``, everything else
→ ``unknown`` with the yac stderr in the message.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

from server.cli.runner import CliError, CliNotFoundError, _strip_ansi

_YAC_INSTALL_HINT = (
    "yac not found. Install yandex-audience-cli and make sure `yac` is on PATH: "
    "https://github.com/axisrow/yandex-audience-cli "
    "(until a real PyPI release exists, install editable from the repo checkout). "
    "Set YANDEX_AUDIENCE_CLI_PATH to pin a specific binary."
)

# rich (yac's JSON renderer) soft-wraps output at the console width it infers
# for non-TTY stdout — historically 80 columns. A wrapped JSON document can
# carry the newline INSIDE a string value, corrupting the value and breaking
# json.loads. shutil.get_terminal_size() honors COLUMNS before the 80 fallback,
# so widening it disables the wrap without touching yac.
_YAC_COLUMNS = "20000"


class AudienceCliError(CliError):
    """A `yac` command failed (non-zero exit or unparseable output)."""


class AudienceCliNotFoundError(CliNotFoundError):
    """The `yac` binary is not installed / not on PATH."""


def _find_yac() -> str | None:
    """Locate the `yac` binary.

    Search order (highest priority first):

    1. ``YANDEX_AUDIENCE_CLI_PATH`` env var (explicit override; broken paths
       fall through to the normal search, matching ``_find_direct``)
    2. ``shutil.which("yac")`` (system PATH)
    3. ``~/.local/bin/yac`` (``pip install --user``)

    No version probing: there is no published floor to verify against yet.
    """
    explicit = os.environ.get("YANDEX_AUDIENCE_CLI_PATH")
    if explicit and Path(explicit).is_file():
        return explicit
    if found := shutil.which("yac"):
        return found
    local_bin = Path.home() / ".local" / "bin" / "yac"
    if local_bin.is_file():
        return str(local_bin)
    return None


# Module-level cache, same rationale as DirectCliRunner: runners are built per
# request, so resolution must amortize per process, not per instance.
_UNCACHED: object = object()
_RESOLVED_YAC: str | None | object = _UNCACHED


def _resolve_yac_cached() -> str | None:
    """Return the cached resolved yac path, computing it on first call."""
    global _RESOLVED_YAC
    if _RESOLVED_YAC is _UNCACHED:
        _RESOLVED_YAC = _find_yac()
    return _RESOLVED_YAC  # type: ignore[return-value]


def _reset_yac_cache() -> None:
    """Test helper: clear the cached resolution so the next call re-resolves."""
    global _RESOLVED_YAC
    _RESOLVED_YAC = _UNCACHED


def _audience_env() -> dict[str, str]:
    """Build subprocess env for `yac`.

    ``YANDEX_AUDIENCE_TOKEN`` and ``YANDEX_AUDIENCE_BASE_URL`` pass through
    untouched — yac owns the token resolution. Only COLUMNS is adjusted (see
    the module docstring).
    """
    env = os.environ.copy()
    env.setdefault("COLUMNS", _YAC_COLUMNS)
    return env


def _raise_for_status(result: subprocess.CompletedProcess[str]) -> None:
    """Raise AudienceCliError for a non-zero yac exit."""
    if result.returncode == 0:
        return
    stderr = _strip_ansi(result.stderr).strip()
    raise AudienceCliError(
        f"yac failed (exit {result.returncode}): "
        f"{stderr or _strip_ansi(result.stdout)[:200]}",
        stderr=stderr,
    )


class AudienceCliRunner:
    """Executes `yac` commands as subprocesses.

    `yac` is installed via `pip install yandex-audience-cli`. It is invoked
    as: yac <group> <command> [args] (JSON output is the CLI default; the
    tool modules rely on it and never switch to `table`).
    """

    def __init__(self, *, timeout: int = 30) -> None:
        self._timeout = timeout

    def run(
        self, args: list[str], *, timeout: int | None = None
    ) -> subprocess.CompletedProcess[str]:
        """Run a yac command.

        Args:
            args: CLI arguments (e.g., ["segments", "list"]).
            timeout: Override default timeout in seconds.

        Returns:
            CompletedProcess with captured stdout/stderr.

        Raises:
            AudienceCliNotFoundError: If `yac` is not found.
            AudienceCliError: If the command exceeds the timeout.
        """
        effective_timeout = timeout if timeout is not None else self._timeout

        yac_bin = _resolve_yac_cached()
        if not yac_bin:
            raise AudienceCliNotFoundError(_YAC_INSTALL_HINT)

        try:
            return subprocess.run(
                [yac_bin, *args],
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                env=_audience_env(),
            )
        except subprocess.TimeoutExpired as e:
            raise AudienceCliError(f"yac timed out after {effective_timeout}s") from e
        except FileNotFoundError:
            raise AudienceCliNotFoundError(_YAC_INSTALL_HINT) from None

    def run_checked(
        self, args: list[str], *, timeout: int | None = None
    ) -> subprocess.CompletedProcess[str]:
        """Run a command and raise AudienceCliError on non-zero exit."""
        result = self.run(args, timeout=timeout)
        _raise_for_status(result)
        return result

    def run_json(
        self, args: list[str], *, timeout: int | None = None
    ) -> list[dict] | dict:
        """Run a command and parse its JSON stdout.

        Returns:
            Parsed JSON response (list or dict).

        Raises:
            AudienceCliError: On CLI execution or JSON parse failures.
        """
        result = self.run_checked(args, timeout=timeout)

        output = _strip_ansi(result.stdout).strip()
        if not output:
            return []

        try:
            parsed = json.loads(output)
        except json.JSONDecodeError as e:
            raise AudienceCliError(f"Failed to parse yac output as JSON: {e}") from e

        if isinstance(parsed, (dict, list)):
            return parsed
        return {"result": parsed}
