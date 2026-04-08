from pathlib import Path
from unittest.mock import patch

import pytest

from tests.cli_recorder import CassetteNotFoundError, CliRecorder

RECORDINGS_DIR = Path(__file__).parent / "recordings"
LIVE_MARKERS = {"integration", "live_safe", "live_unsafe"}


def _is_live_test(node) -> bool:
    return any(node.get_closest_marker(marker) for marker in LIVE_MARKERS)


def pytest_addoption(parser):
    """Add --record option for cassette recording."""
    parser.addoption(
        "--record", action="store_true", help="Record cassettes from live CLI"
    )
    parser.addoption(
        "--run-live-safe",
        action="store_true",
        help="Run read-only live tests against the real Yandex.Direct API",
    )
    parser.addoption(
        "--run-live-unsafe",
        action="store_true",
        help="Run mutating live tests with mandatory rollback against the real API",
    )


def pytest_collection_modifyitems(config, items):
    """Skip live suites unless explicitly enabled."""
    run_live_safe = config.getoption("--run-live-safe")
    run_live_unsafe = config.getoption("--run-live-unsafe")

    skip_live_safe = pytest.mark.skip(
        reason="live_safe tests require --run-live-safe"
    )
    skip_live_unsafe = pytest.mark.skip(
        reason="live_unsafe tests require --run-live-unsafe"
    )

    for item in items:
        if item.get_closest_marker("live_unsafe") and not run_live_unsafe:
            item.add_marker(skip_live_unsafe)
        elif item.get_closest_marker("live_safe") and not run_live_safe:
            item.add_marker(skip_live_safe)


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch, tmp_path, request):
    """Ensure tests don't affect real environment."""
    if _is_live_test(request.node):
        return
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


def _discover_live_plugin_data_dir() -> Path | None:
    import os

    env_value = os.environ.get("CLAUDE_PLUGIN_DATA")
    if env_value:
        env_dir = Path(env_value).expanduser()
        if (env_dir / "tokens.json").exists():
            return env_dir

    for candidate in (
        Path.home() / ".claude" / "plugins" / "data" / "yandex-direct-inline",
        Path.home() / ".claude" / "plugins" / "data" / "yandex-direct",
    ):
        if (candidate / "tokens.json").exists():
            return candidate

    return None


@pytest.fixture()
def live_plugin_data_dir(monkeypatch, request) -> Path:
    """Resolve a real plugin data directory for live API tests."""
    if not _is_live_test(request.node):
        pytest.skip("live_plugin_data_dir is only for live-marked tests")

    if request.node.get_closest_marker("live_unsafe") and not request.config.getoption(
        "--run-live-unsafe"
    ):
        pytest.skip("live_unsafe tests require --run-live-unsafe")

    if request.node.get_closest_marker("live_safe") and not request.config.getoption(
        "--run-live-safe"
    ):
        pytest.skip("live_safe tests require --run-live-safe")

    plugin_data_dir = _discover_live_plugin_data_dir()
    if plugin_data_dir is None:
        pytest.skip(
            "No live token storage found. Set CLAUDE_PLUGIN_DATA or install the plugin locally."
        )

    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(plugin_data_dir))
    return plugin_data_dir


@pytest.fixture()
def live_oauth_manager(monkeypatch, live_plugin_data_dir):
    """Provide a real OAuth manager bound to live token storage."""
    from server.auth.oauth import OAuthManager
    import server.tools.auth_tools as auth_tools

    manager = OAuthManager()
    monkeypatch.setattr(auth_tools, "_oauth", manager)
    return manager


@pytest.fixture()
def live_token_getter(live_oauth_manager):
    """Configure the global token getter for live MCP tool tests."""
    import server.tools

    server.tools.set_token_getter(live_oauth_manager.get_valid_token)
    return live_oauth_manager
