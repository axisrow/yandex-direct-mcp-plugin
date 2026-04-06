"""Tests for DirectCliRunner — edge cases (mock-based)."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from server.cli.runner import CliAuthError, CliNotFoundError, CliTimeoutError, DirectCliRunner


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
class TestRun:
    def test_successful_run(self, runner):
        mock_result = MagicMock()
        mock_result.stdout = '[{"Id": 12345}]'
        mock_result.stderr = ""
        mock_result.returncode = 0

        with (
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
            patch("server.cli.runner.subprocess.run", return_value=mock_result) as mock_run,
        ):
            result = runner.run(["campaigns", "get", "--format", "json"])

            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert cmd[0] == "direct"
            assert "--token" in cmd
            assert "test-token" in cmd
            assert "campaigns" in cmd

    def test_cli_not_found(self, runner):
        """Test 17: direct-cli not in PATH."""
        with patch("server.cli.runner.shutil.which", return_value=None):
            with pytest.raises(CliNotFoundError):
                runner.run(["campaigns", "get"])

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
            patch("server.cli.runner.subprocess.run", side_effect=subprocess.TimeoutExpired("direct", 30)),
        ):
            with pytest.raises(CliTimeoutError):
                runner.run(["campaigns", "get"])


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
