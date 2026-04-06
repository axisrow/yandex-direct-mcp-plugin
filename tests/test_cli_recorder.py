"""Tests for CliRecorder."""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from tests.cli_recorder import CassetteNotFoundError, CliRecorder


@pytest.fixture
def recordings_dir(tmp_path):
    return tmp_path / "recordings"


@pytest.fixture
def recorder(recordings_dir):
    return CliRecorder(recordings_dir)


class TestRecord:
    def test_record_saves_cassette(self, recorder, recordings_dir):
        """Record mode calls real subprocess and saves cassette."""
        mock_result = MagicMock()
        mock_result.stdout = '[{"Id": 1}]'
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("tests.cli_recorder.subprocess.run", return_value=mock_result):
            cassette = recorder.record(["direct", "--token", "test", "campaigns", "get", "--format", "json"])

        assert cassette["returncode"] == 0
        assert cassette["stdout"] == '[{"Id": 1}]'

        # Verify file was saved
        saved = list(recordings_dir.rglob("*.json"))
        assert len(saved) == 1

    def test_record_organizes_by_subcommand(self, recorder, recordings_dir):
        """Cassettes are saved in subcommand subdirectories."""
        mock_result = MagicMock()
        mock_result.stdout = "[]"
        mock_result.stderr = ""
        mock_result.returncode = 0

        with patch("tests.cli_recorder.subprocess.run", return_value=mock_result):
            recorder.record(["direct", "campaigns", "get"])
            recorder.record(["direct", "ads", "get"])

        assert (recordings_dir / "campaigns").exists()
        assert (recordings_dir / "ads").exists()


class TestReplay:
    def test_replay_finds_matching_cassette(self, recorder, recordings_dir):
        """Replay mode finds cassette by exact args match."""
        cassette = {
            "args": ["campaigns", "get", "--format", "json"],
            "stdout": '[{"Id": 12345}]',
            "stderr": "",
            "returncode": 0,
        }
        subcmd_dir = recordings_dir / "campaigns"
        subcmd_dir.mkdir(parents=True)
        (subcmd_dir / "test.json").write_text(json.dumps(cassette))

        result = recorder.replay(["direct", "campaigns", "get", "--format", "json"])
        assert isinstance(result, subprocess.CompletedProcess)
        assert result.stdout == '[{"Id": 12345}]'

    def test_replay_raises_on_missing_cassette(self, recorder):
        """Replay raises CassetteNotFoundError when no match."""
        with pytest.raises(CassetteNotFoundError):
            recorder.replay(["direct", "unknown", "command"])


class TestIsRecording:
    def test_recording_mode_on(self, recorder):
        with patch.dict("os.environ", {"RECORD": "true"}):
            assert recorder.is_recording() is True

    def test_recording_mode_off(self, recorder):
        with patch.dict("os.environ", {"RECORD": "false"}, clear=True):
            assert recorder.is_recording() is False
