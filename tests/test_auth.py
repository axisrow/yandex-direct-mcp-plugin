"""Tests for auth MCP tools delegated to direct-cli."""

import asyncio
import json
import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

from server.tools.auth_tools import (
    _human_readable_time,
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

    def test_auth_setup_passes_plugin_client_options(self, monkeypatch) -> None:
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_client_id", "cid")
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_client_secret", "secret")
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=_completed("ok"),
        ) as mock_run:
            auth_setup("abc123")

        args = mock_run.call_args.args[0]
        assert "--client-id" in args
        assert "cid" in args
        assert "--client-secret" in args
        assert "secret" in args

    def test_auth_setup_with_oauth_code(self) -> None:
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=_completed("✓ Profile 'custom' is saved and active.\n"),
        ) as mock_run:
            result = auth_setup("abc123", profile="custom")

        assert result["success"] is True
        assert result["method"] == "oauth_code"
        assert result["profile"] == "custom"
        mock_run.assert_called_once_with(
            ["auth", "login", "--profile", "custom", "--code", "abc123"],
            timeout=None,
        )

    def test_auth_setup_rejects_empty_code(self) -> None:
        result = auth_setup("")
        assert result["error"] == "invalid_code"

    def test_auth_setup_reports_cli_failure(self) -> None:
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=_completed(stderr="Error: bad code", returncode=1),
        ):
            result = auth_setup("bad")
        assert result["success"] is False
        assert result["error"] == "auth_failed"


class TestAuthLogin:
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
    @patch("server.tools.auth_tools.subprocess.Popen")
    def test_auth_login_cancelled(self, mock_popen, _mock_find, _mock_status) -> None:
        proc = MagicMock()
        proc.poll.return_value = None
        proc.stdout.readline.return_value = "https://oauth.yandex.ru/authorize?x=1\n"
        mock_popen.return_value = proc

        mock_ctx = MagicMock()
        mock_result = MagicMock()
        mock_result.action = "decline"
        mock_result.data = None
        mock_ctx.elicit = AsyncMock(return_value=mock_result)

        result = asyncio.run(auth_login(mock_ctx))
        assert result == {"cancelled": True, "message": "Авторизация отменена."}
        proc.terminate.assert_called_once()

    @patch("server.tools.auth_tools.auth_status", return_value={"valid": False})
    @patch("server.tools.auth_tools._find_direct", return_value="/usr/bin/direct")
    @patch("server.tools.auth_tools.subprocess.Popen")
    def test_auth_login_sends_code_to_same_process(
        self, mock_popen, _mock_find, _mock_status
    ) -> None:
        proc = MagicMock()
        proc.poll.return_value = None
        proc.returncode = 0
        proc.stdout.readline.return_value = "https://oauth.yandex.ru/authorize?x=1\n"
        proc.communicate.return_value = ("saved", "")
        mock_popen.return_value = proc

        mock_ctx = MagicMock()
        credential = MagicMock()
        credential.action = "accept"
        credential.data.value = "ABC123"
        mock_ctx.elicit = AsyncMock(return_value=credential)

        result = asyncio.run(auth_login(mock_ctx, login="client", profile="custom"))

        mock_popen.assert_called_once()
        cmd = mock_popen.call_args.args[0]
        kwargs = mock_popen.call_args.kwargs
        assert cmd == [
            "/usr/bin/direct",
            "auth",
            "login",
            "--profile",
            "custom",
            "--login",
            "client",
        ]
        assert "env" in kwargs
        proc.communicate.assert_called_once_with(input="ABC123\n", timeout=60)
        assert result == {
            "success": True,
            "method": "oauth_code",
            "profile": "custom",
            "login": "client",
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
