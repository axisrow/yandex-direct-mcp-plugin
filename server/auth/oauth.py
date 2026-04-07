"""OAuth 2.0 manager for Yandex.Direct API authentication.

Supports three auth modes:
1. PKCE (default) — built-in app, no secrets needed
2. Direct token — user provides a ready OAuth token
3. Custom app — user's own client_id + client_secret
"""

import os
import time
from pathlib import Path
from urllib.parse import urlencode

import httpx

from server.auth.pkce import generate_code_challenge, generate_code_verifier
from server.auth.storage import FileTokenStorage, TokenData


_ERROR_MESSAGES: dict[str, str] = {
    "invalid_grant": "Неверный или просроченный код. Код действует 10 минут.",
    "invalid_client": "Неверный client_id или client_secret.",
    "unauthorized_client": "Приложение не авторизовано.",
}

_REFRESH_BUFFER_SECONDS = 60
_DEFAULT_CLIENT_ID = "dcf15d9625f6471d94d6d054d52017ba"


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
        self._client_id = (
            os.environ.get("CLAUDE_PLUGIN_OPTION_client_id") or _DEFAULT_CLIENT_ID
        )
        self._client_secret = os.environ.get("CLAUDE_PLUGIN_OPTION_client_secret") or ""
        self._static_token = (
            os.environ.get("YANDEX_DIRECT_TOKEN")
            or os.environ.get("CLAUDE_PLUGIN_OPTION_token")
            or ""
        )
        self._cached_verifier: str | None = None

    @property
    def _use_pkce(self) -> bool:
        """PKCE mode when no client_secret is configured."""
        return not self._client_secret

    @property
    def _verifier_path(self) -> Path:
        return self._storage.path.parent / "pkce_verifier.txt"

    def _save_verifier(self, verifier: str) -> None:
        self._verifier_path.parent.mkdir(parents=True, exist_ok=True)
        self._verifier_path.write_text(verifier)

    def _load_verifier(self) -> str | None:
        if self._verifier_path.exists():
            return self._verifier_path.read_text().strip() or None
        return None

    def _clear_verifier(self) -> None:
        self._cached_verifier = None
        self._verifier_path.unlink(missing_ok=True)

    @property
    def authorize_url(self) -> str:
        """Return authorization URL. No disk writes — safe to call anywhere."""
        params: dict[str, str] = {
            "response_type": "code",
            "client_id": self._client_id,
        }
        if self._use_pkce:
            verifier = (
                self._cached_verifier
                or self._load_verifier()
                or generate_code_verifier()
            )
            self._cached_verifier = verifier
            params["code_challenge"] = generate_code_challenge(verifier)
            params["code_challenge_method"] = "S256"
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"

    def start_auth_flow(self) -> str:
        """Start OAuth flow: persist PKCE verifier to disk and return auth URL.

        Call this only when the user is actually starting authorization.
        """
        if self._use_pkce:
            verifier = self._cached_verifier or generate_code_verifier()
            self._cached_verifier = verifier
            self._save_verifier(verifier)
        return self.authorize_url

    def set_token(self, token: str) -> TokenData:
        """Save a pre-existing OAuth token directly (no exchange needed)."""
        result = TokenData(
            access_token=token,
            refresh_token="",
            expires_at=time.time() + 365 * 24 * 3600,
            scope="",
            login="",
        )
        self._storage.save(result)
        return result

    def exchange_code(self, code: str) -> TokenData:
        """Exchange an authorization code for tokens (PKCE or client_secret)."""
        data: dict[str, str] = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self._client_id,
        }
        if self._use_pkce:
            verifier = self._cached_verifier or self._load_verifier()
            if not verifier:
                raise OAuthError(
                    "invalid_request",
                    "PKCE code_verifier отсутствует. Сначала получите ссылку через start_auth_flow().",
                )
            data["code_verifier"] = verifier
        else:
            data["client_secret"] = self._client_secret
        resp = self._token_request(data)
        self._clear_verifier()
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
        """Get a valid access token. Priority: env token > stored token (auto-refresh)."""
        if self._static_token:
            return self._static_token

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
