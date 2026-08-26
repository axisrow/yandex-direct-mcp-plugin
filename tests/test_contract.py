"""Contract metadata for the optional browser-command surface (#292)."""

from server.contract import (
    BROWSER_SERVICE_METHODS,
    BROWSER_TOOL_NAMES,
    DEFAULT_TOOL_NAMES,
    DIRECT_API_TOOL_NAMES,
    OPTIONAL_TOOL_NAMES,
    PUBLIC_CONTRACT,
    PUBLIC_TOOL_NAMES,
)

EXPECTED_BROWSER_TOOL_NAMES = frozenset(
    {
        "masters_list",
        "masters_get",
        "masters_add",
        "masters_update",
        "masters_launch",
        "masters_suspend",
        "masters_resume",
        "masters_archive",
        "masters_copy",
        "masters_delete",
        "masters_login",
        "masters_logout",
        "masters_adimages_get",
        "masters_adimages_add",
        "masters_adimages_set",
        "masters_adimages_delete",
        "masters_targetactions_get",
        "masters_counters_get",
        "masters_audience_get",
        "history_get",
        "playwright_login",
        "playwright_doctor",
        "trackingparams_get",
    }
)


def _contract_by_name():
    return {tool.public_name: tool for tool in PUBLIC_CONTRACT}


def test_browser_contract_declares_all_23_commands_and_bundles() -> None:
    assert BROWSER_TOOL_NAMES == EXPECTED_BROWSER_TOOL_NAMES
    assert sum(len(methods) for methods in BROWSER_SERVICE_METHODS.values()) == 23

    by_name = _contract_by_name()
    assert {by_name[name].optional_bundle for name in BROWSER_TOOL_NAMES} == {
        "browser",
        "trackingparams",
    }
    assert by_name["trackingparams_get"].optional_bundle == "trackingparams"
    assert all(
        by_name[name].optional_bundle == "browser"
        for name in BROWSER_TOOL_NAMES - {"trackingparams_get"}
    )


def test_browser_tools_have_distinct_authority_and_classification() -> None:
    by_name = _contract_by_name()
    assert all(by_name[name].authority == "browser" for name in BROWSER_TOOL_NAMES)
    assert all(by_name[name].classification == "browser" for name in BROWSER_TOOL_NAMES)
    assert BROWSER_TOOL_NAMES.isdisjoint(DIRECT_API_TOOL_NAMES)


def test_optional_and_default_name_sets_partition_public_contract() -> None:
    assert OPTIONAL_TOOL_NAMES == BROWSER_TOOL_NAMES
    assert DEFAULT_TOOL_NAMES == PUBLIC_TOOL_NAMES - OPTIONAL_TOOL_NAMES
    assert DEFAULT_TOOL_NAMES.isdisjoint(OPTIONAL_TOOL_NAMES)
    assert DEFAULT_TOOL_NAMES | OPTIONAL_TOOL_NAMES == PUBLIC_TOOL_NAMES

    # The current main-branch default surface contains 149 tools. Issue #292's
    # original 146 estimate predated three already-merged default tools; browser
    # declarations must not make existing tools optional just to preserve it.
    assert len(DEFAULT_TOOL_NAMES) == 149


def test_nested_browser_commands_override_flat_kebab_case_path() -> None:
    by_name = _contract_by_name()
    adimages_get = by_name["masters_adimages_get"]

    # The legacy scalar property still demonstrates the trap: flattening the
    # MCP method would invent a command that does not exist in direct-cli.
    assert adimages_get.cli_subcommand == "adimages-get"
    assert adimages_get.cli_subcommand_path == ("masters", "adimages", "get")

    expected_nested_paths = {
        "masters_adimages_add": ("masters", "adimages", "add"),
        "masters_adimages_set": ("masters", "adimages", "set"),
        "masters_adimages_delete": ("masters", "adimages", "delete"),
        "masters_targetactions_get": ("masters", "targetactions", "get"),
        "masters_counters_get": ("masters", "counters", "get"),
        "masters_audience_get": ("masters", "audience", "get"),
        "trackingparams_get": ("trackingparams",),
    }
    for name, path in expected_nested_paths.items():
        assert by_name[name].cli_subcommand_path == path
