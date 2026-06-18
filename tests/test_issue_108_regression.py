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
    """Issue #108: setup.sh must install a supported direct-cli.

    Adapted for #223: the install command now uses ``direct-cli==${DIRECT_CLI_VERSION}``
    sourced from ``scripts/runtime-pins.env`` instead of a hand-typed
    ``direct-cli>=0.4.3``. Any old version range left over from a stale edit
    fails here.
    """
    setup = (REPO_ROOT / "hooks" / "setup.sh").read_text()
    assert "direct-cli==${DIRECT_CLI_VERSION}" in setup
    # No stale floor ranges anywhere.
    for stale in (
        "direct-cli>=0.4.3",
        "direct-cli>=0.4.2",
        "direct-cli>=0.4.1",
        "direct-cli>=0.3.11",
        "direct-cli>=0.3.10",
        "direct-cli>=0.3.4",
    ):
        assert stale not in setup, f"stale floor {stale!r} still in setup.sh"
    # #223: the version-probe helper was removed; the stamp file replaces it.
    for stale_probe in (
        "_has_direct_cli_0403",
        "_has_direct_cli_0402",
        "_has_direct_cli_0311",
        "_has_direct_cli_0310",
    ):
        assert stale_probe not in setup, (
            f"version-probe helper {stale_probe!r} should have been removed in #223"
        )


def test_claude_notes_use_supported_direct_cli_version() -> None:
    """Issue #108: CLAUDE.md must reflect the supported direct-cli version.

    Adapted for #223: the canonical mention now reads "Runtime pin:
    direct-cli==X.Y.Z" instead of "Minimum required: direct-cli>=X.Y.Z".
    Historical 0.4.x alignment sections from older breaking-changes notes
    are not the canonical mention and stay as history.
    """
    notes = (REPO_ROOT / "CLAUDE.md").read_text()
    assert "Runtime pin: `direct-cli==0.4.3`" in notes
    # Catch the old canonical mention if it ever returns.
    assert "Minimum required: `direct-cli>=" not in notes


def test_v4account_runtime_does_not_accept_finance_or_master_tokens() -> None:
    """Issue #120 security policy: finance/master tokens must stay env-only.

    The v4account tool module must never reintroduce ``--finance-token`` /
    ``--master-token`` / ``--finance-login`` literals in argv construction
    or accept the corresponding parameter names. ``direct-cli`` 0.3.11
    reads them from ``YANDEX_DIRECT_FINANCE_TOKEN`` /
    ``YANDEX_DIRECT_MASTER_TOKEN`` / ``YANDEX_DIRECT_FINANCE_LOGIN``
    instead, which keeps the secrets out of MCP argv, logs, and Claude
    context.
    """
    source = (REPO_ROOT / "server" / "tools" / "v4account.py").read_text()
    for forbidden_flag in (
        '"--finance-token"',
        '"--master-token"',
        '"--finance-login"',
    ):
        assert forbidden_flag not in source, forbidden_flag
        single_quoted = forbidden_flag.replace('"', "'")
        assert single_quoted not in source, single_quoted
    for forbidden_param in ("finance_token", "master_token", "finance_login"):
        # Allow the strings inside docstrings that explain the env-only policy
        # (``YANDEX_DIRECT_FINANCE_TOKEN`` etc.), but the bare snake_case
        # parameter names must not appear as parameters.
        assert f"{forbidden_param}:" not in source, forbidden_param
        assert f"{forbidden_param}=" not in source, forbidden_param


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
        "PayCampaignsByCard",
        "CheckPayment",
        "CreateInvoice",
    ):
        assert "financial operations require manual review" in blocked[method].reason

    for method in ("PingAPI", "PingAPI_X", "GetVersion", "GetAvailableVersions"):
        assert "typed subcommand" in blocked[method].reason
        assert "0.3.8" not in blocked[method].reason
