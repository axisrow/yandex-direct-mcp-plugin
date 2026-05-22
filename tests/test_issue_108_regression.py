"""Regression checks for issue #108 CLI 0.3.8+ alignment."""

from pathlib import Path

import server.tools.keywords as keywords_tools
from server.contract import (
    DIRECT_API_SERVICE_METHODS,
    PARAMETER_BREAKING_CHANGES,
    PUBLIC_TOOL_NAMES,
    V4_LIVE_BLOCKED_METHODS,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_keywords_archive_tools_stay_removed() -> None:
    assert "archive" not in DIRECT_API_SERVICE_METHODS["keywords"]
    assert "unarchive" not in DIRECT_API_SERVICE_METHODS["keywords"]
    assert "keywords_archive" not in PUBLIC_TOOL_NAMES
    assert "keywords_unarchive" not in PUBLIC_TOOL_NAMES
    assert not hasattr(keywords_tools, "keywords_archive")
    assert not hasattr(keywords_tools, "keywords_unarchive")


def test_runtime_code_does_not_reintroduce_freeform_json_transport() -> None:
    runtime_paths = [
        *sorted((REPO_ROOT / "server" / "tools").glob("*.py")),
        REPO_ROOT / "server" / "contract.py",
    ]
    for path in runtime_paths:
        source = path.read_text()
        # Guard against argv constructions like ["--json", ...] in either quote
        # style; the bare substring would false-positive on docstrings that
        # explain why CLI 0.3.8 dropped the flag.
        assert '"--json"' not in source, path
        assert "'--json'" not in source, path
        assert "extra_json" not in source, path


def test_setup_hook_installs_supported_direct_cli_version() -> None:
    setup = (REPO_ROOT / "hooks" / "setup.sh").read_text()
    assert "direct-cli>=0.3.10" in setup
    assert "direct-cli>=0.3.4" not in setup
    assert "_has_direct_cli_0310" in setup


def test_breaking_change_notes_describe_typed_bidmodifier_surface() -> None:
    note = PARAMETER_BREAKING_CHANGES["bidmodifiers_set"]
    assert "dry_run" in note
    assert "free-form JSON" in note
    assert "extra_json" not in note


def test_blocked_v4_methods_have_explicit_non_stale_reasons() -> None:
    blocked = {item.method: item for item in V4_LIVE_BLOCKED_METHODS}

    for method in (
        "GetClientsUnits",
        "GetCreditLimits",
        "TransferMoney",
        "PayCampaigns",
        "CheckPayment",
        "CreateInvoice",
    ):
        assert "financial operations require manual review" in blocked[method].reason

    for method in ("PingAPI", "PingAPI_X", "GetVersion", "GetAvailableVersions"):
        assert "typed subcommand" in blocked[method].reason
        assert "0.3.8" not in blocked[method].reason
