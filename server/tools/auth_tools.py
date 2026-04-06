"""MCP tools for OAuth authentication management."""

import time

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


@mcp.tool()
def auth_status() -> dict:
    """Check the current OAuth token status."""
    status = _oauth.get_status()
    if status.get("valid"):
        status["expires_in_human"] = _human_readable_time(status.get("expires_in", 0))
    return status


@mcp.tool()
def auth_setup(code: str) -> dict:
    """Submit a 7-digit authorization code to complete OAuth setup.

    Args:
        code: 7-digit authorization code from Yandex.
    """
    if not code or not code.isdigit() or len(code) != 7:
        return {
            "error": "invalid_code",
            "message": "Код должен состоять из 7 цифр.",
            "auth_url": _oauth.authorize_url,
        }

    try:
        result = _oauth.exchange_code(code)
        return {
            "success": True,
            "access_token_prefix": result["access_token"][:6] + "...",
            "expires_in": max(0, int(result.get("expires_at", 0) - time.time())),
            "login": result.get("login", ""),
        }
    except OAuthError as e:
        return e.to_dict()
