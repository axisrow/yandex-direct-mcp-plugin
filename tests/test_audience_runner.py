"""Unit tests for the AudienceCliRunner (`yac` second transport)."""

import subprocess
from unittest.mock import patch

import pytest

from server.cli import audience_runner
from server.cli.audience_runner import (
    AudienceCliError,
    AudienceCliNotFoundError,
    AudienceCliRunner,
)
from tests.helpers import completed

YAC = "/opt/yac/bin/yac"


def _make_yac(path):
    """Patch resolution + subprocess so runner uses a fake yac binary."""
    audience_runner._reset_yac_cache()
    return (
        patch("server.cli.audience_runner._resolve_yac_cached", return_value=path),
        patch("server.cli.audience_runner.subprocess.run"),
    )


@pytest.fixture(autouse=True)
def _reset_cache():
    audience_runner._reset_yac_cache()
    yield
    audience_runner._reset_yac_cache()


def test_run_json_parses_stdout():
    run_patch, subproc_patch = _make_yac(YAC)
    with run_patch, subproc_patch as mock_run:
        mock_run.return_value = completed(stdout='{"segments": []}')
        assert AudienceCliRunner().run_json(["segments", "list"]) == {"segments": []}
    assert mock_run.call_args.args[0] == [YAC, "segments", "list"]


def test_run_json_empty_stdout_is_empty_list():
    run_patch, subproc_patch = _make_yac(YAC)
    with run_patch, subproc_patch as mock_run:
        mock_run.return_value = completed(stdout="")
        assert AudienceCliRunner().run_json(["pixels", "list"]) == []


def test_run_json_scalar_becomes_result_envelope():
    run_patch, subproc_patch = _make_yac(YAC)
    with run_patch, subproc_patch as mock_run:
        mock_run.return_value = completed(stdout="42")
        assert AudienceCliRunner().run_json(["segments", "list"]) == {"result": 42}


def test_nonzero_exit_raises_with_stderr():
    run_patch, subproc_patch = _make_yac(YAC)
    with run_patch, subproc_patch as mock_run:
        mock_run.return_value = completed(
            stderr="Ошибка: OAuth-токен не найден", returncode=1
        )
        with pytest.raises(AudienceCliError) as excinfo:
            AudienceCliRunner().run_json(["segments", "list"])
    assert "OAuth-токен не найден" in str(excinfo.value)


def test_missing_binary_raises_not_found():
    audience_runner._reset_yac_cache()
    with patch("server.cli.audience_runner._find_yac", return_value=None):
        audience_runner._reset_yac_cache()
        with pytest.raises(AudienceCliNotFoundError):
            AudienceCliRunner().run_json(["segments", "list"])
        error = AudienceCliNotFoundError("x")
        # handle_cli_errors maps this to cli_not_found via the CliNotFoundError base.
        from server.cli.runner import CliNotFoundError

        assert isinstance(error, CliNotFoundError)


def test_find_yac_prefers_explicit_env(monkeypatch, tmp_path):
    fake = tmp_path / "yac"
    fake.write_text("")
    monkeypatch.setenv("YANDEX_AUDIENCE_CLI_PATH", str(fake))
    monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
    monkeypatch.setattr(audience_runner.shutil, "which", lambda _: "/other/yac")
    assert audience_runner._find_yac() == str(fake)


def test_find_yac_falls_through_broken_explicit_path(monkeypatch, tmp_path):
    monkeypatch.setenv("YANDEX_AUDIENCE_CLI_PATH", str(tmp_path / "missing"))
    monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
    monkeypatch.setattr(audience_runner.shutil, "which", lambda _: "/other/yac")
    assert audience_runner._find_yac() == "/other/yac"


def test_find_yac_prefers_plugin_venv_over_path(monkeypatch, tmp_path):
    """Both bootstrap channels install the yac floor into the plugin venv;
    that binary must win over a system-PATH yac (mirrors `_candidate_paths`)."""
    monkeypatch.delenv("YANDEX_AUDIENCE_CLI_PATH", raising=False)
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
    venv_yac = tmp_path / "venv" / "bin" / "yac"
    venv_yac.parent.mkdir(parents=True)
    venv_yac.write_text("")
    monkeypatch.setattr(audience_runner.shutil, "which", lambda _: "/other/yac")
    assert audience_runner._find_yac() == str(venv_yac)


def test_find_yac_uses_local_bin_fallback(monkeypatch, tmp_path):
    monkeypatch.delenv("YANDEX_AUDIENCE_CLI_PATH", raising=False)
    monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
    monkeypatch.setattr(audience_runner.shutil, "which", lambda _: None)
    fake = tmp_path / "yac"
    fake.write_text("")
    monkeypatch.setattr(audience_runner.Path, "home", lambda: tmp_path, raising=False)
    (tmp_path / ".local" / "bin").mkdir(parents=True)
    (tmp_path / ".local" / "bin" / "yac").write_text("")
    assert audience_runner._find_yac() == str(tmp_path / ".local" / "bin" / "yac")


def test_find_yac_missing_everywhere(monkeypatch, tmp_path):
    monkeypatch.delenv("YANDEX_AUDIENCE_CLI_PATH", raising=False)
    monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
    monkeypatch.setattr(audience_runner.shutil, "which", lambda _: None)
    monkeypatch.setattr(audience_runner.Path, "home", lambda: tmp_path, raising=False)
    assert audience_runner._find_yac() is None


def test_env_passthrough_and_columns(monkeypatch):
    monkeypatch.setenv("YANDEX_AUDIENCE_TOKEN", "secret-token")
    monkeypatch.delenv("COLUMNS", raising=False)
    env = audience_runner._audience_env()
    assert env["YANDEX_AUDIENCE_TOKEN"] == "secret-token"
    assert env["COLUMNS"] == audience_runner._YAC_COLUMNS


def test_env_respects_existing_columns(monkeypatch):
    monkeypatch.setenv("COLUMNS", "120")
    assert audience_runner._audience_env()["COLUMNS"] == "120"


def test_file_not_found_maps_to_not_found():
    run_patch, subproc_patch = _make_yac(YAC)
    with run_patch, subproc_patch as mock_run:
        mock_run.side_effect = FileNotFoundError()
        with pytest.raises(AudienceCliNotFoundError):
            AudienceCliRunner().run_json(["segments", "list"])


def test_timeout_maps_to_audience_error():
    run_patch, subproc_patch = _make_yac(YAC)
    with run_patch, subproc_patch as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="yac", timeout=5)
        with pytest.raises(AudienceCliError, match="timed out"):
            AudienceCliRunner().run_json(["segments", "list"], timeout=5)
