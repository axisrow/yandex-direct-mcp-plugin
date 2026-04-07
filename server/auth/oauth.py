"""OAuth 2.0 manager for Yandex.Direct API authentication with PKCE."""

import os
import time
from urllib.parse import urlencode

import httpx

from server.auth.pkce import generate_code_challenge, generate_code_verifier
from server.auth.storage import FileTokenStorage, TokenData


_ERROR_MESSAGES: dict[str, str] = {
    "invalid_grant": "Неверный или просроченный код. Код действует 10 минут.",
    "unauthorized_client": "Приложение не авторизовано.",
}

_REFRESH_BUFFER_SECONDS = 60


class OAuthError(Exception):
    """OAuth-related error."""

    def __init__(self, error: str, message: str, auth_url: str | None = None) -> None:
        self.error = error
        self.message = message
        self.auth_url = auth_url
        super().__init__(message)

    def to_dict(self) -> dict:
        """Convert to a dict suitable for MCP tool responses."""
        result: dict = {"error": self.error, "message": self.message}
        if self.auth_url:
            result["auth_url"] = self.auth_url
        return result


class OAuthManager:
    """Manages OAuth 2.0 token lifecycle for Yandex.Direct using PKCE."""

    TOKEN_URL = "https://oauth.yandex.ru/token"
    AUTHORIZE_URL = "https://oauth.yandex.ru/authorize"

    def __init__(self, storage: FileTokenStorage | None = None) -> None:
        self._storage = storage or FileTokenStorage()
        self._client_id = os.environ.get("CLAUDE_PLUGIN_OPTION_client_id", "")
        self._code_verifier: str | None = None

    @property
    def authorize_url(self) -> str:
        """Return the full authorization URL with PKCE challenge."""
        self._code_verifier = generate_code_verifier()
        params = {
            "response_type": "code",
            "client_id": self._client_id,
            "code_challenge": generate_code_challenge(self._code_verifier),
            "code_challenge_method": "S256",
        }
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"

    def exchange_code(self, code: str) -> TokenData:
        """Exchange an authorization code for tokens using PKCE verifier."""
        data: dict[str, str] = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self._client_id,
        }
        if self._code_verifier:
            data["code_verifier"] = self._code_verifier
        resp = self._token_request(data)
        self._code_verifier = None
        return self._parse_and_save(resp, fallback_refresh_token="")

    def refresh_token(self) -> TokenData:
        """Refresh the access token using a stored refresh token."""
        stored = self._storage.load()
        if not stored or not stored.get("refresh_token"):
            raise OAuthError(
                "auth_expired", "No refresh token available", self.authorize_url
            )

        resp = self._token_request(
            {
                "grant_type": "refresh_token",
                "refresh_token": stored["refresh_token"],
                "client_id": self._client_id,
            }
        )
        return self._parse_and_save(
            resp, fallback_refresh_token=stored.get("refresh_token", "")
        )

    def get_valid_token(self) -> str:
        """Get a valid access token, auto-refreshing if expired or about to expire."""
        data = self._storage.load()
        if not data:
            raise OAuthError("auth_expired", "No tokens stored", self.authorize_url)

        if data.get("expires_at", 0) - time.time() < _REFRESH_BUFFER_SECONDS:
            data = self.refresh_token()

        return data["access_token"]

    def get_status(self) -> dict:
        """Get current token status."""
        data = self._storage.load()
        if not data:
            return {"valid": False}

        expires_in = max(0, data.get("expires_at", 0) - time.time())
        return {
            "valid": expires_in > 0,
            "expires_in": int(expires_in),
            "scope": data.get("scope", ""),
            "login": data.get("login", ""),
        }

    def _token_request(self, data: dict) -> httpx.Response:
        """POST to the token endpoint, raising OAuthError on HTTP errors."""
        try:
            resp = httpx.post(self.TOKEN_URL, data=data, timeout=30)
            resp.raise_for_status()
            return resp
        except httpx.TransportError as e:
            raise OAuthError(
                "network_error", f"Network error: {e}", self.authorize_url
            ) from e
        except httpx.HTTPStatusError as e:
            try:
                error_data = e.response.json() if e.response else {}
            except (ValueError, AttributeError):
                error_data = {}
            error_type = error_data.get("error", "unknown_error")
            raise OAuthError(
                error_type,
                _ERROR_MESSAGES.get(error_type, f"OAuth error: {error_type}"),
                self.authorize_url if error_type != "invalid_grant" else None,
            ) from e

    def _parse_and_save(
        self, resp: httpx.Response, fallback_refresh_token: str
    ) -> TokenData:
        """Parse a token response, persist it, and return the result."""
        token_data = resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise OAuthError(
                "invalid_response", "Missing access_token in token response"
            )
        result = TokenData(
            access_token=access_token,
            refresh_token=token_data.get("refresh_token", fallback_refresh_token),
            expires_at=time.time() + token_data.get("expires_in", 0),
            scope=token_data.get("scope", ""),
            login=token_data.get("login", ""),
        )
        self._storage.save(result)
        return result
