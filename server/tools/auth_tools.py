"""MCP tools and prompts for direct-cli authentication profiles."""

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from mcp.server.fastmcp import Context

from server.cli.runner import (
    DirectCliRunner,
    _direct_env,
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
        "valid": bool(token),
        "profile": profile,
        "source": payload.get("source") or "oauth",
        "has_token": bool(token),
        "login": payload.get("login") or "",
    }
    if isinstance(expires_at, int | float):
        expires_in_value = max(0, int(float(expires_at) - time.time()))
        result["expires_at"] = float(expires_at)
        result["expires_in"] = expires_in_value
        result["expires_in_human"] = _human_readable_time(expires_in_value)
    else:
        result["refresh_unavailable"] = True
    return result


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


def _setup_args(
    code: str, *, login: str | None = None, profile: str = "default"
) -> list[str]:
    args = ["auth", "login", "--profile", profile]
    if code.startswith("y0_"):
        args.extend(["--oauth-token", code])
    else:
        args.extend(["--code", code])
    if login:
        args.extend(["--login", login])
    if client_id := os.environ.get("CLAUDE_PLUGIN_OPTION_client_id"):
        args.extend(["--client-id", client_id])
    if client_secret := os.environ.get("CLAUDE_PLUGIN_OPTION_client_secret"):
        args.extend(["--client-secret", client_secret])
    return args


def _extract_auth_url(line: str) -> str | None:
    for part in line.split():
        if part.startswith("https://oauth.yandex.ru/authorize"):
            return part
    return None


def _login_process_args(
    login: str | None = None, profile: str = "default"
) -> list[str]:
    args = ["auth", "login", "--profile", profile]
    if login:
        args.extend(["--login", login])
    if client_id := os.environ.get("CLAUDE_PLUGIN_OPTION_client_id"):
        args.extend(["--client-id", client_id])
    if client_secret := os.environ.get("CLAUDE_PLUGIN_OPTION_client_secret"):
        args.extend(["--client-secret", client_secret])
    return args


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
    """Save an OAuth code or direct OAuth token into a direct-cli profile.

    Args:
        code: Authorization code from Yandex, or a direct OAuth token (starts with y0_).
        login: Optional Yandex.Direct Client-Login to save with the profile.
        profile: direct-cli profile name to save and activate.
    """
    if not code:
        return {
            "error": "invalid_code",
            "message": "Введите код авторизации или OAuth-токен.",
        }
    result = _run_auth_command(_setup_args(code, login=login, profile=profile))
    if not result.get("success"):
        return result
    return {
        "success": True,
        "method": "direct_token" if code.startswith("y0_") else "oauth_code",
        "profile": profile,
        "login": login or "",
    }


class AuthCredential(BaseModel):
    """Schema for eliciting an authorization code from user."""

    value: str = Field(description="Код авторизации с сайта Яндекса")


@mcp.tool()
async def auth_login(
    ctx: Context, login: str | None = None, profile: str = "default"
) -> dict:
    """Start interactive OAuth login through direct-cli."""
    status = auth_status(profile)
    if status.get("valid"):
        return {"already_authenticated": True, **status}

    direct_bin = _find_direct()
    if not direct_bin:
        return {
            "error": "cli_not_found",
            "message": "direct not found. Install direct-cli.",
        }

    cmd = [direct_bin, *_login_process_args(login=login, profile=profile)]
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=_direct_env(),
        )
    except FileNotFoundError:
        return {
            "error": "cli_not_found",
            "message": "direct not found. Install direct-cli.",
        }

    assert proc.stdout is not None
    auth_url = None
    output_lines: list[str] = []
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and proc.poll() is None:
        line = proc.stdout.readline()
        if not line:
            break
        clean = _strip_ansi(line).strip()
        output_lines.append(clean)
        auth_url = _extract_auth_url(clean) or auth_url
        if auth_url:
            break

    if not auth_url:
        stdout, stderr = proc.communicate(timeout=5)
        return {
            "error": "auth_login_failed",
            "message": _strip_ansi(stderr or stdout or "\n".join(output_lines)).strip(),
        }

    result = await ctx.elicit(
        message=(
            f"Авторизуйтесь в Яндекс.Директ:\n{auth_url}\n\n"
            "После разрешения введите код авторизации."
        ),
        schema=AuthCredential,
    )
    if result.action != "accept" or not result.data:
        proc.terminate()
        return {"cancelled": True, "message": "Авторизация отменена."}

    stdout, stderr = proc.communicate(input=f"{result.data.value}\n", timeout=60)
    if proc.returncode != 0:
        return {
            "success": False,
            "error": "auth_failed",
            "message": _strip_ansi(stderr or stdout).strip(),
            "auth_url": auth_url,
        }
    return {
        "success": True,
        "method": "oauth_code",
        "profile": profile,
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
