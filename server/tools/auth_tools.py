"""MCP tools and prompts for OAuth authentication management."""

import time

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
            "login": result.get("login", ""),
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


class AuthCredential(BaseModel):
    """Schema for eliciting an authorization code or token from user."""

    value: str = Field(
        description="Код авторизации с сайта Яндекса (буквы и цифры) или готовый OAuth-токен (y0_...)"
    )


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

    # Generate PKCE auth URL and ask for code or token in one step
    auth_url = _oauth.start_auth_flow()
    result = await ctx.elicit(
        message=(
            f"Авторизуйтесь в Яндекс.Директ:\n{auth_url}\n\n"
            "После разрешения введите код авторизации (буквы и цифры) "
            "или вставьте готовый OAuth-токен (y0_...)."
        ),
        schema=AuthCredential,
    )
    if result.action != "accept" or not result.data:
        return {"cancelled": True, "message": "Авторизация отменена."}

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
                f"После авторизации я введу код подтверждения."
            ),
        }
    ]
