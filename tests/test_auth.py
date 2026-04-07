"""Tests for token storage, OAuth manager (PKCE), and auth MCP tools."""

import hashlib
import json
import time
from base64 import urlsafe_b64encode
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest

from server.auth.oauth import OAuthError, OAuthManager
from server.auth.pkce import generate_code_challenge, generate_code_verifier
from server.auth.storage import FileTokenStorage, TokenData


# ---------------------------------------------------------------------------
# Token Storage Tests
# ---------------------------------------------------------------------------


class TestFileTokenStorage:
    """Tests for FileTokenStorage."""

    def test_load_returns_none_for_missing_file(self, tmp_path: Path) -> None:
        storage = FileTokenStorage(path=tmp_path / "tokens.json")
        assert storage.load() is None

    def test_load_returns_none_for_corrupt_json(self, tmp_path: Path) -> None:
        token_path = tmp_path / "tokens.json"
        token_path.write_text("not valid json{{{")
        storage = FileTokenStorage(path=token_path)
        assert storage.load() is None

    def test_save_writes_valid_json(self, tmp_path: Path) -> None:
        token_path = tmp_path / "tokens.json"
        storage = FileTokenStorage(path=token_path)
        data: TokenData = TokenData(
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            expires_at=1700000000.0,
            scope="direct:api",
            login="test-user",
        )
        storage.save(data)

        raw = json.loads(token_path.read_text())
        assert raw["access_token"] == "test-access-token"
        assert raw["refresh_token"] == "test-refresh-token"
        assert raw["expires_at"] == 1700000000.0

    def test_save_creates_parent_directories(self, tmp_path: Path) -> None:
        token_path = tmp_path / "deep" / "nested" / "dir" / "tokens.json"
        storage = FileTokenStorage(path=token_path)
        storage.save(TokenData(access_token="tok"))
        assert token_path.exists()

    def test_save_is_atomic(self, tmp_path: Path) -> None:
        """Verify no .tmp files are left after successful save."""
        token_path = tmp_path / "tokens.json"
        storage = FileTokenStorage(path=token_path)
        storage.save(TokenData(access_token="tok"))

        tmp_files = list(tmp_path.glob("*.tmp"))
        assert tmp_files == []

    def test_roundtrip(self, tmp_path: Path) -> None:
        """Data saved then loaded should be identical."""
        token_path = tmp_path / "tokens.json"
        storage = FileTokenStorage(path=token_path)
        original = TokenData(
            access_token="abc123",
            refresh_token="ref456",
            expires_at=1700000000.0,
            scope="direct:api",
            login="user@example.com",
        )
        storage.save(original)
        loaded = storage.load()
        assert loaded is not None
        assert loaded["access_token"] == "abc123"
        assert loaded["refresh_token"] == "ref456"
        assert loaded["login"] == "user@example.com"

    def test_path_property(self, tmp_path: Path) -> None:
        token_path = tmp_path / "tokens.json"
        storage = FileTokenStorage(path=token_path)
        assert storage.path == token_path

    def test_load_returns_none_for_empty_file(self, tmp_path: Path) -> None:
        token_path = tmp_path / "tokens.json"
        token_path.write_text("")
        storage = FileTokenStorage(path=token_path)
        assert storage.load() is None


# ---------------------------------------------------------------------------
# OAuth Manager Tests
# ---------------------------------------------------------------------------


def _make_httpx_response(status_code: int, json_data: dict) -> MagicMock:
    """Create a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    if status_code >= 400:
        error = MagicMock()
        error.response = resp
        error.response.json.return_value = json_data
        resp.raise_for_status.side_effect = __import__("httpx").HTTPStatusError(
            message="error", request=MagicMock(), response=resp
        )
    else:
        resp.raise_for_status = MagicMock()
    return resp


class TestOAuthManager:
    """Tests for OAuthManager."""

    def _storage(self, tmp_path: Path) -> FileTokenStorage:
        return FileTokenStorage(path=tmp_path / "tokens.json")

    @patch("server.auth.oauth.httpx.post")
    def test_exchange_code_succeeds(self, mock_post, tmp_path: Path) -> None:
        mock_post.return_value = _make_httpx_response(
            200,
            {
                "access_token": "new-access-token",
                "refresh_token": "new-refresh-token",
                "expires_in": 3600,
                "scope": "direct:api",
                "login": "user@example.com",
            },
        )
        manager = OAuthManager(storage=self._storage(tmp_path))
        # Trigger PKCE verifier generation via authorize_url
        _ = manager.authorize_url
        result = manager.exchange_code("1234567")

        assert result["access_token"] == "new-access-token"
        assert result["refresh_token"] == "new-refresh-token"
        assert result["login"] == "user@example.com"
        assert result["expires_at"] > time.time()

        # Verify PKCE: code_verifier sent, client_secret NOT sent
        call_data = mock_post.call_args[1].get("data", mock_post.call_args[0][1] if len(mock_post.call_args[0]) > 1 else {})
        assert "code_verifier" in call_data
        assert "client_secret" not in call_data

    @patch("server.auth.oauth.httpx.post")
    def test_exchange_code_fails_with_invalid_grant(
        self, mock_post, tmp_path: Path
    ) -> None:
        mock_post.return_value = _make_httpx_response(
            400,
            {
                "error": "invalid_grant",
                "error_description": "Code is invalid",
            },
        )
        manager = OAuthManager(storage=self._storage(tmp_path))

        with pytest.raises(OAuthError) as exc_info:
            manager.exchange_code("bad-code")

        assert exc_info.value.error == "invalid_grant"
        assert "просроченный" in exc_info.value.message

    @patch("server.auth.oauth.httpx.post")
    def test_refresh_token_succeeds(self, mock_post, tmp_path: Path) -> None:
        storage = self._storage(tmp_path)
        storage.save(
            TokenData(
                access_token="old-token",
                refresh_token="old-refresh",
                expires_at=time.time() + 100,
            )
        )
        mock_post.return_value = _make_httpx_response(
            200,
            {
                "access_token": "refreshed-token",
                "refresh_token": "new-refresh",
                "expires_in": 3600,
                "scope": "direct:api",
                "login": "user@example.com",
            },
        )
        manager = OAuthManager(storage=storage)
        result = manager.refresh_token()

        assert result["access_token"] == "refreshed-token"
        assert result["refresh_token"] == "new-refresh"

    def test_refresh_token_raises_when_no_token(self, tmp_path: Path) -> None:
        manager = OAuthManager(storage=self._storage(tmp_path))
        with pytest.raises(OAuthError) as exc_info:
            manager.refresh_token()
        assert exc_info.value.error == "auth_expired"
        assert exc_info.value.auth_url is not None

    @patch("server.auth.oauth.httpx.post")
    def test_get_valid_token_auto_refreshes_when_expired(
        self, mock_post, tmp_path: Path
    ) -> None:
        storage = self._storage(tmp_path)
        # Token expires in 30 seconds (within 60s buffer)
        storage.save(
            TokenData(
                access_token="expired-token",
                refresh_token="refresh-me",
                expires_at=time.time() + 30,
            )
        )
        mock_post.return_value = _make_httpx_response(
            200,
            {
                "access_token": "auto-refreshed",
                "refresh_token": "new-refresh",
                "expires_in": 3600,
                "scope": "direct:api",
            },
        )
        manager = OAuthManager(storage=storage)
        token = manager.get_valid_token()

        assert token == "auto-refreshed"
        mock_post.assert_called_once()

    @patch("server.auth.oauth.httpx.post")
    def test_get_valid_token_returns_existing_when_valid(
        self, mock_post, tmp_path: Path
    ) -> None:
        storage = self._storage(tmp_path)
        # Token expires in 1 hour (well beyond 60s buffer)
        storage.save(
            TokenData(
                access_token="valid-token",
                refresh_token="refresh-me",
                expires_at=time.time() + 3600,
            )
        )
        manager = OAuthManager(storage=storage)
        token = manager.get_valid_token()

        assert token == "valid-token"
        mock_post.assert_not_called()

    def test_get_valid_token_raises_when_no_tokens(self, tmp_path: Path) -> None:
        manager = OAuthManager(storage=self._storage(tmp_path))
        with pytest.raises(OAuthError) as exc_info:
            manager.get_valid_token()
        assert exc_info.value.error == "auth_expired"

    def test_get_status_returns_valid(self, tmp_path: Path) -> None:
        storage = self._storage(tmp_path)
        storage.save(
            TokenData(
                access_token="tok",
                expires_at=time.time() + 3600,
                scope="direct:api",
                login="user@example.com",
            )
        )
        manager = OAuthManager(storage=storage)
        status = manager.get_status()

        assert status["valid"] is True
        assert status["expires_in"] > 0
        assert status["login"] == "user@example.com"

    def test_get_status_returns_invalid_when_no_tokens(self, tmp_path: Path) -> None:
        manager = OAuthManager(storage=self._storage(tmp_path))
        status = manager.get_status()
        assert status["valid"] is False


# ---------------------------------------------------------------------------
# Auth MCP Tools Tests
# ---------------------------------------------------------------------------


class TestAuthTools:
    """Tests for auth_status and auth_setup MCP tools."""

    def test_auth_status_returns_valid_dict(self, tmp_path: Path) -> None:
        """auth_status returns a dict with valid key."""
        # The global _oauth uses CLAUDE_PLUGIN_DATA which conftest sets to tmp_path
        # We need to test with a fresh manager pointing at our tmp_path
        from server.tools.auth_tools import auth_status

        result = auth_status()
        assert isinstance(result, dict)
        assert "valid" in result

    @patch("server.tools.auth_tools._oauth")
    def test_auth_setup_with_valid_code(self, mock_oauth) -> None:
        mock_oauth.exchange_code.return_value = TokenData(
            access_token="1234567890abcdef",
            refresh_token="refresh",
            expires_at=1700000000.0,
            scope="direct:api",
            login="user@example.com",
        )
        from server.tools.auth_tools import auth_setup

        result = auth_setup("1234567")
        assert result["success"] is True
        assert result["access_token_prefix"] == "123456..."
        mock_oauth.exchange_code.assert_called_once_with("1234567")

    def test_auth_setup_with_invalid_code_special_chars(self) -> None:
        from server.tools.auth_tools import auth_setup

        result = auth_setup("abc!@#$")
        assert result["error"] == "invalid_code"

    def test_auth_setup_with_empty_code(self) -> None:
        from server.tools.auth_tools import auth_setup

        result = auth_setup("")
        assert result["error"] == "invalid_code"

    @patch("server.tools.auth_tools._oauth")
    def test_auth_setup_with_direct_token(self, mock_oauth) -> None:
        mock_oauth.set_token.return_value = TokenData(
            access_token="y0_test_token_12345",
            refresh_token="",
            expires_at=1700000000.0,
        )
        from server.tools.auth_tools import auth_setup

        result = auth_setup("y0_test_token_12345")
        assert result["success"] is True
        assert result["method"] == "direct_token"
        mock_oauth.set_token.assert_called_once_with("y0_test_token_12345")

    @patch("server.tools.auth_tools._oauth")
    def test_auth_setup_propagates_oauth_errors(self, mock_oauth) -> None:
        mock_oauth.exchange_code.side_effect = OAuthError(
            "invalid_grant",
            "Неверный или просроченный код. Код действует 10 минут.",
        )
        from server.tools.auth_tools import auth_setup

        result = auth_setup("1234567")
        assert result["error"] == "invalid_grant"
        assert "просроченный" in result["message"]


# ---------------------------------------------------------------------------
# PKCE Tests
# ---------------------------------------------------------------------------


class TestPKCE:
    """Tests for PKCE code_verifier / code_challenge generation."""

    def test_generate_code_verifier_length(self) -> None:
        verifier = generate_code_verifier()
        assert 43 <= len(verifier) <= 128

    def test_generate_code_verifier_charset(self) -> None:
        import re

        verifier = generate_code_verifier()
        assert re.fullmatch(r"[A-Za-z0-9_\-]+", verifier)

    def test_generate_code_challenge_s256(self) -> None:
        verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        expected_digest = hashlib.sha256(verifier.encode("ascii")).digest()
        expected = urlsafe_b64encode(expected_digest).rstrip(b"=").decode("ascii")
        assert generate_code_challenge(verifier) == expected

    def test_authorize_url_contains_pkce_params(self) -> None:
        storage = FileTokenStorage(path=Path("/tmp/test-pkce-tokens.json"))
        manager = OAuthManager(storage=storage)
        url = manager.authorize_url
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        assert "code_challenge" in params
        assert params["code_challenge_method"] == ["S256"]
        assert params["response_type"] == ["code"]

    @patch("server.auth.oauth.httpx.post")
    def test_exchange_sends_verifier_not_secret(self, mock_post) -> None:
        mock_post.return_value = _make_httpx_response(
            200,
            {
                "access_token": "tok",
                "refresh_token": "ref",
                "expires_in": 3600,
            },
        )
        storage = FileTokenStorage(path=Path("/tmp/test-pkce-tokens.json"))
        manager = OAuthManager(storage=storage)
        _ = manager.authorize_url  # generates code_verifier
        manager.exchange_code("1234567")

        call_kwargs = mock_post.call_args
        sent_data = call_kwargs.kwargs.get("data", {})
        assert "code_verifier" in sent_data
        assert "client_secret" not in sent_data

    def test_set_token_saves_directly(self, tmp_path: Path) -> None:
        storage = FileTokenStorage(path=tmp_path / "tokens.json")
        manager = OAuthManager(storage=storage)
        result = manager.set_token("y0_direct_token_value")
        assert result["access_token"] == "y0_direct_token_value"
        loaded = storage.load()
        assert loaded is not None
        assert loaded["access_token"] == "y0_direct_token_value"

    @patch("server.auth.oauth.httpx.post")
    def test_exchange_with_client_secret_no_pkce(self, mock_post, tmp_path: Path) -> None:
        mock_post.return_value = _make_httpx_response(
            200, {"access_token": "tok", "expires_in": 3600},
        )
        storage = FileTokenStorage(path=tmp_path / "tokens.json")
        manager = OAuthManager(storage=storage)
        manager._client_secret = "my_secret"
        manager.exchange_code("somecode")
        sent_data = mock_post.call_args.kwargs.get("data", {})
        assert sent_data["client_secret"] == "my_secret"
        assert "code_verifier" not in sent_data

    def test_env_token_takes_priority(self, tmp_path: Path) -> None:
        storage = FileTokenStorage(path=tmp_path / "tokens.json")
        storage.save(TokenData(access_token="stored", expires_at=time.time() + 3600))
        manager = OAuthManager(storage=storage)
        manager._static_token = "y0_from_env"
        assert manager.get_valid_token() == "y0_from_env"

    def test_authorize_url_no_pkce_when_secret(self, tmp_path: Path) -> None:
        storage = FileTokenStorage(path=tmp_path / "tokens.json")
        manager = OAuthManager(storage=storage)
        manager._client_secret = "secret"
        url = manager.authorize_url
        assert "code_challenge" not in url

    def test_code_verifier_cleared_after_exchange(self, tmp_path: Path) -> None:
        storage = FileTokenStorage(path=tmp_path / "tokens.json")
        manager = OAuthManager(storage=storage)
        _ = manager.authorize_url
        assert manager._verifier_path.exists()
        with patch("server.auth.oauth.httpx.post") as mock_post:
            mock_post.return_value = _make_httpx_response(
                200, {"access_token": "t", "expires_in": 3600}
            )
            manager.exchange_code("1234567")
        assert not manager._verifier_path.exists()
