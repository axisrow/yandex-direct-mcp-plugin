from pathlib import Path
from unittest.mock import patch

import pytest

from tests.cli_recorder import CassetteNotFoundError, CliRecorder

RECORDINGS_DIR = Path(__file__).parent / "recordings"


def pytest_addoption(parser):
    """Add --record option for cassette recording."""
    parser.addoption("--record", action="store_true", help="Record cassettes from live CLI")


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch, tmp_path):
    """Ensure tests don't affect real environment."""
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))


@pytest.fixture()
def cli_recorder(monkeypatch, request):
    """CliRecorder fixture with auto-patch subprocess.run for cassette replay.

    In record mode (--record flag): records real CLI calls as cassettes.
    In replay mode (default): patches subprocess.run to replay saved cassettes.
    """
    recorder = CliRecorder(RECORDINGS_DIR)
    is_recording = request.config.getoption("--record", default=False)

    if is_recording:
        # Record mode: let real subprocess calls through
        yield recorder
    else:
        # Replay mode: patch subprocess.run
        import subprocess

        original_run = subprocess.run

        def _patched_run(args, **kwargs):
            try:
                return recorder.replay(args)
            except CassetteNotFoundError:
                # No cassette found — fall through to real subprocess
                return original_run(args, **kwargs)

        with patch("subprocess.run", side_effect=_patched_run):
            yield recorder
