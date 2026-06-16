"""Tests for auth MCP tools delegated to `direct`."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, call, patch

from server.cli.runner import CliError, CliNotFoundError, CliTimeoutError
from server.tools.auth_tools import (
    _human_readable_time,
    _login_finish_args,
    _login_finish_legacy_args,
    _login_start_args,
    _token_setup_args,
    auth_login,
    auth_setup,
    auth_status,
    oauth_login_prompt,
)

from tests.helpers import completed


class TestAuthStatus:
    def test_auth_status_returns_invalid_without_credentials(self) -> None:
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                json.dumps(
                    {
                        "profile": None,
                        "source": None,
                        "has_token": False,
                        "login": None,
                    }
                )
            ),
        ) as mock_run:
            result = auth_status()

        assert result == {
            "valid": False,
            "reason": "not_authenticated",
            "profile": "default",
        }
        mock_run.assert_called_once_with(["auth", "status", "--format", "json"])

    def test_auth_status_normalizes_legacy_no_active_profile_text(self) -> None:
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed("ℹ Нет активного профиля.\n"),
        ):
            result = auth_status()

        assert result == {
            "valid": False,
            "reason": "not_authenticated",
            "profile": "default",
        }

    def test_auth_status_reads_direct_cli_status(self) -> None:
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                json.dumps(
                    {
                        "profile": "default",
                        "source": "oauth",
                        "has_token": True,
                        "login": "client",
                        "expires_at": 2_000_000_000.0,
                        "expires_in_seconds": 3600,
                    }
                )
            ),
        ):
            result = auth_status()
        assert result["valid"] is True
        assert result["profile"] == "default"
        assert result["source"] == "oauth"
        assert result["has_token"] is True
        assert result["login"] == "client"
        assert result["expires_at"] == 2_000_000_000.0
        assert result["expires_in"] == 3600
        assert result["expires_in_human"] == "1 ч."

    def test_auth_status_explicit_profile_delegates_to_direct(self) -> None:
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                json.dumps(
                    {
                        "profile": "legacy",
                        "source": "manual",
                        "has_token": True,
                        "login": "client",
                    }
                )
            ),
        ) as mock_run:
            result = auth_status("legacy")

        assert result["valid"] is True
        assert result["source"] == "manual"
        assert result["login"] == "client"
        mock_run.assert_called_once_with(
            ["auth", "status", "--profile", "legacy", "--format", "json"]
        )

    def test_auth_status_reports_env_source_from_direct(self) -> None:
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                json.dumps(
                    {
                        "profile": None,
                        "source": "env",
                        "has_token": True,
                        "login": "dotenv-login",
                    }
                )
            ),
        ):
            result = auth_status()

        assert result["valid"] is True
        assert result["profile"] is None
        assert result["source"] == "env"
        assert result["login"] == "dotenv-login"

    def test_auth_status_marks_expired_profile_invalid(self) -> None:
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                json.dumps(
                    {
                        "profile": "default",
                        "source": "oauth",
                        "has_token": True,
                        "login": "client",
                        "expires_at": 1.0,
                        "expires_in_seconds": 0,
                    }
                )
            ),
        ):
            result = auth_status()
        assert result["valid"] is False
        assert result["has_token"] is True
        assert result["expires_in"] == 0

    def test_auth_status_reports_cli_not_found(self) -> None:
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            side_effect=CliNotFoundError("direct missing"),
        ):
            result = auth_status()

        assert result == {
            "valid": False,
            "error": "cli_not_found",
            "message": "direct missing",
            "profile": "default",
        }

    def test_auth_status_nonzero_exit_real_error_is_not_flattened(self) -> None:
        """A non-zero exit whose message is NOT a "not authenticated" message is
        a real failure (auth_failed), not a silent not_authenticated (#170-26)."""
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                stderr="Network is unreachable: could not reach api.direct.yandex.com",
                returncode=1,
            ),
        ):
            result = auth_status()

        assert result["valid"] is False
        assert result["error"] == "auth_failed"
        assert result.get("reason") != "not_authenticated"
        assert "Network is unreachable" in result["message"]

    def test_auth_status_nonzero_exit_not_authenticated_message(self) -> None:
        """A non-zero exit that IS a not-authenticated message still maps to
        not_authenticated (#170-26)."""
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(stderr="No active profile.", returncode=1),
        ):
            result = auth_status()

        assert result["valid"] is False
        assert result["reason"] == "not_authenticated"

    def test_auth_status_unconfigured_profile_is_not_authenticated(self) -> None:
        """An unconfigured profile means "not logged in", not a hard failure:
        `direct auth status --profile X` emits "Profile 'X' is not configured."
        (#170-26)."""
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                stderr="Profile 'missing' is not configured.", returncode=1
            ),
        ):
            result = auth_status(profile="missing")

        assert result["valid"] is False
        assert result["reason"] == "not_authenticated"


class TestAuthSetup:
    def test_auth_setup_with_direct_token(self) -> None:
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            side_effect=[
                completed("✓ Profile 'default' is saved and active.\n"),
                completed(
                    json.dumps(
                        {
                            "profile": "default",
                            "source": "manual",
                            "has_token": True,
                            "login": "client",
                        }
                    )
                ),
            ],
        ) as mock_run:
            result = auth_setup("y0_token", login="client")

        assert result == {
            "success": True,
            "method": "direct_token",
            "profile": "default",
            "login": "client",
        }
        assert mock_run.call_args_list == [
            call(
                [
                    "auth",
                    "login",
                    "--profile",
                    "default",
                    "--oauth-token",
                    "y0_token",
                    "--login",
                    "client",
                ],
                timeout=None,
            ),
            call(["auth", "status", "--profile", "default", "--format", "json"]),
        ]

    def test_auth_setup_accepts_legacy_aqaa_token(self) -> None:
        """Legacy AQAA… tokens are valid and must not be rejected by the prefix
        guard — they reach the CLI like y0_ tokens (#170-30)."""
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            side_effect=[
                completed("✓ Profile 'default' is saved and active.\n"),
                completed(
                    json.dumps(
                        {
                            "profile": "default",
                            "source": "manual",
                            "has_token": True,
                            "login": None,
                        }
                    )
                ),
            ],
        ) as mock_run:
            result = auth_setup("AQAA-legacy-token")

        assert result["success"] is True
        # The token reached the CLI rather than being rejected up front.
        assert mock_run.call_args_list[0].args[0][:2] == ["auth", "login"]
        assert "AQAA-legacy-token" in mock_run.call_args_list[0].args[0]

    def test_auth_setup_returns_status_login_when_param_omitted(self) -> None:
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            side_effect=[
                completed("ok"),
                completed(
                    json.dumps(
                        {
                            "profile": "default",
                            "source": "manual",
                            "has_token": True,
                            "login": "gtoil-ru-direct",
                        }
                    )
                ),
            ],
        ):
            result = auth_setup("y0_token")

        assert result == {
            "success": True,
            "method": "direct_token",
            "profile": "default",
            "login": "gtoil-ru-direct",
        }

    def test_auth_setup_ignores_plugin_client_options(self, monkeypatch) -> None:
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_client_id", "cid")
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_client_secret", "secret")
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            side_effect=[
                completed("ok"),
                completed(
                    json.dumps(
                        {
                            "profile": "default",
                            "source": "manual",
                            "has_token": True,
                            "login": "client",
                        }
                    )
                ),
            ],
        ) as mock_run:
            auth_setup("y0_token")

        setup_args = mock_run.call_args_list[0].args[0]
        assert "--client-id" not in setup_args
        assert "cid" not in setup_args
        assert "--client-secret" not in setup_args
        assert "secret" not in setup_args
        assert setup_args == [
            "auth",
            "login",
            "--profile",
            "default",
            "--oauth-token",
            "y0_token",
        ]

    def test_auth_command_args_ignore_plugin_client_options(self, monkeypatch) -> None:
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_client_id", "cid")
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_client_secret", "secret")

        setup_args = _token_setup_args("y0_token")
        login_args = _login_start_args()

        assert "--client-id" not in setup_args
        assert "--client-id" not in login_args
        assert "cid" not in setup_args
        assert "cid" not in login_args
        assert "--client-secret" not in setup_args
        assert "--client-secret" not in login_args
        assert "secret" not in setup_args
        assert "secret" not in login_args
        assert setup_args == [
            "auth",
            "login",
            "--profile",
            "default",
            "--oauth-token",
            "y0_token",
        ]
        assert login_args == [
            "auth",
            "login",
            "--profile",
            "default",
            "--format",
            "json",
        ]
        assert _login_finish_args() == [
            "auth",
            "login",
            "--profile",
            "default",
            "--code",
            "-",
        ]
        assert _login_finish_legacy_args() == [
            "auth",
            "login",
            "--profile",
            "default",
            "--code-stdin",
        ]

    def test_auth_setup_rejects_browser_oauth_code_without_cli_call(self) -> None:
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed("✓ Profile 'custom' is saved and active.\n"),
        ) as mock_run:
            result = auth_setup("abc123", profile="custom")

        assert result["success"] is False
        assert result["error"] == "unsupported_oauth_code_flow"
        assert "auth_setup" in result["message"]
        assert "PKCE" in result["message"]
        assert "auth_login()" in result["hint"]
        mock_run.assert_not_called()

    def test_auth_setup_rejects_empty_code(self) -> None:
        result = auth_setup("")
        assert result["error"] == "invalid_code"
        assert "y0_" in result["message"]
        assert "auth_login()" in result["hint"]
        assert "код авторизации" not in result["message"]

    def test_auth_setup_reports_cli_failure(self) -> None:
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(stderr="Error: bad code", returncode=1),
        ):
            result = auth_setup("y0_bad")
        assert result["success"] is False
        assert result["error"] == "auth_failed"

    def test_auth_setup_reports_runner_exceptions(self) -> None:
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            side_effect=CliTimeoutError("direct timed out after 30s"),
        ):
            result = auth_setup("y0_token")

        assert result == {
            "success": False,
            "error": "timeout",
            "message": "direct timed out after 30s",
        }


class TestAuthLogin:
    def _accepted_ctx(self, code: str = "ABC123") -> MagicMock:
        mock_ctx = MagicMock()
        credential = MagicMock()
        credential.action = "accept"
        credential.data.value = code
        mock_ctx.elicit = AsyncMock(return_value=credential)
        return mock_ctx

    @patch("server.tools.auth_tools.auth_status", return_value={"valid": True})
    def test_auth_login_already_authenticated(self, _mock_status) -> None:
        result = asyncio.run(auth_login(MagicMock()))
        assert result["already_authenticated"] is True

    @patch("server.tools.auth_tools.auth_status", return_value={"valid": True})
    @patch("server.tools.auth_tools._find_direct", return_value="/usr/bin/direct")
    @patch("server.tools.auth_tools._resolve_profile_name", return_value="default")
    @patch("server.tools.auth_tools.DirectCliRunner.run")
    def test_auth_login_force_reauth_when_already_valid(
        self, mock_run, _mock_resolve, _mock_find, _mock_status
    ) -> None:
        mock_run.return_value = completed(
            json.dumps({"authorize_url": "https://oauth.yandex.ru/authorize?x=1"})
        )
        mock_ctx = MagicMock()
        mock_result = MagicMock()
        mock_result.action = "decline"
        mock_result.data = None
        mock_ctx.elicit = AsyncMock(return_value=mock_result)

        result = asyncio.run(auth_login(mock_ctx, force=True))

        assert result == {"cancelled": True, "message": "Авторизация отменена."}
        mock_run.assert_called_once_with(
            ["auth", "login", "--profile", "default", "--format", "json"],
            timeout=30,
            input="",
        )

    @patch("server.tools.auth_tools.auth_status", return_value={"valid": False})
    @patch("server.tools.auth_tools._find_direct", return_value=None)
    def test_auth_login_cli_not_found(self, _mock_find, _mock_status) -> None:
        result = asyncio.run(auth_login(MagicMock()))
        assert result["error"] == "cli_not_found"

    @patch("server.tools.auth_tools.auth_status", return_value={"valid": False})
    @patch("server.tools.auth_tools._find_direct", return_value="/usr/bin/direct")
    @patch("server.tools.auth_tools._resolve_profile_name", return_value="default")
    @patch("server.tools.auth_tools.DirectCliRunner.run")
    def test_auth_login_cancelled(
        self, mock_run, _mock_resolve, _mock_find, _mock_status
    ) -> None:
        mock_run.return_value = completed(
            json.dumps({"authorize_url": "https://oauth.yandex.ru/authorize?x=1"})
        )

        mock_ctx = MagicMock()
        mock_result = MagicMock()
        mock_result.action = "decline"
        mock_result.data = None
        mock_ctx.elicit = AsyncMock(return_value=mock_result)

        result = asyncio.run(auth_login(mock_ctx))
        assert result == {"cancelled": True, "message": "Авторизация отменена."}
        mock_run.assert_called_once_with(
            ["auth", "login", "--profile", "default", "--format", "json"],
            timeout=30,
            input="",
        )

    @patch("server.tools.auth_tools.auth_status", return_value={"valid": False})
    @patch("server.tools.auth_tools._find_direct", return_value="/usr/bin/direct")
    @patch("server.tools.auth_tools._resolve_profile_name", return_value="default")
    @patch("server.tools.auth_tools.DirectCliRunner.run")
    def test_auth_login_start_cli_failure(
        self, mock_run, _mock_resolve, _mock_find, _mock_status
    ) -> None:
        mock_run.return_value = completed(stderr="\x1b[31mboom\x1b[0m", returncode=2)

        result = asyncio.run(auth_login(MagicMock()))

        assert result == {
            "success": False,
            "error": "auth_login_failed",
            "message": "boom",
        }

    @patch("server.tools.auth_tools.auth_status", return_value={"valid": False})
    @patch("server.tools.auth_tools._find_direct", return_value="/usr/bin/direct")
    @patch("server.tools.auth_tools._resolve_profile_name", return_value="default")
    @patch("server.tools.auth_tools.DirectCliRunner.run")
    def test_auth_login_start_invalid_json(
        self, mock_run, _mock_resolve, _mock_find, _mock_status
    ) -> None:
        mock_run.return_value = completed("not json")

        result = asyncio.run(auth_login(MagicMock()))

        assert result["success"] is False
        assert result["error"] == "auth_login_failed"
        assert result["message"] == "not json"

    @patch("server.tools.auth_tools.auth_status", return_value={"valid": False})
    @patch("server.tools.auth_tools._find_direct", return_value="/usr/bin/direct")
    @patch("server.tools.auth_tools._resolve_profile_name", return_value="default")
    @patch("server.tools.auth_tools.DirectCliRunner.run")
    def test_auth_login_start_missing_authorize_url(
        self, mock_run, _mock_resolve, _mock_find, _mock_status
    ) -> None:
        mock_run.return_value = completed(json.dumps({"status": "pending"}))

        result = asyncio.run(auth_login(MagicMock()))

        assert result["success"] is False
        assert result["error"] == "auth_login_failed"
        assert "authorize_url" in result["message"]

    @patch("server.tools.auth_tools.auth_status", return_value={"valid": False})
    @patch("server.tools.auth_tools._find_direct", return_value="/usr/bin/direct")
    @patch("server.tools.auth_tools._resolve_profile_name", return_value="default")
    @patch("server.tools.auth_tools.DirectCliRunner.run")
    def test_auth_login_start_runner_exception(
        self, mock_run, _mock_resolve, _mock_find, _mock_status
    ) -> None:
        mock_run.side_effect = CliNotFoundError("direct missing")

        result = asyncio.run(auth_login(MagicMock()))

        assert result == {
            "success": False,
            "error": "cli_not_found",
            "message": "direct missing",
        }

    @patch("server.tools.auth_tools.auth_status")
    @patch("server.tools.auth_tools._find_direct", return_value="/usr/bin/direct")
    @patch("server.tools.auth_tools.DirectCliRunner.run")
    def test_auth_login_uses_default_profile_when_omitted(
        self, mock_run, _mock_find, mock_status
    ) -> None:
        mock_status.side_effect = [
            {"valid": False},
            {
                "valid": True,
                "profile": "default",
                "source": "oauth",
                "has_token": True,
                "login": "client",
            },
        ]
        mock_run.side_effect = [
            completed(
                json.dumps({"authorize_url": "https://oauth.yandex.ru/authorize?x=1"})
            ),
            completed("saved"),
        ]

        result = asyncio.run(auth_login(self._accepted_ctx()))

        assert result["profile"] == "default"
        assert result["login"] == "client"
        assert mock_status.call_args_list == [call(None), call("default")]
        assert mock_run.call_args_list[0].args[0] == [
            "auth",
            "login",
            "--profile",
            "default",
            "--format",
            "json",
        ]

    @patch("server.tools.auth_tools.auth_status")
    @patch("server.tools.auth_tools._find_direct", return_value="/usr/bin/direct")
    @patch("server.tools.auth_tools._resolve_profile_name", return_value="custom")
    @patch("server.tools.auth_tools.DirectCliRunner.run")
    def test_auth_login_completes_two_step_pkce_flow(
        self,
        mock_run,
        _mock_resolve,
        _mock_find,
        mock_status,
        monkeypatch,
    ) -> None:
        mock_status.side_effect = [
            {"valid": False},
            {
                "valid": True,
                "profile": "custom",
                "source": "oauth",
                "has_token": True,
                "login": "client",
            },
        ]
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_client_id", "cid")
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_client_secret", "secret")
        monkeypatch.delenv("YANDEX_DIRECT_CLIENT_ID", raising=False)
        monkeypatch.delenv("YANDEX_DIRECT_CLIENT_SECRET", raising=False)
        mock_run.side_effect = [
            completed(
                json.dumps({"authorize_url": "https://oauth.yandex.ru/authorize?x=1"})
            ),
            completed("saved"),
        ]

        result = asyncio.run(
            auth_login(self._accepted_ctx(), login="client", profile="custom")
        )

        assert mock_run.call_args_list[0].args[0] == [
            "auth",
            "login",
            "--profile",
            "custom",
            "--format",
            "json",
            "--login",
            "client",
        ]
        assert mock_run.call_args_list[0].kwargs == {"timeout": 30, "input": ""}
        assert mock_run.call_args_list[1].args[0] == [
            "auth",
            "login",
            "--profile",
            "custom",
            "--code",
            "-",
        ]
        assert mock_run.call_args_list[1].kwargs == {
            "timeout": 60,
            "input": "ABC123\n",
        }
        for recorded_call in mock_run.call_args_list:
            args = recorded_call.args[0]
            assert "--client-id" not in args
            assert "cid" not in args
            assert "--client-secret" not in args
            assert "secret" not in args
            assert "ABC123" not in args
        assert result == {
            "success": True,
            "method": "oauth_code",
            "profile": "custom",
            "login": "client",
        }

    @patch("server.tools.auth_tools.auth_status", return_value={"valid": False})
    @patch("server.tools.auth_tools._find_direct", return_value="/usr/bin/direct")
    @patch("server.tools.auth_tools._resolve_profile_name", return_value="custom")
    @patch("server.tools.auth_tools.DirectCliRunner.run")
    def test_auth_login_falls_back_to_legacy_code_stdin(
        self, mock_run, _mock_resolve, _mock_find, _mock_status, monkeypatch, tmp_path
    ) -> None:
        # No saved profile and no login parameter → response login is "".
        monkeypatch.setenv("HOME", str(tmp_path))
        mock_run.side_effect = [
            completed(
                json.dumps({"authorize_url": "https://oauth.yandex.ru/authorize?x=1"})
            ),
            completed(stderr="invalid authorization code", returncode=1),
            completed("saved"),
        ]

        result = asyncio.run(auth_login(self._accepted_ctx(), profile="custom"))

        assert mock_run.call_args_list[1].args[0] == [
            "auth",
            "login",
            "--profile",
            "custom",
            "--code",
            "-",
        ]
        assert mock_run.call_args_list[2].args[0] == [
            "auth",
            "login",
            "--profile",
            "custom",
            "--code-stdin",
        ]
        assert mock_run.call_args_list[1].kwargs == {
            "timeout": 60,
            "input": "ABC123\n",
        }
        assert mock_run.call_args_list[2].kwargs == {
            "timeout": 60,
            "input": "ABC123\n",
        }
        for recorded_call in mock_run.call_args_list:
            assert "ABC123" not in recorded_call.args[0]
        assert result == {
            "success": True,
            "method": "oauth_code",
            "profile": "custom",
            "login": "",
        }

    @patch("server.tools.auth_tools.auth_status", return_value={"valid": False})
    @patch("server.tools.auth_tools._find_direct", return_value="/usr/bin/direct")
    @patch("server.tools.auth_tools._resolve_profile_name", return_value="custom")
    @patch("server.tools.auth_tools.DirectCliRunner.run")
    def test_auth_login_finish_cli_failure(
        self, mock_run, _mock_resolve, _mock_find, _mock_status
    ) -> None:
        mock_run.side_effect = [
            completed(
                json.dumps({"authorize_url": "https://oauth.yandex.ru/authorize?x=1"})
            ),
            completed(stderr="\x1b[31mbad code\x1b[0m", returncode=1),
            completed(stderr="\x1b[31mbad code\x1b[0m", returncode=1),
        ]

        result = asyncio.run(auth_login(self._accepted_ctx(), profile="custom"))

        assert result == {
            "success": False,
            "error": "auth_failed",
            "message": "bad code",
            "auth_url": "https://oauth.yandex.ru/authorize?x=1",
        }

    @patch("server.tools.auth_tools.auth_status", return_value={"valid": False})
    @patch("server.tools.auth_tools._find_direct", return_value="/usr/bin/direct")
    @patch("server.tools.auth_tools._resolve_profile_name", return_value="custom")
    @patch("server.tools.auth_tools.DirectCliRunner.run")
    def test_auth_login_finish_runner_exception(
        self, mock_run, _mock_resolve, _mock_find, _mock_status
    ) -> None:
        mock_run.side_effect = [
            completed(
                json.dumps({"authorize_url": "https://oauth.yandex.ru/authorize?x=1"})
            ),
            CliError("direct failed"),
            CliError("direct failed"),
        ]

        result = asyncio.run(auth_login(self._accepted_ctx(), profile="custom"))

        assert result == {
            "success": False,
            "error": "auth_failed",
            "message": "direct failed",
            "auth_url": "https://oauth.yandex.ru/authorize?x=1",
        }


def test_oauth_login_prompt_points_to_auth_login() -> None:
    prompt = oauth_login_prompt()
    assert len(prompt) == 1
    assert prompt[0]["role"] == "user"
    assert "auth_login" in prompt[0]["content"]


def test_human_readable_time_formats_expected_ranges() -> None:
    assert _human_readable_time(0) == "истёк"
    assert _human_readable_time(59) == "59 сек."
    assert _human_readable_time(90) == "1 мин. 30 сек."
    assert _human_readable_time(3660) == "1 ч. 1 мин."
