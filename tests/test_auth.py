"""Tests for auth MCP tools delegated to `direct`."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, call, patch

from server.cli.runner import CliError, CliNotFoundError, CliTimeoutError
from server.tools.auth_tools import (
    _browser_login_args,
    _human_readable_time,
    _login_finish_args,
    _login_start_args,
    _token_setup_args,
    auth_browser_login,
    auth_browser_logout,
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

    def test_auth_status_normalizes_combined_api_and_browser_payload(self) -> None:
        """direct-cli 0.5.4 answers `auth status --format json` with both
        domains nested in {api, browser}; the API contract of this tool gains
        the browser section without changing existing keys (#313). Since
        direct-cli #951 the browser section is a flat report of the single
        store playwright/session.json."""
        browser = {
            "exists": True,
            "owner_login": "ksamatadirect",
            "expired": False,
            "cookie_count": 47,
            "path": "/home/u/.direct-cli/playwright/session.json",
            "error": None,
        }
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                json.dumps(
                    {
                        "api": {
                            "profile": "default",
                            "source": "oauth",
                            "has_token": True,
                            "login": "client",
                            "expires_at": 2_000_000_000.0,
                            "expires_in_seconds": 3600,
                        },
                        "browser": browser,
                    }
                )
            ),
        ) as mock_run:
            result = auth_status()

        assert result["valid"] is True
        assert result["profile"] == "default"
        assert result["source"] == "oauth"
        assert result["has_token"] is True
        assert result["login"] == "client"
        assert result["expires_at"] == 2_000_000_000.0
        assert result["expires_in"] == 3600
        assert result["expires_in_human"] == "1 ч."
        assert result["browser"] == browser
        assert result["browser_valid"] is True
        mock_run.assert_called_once_with(["auth", "status", "--format", "json"])

    def test_auth_status_parses_legacy_tier_browser_payload(self) -> None:
        """The pinned direct-cli 0.5.5 wheel predates #951 and still reports
        the tier form; an active tier must yield browser_valid True (#313,
        review of PR #330)."""
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                json.dumps(
                    {
                        "api": {
                            "profile": "default",
                            "source": "oauth",
                            "has_token": True,
                            "login": "client",
                        },
                        "browser": {
                            "active_tier": "1.5",
                            "active_source": "masters login",
                            "persistent_profile": {
                                "path": "/home/u/.direct-cli/chrome-profile",
                                "usable": True,
                            },
                            "saved_session": {"exists": True, "expired": False},
                        },
                    }
                )
            ),
        ):
            result = auth_status()

        assert result["valid"] is True
        assert result["browser"] == {
            "active_tier": "1.5",
            "active_source": "masters login",
            "persistent_profile": {
                "path": "/home/u/.direct-cli/chrome-profile",
                "usable": True,
            },
            "saved_session": {"exists": True, "expired": False},
        }
        assert result["browser_valid"] is True

    def test_auth_status_parses_legacy_tier_without_usable_session(self) -> None:
        """active_tier=None on the tier form means no usable browser session,
        next to a valid API token (#313)."""
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                json.dumps(
                    {
                        "api": {
                            "profile": "default",
                            "source": "oauth",
                            "has_token": True,
                            "login": "client",
                        },
                        "browser": {
                            "active_tier": None,
                            "active_source": None,
                            "persistent_profile": {
                                "path": "/home/u/.direct-cli/chrome-profile",
                                "usable": False,
                            },
                            "saved_session": {"exists": False, "expired": None},
                        },
                    }
                )
            ),
        ):
            result = auth_status()

        assert result["valid"] is True
        assert result["browser_valid"] is False

    def test_auth_status_reports_browser_valid_without_api_token(self) -> None:
        """The browser session is independent of the API token: an
        authenticated browser next to a missing API token must still surface
        as browser_valid (#313)."""
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                json.dumps(
                    {
                        "api": {
                            "profile": None,
                            "source": None,
                            "has_token": False,
                            "login": None,
                        },
                        "browser": {
                            "exists": True,
                            "owner_login": "ksamatadirect",
                            "expired": False,
                            "cookie_count": 47,
                            "path": "/home/u/.direct-cli/playwright/session.json",
                            "error": None,
                        },
                    }
                )
            ),
        ):
            result = auth_status()

        assert result["valid"] is False
        assert result["reason"] == "not_authenticated"
        assert result["browser_valid"] is True

    def test_auth_status_reports_expired_browser_session_invalid(self) -> None:
        """An expired session store with a valid API token means the browser
        session needs re-login before the next masters call (#313)."""
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                json.dumps(
                    {
                        "api": {
                            "profile": "default",
                            "source": "oauth",
                            "has_token": True,
                            "login": "client",
                        },
                        "browser": {
                            "exists": True,
                            "owner_login": "ksamatadirect",
                            "expired": True,
                            "cookie_count": None,
                            "path": "/home/u/.direct-cli/playwright/session.json",
                            "error": None,
                        },
                    }
                )
            ),
        ):
            result = auth_status()

        assert result["valid"] is True
        assert result["browser_valid"] is False

    def test_auth_status_reports_broken_browser_session_invalid(self) -> None:
        """A non-null error on the session store makes the browser session
        unusable even though an envelope exists (direct-cli #951)."""
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                json.dumps(
                    {
                        "api": {
                            "profile": "default",
                            "source": "oauth",
                            "has_token": True,
                            "login": "client",
                        },
                        "browser": {
                            "exists": True,
                            "owner_login": None,
                            "expired": None,
                            "cookie_count": None,
                            "path": "/home/u/.direct-cli/playwright/session.json",
                            "error": "corrupt envelope",
                        },
                    }
                )
            ),
        ):
            result = auth_status()

        assert result["valid"] is True
        assert result["browser_valid"] is False

    def test_auth_status_reports_revoked_browser_session_invalid(self) -> None:
        """A server-revoked SSO session (probe=revoked) must read as invalid
        even though the cookies themselves are fresh — exactly the case the
        CLI probe names instead of guessing (direct-cli #954)."""
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                json.dumps(
                    {
                        "api": {
                            "profile": "default",
                            "source": "oauth",
                            "has_token": True,
                            "login": "client",
                        },
                        "browser": {
                            "exists": True,
                            "owner_login": "ksamatadirect",
                            "expired": False,
                            "cookie_count": 46,
                            "path": "/home/u/.direct-cli/playwright/session.json",
                            "error": None,
                            "probe": "revoked",
                        },
                    }
                )
            ),
        ):
            result = auth_status()

        assert result["valid"] is True
        assert result["browser_valid"] is False

    def test_auth_status_reports_alive_probe_browser_valid(self) -> None:
        """probe=alive keeps the flat-form verdict positive (direct-cli #954)."""
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                json.dumps(
                    {
                        "api": {
                            "profile": "default",
                            "source": "oauth",
                            "has_token": True,
                            "login": "client",
                        },
                        "browser": {
                            "exists": True,
                            "owner_login": "ksamatadirect",
                            "expired": False,
                            "cookie_count": 46,
                            "path": "/home/u/.direct-cli/playwright/session.json",
                            "error": None,
                            "probe": "alive",
                        },
                    }
                )
            ),
        ):
            result = auth_status()

        assert result["valid"] is True
        assert result["browser_valid"] is True

    def test_auth_status_reports_probe_absent_browser_valid(self) -> None:
        """Wheels before the probe (pinned direct-cli 0.5.5) carry no probe
        key at all; its absence must not flip the verdict (#954)."""
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                json.dumps(
                    {
                        "api": {
                            "profile": "default",
                            "source": "oauth",
                            "has_token": True,
                            "login": "client",
                        },
                        "browser": {
                            "exists": True,
                            "owner_login": "ksamatadirect",
                            "expired": False,
                            "cookie_count": 46,
                            "path": "/home/u/.direct-cli/playwright/session.json",
                            "error": None,
                        },
                    }
                )
            ),
        ):
            result = auth_status()

        assert result["valid"] is True
        assert result["browser_valid"] is True

    def test_auth_status_reads_nested_api_payload_with_global_fallback(self) -> None:
        """Verbatim `direct auth status --format json` shape (direct-cli 0.5.5,
        #951): both domains nested under api/browser; an unconfigured API
        profile still reports global fallback credentials the tool must ignore
        when deciding validity (direct-cli#969)."""
        browser = {
            "exists": True,
            "path": "/Users/u/.direct-cli/playwright/session.json",
            "version": 1,
            "created_at": 1793602849.103184,
            "owner_login": "ksamatadirect",
            "age_seconds": 38331,
            "cookie_count": 46,
            "expires_at": 1828072537.388149,
            "expired": False,
            "mode": "0600",
            "error": None,
            "sso_cookie_names": ["Session_id", "sessionid2", "yandex_login"],
            "sso_cookies": 3,
            "probe": "unknown",
        }
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                json.dumps(
                    {
                        "api": {
                            "profile": None,
                            "source": None,
                            "has_token": False,
                            "login": None,
                            "global_profile": "engineeringprint",
                            "global_login": "engineeringprint.ru",
                        },
                        "browser": browser,
                    }
                )
            ),
        ) as mock_run:
            result = auth_status()

        assert result["valid"] is False
        assert result["reason"] == "not_authenticated"
        assert result["profile"] == "default"
        # Global fallback credentials are proxied inside the api payload only;
        # the flat tool surface must not invent a login for them.
        assert "login" not in result
        assert result["browser"] == browser
        assert result["browser_valid"] is True
        mock_run.assert_called_once_with(["auth", "status", "--format", "json"])


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
            result = auth_setup("y0_FAKE-TEST-TOKEN", login="client")

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
                    "api",
                    "--profile",
                    "default",
                    "--oauth-token",
                    "y0_FAKE-TEST-TOKEN",
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
        # The token reached the CLI's api subcommand rather than being
        # rejected up front.
        assert mock_run.call_args_list[0].args[0][:3] == ["auth", "login", "api"]
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
            "api",
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
            "api",
            "--profile",
            "default",
            "--oauth-token",
            "y0_token",
        ]
        assert login_args == [
            "auth",
            "login",
            "api",
            "--profile",
            "default",
            "--format",
            "json",
        ]
        assert _login_finish_args() == [
            "auth",
            "login",
            "api",
            "--profile",
            "default",
            "--code",
            "-",
        ]
        assert _login_start_args(force=True)[-1] == "--force"
        assert _login_finish_args(profile="p", force=True)[-1] == "--force"

    def test_auth_setup_force_flag_reaches_cli(self) -> None:
        """force=true is forwarded as the CLI's --force (direct-cli#970):
        the only way an existing profile's credentials get overwritten."""
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
            result = auth_setup("y0_FAKE-TEST-TOKEN", force=True)

        assert result["success"] is True
        assert mock_run.call_args_list[0].args[0][-1] == "--force"

    def test_auth_setup_default_never_passes_force(self) -> None:
        """Without force the CLI must stay free to refuse the overwrite:
        no implicit rewriting of an existing profile (direct-cli#970)."""
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
            auth_setup("y0_FAKE-TEST-TOKEN")

        assert "--force" not in mock_run.call_args_list[0].args[0]

    def test_auth_setup_overwrite_refusal_maps_to_profile_exists(self) -> None:
        """The CLI's overwrite refusal becomes a machine-readable
        profile_exists error with a force=true hint — no implicit retry
        (direct-cli#970). stderr text is verbatim `direct auth login api`
        output (click UsageError, direct-cli 0.5.5 commands/auth.py)."""
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                stderr=(
                    "Error: Profile 'default' already exists "
                    "(login=engineeringprint.ru). Overwriting requires --force, "
                    "or pick another name with --profile NAME."
                ),
                returncode=1,
            ),
        ) as mock_run:
            result = auth_setup("y0_FAKE-TEST-TOKEN", login="engineeringprint.ru")

        assert result["success"] is False
        assert result["error"] == "profile_exists"
        assert "already exists" in result["message"]
        assert "force=true" in result["hint"]
        # Exactly one CLI call: the refusal is surfaced, not retried implicitly.
        assert mock_run.call_count == 1

    def test_auth_setup_refusal_heuristic_accepts_localized_text(self) -> None:
        """The refusal heuristic also matches a localized «уже существует»
        message so a translated CLI stays covered (direct-cli#970 review)."""
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                stderr=(
                    "Профиль 'default' уже существует (login=client). "
                    "Перезапись требует --force."
                ),
                returncode=1,
            ),
        ):
            result = auth_setup("y0_FAKE-TEST-TOKEN")

        assert result["error"] == "profile_exists"
        assert "force=true" in result["hint"]

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

    @patch("server.tools.auth_tools.auth_status")
    def test_auth_login_preflight_refuses_stored_token_without_force(
        self, mock_status
    ) -> None:
        """An existing profile with a stored (invalid/expired) token refuses
        BEFORE elicitation: the CLI gates every save on profile existence, so
        the finish would reject the code anyway — the user's manual step must
        not be spent on a doomed flow (#970 review)."""
        mock_status.return_value = {
            "valid": False,
            "has_token": True,
            "profile": "default",
            "login": "client",
        }
        mock_ctx = MagicMock()
        mock_ctx.elicit = AsyncMock()

        result = asyncio.run(auth_login(mock_ctx))

        assert result["success"] is False
        assert result["error"] == "profile_exists"
        assert "force=true" in result["hint"]
        mock_ctx.elicit.assert_not_called()

    @patch("server.tools.auth_tools.auth_status")
    def test_auth_login_preflight_skipped_with_force(self, mock_status) -> None:
        """force=true acknowledges the overwrite and proceeds into the OAuth
        flow despite the stored token (#970 review)."""
        mock_status.return_value = {
            "valid": False,
            "has_token": True,
            "profile": "default",
            "login": "client",
        }
        mock_ctx = MagicMock()
        decline = MagicMock()
        decline.action = "decline"
        decline.data = None
        mock_ctx.elicit = AsyncMock(return_value=decline)
        with (
            patch(
                "server.tools.auth_tools._find_direct", return_value="/usr/bin/direct"
            ),
            patch(
                "server.tools.auth_tools.DirectCliRunner.run",
                return_value=completed(
                    json.dumps(
                        {"authorize_url": "https://oauth.yandex.ru/authorize?x=1"}
                    )
                ),
            ),
        ):
            result = asyncio.run(auth_login(mock_ctx, force=True))

        # force passes the pre-flight; the flow reaches elicitation (declined
        # here) instead of refusing.
        assert result == {"cancelled": True, "message": "Авторизация отменена."}

    @patch("server.tools.auth_tools.auth_status", return_value={"valid": False})
    @patch("server.tools.auth_tools._find_direct", return_value="/usr/bin/direct")
    @patch("server.tools.auth_tools._resolve_profile_name", return_value="custom")
    @patch("server.tools.auth_tools.DirectCliRunner.run")
    def test_auth_login_finish_refusal_maps_to_profile_exists(
        self, mock_run, _mock_resolve, _mock_find, _mock_status
    ) -> None:
        """Belt-and-suspenders for a pre-flight miss (profile exists without a
        token in status): the finish-time CLI refusal maps to profile_exists
        like auth_setup (direct-cli#970 review)."""
        mock_run.side_effect = [
            completed(
                json.dumps({"authorize_url": "https://oauth.yandex.ru/authorize?x=1"})
            ),
            completed(
                stderr=(
                    "Error: Profile 'custom' already exists. Overwriting "
                    "requires --force, or pick another name with --profile NAME."
                ),
                returncode=1,
            ),
        ]

        result = asyncio.run(auth_login(self._accepted_ctx(), profile="custom"))

        assert result["success"] is False
        assert result["error"] == "profile_exists"
        assert "already exists" in result["message"]
        assert "force=true" in result["hint"]
        # The dead authorize URL is not echoed back: retrying with force
        # re-runs the whole flow, so the old URL would be misleading.
        assert "auth_url" not in result

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
            [
                "auth",
                "login",
                "api",
                "--profile",
                "default",
                "--format",
                "json",
                "--force",
            ],
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
            ["auth", "login", "api", "--profile", "default", "--format", "json"],
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
            "api",
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
            "api",
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
            "api",
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
    def test_auth_login_force_authorizes_cli_overwrite(
        self, mock_run, _mock_resolve, _mock_find, _mock_status
    ) -> None:
        """force=True travels into both CLI calls as --force: finishing an
        OAuth re-auth into an existing profile is an explicit overwrite
        (direct-cli#970)."""
        mock_run.side_effect = [
            completed(
                json.dumps({"authorize_url": "https://oauth.yandex.ru/authorize?x=1"})
            ),
            completed("saved"),
        ]

        result = asyncio.run(
            auth_login(self._accepted_ctx(), profile="custom", force=True)
        )

        assert mock_run.call_args_list[0].args[0][-1] == "--force"
        assert mock_run.call_args_list[1].args[0][-1] == "--force"
        assert result["success"] is True

    @patch("server.tools.auth_tools.auth_status", return_value={"valid": False})
    @patch("server.tools.auth_tools._find_direct", return_value="/usr/bin/direct")
    @patch("server.tools.auth_tools._resolve_profile_name", return_value="custom")
    @patch("server.tools.auth_tools.DirectCliRunner.run")
    def test_auth_login_finishes_single_api_code_form(
        self, mock_run, _mock_resolve, _mock_find, _mock_status, monkeypatch, tmp_path
    ) -> None:
        # No saved profile and no login parameter → response login is "".
        # The removed --code-stdin fallback is gone with direct-cli #951:
        # one finish call, one form (#969).
        monkeypatch.setenv("HOME", str(tmp_path))
        mock_run.side_effect = [
            completed(
                json.dumps({"authorize_url": "https://oauth.yandex.ru/authorize?x=1"})
            ),
            completed("saved"),
        ]

        result = asyncio.run(auth_login(self._accepted_ctx(), profile="custom"))

        assert mock_run.call_args_list[1].args[0] == [
            "auth",
            "login",
            "api",
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
            assert "ABC123" not in recorded_call.args[0]
            assert "--code-stdin" not in recorded_call.args[0]
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


class TestAuthBrowserLogin:
    def test_browser_login_args_manual_defaults(self) -> None:
        assert _browser_login_args("manual") == [
            "auth",
            "login",
            "browser",
            "--source",
            "manual",
            "--format",
            "json",
            "--timeout",
            "300",
            "--allow-no-tty",
        ]

    def test_browser_login_args_chrome_omits_manual_only_flags(self) -> None:
        """The CLI rejects mixed options (--timeout/--allow-no-tty with
        chrome, --profile-dir/--chrome-profile with manual), so they never
        travel. --profile-dir is chrome-only since direct-cli #951 removed it
        from the manual flow."""
        assert _browser_login_args(
            "chrome",
            profile_dir="/tmp/chrome-data",
            chrome_profile="Profile 1",
            timeout=60,
            allow_no_tty=False,
            profile="work",
        ) == [
            "auth",
            "login",
            "browser",
            "--source",
            "chrome",
            "--format",
            "json",
            "--profile",
            "work",
            "--profile-dir",
            "/tmp/chrome-data",
            "--chrome-profile",
            "Profile 1",
        ]

    def test_auth_browser_login_manual_success_reports_browser_status(self) -> None:
        browser = {
            "exists": True,
            "owner_login": "ksamatadirect",
            "expired": False,
            "cookie_count": 47,
            "path": "/h/.direct-cli/playwright/session.json",
            "error": None,
        }
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            side_effect=[
                completed(json.dumps({"saved": True, "source": "manual"})),
                completed(
                    json.dumps(
                        {
                            "api": {
                                "profile": "default",
                                "source": "oauth",
                                "has_token": True,
                                "login": "client",
                            },
                            "browser": browser,
                        }
                    )
                ),
            ],
        ) as mock_run:
            result = auth_browser_login(timeout=60)

        assert result["success"] is True
        assert result["saved"] is True
        assert result["source"] == "manual"
        assert result["profile"] == "default"
        assert result["browser"] == browser
        assert result["browser_valid"] is True
        # The CLI owns the wait: subprocess timeout = CLI timeout + headroom,
        # and stdin is an empty pipe (no TTY inheritance from the MCP host).
        assert mock_run.call_args_list[0].args[0] == [
            "auth",
            "login",
            "browser",
            "--source",
            "manual",
            "--format",
            "json",
            "--timeout",
            "60",
            "--allow-no-tty",
        ]
        assert mock_run.call_args_list[0].kwargs == {"timeout": 90, "input": ""}
        assert mock_run.call_args_list[1].args[0] == [
            "auth",
            "status",
            "--format",
            "json",
        ]

    def test_auth_browser_login_non_json_output_still_succeeds(self) -> None:
        """A text-format fallback output must not fail the tool: the session
        state comes from the follow-up status call anyway."""
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            side_effect=[
                completed("✓ Login confirmed."),
                completed(
                    json.dumps(
                        {
                            "api": {
                                "profile": "default",
                                "source": "oauth",
                                "has_token": True,
                                "login": "client",
                            },
                            "browser": {
                                "exists": False,
                                "owner_login": None,
                                "expired": None,
                                "cookie_count": None,
                                "path": "/h/.direct-cli/playwright/session.json",
                                "error": None,
                            },
                        }
                    )
                ),
            ],
        ):
            result = auth_browser_login()

        assert result["success"] is True
        assert "saved" not in result
        assert result["browser_valid"] is False

    def test_auth_browser_login_cli_failure_is_returned(self) -> None:
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                stderr=(
                    "Manual browser login needs an interactive terminal. Run "
                    "`direct auth login browser` in a terminal "
                    "(override: --allow-no-tty)."
                ),
                returncode=1,
            ),
        ) as mock_run:
            result = auth_browser_login(allow_no_tty=False)

        assert result == {
            "success": False,
            "error": "auth_failed",
            "message": (
                "Manual browser login needs an interactive terminal. Run "
                "`direct auth login browser` in a terminal "
                "(override: --allow-no-tty)."
            ),
        }
        assert "--allow-no-tty" not in mock_run.call_args.args[0]


class TestAuthBrowserLogout:
    def test_auth_browser_logout_proxies_cli_result(self) -> None:
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed("✓ Browser sessions removed."),
        ) as mock_run:
            result = auth_browser_logout()

        assert result == {"success": True, "message": "✓ Browser sessions removed."}
        # The subcommand takes no flags (CLI 0.5.5): bare argv, and unlike
        # login there is no follow-up status call.
        mock_run.assert_called_once_with(
            ["auth", "logout", "browser"], timeout=None, input=""
        )

    def test_auth_browser_logout_cli_failure_is_returned(self) -> None:
        with patch(
            "server.tools.auth_tools.DirectCliRunner.run",
            return_value=completed(
                stderr="✗ No saved browser sessions.",
                returncode=1,
            ),
        ):
            result = auth_browser_logout()

        assert result == {
            "success": False,
            "error": "auth_failed",
            "message": "✗ No saved browser sessions.",
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
