"""Tests for auth MCP tools delegated to direct-cli."""

import asyncio
import json
import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

from server.cli.runner import CliError, CliNotFoundError, CliTimeoutError
from server.tools.auth_tools import (
    _human_readable_time,
    _login_finish_args,
    _login_start_args,
    _token_setup_args,
    auth_login,
    auth_setup,
    auth_status,
    oauth_login_prompt,
)


def _completed(stdout: str = "", stderr: str = "", returncode: int = 0):
    return subprocess.CompletedProcess(
        args=["direct"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


class TestAuthStatus:
    def test_auth_status_returns_invalid_without_active_profile(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("HOME", str(tmp_path))
        assert auth_status() == {
            "valid": False,
            "reason": "not_authenticated",
            "profile": "default",
        }

    def test_auth_status_reads_direct_cli_profile(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("HOME", str(tmp_path))
        auth_path = tmp_path / ".direct-cli" / "auth.json"
        auth_path.parent.mkdir()
        auth_path.write_text(
            json.dumps(
                {
                    "active_profile": "default",
                    "profiles": {
                        "default": {
                            "token": "token",
                            "login": "client",
                            "source": "oauth",
                            "expires_at": 2_000_000_000.0,
                        }
                    },
                }
            )
        )

        result = auth_status()
        assert result["valid"] is True
        assert result["profile"] == "default"
        assert result["login"] == "client"
        assert result["expires_in"] > 0
        assert "expires_in_human" in result

    def test_auth_status_marks_old_profile_refresh_unavailable(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("HOME", str(tmp_path))
        auth_path = tmp_path / ".direct-cli" / "auth.json"
        auth_path.parent.mkdir()
        auth_path.write_text(
            json.dumps(
                {
                    "profiles": {
                        "legacy": {
                            "token": "token",
                            "login": "client",
                            "source": "manual",
                        }
                    }
                }
            )
        )

        result = auth_status("legacy")
        assert result["valid"] is True
        assert result["refresh_unavailable"] is True

    def test_auth_status_marks_expired_profile_invalid(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("HOME", str(tmp_path))
        auth_path = tmp_path / ".direct-cli" / "auth.json"
        auth_path.parent.mkdir()
        auth_path.write_text(
            json.dumps(
                {
                    "active_profile": "default",
                    "profiles": {
                        "default": {
                            "token": "token",
                            "login": "client",
                            "expires_at": 1.0,
                        }
                    },
                }
            )
        )

        result = auth_status()
        assert result["valid"] is False
        assert result["has_token"] is True
        assert result["expires_in"] == 0


class TestAuthSetup:
    def test_auth_setup_with_direct_token(self) -> None:
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=_completed("✓ Profile 'default' is saved and active.\n"),
        ) as mock_run:
            result = auth_setup("y0_token", login="client")

        assert result == {
            "success": True,
            "method": "direct_token",
            "profile": "default",
            "login": "client",
        }
        mock_run.assert_called_once_with(
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
        )

    def test_auth_setup_ignores_plugin_client_options(self, monkeypatch) -> None:
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_client_id", "cid")
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_client_secret", "secret")
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=_completed("ok"),
        ) as mock_run:
            auth_setup("y0_token")

        args = mock_run.call_args.args[0]
        assert "--client-id" not in args
        assert "cid" not in args
        assert "--client-secret" not in args
        assert "secret" not in args

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
            "--code-stdin",
        ]

    def test_auth_setup_rejects_browser_oauth_code_without_cli_call(self) -> None:
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=_completed("✓ Profile 'custom' is saved and active.\n"),
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
            return_value=_completed(stderr="Error: bad code", returncode=1),
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
        mock_run.return_value = _completed(
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
        mock_run.return_value = _completed(stderr="\x1b[31mboom\x1b[0m", returncode=2)

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
        mock_run.return_value = _completed("not json")

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
        mock_run.return_value = _completed(json.dumps({"status": "pending"}))

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

    @patch("server.tools.auth_tools._read_auth_store")
    @patch("server.tools.auth_tools._find_direct", return_value="/usr/bin/direct")
    @patch("server.tools.auth_tools.DirectCliRunner.run")
    def test_auth_login_uses_active_profile_when_omitted(
        self, mock_run, _mock_find, mock_store
    ) -> None:
        mock_store.return_value = {
            "active_profile": "agency",
            "profiles": {"agency": {"token": "", "login": "client"}},
        }
        mock_run.side_effect = [
            _completed(
                json.dumps({"authorize_url": "https://oauth.yandex.ru/authorize?x=1"})
            ),
            _completed("saved"),
        ]

        result = asyncio.run(auth_login(self._accepted_ctx()))

        assert result["profile"] == "agency"
        assert mock_run.call_args_list[0].args[0] == [
            "auth",
            "login",
            "--profile",
            "agency",
            "--format",
            "json",
        ]

    @patch("server.tools.auth_tools.auth_status", return_value={"valid": False})
    @patch("server.tools.auth_tools._find_direct", return_value="/usr/bin/direct")
    @patch("server.tools.auth_tools._resolve_profile_name", return_value="custom")
    @patch("server.tools.auth_tools.DirectCliRunner.run")
    def test_auth_login_completes_two_step_pkce_flow(
        self,
        mock_run,
        _mock_resolve,
        _mock_find,
        _mock_status,
        monkeypatch,
    ) -> None:
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_client_id", "cid")
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_client_secret", "secret")
        monkeypatch.delenv("YANDEX_DIRECT_CLIENT_ID", raising=False)
        monkeypatch.delenv("YANDEX_DIRECT_CLIENT_SECRET", raising=False)
        mock_run.side_effect = [
            _completed(
                json.dumps({"authorize_url": "https://oauth.yandex.ru/authorize?x=1"})
            ),
            _completed("saved"),
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
            "--code-stdin",
        ]
        assert mock_run.call_args_list[1].kwargs == {
            "timeout": 60,
            "input": "ABC123\n",
        }
        for call in mock_run.call_args_list:
            args = call.args[0]
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
    def test_auth_login_finish_cli_failure(
        self, mock_run, _mock_resolve, _mock_find, _mock_status
    ) -> None:
        mock_run.side_effect = [
            _completed(
                json.dumps({"authorize_url": "https://oauth.yandex.ru/authorize?x=1"})
            ),
            _completed(stderr="\x1b[31mbad code\x1b[0m", returncode=1),
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
            _completed(
                json.dumps({"authorize_url": "https://oauth.yandex.ru/authorize?x=1"})
            ),
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
