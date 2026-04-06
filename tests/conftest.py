import pytest


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch, tmp_path):
    """Ensure tests don't affect real environment."""
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
