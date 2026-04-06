"""OAuth 2.0 flow for Yandex.Direct API."""

from __future__ import annotations


class OAuthError(Exception):
    """Raised when an OAuth operation fails."""


class OAuthManager:
    """Manage Yandex OAuth 2.0 token lifecycle."""

    def __init__(self, client_id: str, client_secret: str, storage_path: str) -> None:
        """Initialize the OAuth manager.

        Args:
            client_id: Yandex OAuth application ID.
            client_secret: Yandex OAuth application secret.
            storage_path: Path to the token storage file.
        """
        self._client_id = client_id
        self._client_secret = client_secret
        self._storage_path = storage_path

    def get_authorization_url(self) -> str:
        """Return the URL for the user to authorize the application."""
        ...

    def exchange_code(self, code: str) -> dict[str, object]:
        """Exchange a 7-digit authorization code for tokens.

        Args:
            code: The 7-digit confirmation code from Yandex.

        Returns:
            Token response dict with access_token, refresh_token, expires_in.

        Raises:
            OAuthError: If the code exchange fails.
        """
        ...

    def refresh_access_token(self) -> str:
        """Refresh the access token using the stored refresh token.

        Returns:
            The new access token.

        Raises:
            OAuthError: If the refresh fails or no refresh token is available.
        """
        ...

    def get_valid_token(self) -> str:
        """Return a valid access token, refreshing if needed.

        Returns:
            A valid access token.

        Raises:
            OAuthError: If no token is available and refresh fails.
        """
        ...
