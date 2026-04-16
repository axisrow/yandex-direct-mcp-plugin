"""Tests for DirectCliRunner — edge cases (mock-based)."""

import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from server.cli.runner import (
    CliAuthError,
    CliNotFoundError,
    CliRegistrationError,
    CliTimeoutError,
    DirectCliRunner,
    _find_direct,
)


@pytest.fixture
def runner():
    return DirectCliRunner(token="test-token")


@pytest.mark.mocks
class TestIsAvailable:
    def test_available(self, runner):
        with patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"):
            assert runner.is_available() is True

    def test_not_available(self, runner):
        with patch("server.cli.runner.shutil.which", return_value=None):
            assert runner.is_available() is False


@pytest.mark.mocks
class TestFindDirect:
    def test_explicit_env_var(self, tmp_path):
        direct_bin = tmp_path / "direct"
        direct_bin.touch()
        with patch.dict(os.environ, {"YANDEX_DIRECT_CLI_PATH": str(direct_bin)}):
            assert _find_direct() == str(direct_bin)

    def test_plugin_venv(self, tmp_path):
        venv_bin = tmp_path / "venv" / "bin" / "direct"
        venv_bin.parent.mkdir(parents=True)
        venv_bin.touch()
        with (
            patch.dict(os.environ, {"CLAUDE_PLUGIN_DATA": str(tmp_path)}),
            patch("server.cli.runner.shutil.which", return_value=None),
        ):
            assert _find_direct() == str(venv_bin)

    def test_system_path(self):
        with (
            patch.dict(os.environ, {"CLAUDE_PLUGIN_DATA": ""}, clear=False),
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
        ):
            assert _find_direct() == "/usr/bin/direct"

    def test_user_local_bin(self, tmp_path):
        local_bin = tmp_path / ".local" / "bin" / "direct"
        local_bin.parent.mkdir(parents=True)
        local_bin.touch()
        with (
            patch.dict(os.environ, {"HOME": str(tmp_path), "CLAUDE_PLUGIN_DATA": ""}, clear=False),
            patch("server.cli.runner.shutil.which", return_value=None),
        ):
            assert _find_direct() == str(local_bin)

    def test_not_found(self, tmp_path):
        with (
            patch.dict(os.environ, {"HOME": str(tmp_path), "CLAUDE_PLUGIN_DATA": ""}, clear=False),
            patch("server.cli.runner.shutil.which", return_value=None),
        ):
            assert _find_direct() is None

    def test_plugin_venv_takes_priority_over_system(self, tmp_path):
        venv_bin = tmp_path / "venv" / "bin" / "direct"
        venv_bin.parent.mkdir(parents=True)
        venv_bin.touch()
        with (
            patch.dict(os.environ, {"CLAUDE_PLUGIN_DATA": str(tmp_path)}),
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
        ):
            assert _find_direct() == str(venv_bin)


@pytest.mark.mocks
class TestRun:
    def test_successful_run(self, runner):
        mock_result = MagicMock()
        mock_result.stdout = '[{"Id": 12345}]'
        mock_result.stderr = ""
        mock_result.returncode = 0

        with (
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
            patch(
                "server.cli.runner.subprocess.run", return_value=mock_result
            ) as mock_run,
        ):
            runner.run(["campaigns", "get", "--format", "json"])

            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert cmd[0] == "/usr/bin/direct"
            assert "--token" in cmd
            assert "test-token" in cmd
            assert "campaigns" in cmd

    def test_cli_not_found(self, runner):
        """Test 17: direct-cli not in PATH."""
        with patch("server.cli.runner.shutil.which", return_value=None):
            with pytest.raises(CliNotFoundError) as exc_info:
                runner.run(["campaigns", "get"])
            assert "Install package direct-cli and run `direct`" in str(
                exc_info.value
            )

    def test_cli_not_found_file_not_found(self, runner):
        """Test 17: FileNotFoundError from subprocess."""
        with (
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
            patch("server.cli.runner.subprocess.run", side_effect=FileNotFoundError),
        ):
            with pytest.raises(CliNotFoundError):
                runner.run(["campaigns", "get"])

    def test_timeout(self, runner):
        """Test 19: CLI hangs >30s."""
        with (
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
            patch(
                "server.cli.runner.subprocess.run",
                side_effect=subprocess.TimeoutExpired("direct", 30),
            ),
        ):
            with pytest.raises(CliTimeoutError) as exc_info:
                runner.run(["campaigns", "get"])
            assert "direct timed out after 30s" in str(exc_info.value)


@pytest.mark.mocks
class TestRunJson:
    def test_empty_response(self, runner):
        """Test 18: Empty API response."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0

        with (
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
            patch("server.cli.runner.subprocess.run", return_value=mock_result),
        ):
            result = runner.run_json(["campaigns", "get"])
            assert result == []

    def test_json_parse(self, runner):
        mock_result = MagicMock()
        mock_result.stdout = '[{"Id": 12345, "Name": "Test"}]'
        mock_result.stderr = ""
        mock_result.returncode = 0

        with (
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
            patch("server.cli.runner.subprocess.run", return_value=mock_result),
        ):
            result = runner.run_json(["campaigns", "get", "--format", "json"])
            assert len(result) == 1
            assert result[0]["Id"] == 12345

    def test_auth_error(self, runner):
        """Test 401 response."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "401 Unauthorized"
        mock_result.returncode = 1

        with (
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
            patch("server.cli.runner.subprocess.run", return_value=mock_result),
        ):
            with pytest.raises(CliAuthError):
                runner.run_json(["campaigns", "get"])

    def test_registration_error_58(self, runner):
        """Test error code 58 (incomplete registration)."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = (
            "✗ request_id=123, error_code=58, "
            "error_string=Incomplete registration, "
            "error_detail=You need to fill out an app access request"
        )
        mock_result.returncode = 1

        with (
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
            patch("server.cli.runner.subprocess.run", return_value=mock_result),
        ):
            with pytest.raises(CliRegistrationError):
                runner.run_json(["campaigns", "get"])

    def test_no_false_positive_error_580(self, runner):
        """Test that error_code=580 does NOT trigger CliRegistrationError."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "error_code=580"
        mock_result.returncode = 1

        with (
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
            patch("server.cli.runner.subprocess.run", return_value=mock_result),
        ):
            from server.cli.runner import CliError

            with pytest.raises(CliError) as exc_info:
                runner.run_json(["campaigns", "get"])
            assert not isinstance(exc_info.value, CliRegistrationError)
