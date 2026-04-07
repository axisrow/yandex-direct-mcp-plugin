"""MCP tools and prompts for OAuth authentication management."""

import time
from typing import Literal

from pydantic import BaseModel, Field

from mcp.server.fastmcp import Context

from server.auth.oauth import OAuthError, OAuthManager
from server.main import mcp

_oauth = OAuthManager()


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


def _exchange_or_set_token(code: str) -> dict:
    """Exchange authorization code or set direct token. Shared logic."""
    if not code:
        return {
            "error": "invalid_code",
            "message": "Введите код авторизации или OAuth-токен.",
            "auth_url": _oauth.start_auth_flow(),
        }

    # Direct token (starts with y0_)
    if code.startswith("y0_"):
        result = _oauth.set_token(code)
        return {
            "success": True,
            "method": "direct_token",
            "access_token_prefix": result["access_token"][:6] + "...",
        }

    # Authorization code (alphanumeric, from Yandex OAuth page)
    if not code.isalnum():
        return {
            "error": "invalid_code",
            "message": "Код должен содержать только буквы и цифры.",
            "auth_url": _oauth.start_auth_flow(),
        }

    try:
        result = _oauth.exchange_code(code)
        return {
            "success": True,
            "method": "oauth_code",
            "access_token_prefix": result["access_token"][:6] + "...",
            "expires_in": max(0, int(result.get("expires_at", 0) - time.time())),
            "login": result.get("login", ""),
        }
    except OAuthError as e:
        return e.to_dict()


# --- MCP Tools ---


@mcp.tool()
def auth_status() -> dict:
    """Check the current OAuth token status."""
    status = _oauth.get_status()
    if status.get("valid"):
        status["expires_in_human"] = _human_readable_time(status.get("expires_in", 0))
    return status


@mcp.tool()
def auth_setup(code: str) -> dict:
    """Submit an authorization code or direct OAuth token.

    Args:
        code: Authorization code from Yandex, or a direct OAuth token (starts with y0_).
    """
    return _exchange_or_set_token(code)


class AuthMethodChoice(BaseModel):
    """Schema for choosing authentication method."""

    method: Literal["pkce", "token"] = Field(
        description="pkce — авторизация через браузер (рекомендуется), "
        "token — вставить готовый OAuth-токен"
    )


class AuthCredential(BaseModel):
    """Schema for eliciting an authorization code or token from user."""

    value: str = Field(description="Код авторизации (7 цифр) или OAuth-токен (y0_...)")


@mcp.tool()
async def auth_login(ctx: Context) -> dict:
    """Start interactive OAuth login flow.

    Asks the user how they want to authenticate, then guides them through
    the chosen flow. No arguments needed — everything happens interactively.
    """
    # Check if already authenticated
    status = _oauth.get_status()
    if status.get("valid"):
        status["expires_in_human"] = _human_readable_time(status.get("expires_in", 0))
        return {"already_authenticated": True, **status}

    # Step 1: Ask how to authenticate
    choice = await ctx.elicit(
        message="Как хотите авторизоваться в Яндекс.Директ?",
        schema=AuthMethodChoice,
    )
    if choice.action != "accept" or not choice.data:
        return {"cancelled": True, "message": "Авторизация отменена."}

    # Step 2a: Direct token
    if choice.data.method == "token":
        result = await ctx.elicit(
            message="Вставьте OAuth-токен (начинается с y0_)",
            schema=AuthCredential,
        )
        if result.action != "accept" or not result.data:
            return {"cancelled": True, "message": "Ввод токена отменён."}
        return _exchange_or_set_token(result.data.value)

    # Step 2b: PKCE flow — open browser, collect code
    auth_url = _oauth.start_auth_flow()
    url_result = await ctx.elicit_url(
        message="Перейдите по ссылке для авторизации в Яндекс.Директ",
        url=auth_url,
        elicitation_id="yandex-oauth-login",
    )
    if url_result.action != "accept":
        return {"cancelled": True, "message": "Авторизация отменена пользователем."}

    result = await ctx.elicit(
        message="Введите код авторизации (7 цифр)",
        schema=AuthCredential,
    )
    if result.action != "accept" or not result.data:
        return {"cancelled": True, "message": "Ввод кода отменён."}

    return _exchange_or_set_token(result.data.value)


# --- MCP Prompt ---


@mcp.prompt(
    name="oauth_login",
    title="Авторизация в Яндекс.Директ",
    description="Запустить OAuth авторизацию через PKCE",
)
def oauth_login_prompt() -> list[dict]:
    """Generate OAuth login prompt with authorization URL."""
    auth_url = _oauth.start_auth_flow()
    return [
        {
            "role": "user",
            "content": (
                f"Авторизуй меня в Яндекс.Директ.\n\n"
                f"Ссылка для авторизации: {auth_url}\n\n"
                f"После авторизации я введу 7-значный код."
            ),
        }
    ]
