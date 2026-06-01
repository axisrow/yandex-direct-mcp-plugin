"""MCP tools and prompts for direct auth profiles."""

import json
import time

from pydantic import BaseModel, Field

from mcp.server.fastmcp import Context

from server.cli.runner import (
    CliError,
    CliNotFoundError,
    CliTimeoutError,
    DirectCliRunner,
    _find_direct,
    _strip_ansi,
)
from server.main import mcp


def _human_readable_time(seconds: float) -> str:
    """Convert seconds to human-readable Russian string."""
    seconds = int(seconds)
    if seconds <= 0:
        return "истёк"
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    parts = []
    if hours > 0:
        parts.append(f"{hours} ч.")
    if minutes > 0:
        parts.append(f"{minutes} мин.")
    if secs > 0 and hours == 0:
        parts.append(f"{secs} сек.")
    return " ".join(parts) if parts else "0 сек."


def _runner() -> DirectCliRunner:
    return DirectCliRunner()


def _status_args(profile: str | None = None) -> list[str]:
    args = ["auth", "status"]
    if profile:
        args.extend(["--profile", profile])
    args.extend(["--format", "json"])
    return args


def _not_authenticated(profile: str | None = None, message: str | None = None) -> dict:
    result = {
        "valid": False,
        "reason": "not_authenticated",
        "profile": profile or "default",
    }
    if message:
        result["message"] = message
    return result


def _normalize_status_payload(profile: str | None, payload: dict) -> dict:
    has_token = bool(payload.get("has_token"))
    payload_profile = payload.get("profile")
    selected_profile = payload_profile if isinstance(payload_profile, str) else profile
    if not has_token:
        return _not_authenticated(selected_profile or profile)

    expires_at = payload.get("expires_at")
    expires_in = payload.get("expires_in_seconds")
    if not isinstance(expires_in, (int, float)) and isinstance(
        expires_at, (int, float)
    ):
        expires_in = max(0, int(float(expires_at) - time.time()))

    result: dict[str, object] = {
        "profile": selected_profile,
        "source": payload.get("source") or "",
        "has_token": has_token,
        "login": payload.get("login") or "",
        "valid": has_token,
    }
    if isinstance(expires_at, (int, float)):
        result["expires_at"] = float(expires_at)
    if isinstance(expires_in, (int, float)):
        expires_in_value = max(0, int(expires_in))
        result["valid"] = has_token and expires_in_value > 0
        result["expires_in"] = expires_in_value
        result["expires_in_human"] = _human_readable_time(expires_in_value)
    return result


def _status_from_cli(profile: str | None = None) -> dict:
    def _error(error: str, message: str) -> dict:
        return {
            "valid": False,
            "error": error,
            "message": message,
            "profile": _resolve_profile_name(profile),
        }

    try:
        result = _runner().run(_status_args(profile))
    except CliError as e:
        # CliNotFoundError / CliTimeoutError are CliError subclasses (same
        # catch order as _run_auth_command); map the type to an error code.
        error = {
            CliNotFoundError: "cli_not_found",
            CliTimeoutError: "timeout",
        }.get(type(e), "auth_failed")
        return _error(error, str(e))

    stdout = _strip_ansi(result.stdout).strip()
    stderr = _strip_ansi(result.stderr).strip()
    if result.returncode != 0:
        return _not_authenticated(profile, stderr or stdout)

    try:
        payload = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        return _error(
            "auth_failed", stdout or "direct auth status did not return JSON."
        )
    if not isinstance(payload, dict):
        return _error(
            "auth_failed", "direct auth status returned an unexpected payload."
        )
    return _normalize_status_payload(profile, payload)


def _status_login(status: dict) -> str:
    login = status.get("login")
    return login if isinstance(login, str) else ""


def _status_profile(profile: str, status: dict) -> str:
    selected = status.get("profile")
    return selected if isinstance(selected, str) and selected else profile


def _resolve_profile_name(profile: str | None = None) -> str:
    return profile or "default"


def _run_auth_command(
    args: list[str], *, timeout: int | None = None, input: str | None = None
) -> dict:
    try:
        if input is None:
            result = _runner().run(args, timeout=timeout)
        else:
            result = _runner().run(args, timeout=timeout, input=input)
    except CliNotFoundError as e:
        return {"success": False, "error": "cli_not_found", "message": str(e)}
    except CliTimeoutError as e:
        return {"success": False, "error": "timeout", "message": str(e)}
    except CliError as e:
        return {"success": False, "error": "auth_failed", "message": str(e)}
    stdout = _strip_ansi(result.stdout).strip()
    stderr = _strip_ansi(result.stderr).strip()
    if result.returncode != 0:
        return {
            "success": False,
            "error": "auth_failed",
            "message": stderr
            or stdout
            or f"direct failed with exit {result.returncode}",
        }
    return {"success": True, "message": stdout or stderr}


def _token_setup_args(
    token: str, *, login: str | None = None, profile: str = "default"
) -> list[str]:
    args = ["auth", "login", "--profile", profile, "--oauth-token", token]
    if login:
        args.extend(["--login", login])
    return args


def _login_start_args(login: str | None = None, profile: str = "default") -> list[str]:
    args = ["auth", "login", "--profile", profile, "--format", "json"]
    if login:
        args.extend(["--login", login])
    return args


def _login_finish_args(*, profile: str = "default") -> list[str]:
    return ["auth", "login", "--profile", profile, "--code", "-"]


def _login_finish_legacy_args(*, profile: str = "default") -> list[str]:
    return ["auth", "login", "--profile", profile, "--code-stdin"]


def _clean_cli_output(stdout: str = "", stderr: str = "") -> str:
    return _strip_ansi(stderr or stdout).strip()


def _parse_authorize_url(stdout: str) -> str | None:
    try:
        payload = json.loads(_strip_ansi(stdout).strip())
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    authorize_url = payload.get("authorize_url")
    return authorize_url if isinstance(authorize_url, str) and authorize_url else None


def _complete_login_with_code(profile: str, code: str) -> dict:
    stdin = f"{code}\n"
    result = _run_auth_command(
        _login_finish_args(profile=profile),
        timeout=60,
        input=stdin,
    )
    if result.get("success"):
        return result
    legacy_result = _run_auth_command(
        _login_finish_legacy_args(profile=profile),
        timeout=60,
        input=stdin,
    )
    if legacy_result.get("success"):
        return legacy_result
    return result


# --- MCP Tools ---


@mcp.tool()
def auth_status(profile: str | None = None) -> dict:
    """Check the current direct auth profile status."""
    return _status_from_cli(profile)


@mcp.tool()
def auth_setup(code: str, login: str | None = None, profile: str = "default") -> dict:
    """Save a direct OAuth token into a direct auth profile.

    Args:
        code: Direct OAuth token (starts with y0_).
        login: Optional Yandex.Direct Client-Login to save with the profile.
        profile: direct auth profile name to save and activate.
    """
    if not code:
        return {
            "error": "invalid_code",
            "message": "Введите готовый OAuth-токен, начинающийся с y0_.",
            "hint": (
                "Для browser OAuth запустите auth_login(); "
                'auth_setup принимает только auth_setup(code="y0_...").'
            ),
        }
    if not code.startswith("y0_"):
        return {
            "success": False,
            "error": "unsupported_oauth_code_flow",
            "message": (
                "Код из браузерного OAuth нельзя сохранить через auth_setup: "
                "он завершается только через pending PKCE flow в auth_login()."
            ),
            "hint": (
                "Для browser OAuth запустите auth_login() и введите код в его форму; "
                'для готового токена передайте auth_setup(code="y0_...").'
            ),
        }
    result = _run_auth_command(_token_setup_args(code, login=login, profile=profile))
    if not result.get("success"):
        return result
    status = auth_status(profile)
    return {
        "success": True,
        "method": "direct_token",
        "profile": _status_profile(profile, status),
        "login": _status_login(status),
    }


class AuthCredential(BaseModel):
    """Schema for eliciting an authorization code from user."""

    value: str = Field(description="Код авторизации с сайта Яндекса")


@mcp.tool()
async def auth_login(
    ctx: Context,
    login: str | None = None,
    profile: str | None = None,
    force: bool = False,
) -> dict:
    """Start interactive OAuth login through `direct`.

    Args:
        login: Optional Yandex.Direct Client-Login to save with the profile.
        profile: direct auth profile name (default — "default").
        force: Re-run OAuth flow even if the profile is already valid. Use
            this to switch the active account or to refresh an existing token
            without manually changing CLI auth configuration.
    """
    status = auth_status(profile)
    if status.get("valid") and not force:
        return {"already_authenticated": True, **status}
    target_profile = _resolve_profile_name(profile)

    if not _find_direct():
        return {
            "error": "cli_not_found",
            "message": "direct not found. Install package direct-cli and run `direct`.",
        }

    try:
        start_result = _runner().run(
            _login_start_args(login=login, profile=target_profile),
            timeout=30,
            input="",
        )
    except CliNotFoundError as e:
        return {"success": False, "error": "cli_not_found", "message": str(e)}
    except CliTimeoutError as e:
        return {"success": False, "error": "timeout", "message": str(e)}
    except CliError as e:
        return {"success": False, "error": "auth_login_failed", "message": str(e)}
    start_stdout = _strip_ansi(start_result.stdout).strip()
    start_stderr = _strip_ansi(start_result.stderr).strip()
    if start_result.returncode != 0:
        return {
            "success": False,
            "error": "auth_login_failed",
            "message": _clean_cli_output(start_stdout, start_stderr)
            or f"direct failed with exit {start_result.returncode}",
        }

    auth_url = _parse_authorize_url(start_stdout)
    if not auth_url:
        message = _clean_cli_output(start_stdout, start_stderr)
        try:
            parsed_stdout = json.loads(start_stdout)
        except json.JSONDecodeError:
            parsed_stdout = None
        if isinstance(parsed_stdout, dict):
            message = "direct auth login did not return authorize_url."
        return {
            "success": False,
            "error": "auth_login_failed",
            "message": message or "direct auth login did not return authorize_url.",
        }

    result = await ctx.elicit(
        message=(
            f"Авторизуйтесь в Яндекс.Директ:\n{auth_url}\n\n"
            "После разрешения введите код авторизации."
        ),
        schema=AuthCredential,
    )
    if result.action != "accept" or not result.data:
        return {"cancelled": True, "message": "Авторизация отменена."}

    finish_result = _complete_login_with_code(target_profile, result.data.value)
    if not finish_result.get("success"):
        return {**finish_result, "auth_url": auth_url}
    status = auth_status(target_profile)
    return {
        "success": True,
        "method": "oauth_code",
        "profile": _status_profile(target_profile, status),
        "login": _status_login(status),
    }


# --- MCP Prompt ---


@mcp.prompt(
    name="oauth_login",
    title="Авторизация в Яндекс.Директ",
    description="Запустить OAuth авторизацию через `direct`",
)
def oauth_login_prompt() -> list[dict]:
    """Generate OAuth login prompt."""
    return [
        {
            "role": "user",
            "content": (
                "Авторизуй меня в Яндекс.Директ через auth_login. "
                "Плагин сохранит токен и login в активный direct auth profile."
            ),
        }
    ]
