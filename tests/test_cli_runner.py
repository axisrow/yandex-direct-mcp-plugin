"""Tests for DirectCliRunner — edge cases (mock-based)."""

import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from server.cli.runner import (
    MIN_DIRECT_VERSION,
    CliAuthError,
    CliNotFoundError,
    CliRegistrationError,
    CliTimeoutError,
    DirectCliRunner,
    _find_direct,
    _probe_direct_version,
    _reset_direct_cache,
)

# Use the runtime floor as the "known-good" version in mocks so that future
# bumps of MIN_DIRECT_VERSION don't silently turn every mocked binary stale.
_KNOWN_GOOD_VERSION = MIN_DIRECT_VERSION
_KNOWN_STALE_VERSION = (
    MIN_DIRECT_VERSION[0],
    MIN_DIRECT_VERSION[1],
    max(0, MIN_DIRECT_VERSION[2] - 1),
)


@pytest.fixture
def runner():
    return DirectCliRunner()


@pytest.fixture(autouse=True)
def _isolate_direct_cache():
    """Reset module-level resolved-binary cache around every test.

    ``_resolve_direct_cached`` memoises ``_find_direct()`` for the lifetime
    of the process. Without per-test isolation, the first test's resolved
    binary leaks into subsequent tests and makes patches of
    ``shutil.which``/``_probe_direct_version`` look like they did nothing.
    """
    _reset_direct_cache()
    yield
    _reset_direct_cache()


@pytest.fixture(autouse=True)
def _isolate_explicit_env_var():
    """Default-clear ``YANDEX_DIRECT_CLI_PATH`` for every test.

    A developer machine may set this env var to point at a custom binary;
    that would shadow ``shutil.which`` patches in every test that doesn't
    explicitly override it. Tests that want to exercise the env-var
    branch can re-set it via their own ``patch.dict``.
    """
    with patch.dict(os.environ, {"YANDEX_DIRECT_CLI_PATH": ""}, clear=False):
        yield


@pytest.mark.mocks
class TestIsAvailable:
    @pytest.fixture(autouse=True)
    def _accept_all_versions(self):
        # Otherwise a real `/usr/bin/direct` below the runtime floor would
        # cause `is_available()` to fail-closed and break test_available.
        with patch(
            "server.cli.runner._probe_direct_version",
            return_value=_KNOWN_GOOD_VERSION,
        ):
            yield

    def test_available(self, runner, tmp_path):
        with (
            patch.dict(
                os.environ,
                {"HOME": str(tmp_path), "CLAUDE_PLUGIN_DATA": ""},
                clear=False,
            ),
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
        ):
            assert runner.is_available() is True

    def test_not_available(self, runner, tmp_path):
        # Isolate HOME / CLAUDE_PLUGIN_DATA so a real `~/.local/bin/direct`
        # on a developer machine doesn't satisfy the fallback search step.
        with (
            patch.dict(
                os.environ,
                {"HOME": str(tmp_path), "CLAUDE_PLUGIN_DATA": ""},
                clear=False,
            ),
            patch("server.cli.runner.shutil.which", return_value=None),
        ):
            assert runner.is_available() is False


@pytest.mark.mocks
class TestFindDirect:
    """Treat every probed binary as known-good so legacy candidates resolve
    normally; the explicit min-version regression cases live in
    TestFindDirectVersionFloor."""

    @pytest.fixture(autouse=True)
    def _accept_all_versions(self):
        with patch(
            "server.cli.runner._probe_direct_version",
            return_value=_KNOWN_GOOD_VERSION,
        ):
            yield

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
            patch.dict(
                os.environ,
                {"HOME": str(tmp_path), "CLAUDE_PLUGIN_DATA": ""},
                clear=False,
            ),
            patch("server.cli.runner.shutil.which", return_value=None),
        ):
            assert _find_direct() == str(local_bin)

    def test_not_found(self, tmp_path):
        with (
            patch.dict(
                os.environ,
                {"HOME": str(tmp_path), "CLAUDE_PLUGIN_DATA": ""},
                clear=False,
            ),
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
class TestFindDirectVersionFloor:
    """Regression for the PATH-skew adversarial finding on PR #122.

    A stale `direct` on $PATH must not shadow a fresh ``~/.local/bin/direct``.
    """

    def test_stale_path_falls_through_to_user_local_bin(self, tmp_path):
        local_bin = tmp_path / ".local" / "bin" / "direct"
        local_bin.parent.mkdir(parents=True)
        local_bin.touch()

        def fake_probe(executable: str) -> tuple[int, int, int] | None:
            if executable == "/usr/bin/direct":
                return _KNOWN_STALE_VERSION  # stale CLI on PATH
            if executable == str(local_bin):
                return _KNOWN_GOOD_VERSION  # freshly installed by setup.sh
            return None

        with (
            patch.dict(
                os.environ,
                {"HOME": str(tmp_path), "CLAUDE_PLUGIN_DATA": ""},
                clear=False,
            ),
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
            patch("server.cli.runner._probe_direct_version", side_effect=fake_probe),
        ):
            assert _find_direct() == str(local_bin)

    def test_explicit_env_var_known_good_wins(self, tmp_path):
        """``YANDEX_DIRECT_CLI_PATH`` outranks PATH / venv / local_bin when good."""
        direct_bin = tmp_path / "direct"
        direct_bin.touch()
        local_bin = tmp_path / ".local" / "bin" / "direct"
        local_bin.parent.mkdir(parents=True)
        local_bin.touch()

        def fake_probe(executable: str) -> tuple[int, int, int] | None:
            return _KNOWN_GOOD_VERSION  # everyone is known-good

        with (
            patch.dict(
                os.environ,
                {
                    "HOME": str(tmp_path),
                    "CLAUDE_PLUGIN_DATA": "",
                    "YANDEX_DIRECT_CLI_PATH": str(direct_bin),
                },
                clear=False,
            ),
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
            patch("server.cli.runner._probe_direct_version", side_effect=fake_probe),
        ):
            assert _find_direct() == str(direct_bin)

    def test_explicit_env_var_stale_returns_none(self, tmp_path):
        """A stale explicit path must not shadow good fallbacks — fail fast.

        Adversarial-review-round-3 finding 1: if a user pins
        ``YANDEX_DIRECT_CLI_PATH`` at an older binary, the plugin used to
        run against an incompatible CLI silently. The new policy: if the
        explicit path is provably below the floor, return ``None`` so the
        plugin surfaces a clear "not found" error.
        """
        direct_bin = tmp_path / "direct"
        direct_bin.touch()
        local_bin = tmp_path / ".local" / "bin" / "direct"
        local_bin.parent.mkdir(parents=True)
        local_bin.touch()

        def fake_probe(executable: str) -> tuple[int, int, int] | None:
            if executable == str(direct_bin):
                return _KNOWN_STALE_VERSION  # stale explicit override
            if executable == str(local_bin):
                return _KNOWN_GOOD_VERSION  # fresh user-local install
            return None

        with (
            patch.dict(
                os.environ,
                {
                    "HOME": str(tmp_path),
                    "CLAUDE_PLUGIN_DATA": "",
                    "YANDEX_DIRECT_CLI_PATH": str(direct_bin),
                },
                clear=False,
            ),
            patch("server.cli.runner.shutil.which", return_value=None),
            patch("server.cli.runner._probe_direct_version", side_effect=fake_probe),
        ):
            # Explicit stale must NOT silently fall through to local_bin.
            assert _find_direct() is None

    def test_explicit_env_var_unknown_defers_to_known_good_fallback(self, tmp_path):
        """A broken explicit override (probe → None) is deferred, not chosen."""
        direct_bin = tmp_path / "direct"
        direct_bin.touch()
        local_bin = tmp_path / ".local" / "bin" / "direct"
        local_bin.parent.mkdir(parents=True)
        local_bin.touch()

        def fake_probe(executable: str) -> tuple[int, int, int] | None:
            if executable == str(direct_bin):
                return None  # broken wrapper (e.g. ModuleNotFoundError)
            if executable == str(local_bin):
                return _KNOWN_GOOD_VERSION
            return None

        with (
            patch.dict(
                os.environ,
                {
                    "HOME": str(tmp_path),
                    "CLAUDE_PLUGIN_DATA": "",
                    "YANDEX_DIRECT_CLI_PATH": str(direct_bin),
                },
                clear=False,
            ),
            patch("server.cli.runner.shutil.which", return_value=None),
            patch("server.cli.runner._probe_direct_version", side_effect=fake_probe),
        ):
            assert _find_direct() == str(local_bin)

    def test_unprobable_binary_is_accepted_fail_open(self, tmp_path):
        """If --version cannot run AND no other candidate exists, accept it."""
        local_bin = tmp_path / ".local" / "bin" / "direct"
        local_bin.parent.mkdir(parents=True)
        local_bin.touch()
        with (
            patch.dict(
                os.environ,
                {"HOME": str(tmp_path), "CLAUDE_PLUGIN_DATA": ""},
                clear=False,
            ),
            patch("server.cli.runner.shutil.which", return_value=None),
            patch("server.cli.runner._probe_direct_version", return_value=None),
        ):
            assert _find_direct() == str(local_bin)

    def test_broken_path_falls_through_to_known_good_user_local_bin(self, tmp_path):
        """Regression for PR #122 adversarial round 2.

        A broken PATH `direct` (probe returns None — e.g. wrapper that
        exits with ModuleNotFoundError, or an old CLI without --version)
        must not shadow a freshly installed ``~/.local/bin/direct`` whose
        version satisfies the floor.
        """
        local_bin = tmp_path / ".local" / "bin" / "direct"
        local_bin.parent.mkdir(parents=True)
        local_bin.touch()

        def fake_probe(executable: str) -> tuple[int, int, int] | None:
            if executable == "/usr/bin/direct":
                return None  # broken PATH binary (e.g. ModuleNotFoundError)
            if executable == str(local_bin):
                return _KNOWN_GOOD_VERSION
            return None

        with (
            patch.dict(
                os.environ,
                {"HOME": str(tmp_path), "CLAUDE_PLUGIN_DATA": ""},
                clear=False,
            ),
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
            patch("server.cli.runner._probe_direct_version", side_effect=fake_probe),
        ):
            assert _find_direct() == str(local_bin)

    def test_broken_path_is_last_resort_when_no_known_good_exists(self, tmp_path):
        """If every candidate is unknown, fall back to the first one in order."""

        def fake_probe(executable: str) -> tuple[int, int, int] | None:
            return None  # everything broken

        with (
            patch.dict(
                os.environ,
                {"HOME": str(tmp_path), "CLAUDE_PLUGIN_DATA": ""},
                clear=False,
            ),
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
            patch("server.cli.runner._probe_direct_version", side_effect=fake_probe),
        ):
            assert _find_direct() == "/usr/bin/direct"

    def test_only_stale_candidates_returns_none(self, tmp_path):
        """If every candidate is provably below the floor, return None."""
        local_bin = tmp_path / ".local" / "bin" / "direct"
        local_bin.parent.mkdir(parents=True)
        local_bin.touch()
        with (
            patch.dict(
                os.environ,
                {"HOME": str(tmp_path), "CLAUDE_PLUGIN_DATA": ""},
                clear=False,
            ),
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
            patch(
                "server.cli.runner._probe_direct_version",
                return_value=_KNOWN_STALE_VERSION,
            ),
        ):
            assert _find_direct() is None

    def test_broken_path_with_stale_local_bin_returns_broken_path(self, tmp_path):
        """Broken trumps stale: unknown is preferred over known-stale."""
        local_bin = tmp_path / ".local" / "bin" / "direct"
        local_bin.parent.mkdir(parents=True)
        local_bin.touch()

        def fake_probe(executable: str) -> tuple[int, int, int] | None:
            if executable == "/usr/bin/direct":
                return None  # broken
            if executable == str(local_bin):
                return _KNOWN_STALE_VERSION  # known-stale
            return None

        with (
            patch.dict(
                os.environ,
                {"HOME": str(tmp_path), "CLAUDE_PLUGIN_DATA": ""},
                clear=False,
            ),
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
            patch("server.cli.runner._probe_direct_version", side_effect=fake_probe),
        ):
            assert _find_direct() == "/usr/bin/direct"


@pytest.mark.mocks
class TestResolvedDirectCaching:
    """Module-level cache so per-request ``DirectCliRunner`` instances share it.

    Adversarial-review-round-3 finding 2: ``get_runner()`` creates a fresh
    ``DirectCliRunner`` on every MCP tool call, so an instance-level cache
    misses every time and the ~3s × N-candidate version probe is re-run.
    """

    def test_resolve_caches_across_runner_instances(self):
        from server.cli.runner import _resolve_direct_cached

        with patch(
            "server.cli.runner._find_direct", return_value="/usr/bin/direct"
        ) as mock_find:
            assert _resolve_direct_cached() == "/usr/bin/direct"
            # New runner instance — cache must still hit.
            DirectCliRunner()
            assert _resolve_direct_cached() == "/usr/bin/direct"
            assert _resolve_direct_cached() == "/usr/bin/direct"
            assert mock_find.call_count == 1

    def test_resolve_caches_none_result(self):
        """Cache must distinguish 'not yet resolved' from 'resolved to None'."""
        from server.cli.runner import _resolve_direct_cached

        with patch("server.cli.runner._find_direct", return_value=None) as mock_find:
            assert _resolve_direct_cached() is None
            assert _resolve_direct_cached() is None
            assert mock_find.call_count == 1

    def test_run_uses_module_level_cache_across_runners(self):
        """Two ``run()`` calls — possibly through different runner instances —
        share one resolution."""
        mock_result = MagicMock()
        mock_result.stdout = "{}"
        mock_result.stderr = ""
        mock_result.returncode = 0
        with (
            patch(
                "server.cli.runner._find_direct", return_value="/usr/bin/direct"
            ) as mock_find,
            patch("server.cli.runner.subprocess.run", return_value=mock_result),
        ):
            DirectCliRunner().run(["campaigns", "get"])
            DirectCliRunner().run(["ads", "get"])
            assert mock_find.call_count == 1


@pytest.mark.mocks
class TestProbeDirectVersion:
    """Adversarial-review-round-3 finding 3: regex must be anchored.

    Without anchoring, a wrapper banner like ``Python 3.12.0`` is picked
    up before the actual ``direct, version 0.3.4`` line, promoting a
    stale install to known-good.
    """

    def test_anchored_to_version_keyword(self):
        mock_result = MagicMock()
        mock_result.stdout = "Python 3.12.0\ndirect, version 0.3.4\n"
        mock_result.stderr = ""
        mock_result.returncode = 0
        with patch("server.cli.runner.subprocess.run", return_value=mock_result):
            assert _probe_direct_version("/usr/bin/direct") == (0, 3, 4)

    def test_no_version_keyword_returns_none(self):
        """Wrapper banner without the literal word ``version`` → unknown."""
        mock_result = MagicMock()
        mock_result.stdout = "Python 3.12.0\nsomething 1.2.3\n"
        mock_result.stderr = ""
        mock_result.returncode = 0
        with patch("server.cli.runner.subprocess.run", return_value=mock_result):
            assert _probe_direct_version("/usr/bin/direct") is None

    def test_click_version_option_format_parses(self):
        """Real ``click.version_option`` output: ``direct, version X.Y.Z``."""
        mock_result = MagicMock()
        mock_result.stdout = "direct, version 0.3.10\n"
        mock_result.stderr = ""
        mock_result.returncode = 0
        with patch("server.cli.runner.subprocess.run", return_value=mock_result):
            assert _probe_direct_version("/usr/bin/direct") == (0, 3, 10)

    def test_nonzero_returncode_is_unknown(self):
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "ModuleNotFoundError: direct_cli"
        mock_result.returncode = 1
        with patch("server.cli.runner.subprocess.run", return_value=mock_result):
            assert _probe_direct_version("/usr/bin/direct") is None

    def test_anchored_to_direct_program_name(self):
        """Adversarial-review-round-4 finding 2 regression.

        ``Python version 3.12.0`` ahead of ``direct, version 0.3.4`` used to
        promote (3, 12, 0) — the regex now requires the program name
        ``direct`` (or its package alias ``direct-cli``) right before the
        ``version X.Y.Z`` triplet.
        """
        mock_result = MagicMock()
        mock_result.stdout = "Python version 3.12.0\ndirect, version 0.3.4\n"
        mock_result.stderr = ""
        mock_result.returncode = 0
        with patch("server.cli.runner.subprocess.run", return_value=mock_result):
            assert _probe_direct_version("/usr/bin/direct") == (0, 3, 4)

    def test_unrelated_version_banner_without_direct_returns_none(self):
        """A banner like ``Python version 3.12.0`` alone must not match."""
        mock_result = MagicMock()
        mock_result.stdout = "Python version 3.12.0\nsome wrapper 9.9.9\n"
        mock_result.stderr = ""
        mock_result.returncode = 0
        with patch("server.cli.runner.subprocess.run", return_value=mock_result):
            assert _probe_direct_version("/usr/bin/direct") is None

    def test_direct_cli_alias_in_version_output_is_parsed(self):
        """Some wrappers may print ``direct-cli version X.Y.Z`` — accept that too."""
        mock_result = MagicMock()
        mock_result.stdout = "direct-cli version 0.3.10\n"
        mock_result.stderr = ""
        mock_result.returncode = 0
        with patch("server.cli.runner.subprocess.run", return_value=mock_result):
            assert _probe_direct_version("/usr/bin/direct") == (0, 3, 10)


@pytest.mark.mocks
class TestUnverifiedDirectWarning:
    """Adversarial-review-round-4 finding 1: warn-and-use fallback.

    Fail-open is intentional (legitimate fresh installs whose --version
    momentarily fails should still work), but the user must see that
    the floor could not be verified.
    """

    def test_warning_emitted_when_returning_unknown(self, tmp_path, capsys):
        local_bin = tmp_path / ".local" / "bin" / "direct"
        local_bin.parent.mkdir(parents=True)
        local_bin.touch()
        with (
            patch.dict(
                os.environ,
                {"HOME": str(tmp_path), "CLAUDE_PLUGIN_DATA": ""},
                clear=False,
            ),
            patch("server.cli.runner.shutil.which", return_value=None),
            patch("server.cli.runner._probe_direct_version", return_value=None),
        ):
            assert _find_direct() == str(local_bin)
        captured = capsys.readouterr()
        assert "could not be verified" in captured.err
        assert str(local_bin) in captured.err

    def test_no_warning_when_known_good_candidate_exists(self, tmp_path, capsys):
        with (
            patch.dict(
                os.environ,
                {"HOME": str(tmp_path), "CLAUDE_PLUGIN_DATA": ""},
                clear=False,
            ),
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
            patch(
                "server.cli.runner._probe_direct_version",
                return_value=_KNOWN_GOOD_VERSION,
            ),
        ):
            assert _find_direct() == "/usr/bin/direct"
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_no_warning_when_nothing_found(self, tmp_path, capsys):
        with (
            patch.dict(
                os.environ,
                {"HOME": str(tmp_path), "CLAUDE_PLUGIN_DATA": ""},
                clear=False,
            ),
            patch("server.cli.runner.shutil.which", return_value=None),
        ):
            assert _find_direct() is None
        captured = capsys.readouterr()
        assert captured.err == ""


@pytest.mark.mocks
class TestRun:
    @pytest.fixture(autouse=True)
    def _accept_all_versions(self):
        # Skip the `direct --version` probe so each test's subprocess.run
        # mock observes only the command under test.
        with patch(
            "server.cli.runner._probe_direct_version", return_value=_KNOWN_GOOD_VERSION
        ):
            yield

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
            assert "--token" not in cmd
            assert "campaigns" in cmd

    def test_run_can_force_stdin_eof(self, runner):
        mock_result = MagicMock()
        mock_result.stdout = "{}"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with (
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
            patch(
                "server.cli.runner.subprocess.run", return_value=mock_result
            ) as mock_run,
        ):
            runner.run(["auth", "login", "--format", "json"], input="")

        assert mock_run.call_args.kwargs["input"] == ""

    def test_plugin_auth_options_are_not_mapped_to_direct_env(
        self, runner, monkeypatch
    ):
        mock_result = MagicMock()
        mock_result.stdout = "[]"
        mock_result.stderr = ""
        mock_result.returncode = 0
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_token", "plugin-token")
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_login", "plugin-login")
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_client_id", "plugin-client-id")
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_client_secret", "plugin-secret")
        monkeypatch.delenv("YANDEX_DIRECT_TOKEN", raising=False)
        monkeypatch.delenv("YANDEX_DIRECT_LOGIN", raising=False)
        monkeypatch.delenv("YANDEX_DIRECT_CLIENT_ID", raising=False)
        monkeypatch.delenv("YANDEX_DIRECT_CLIENT_SECRET", raising=False)

        with (
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
            patch(
                "server.cli.runner.subprocess.run", return_value=mock_result
            ) as mock_run,
        ):
            runner.run(["campaigns", "get"])

        env = mock_run.call_args.kwargs["env"]
        assert "YANDEX_DIRECT_TOKEN" not in env
        assert "YANDEX_DIRECT_LOGIN" not in env
        assert "YANDEX_DIRECT_CLIENT_ID" not in env
        assert "YANDEX_DIRECT_CLIENT_SECRET" not in env

    def test_cli_not_found(self, runner, tmp_path):
        """Test 17: direct not in PATH."""
        # Isolate HOME / CLAUDE_PLUGIN_DATA so a real `~/.local/bin/direct`
        # on a developer machine doesn't satisfy the fallback search step.
        with (
            patch.dict(
                os.environ,
                {"HOME": str(tmp_path), "CLAUDE_PLUGIN_DATA": ""},
                clear=False,
            ),
            patch("server.cli.runner.shutil.which", return_value=None),
        ):
            with pytest.raises(CliNotFoundError) as exc_info:
                runner.run(["campaigns", "get"])
            assert "Install package direct-cli and run `direct`" in str(exc_info.value)

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

    def test_auth_error_via_error_code_53(self, runner):
        """error_code=53 (Authorization error) triggers CliAuthError so that
        handle_cli_errors retries the call after refreshing the token, even when
        stderr lacks the '401'/'Unauthorized' literal strings."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = (
            "✗ request_id=99, error_code=53, error_string=Authorization error, "
            "error_detail=Invalid OAuth token"
        )
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

    def test_error_code_parsed_through_ansi_escape(self, runner):
        """Stderr with ANSI color codes still yields a parsed error_code on CliError."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = (
            "\x1b[31m✗ request_id=42, error_code=8000, error_string=Invalid request, "
            "error_detail=Field contains an invalid enumeration value\x1b[0m"
        )
        mock_result.returncode = 1

        with (
            patch("server.cli.runner.shutil.which", return_value="/usr/bin/direct"),
            patch("server.cli.runner.subprocess.run", return_value=mock_result),
        ):
            from server.cli.runner import CliError

            with pytest.raises(CliError) as exc_info:
                runner.run_json(["reports", "get"])
            assert exc_info.value.error_code == 8000
            # ANSI escapes stripped from message and stderr, full detail preserved.
            assert "\x1b" not in str(exc_info.value)
            assert "error_detail=Field contains an invalid enumeration value" in str(
                exc_info.value
            )
            assert exc_info.value.stderr is not None
            assert "\x1b" not in exc_info.value.stderr
