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

_NOTICE_LINE_RE = re.compile(r"^\s*[ℹ✓⚠]\s+(?P<message>.*)$")

# These are stable, user-facing fragments owned by direct-cli. Keep every
# pattern as a literal substring (rather than a loose keyword soup): the tests
# verify that each one still exists in the installed
# ``direct_cli.browser.session`` source, so upstream wording changes fail CI
# instead of silently degrading a browser failure back to ``unknown``.
_BROWSER_ERROR_ANCHORS: tuple[tuple[str, str], ...] = (
    ("captcha", "Yandex served a SmartCaptcha challenge instead of the Direct page"),
    ("auth", "Yandex served its login page instead of Direct"),
    ("auth", "waiting for login to"),
    (
        "auth",
        "verifying the session. Retry `direct playwright login`",
    ),
    ("auth", "No persistent browser profile found at"),
    ("profile", "Chrome profile directory"),
    ("profile", "Chrome profile"),
    ("profile", "browser profile"),
    ("profile", "Chrome cookie"),
    ("profile", "Keychain"),
    ("browser", "playwright is required for this command"),
)
_BROWSER_ERROR_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (error_kind, re.compile(re.escape(anchor)))
    for error_kind, anchor in _BROWSER_ERROR_ANCHORS
)

BROWSER_DEFAULT_TIMEOUT = 180
BROWSER_LOGIN_TIMEOUT = 300

# JavaScript MCP hosts cannot represent integers outside this range exactly.
# Keep the original JSON token as a string before the parsed CLI response
# crosses the MCP boundary; smaller counters and monetary values stay numeric.
_MAX_SAFE_JSON_INTEGER = 2**53 - 1


def _parse_json_integer(value: str) -> int | str:
    """Parse safe JSON integers normally and preserve larger ones as strings."""
    parsed = int(value)
    if -_MAX_SAFE_JSON_INTEGER <= parsed <= _MAX_SAFE_JSON_INTEGER:
        return parsed
    return value


# direct-cli surfaces errors two ways: top-level HTTP API errors as
# "error_code=<N>" and per-action result errors as "Error <N>: <message>"
# (output.py _format_api_result_error). Match both so action-level codes
# (8800 not-found, 8300/8301 can't-delete, 9300/7001 limit) are extracted and
# their hints/classifications fire. (#170-2)
_ERROR_CODE_RE = re.compile(r"(?:error_code=|\bError\s+)(\d+)\b")
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

MIN_DIRECT_VERSION: tuple[int, int, int] = (0, 5, 2)


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


# Paths already warned about this process — keeps _warn_unverified_direct
# idempotent per path so a noisy diagnostic does not repeat on every
# re-resolution. (#170-29)
_WARNED_UNVERIFIED_PATHS: set[str] = set()


def _warn_unverified_direct(path: str) -> None:
    """Surface the fail-open fallback so users notice an unverified binary.

    Adversarial-review-round-4 finding 1 wanted hard fail-closed for
    unknown-version candidates. Pure fail-closed breaks legitimate edge
    cases (fresh installs whose ``--version`` momentarily errors, very
    old CLI binaries without ``--version`` support). The compromise is
    warn-and-use: pick the candidate so MCP tool calls keep working,
    but write a single diagnostic to stderr so the user sees that the
    floor could not be verified. The module-level ``_WARNED_UNVERIFIED_PATHS``
    cache makes this fire at most once per path per process.
    """
    if path in _WARNED_UNVERIFIED_PATHS:
        return
    _WARNED_UNVERIFIED_PATHS.add(path)
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
    _WARNED_UNVERIFIED_PATHS.clear()


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
            raw_partial = getattr(e, "stdout", None) or getattr(e, "output", None)
            partial_stdout = (
                raw_partial.decode("utf-8", errors="replace")
                if isinstance(raw_partial, bytes)
                else raw_partial
            )
            raise CliTimeoutError(
                f"direct timed out after {effective_timeout}s",
                partial_stdout=partial_stdout,
            ) from e
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

        Note on warnings: Yandex Direct per-action Warnings (with their
        ``Details``) travel *inside* the JSON payload the CLI prints to stdout
        — e.g. each ``AddResults`` element carries its own ``Warnings`` list —
        so they are already returned to the caller verbatim and are never
        truncated here. Should the CLI additionally emit a diagnostic to stderr
        on a *successful* (exit 0) run, it would otherwise be dropped silently;
        that residual stderr is surfaced as ``_cli_warnings`` rather than
        swallowed (issue #256). Empty stderr leaves the payload untouched.
        """
        result = self.run_checked(args, timeout=timeout)

        output = result.stdout.strip()
        residual_stderr = _strip_ansi(result.stderr).strip()

        if not output:
            return _attach_cli_warnings([], residual_stderr)

        try:
            parsed = json.loads(output, parse_int=_parse_json_integer)
        except json.JSONDecodeError as e:
            raise CliError(f"Failed to parse CLI output as JSON: {e}") from e

        if isinstance(parsed, (dict, list)):
            return _attach_cli_warnings(parsed, residual_stderr)
        return _attach_cli_warnings({"result": parsed}, residual_stderr)

    def run_json_lenient(
        self,
        args: list[str],
        *,
        timeout: int | None = None,
        allow_nonzero: bool = False,
    ) -> list[dict] | dict:
        """Parse JSON surrounded by direct-cli informational notices.

        Browser commands can print ``ℹ``/``✓``/``⚠`` notices to stdout before
        or after their JSON payload. Unlike :meth:`run_json`, this method
        deliberately accepts that narrow envelope while still failing closed
        on unrelated stdout text or malformed JSON.
        """
        # Masters lifecycle batches emit the complete per-ID result array and
        # then use exit 2 (or 1) to report that one of the IDs failed.  Preserve
        # that payload for callers which explicitly opt in; all other commands
        # retain the existing fail-closed behavior.  A timeout mid-batch keeps
        # the same contract: whatever per-ID results were printed before the
        # kill come back marked as a partial timeout outcome.
        try:
            result = (
                self.run(args, timeout=timeout)
                if allow_nonzero
                else self.run_checked(args, timeout=timeout)
            )
        except CliTimeoutError as exc:
            if not allow_nonzero:
                raise
            partial = _strip_ansi(exc.partial_stdout or "").strip()
            if not partial:
                raise
            try:
                parsed_partial, partial_notices = _parse_lenient_payload(partial)
            except CliError:
                raise exc from None
            if isinstance(parsed_partial, list):
                return _attach_notices(
                    {
                        "results": parsed_partial,
                        "_timeout_partial": True,
                        "_cli_error": (
                            f"{exc}; the listed results completed before the "
                            "timeout, outcomes for the remaining IDs are unknown"
                        ),
                    },
                    partial_notices,
                )
            parsed_partial["_timeout_partial"] = True
            parsed_partial.setdefault(
                "_cli_error",
                f"{exc}; parsed from partial output before the timeout",
            )
            return parsed_partial

        output = _strip_ansi(result.stdout).strip()
        residual_stderr = _strip_ansi(result.stderr).strip()

        if not output:
            if allow_nonzero:
                _raise_for_status(result)
            return _attach_cli_warnings([], residual_stderr)

        parsed, notices = _parse_lenient_payload(output)
        parsed = _attach_notices(parsed, notices)
        if result.returncode == 0:
            parsed = _attach_cli_warnings(parsed, residual_stderr)
        if allow_nonzero and result.returncode != 0:
            if isinstance(parsed, list):
                return {
                    "results": parsed,
                    "_partial_failure": True,
                    "_cli_error": residual_stderr,
                }
            parsed.setdefault("_partial_failure", True)
            parsed.setdefault("_cli_error", residual_stderr)
        return parsed


def _strip_single_line_edge_notices(text: str) -> tuple[str, list[str]]:
    """Remove sentinel-prefixed, single-line notices at either output edge."""
    lines = text.splitlines()
    leading: list[str] = []
    trailing: list[str] = []

    while lines and (match := _NOTICE_LINE_RE.match(lines[0])):
        leading.append(match.group("message").strip())
        lines.pop(0)
    while lines and (match := _NOTICE_LINE_RE.match(lines[-1])):
        trailing.append(match.group("message").strip())
        lines.pop()

    trailing.reverse()
    return "\n".join(lines).strip(), [*leading, *trailing]


def _parse_lenient_payload(output: str) -> tuple[list[dict] | dict, list[str]]:
    """Parse stdout that may wrap its JSON payload in informational notices.

    Accepts either a direct JSON document or a largest balanced JSON fragment
    surrounded by notices; anything else raises CliError (fail closed).
    """
    stripped_output, notices = _strip_single_line_edge_notices(output)
    try:
        parsed = json.loads(stripped_output, parse_int=_parse_json_integer)
    except json.JSONDecodeError as original_error:
        fragment = _largest_balanced_json_fragment(output)
        if fragment is None:
            raise CliError(
                f"Failed to parse CLI output as JSON: {original_error}"
            ) from original_error

        fragment_start, fragment_end = fragment
        leading_notices = _parse_notice_region(output[:fragment_start])
        trailing_notices = _parse_notice_region(output[fragment_end:])
        if leading_notices is None or trailing_notices is None:
            raise CliError(
                f"Failed to parse CLI output as JSON: {original_error}"
            ) from original_error

        notices = [*leading_notices, *trailing_notices]
        fragment_text = output[fragment_start:fragment_end]
        try:
            parsed = json.loads(fragment_text, parse_int=_parse_json_integer)
        except json.JSONDecodeError as fragment_error:
            raise CliError(
                f"Failed to parse CLI output as JSON: {fragment_error}"
            ) from fragment_error

    if not isinstance(parsed, (dict, list)):
        parsed = {"result": parsed}
    return parsed, notices


def _parse_notice_region(text: str) -> list[str] | None:
    """Parse one outer stdout region as sentinel-led, possibly multiline notices.

    ``None`` means the region contained non-notice text. Continuation lines are
    accepted only after a sentinel line, keeping the fallback narrow enough not
    to hide arbitrary CLI corruption.
    """
    lines = text.strip().splitlines()
    if not lines:
        return []

    notices: list[str] = []
    current: list[str] | None = None
    for line in lines:
        if match := _NOTICE_LINE_RE.match(line):
            if current is not None:
                notices.append("\n".join(current).strip())
            current = [match.group("message").strip()]
        elif current is None:
            return None
        else:
            current.append(line.strip())
    if current is not None:
        notices.append("\n".join(current).strip())
    return notices


def _largest_balanced_json_fragment(text: str) -> tuple[int, int] | None:
    """Return bounds of the largest balanced object/array in ``text``.

    Brackets inside JSON strings are ignored, including escaped quotes. The
    caller still runs ``json.loads`` on the selected fragment; balancing alone
    never turns malformed data into a successful response.
    """
    pairs = {"{": "}", "[": "]"}
    candidates: list[tuple[int, int]] = []
    stack: list[str] = []
    start: int | None = None
    in_string = False
    escaped = False

    for index, char in enumerate(text):
        if start is None:
            if char in pairs:
                start = index
                stack.append(pairs[char])
            continue

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char in pairs:
            stack.append(pairs[char])
        elif char in ("}", "]"):
            if char != stack[-1]:
                # A mismatched candidate is not valid JSON. Reset and keep
                # scanning for the next independent object/array.
                start = None
                stack.clear()
                in_string = False
                escaped = False
                continue
            stack.pop()
            if not stack:
                candidates.append((start, index + 1))
                start = None

    if not candidates:
        return None
    return max(candidates, key=lambda bounds: bounds[1] - bounds[0])


def _attach_notices(parsed: list[dict] | dict, notices: list[str]) -> list[dict] | dict:
    """Attach stdout notices without changing a top-level list's wire shape."""
    notices = [notice for notice in notices if notice]
    if not notices:
        return parsed
    if isinstance(parsed, dict):
        existing = parsed.get("notices")
        if existing is None:
            parsed["notices"] = notices
        elif isinstance(existing, list):
            existing.extend(notices)
        else:
            sys.stderr.write(
                "direct emitted stdout notices but the JSON payload already "
                "contains a non-list 'notices' field\n"
            )
        return parsed
    sys.stderr.write(f"direct emitted stdout notices: {'; '.join(notices)}\n")
    return parsed


def _attach_cli_warnings(
    parsed: list[dict] | dict, residual_stderr: str
) -> list[dict] | dict:
    """Surface a successful run's residual stderr instead of dropping it.

    When ``residual_stderr`` is empty (the common case — Direct warnings live in
    the stdout JSON, not stderr), the parsed payload is returned unchanged so the
    wire contract and shape are identical to before. When the CLI writes
    something to stderr on an exit-0 run:

    - dict payload → a ``_cli_warnings`` key is added (non-destructive; the CLI
      response never uses that reserved key).
    - list payload → the shape is preserved (a ``*_get`` result stays a bare
      array the LLM can iterate). Wrapping it in a dict would silently change
      the response contract, so the diagnostic is written to the server's stderr
      instead of reshaping the payload (issue #256, review Finding 3). In
      practice ``direct`` writes nothing to stderr on success, so this branch is
      a defensive backstop, not a routine path.
    """
    if not residual_stderr:
        return parsed
    if isinstance(parsed, dict):
        # Do not clobber a real API field named _cli_warnings (there is none).
        parsed.setdefault("_cli_warnings", residual_stderr)
        return parsed
    # List payload: never reshape it into a dict — preserve the array contract
    # and surface the stray diagnostic out-of-band.
    sys.stderr.write(f"direct emitted stderr on a successful run: {residual_stderr}\n")
    return parsed


def _raise_for_status(result: subprocess.CompletedProcess[str]) -> None:
    """Raise a structured CliError (or subclass) for a non-zero exit code."""
    if result.returncode == 0:
        return
    stderr = _strip_ansi(result.stderr).strip()
    error_code: int | None = None
    if match := _ERROR_CODE_RE.search(stderr):
        error_code = int(match.group(1))
    # Rely on the structured signals, not a bare "401" substring: request_ids
    # are long random digit runs that frequently contain "401", which used to
    # misclassify funds/limit errors as auth failures. (#170-3)
    if error_code == 53 or "Unauthorized" in stderr:
        raise CliAuthError("Token expired or invalid")
    if error_code == 58:
        raise CliRegistrationError(
            "Незаконченная регистрация. "
            "Вам нужно подать или переподать заявку на регистрацию приложения "
            "в Яндекс.Директ: https://direct.yandex.ru → Инструменты → API → Мои заявки."
        )
    # Browser ClickExceptions do not carry Direct API error codes. Restrict the
    # text classifier to that code-less transport shape so an API error_detail
    # that happens to mention Chrome/Keychain keeps its existing classification.
    if error_code is None:
        browser_error_types: dict[str, type[CliBrowserError]] = {
            "browser": CliBrowserError,
            "auth": CliBrowserAuthError,
            "captcha": CliBrowserCaptchaError,
            "profile": CliBrowserProfileError,
        }
        for error_kind, pattern in _BROWSER_ERROR_PATTERNS:
            if pattern.search(stderr):
                error_type = browser_error_types[error_kind]
                raise error_type(
                    f"direct failed (exit {result.returncode}): {stderr}",
                    error_code=error_code,
                    stderr=stderr,
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


class CliTimeoutError(CliError):
    """The CLI command timed out.

    On POSIX, subprocess.run attaches the stdout collected before the kill to
    TimeoutExpired; keep it decoded here so batch callers can report which
    per-ID outcomes completed before the process died.
    """

    def __init__(self, message: str, *, partial_stdout: str | None = None) -> None:
        super().__init__(message)
        self.partial_stdout = partial_stdout


class CliAuthError(CliError):
    """Authentication error (401)."""


class CliRegistrationError(CliError):
    """Application not registered in Yandex.Direct (error 58)."""


class CliBrowserError(CliError):
    """Base error for browser-backed direct-cli commands."""


class CliBrowserAuthError(CliBrowserError):
    """The browser session is missing, expired, or requires login."""


class CliBrowserCaptchaError(CliBrowserError):
    """Yandex served a captcha instead of the requested browser page."""


class CliBrowserProfileError(CliBrowserError):
    """The Chrome profile, cookies, or Keychain cannot be used."""
