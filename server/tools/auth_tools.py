"""MCP tools for OAuth authentication management."""

from server.auth.oauth import OAuthError, OAuthManager
from server.main import mcp

_oauth = OAuthManager()


@mcp.tool()
def auth_status() -> dict:
    """Check the current OAuth token status."""
    return _oauth.get_status()


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
            "expires_in": int(result.get("expires_at", 0)),
            "login": result.get("login", ""),
        }
    except OAuthError as e:
        return e.to_dict()
