"""Pytest configuration and fixtures for cassette-based testing."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.cli_recorder import CliRecorder


RECORDINGS_DIR = Path(__file__).parent / "recordings"


@pytest.fixture
def cli_recorder():
    """Provide a CliRecorder instance."""
    return CliRecorder(RECORDINGS_DIR)


@pytest.fixture(autouse=True)
def mock_subprocess_run(cli_recorder):
    """Patch subprocess.run to use cassette replay (unless recording)."""
    if cli_recorder.is_recording():
        yield  # In recording mode, use real subprocess
    else:
        with patch("subprocess.run", side_effect=lambda *a, **kw: cli_recorder.replay(a[0] if a else [])):
            yield


def pytest_addoption(parser):
    """Add --record option to pytest."""
    parser.addoption(
        "--record",
        action="store_true",
        default=False,
        help="Record cassettes from live API",
    )


def pytest_configure(config):
    """Set RECORD env var when --record is used."""
    if config.getoption("record"):
        os.environ["RECORD"] = "true"
