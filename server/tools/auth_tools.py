"""MCP tools and prompts for direct-cli authentication profiles."""

import json
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from mcp.server.fastmcp import Context

from server.cli.runner import (
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


def _auth_store_path() -> Path:
    return Path.home() / ".direct-cli" / "auth.json"


def _read_auth_store(path: Path | None = None) -> dict[str, Any]:
    store_path = path or _auth_store_path()
    try:
        raw = store_path.read_text(encoding="utf-8")
    except OSError:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _read_cli_profile(
    name: str | None = None,
) -> tuple[str | None, dict[str, Any] | None]:
    store = _read_auth_store()
    selected = name
    if selected is None:
        active = store.get("active_profile")
        selected = active if isinstance(active, str) else None
    if not selected:
        return None, None
    profiles = store.get("profiles")
    if not isinstance(profiles, dict):
        return selected, None
    profile = profiles.get(selected)
    if not isinstance(profile, dict):
        return selected, None
    return selected, profile


def _normalize_status(profile: str, payload: dict[str, Any]) -> dict:
    token = payload.get("token")
    expires_at = payload.get("expires_at")
    result: dict[str, Any] = {
        "profile": profile,
        "source": payload.get("source") or "oauth",
        "has_token": bool(token),
        "login": payload.get("login") or "",
    }
    if isinstance(expires_at, int | float):
        expires_in_value = max(0, int(float(expires_at) - time.time()))
        result["valid"] = bool(token) and expires_in_value > 0
        result["expires_at"] = float(expires_at)
        result["expires_in"] = expires_in_value
        result["expires_in_human"] = _human_readable_time(expires_in_value)
    else:
        result["valid"] = bool(token)
        result["refresh_unavailable"] = True
    return result


def _resolve_profile_name(profile: str | None = None) -> str:
    if profile:
        return profile
    selected, _payload = _read_cli_profile(None)
    return selected or "default"


def _run_auth_command(args: list[str], *, timeout: int | None = None) -> dict:
    result = _runner().run(args, timeout=timeout)
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


def _login_start_args(
    login: str | None = None, profile: str = "default"
) -> list[str]:
    args = ["auth", "login", "--profile", profile, "--format", "json"]
    if login:
        args.extend(["--login", login])
    return args


def _login_finish_args(code: str, *, profile: str = "default") -> list[str]:
    return ["auth", "login", "--profile", profile, "--code", code]


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


# --- MCP Tools ---


@mcp.tool()
def auth_status(profile: str | None = None) -> dict:
    """Check the current direct-cli authentication profile status."""
    selected, payload = _read_cli_profile(profile)
    if not selected or payload is None:
        return {
            "valid": False,
            "reason": "not_authenticated",
            "profile": selected or profile or "default",
        }
    return _normalize_status(selected, payload)


@mcp.tool()
def auth_setup(code: str, login: str | None = None, profile: str = "default") -> dict:
    """Save a direct OAuth token into a direct-cli profile.

    Args:
        code: Direct OAuth token (starts with y0_).
        login: Optional Yandex.Direct Client-Login to save with the profile.
        profile: direct-cli profile name to save and activate.
    """
    if not code:
        return {
            "error": "invalid_code",
            "message": "Введите код авторизации или OAuth-токен.",
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
                "для готового токена передайте auth_setup(code=\"y0_...\")."
            ),
        }
    result = _run_auth_command(_token_setup_args(code, login=login, profile=profile))
    if not result.get("success"):
        return result
    return {
        "success": True,
        "method": "direct_token",
        "profile": profile,
        "login": login or "",
    }


class AuthCredential(BaseModel):
    """Schema for eliciting an authorization code from user."""

    value: str = Field(description="Код авторизации с сайта Яндекса")


@mcp.tool()
async def auth_login(
    ctx: Context, login: str | None = None, profile: str | None = None
) -> dict:
    """Start interactive OAuth login through direct-cli."""
    status = auth_status(profile)
    if status.get("valid"):
        return {"already_authenticated": True, **status}
    target_profile = _resolve_profile_name(profile)

    if not _find_direct():
        return {
            "error": "cli_not_found",
            "message": "direct not found. Install direct-cli.",
        }

    start_result = _runner().run(
        _login_start_args(login=login, profile=target_profile),
        timeout=30,
    )
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

    finish_result = _run_auth_command(
        _login_finish_args(result.data.value, profile=target_profile),
        timeout=60,
    )
    if not finish_result.get("success"):
        return {**finish_result, "auth_url": auth_url}
    return {
        "success": True,
        "method": "oauth_code",
        "profile": target_profile,
        "login": login or "",
    }


# --- MCP Prompt ---


@mcp.prompt(
    name="oauth_login",
    title="Авторизация в Яндекс.Директ",
    description="Запустить OAuth авторизацию через direct-cli",
)
def oauth_login_prompt() -> list[dict]:
    """Generate OAuth login prompt."""
    return [
        {
            "role": "user",
            "content": (
                "Авторизуй меня в Яндекс.Директ через auth_login. "
                "Плагин сохранит токен и login в активный профиль direct-cli."
            ),
        }
    ]
