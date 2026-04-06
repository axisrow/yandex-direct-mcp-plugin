"""OAuth 2.0 manager for Yandex ID authentication."""

from server.auth.storage import TokenData


class OAuthManager:
    """Manages OAuth 2.0 authentication flow with Yandex ID."""

    def exchange_code(self, code: str) -> TokenData:
        """Exchange authorization code for access and refresh tokens."""
        raise NotImplementedError

    def refresh_token(self) -> TokenData:
        """Refresh the access token using the refresh token."""
        raise NotImplementedError

    def get_valid_token(self) -> str:
        """Get a valid access token, auto-refreshing if needed."""
        raise NotImplementedError

    def get_status(self) -> dict:
        """Get the current token status."""
        raise NotImplementedError
