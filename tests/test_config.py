"""Tests for the tool-surface group taxonomy and config resolution (#149)."""

from server.config import (
    ACTION_GROUPS,
    AREA_GROUPS,
    PROFILES,
    SCENARIO_GROUPS,
    ToolSurfaceConfig,
    all_groups,
    apply_tool_surface,
    config_from_env,
    env_config_warnings,
    groups_for_tool,
    tool_names,
)
from server.contract import PUBLIC_CONTRACT


def test_tool_names_match_contract():
    assert tool_names() == frozenset(ct.public_name for ct in PUBLIC_CONTRACT)
    assert len(tool_names()) == 146


def test_every_tool_has_exactly_one_action_group():
    for name in tool_names():
        actions = groups_for_tool(name) & ACTION_GROUPS
        assert len(actions) == 1, f"{name} has action groups {actions}"


def test_every_tool_has_at_most_one_area_group():
    for name in tool_names():
        areas = groups_for_tool(name) & AREA_GROUPS
        assert len(areas) <= 1, f"{name} has area groups {areas}"


def test_group_membership_examples():
    # delete is the only irreversible removal → destructive.
    assert groups_for_tool("campaigns_delete") == frozenset(
        {"campaigns", "campaign_management", "destructive"}
    )
    # archive is a reversible state change → lifecycle, not destructive (#205-A).
    assert groups_for_tool("ads_archive") == frozenset(
        {"ads", "campaign_management", "lifecycle"}
    )
    assert groups_for_tool("reports_get") == frozenset({"reports", "analytics", "read"})
    # Money movement keeps its mutate action and additionally carries the
    # financial risk group (#205-B).
    assert groups_for_tool("v4account_deposit") == frozenset(
        {"v4account", "bidding_budget", "mutate", "financial"}
    )
    # update_account adjusts settings (day budget / spend mode), not a transfer,
    # so it stays mutate-only — NOT financial.
    assert groups_for_tool("v4account_update_account") == frozenset(
        {"v4account", "bidding_budget", "mutate"}
    )
    # AccountManagement is one CLI verb split by action: get is read, deposit mutate.
    assert "read" in groups_for_tool("v4account_get_accounts")
    # Plugin utilities get the "plugin" service group, no product area.
    assert groups_for_tool("auth_status") == frozenset({"plugin", "read"})
    assert groups_for_tool("auth_login") == frozenset({"plugin", "mutate"})


def test_all_groups_includes_services_and_scenarios():
    groups = all_groups()
    assert SCENARIO_GROUPS <= groups
    assert "campaigns" in groups and "plugin" in groups


def test_default_config_is_full_surface():
    cfg = ToolSurfaceConfig()
    assert cfg.enabled_tool_names() == tool_names()


def test_disabled_group_removes_its_tools():
    cfg = ToolSurfaceConfig(disabled_groups=frozenset({"destructive"}))
    enabled = cfg.enabled_tool_names()
    assert "campaigns_delete" not in enabled
    assert "ads_archive" in enabled  # archive is lifecycle now, not destructive
    assert "campaigns_get" in enabled  # read tool stays


def test_disabled_lifecycle_group_keeps_destructive_separate():
    # Disabling lifecycle removes state churn but NOT irreversible delete, and
    # vice versa — the two axes are independent (#205-A).
    no_lifecycle = ToolSurfaceConfig(disabled_groups=frozenset({"lifecycle"}))
    enabled = no_lifecycle.enabled_tool_names()
    assert "ads_archive" not in enabled
    assert "ads_unarchive" not in enabled
    assert "campaigns_delete" in enabled  # delete is destructive, not lifecycle


def test_disabled_financial_group_removes_money_movement():
    cfg = ToolSurfaceConfig(disabled_groups=frozenset({"financial"}))
    enabled = cfg.enabled_tool_names()
    assert "v4account_deposit" not in enabled
    assert "v4account_transfer_money" not in enabled
    assert "v4account_update_account" in enabled  # settings, not money movement
    assert "v4account_get_accounts" in enabled  # read stays


def test_allowlist_profile_enables_only_named_groups():
    cfg = ToolSurfaceConfig(
        enabled_groups=frozenset({"analytics"}), default_enabled=False
    )
    enabled = cfg.enabled_tool_names()
    assert "reports_get" in enabled
    assert "changes_check" in enabled
    assert "campaigns_add" not in enabled


def test_tool_level_overrides_group_level():
    # enabled_tools wins over a disabled group...
    cfg = ToolSurfaceConfig(
        disabled_groups=frozenset({"destructive"}),
        enabled_tools=frozenset({"campaigns_delete"}),
    )
    assert cfg.is_enabled("campaigns_delete") is True
    # ...and disabled_tools wins over an enabled group.
    cfg2 = ToolSurfaceConfig(
        enabled_groups=frozenset({"campaigns"}),
        disabled_tools=frozenset({"campaigns_get"}),
        default_enabled=False,
    )
    assert cfg2.is_enabled("campaigns_get") is False
    assert cfg2.is_enabled("campaigns_add") is True


def test_disable_group_beats_enable_group():
    # campaigns_delete is in both the enabled "campaigns" group and the disabled
    # "destructive" group → disable wins.
    cfg = ToolSurfaceConfig(
        enabled_groups=frozenset({"campaigns"}),
        disabled_groups=frozenset({"destructive"}),
        default_enabled=False,
    )
    assert cfg.is_enabled("campaigns_delete") is False
    assert cfg.is_enabled("campaigns_get") is True


def test_unknown_groups_flags_typos():
    cfg = ToolSurfaceConfig(
        enabled_groups=frozenset({"campaigns", "campaignz"}),
        disabled_groups=frozenset({"destructiv"}),
    )
    assert cfg.unknown_groups() == frozenset({"campaignz", "destructiv"})


# --- env config + registration -------------------------------------------


def test_config_from_env_default_is_full():
    cfg = config_from_env({})
    assert cfg.enabled_tool_names() == tool_names()


def test_config_from_env_disabled_groups_subtracts_from_full():
    cfg = config_from_env({"YANDEX_DIRECT_DISABLED_GROUPS": "destructive"})
    enabled = cfg.enabled_tool_names()
    assert "campaigns_delete" not in enabled
    assert "campaigns_get" in enabled


def test_config_from_env_enabled_groups_is_allowlist():
    cfg = config_from_env({"YANDEX_DIRECT_ENABLED_GROUPS": "analytics"})
    enabled = cfg.enabled_tool_names()
    assert "reports_get" in enabled
    assert "campaigns_add" not in enabled


def test_config_from_env_csv_and_tools():
    cfg = config_from_env(
        {"YANDEX_DIRECT_DISABLED_TOOLS": "campaigns_delete, ads_archive"}
    )
    assert cfg.is_enabled("campaigns_delete") is False
    assert cfg.is_enabled("ads_archive") is False
    assert cfg.is_enabled("campaigns_get") is True


def test_config_from_env_known_profile_full():
    assert config_from_env(
        {"YANDEX_DIRECT_TOOL_PROFILE": "full"}
    ).enabled_tool_names() == (tool_names())


def test_env_config_warnings_unknown_profile():
    env = {"YANDEX_DIRECT_TOOL_PROFILE": "nope"}
    cfg = config_from_env(env)
    warnings = env_config_warnings(env, cfg)
    assert any("nope" in w for w in warnings)
    # unknown profile falls back to full
    assert cfg.enabled_tool_names() == tool_names()


def test_env_config_warnings_unknown_group():
    env = {"YANDEX_DIRECT_DISABLED_GROUPS": "destructiv"}
    cfg = config_from_env(env)
    assert any("destructiv" in w for w in env_config_warnings(env, cfg))


class _StubManager:
    def __init__(self, names):
        self._tools = {n: object() for n in names}


class _StubMcp:
    def __init__(self, names):
        self._tool_manager = _StubManager(names)

    def remove_tool(self, name):
        del self._tool_manager._tools[name]


def test_apply_tool_surface_removes_disabled():
    mcp = _StubMcp(["campaigns_get", "campaigns_delete", "ads_archive"])
    # destructive=delete only; lifecycle=archive — disable both to strip them.
    cfg = ToolSurfaceConfig(disabled_groups=frozenset({"destructive", "lifecycle"}))
    removed = apply_tool_surface(mcp, cfg)
    assert set(removed) == {"campaigns_delete", "ads_archive"}
    assert set(mcp._tool_manager._tools) == {"campaigns_get"}


def test_apply_tool_surface_full_removes_nothing():
    mcp = _StubMcp(["campaigns_get", "campaigns_delete"])
    removed = apply_tool_surface(mcp, ToolSurfaceConfig())
    assert removed == []
    assert set(mcp._tool_manager._tools) == {"campaigns_get", "campaigns_delete"}


def test_apply_tool_surface_failsafe_keeps_full_when_all_disabled():
    """An allow-list that matches nothing must NOT wipe the whole surface."""
    mcp = _StubMcp(["campaigns_get", "ads_get"])
    # allow-list mode naming a non-existent group → every tool 'disabled'
    cfg = ToolSurfaceConfig(
        default_enabled=False, enabled_groups=frozenset({"typo_group"})
    )
    removed = apply_tool_surface(mcp, cfg)
    assert removed == []
    assert set(mcp._tool_manager._tools) == {"campaigns_get", "ads_get"}


def test_config_from_env_enabled_groups_typo_warns_and_keeps_full():
    """A typo in YANDEX_DIRECT_ENABLED_GROUPS surfaces a zero-tools warning."""
    cfg = config_from_env({"YANDEX_DIRECT_ENABLED_GROUPS": "analyticz"})
    warnings = env_config_warnings({"YANDEX_DIRECT_ENABLED_GROUPS": "analyticz"}, cfg)
    assert any("zero tools" in w for w in warnings)
    assert any("unknown tool groups" in w for w in warnings)


def test_config_from_env_enabled_tools_typo_warns():
    """A typo in YANDEX_DIRECT_ENABLED_TOOLS is now flagged (previously silent)."""
    env = {"YANDEX_DIRECT_ENABLED_TOOLS": "campaign_delete"}  # missing 's'
    cfg = config_from_env(env)
    warnings = env_config_warnings(env, cfg)
    assert any("unknown tool names" in w for w in warnings)
    assert any("zero tools" in w for w in warnings)


def test_config_from_env_valid_enabled_group_no_zero_warning():
    """A valid allow-list group narrows the surface without the zero-tools warning."""
    env = {"YANDEX_DIRECT_ENABLED_GROUPS": "read"}
    cfg = config_from_env(env)
    warnings = env_config_warnings(env, cfg)
    assert not any("zero tools" in w for w in warnings)
    assert any(cfg.is_enabled(name) for name in tool_names())


# --- preset profiles ------------------------------------------------------


def test_full_profile_is_the_whole_surface():
    assert PROFILES["full"].enabled_tool_names() == tool_names()


def test_every_profile_keeps_auth_and_help():
    for name, cfg in PROFILES.items():
        enabled = cfg.enabled_tool_names()
        assert {"auth_status", "auth_login", "tool_help"} <= enabled, name


def test_core_profile_is_read_only_campaign_basics():
    enabled = PROFILES["core"].enabled_tool_names()
    assert "campaigns_get" in enabled
    assert "ads_get" in enabled
    assert "campaigns_add" not in enabled  # no mutate
    assert "campaigns_delete" not in enabled  # no destructive
    assert "reports_get" not in enabled  # analytics not in core


def test_analytics_profile_has_reporting_not_campaign_mutations():
    enabled = PROFILES["analytics"].enabled_tool_names()
    assert "reports_get" in enabled
    assert "changes_check" in enabled
    assert "campaigns_add" not in enabled


def test_campaign_editor_allows_mutate_not_destructive():
    enabled = PROFILES["campaign-editor"].enabled_tool_names()
    assert "campaigns_add" in enabled
    assert "campaigns_update" in enabled
    assert "campaigns_delete" not in enabled  # destructive excluded
    assert "ads_archive" not in enabled  # lifecycle excluded
    assert "ads_suspend" not in enabled  # lifecycle excluded


def test_scenario_profiles_are_smaller_than_full():
    full = len(tool_names())
    for name in ("core", "analytics", "campaign-editor"):
        assert 0 < len(PROFILES[name].enabled_tool_names()) < full


def test_no_scenario_profile_exposes_money_movement_tools():
    """No scenario profile may expose financial v4account money-movement tools.

    #205-B reclassified deposit/invoice/transfer_money into the denyable
    ``financial`` risk group, so the scenario profiles exclude them via that
    group (no per-tool deny list). update_account is settings, not money
    movement, so it is NOT in this set."""
    financial = {
        "v4account_deposit",
        "v4account_invoice",
        "v4account_transfer_money",
    }
    for name in ("core", "analytics", "campaign-editor"):
        enabled = PROFILES[name].enabled_tool_names()
        leaked = financial & enabled
        assert not leaked, f"profile {name} leaks financial tools: {sorted(leaked)}"


def test_no_scenario_profile_exposes_destructive_deletes():
    """No scenario profile may expose an irreversible delete tool.

    Regression guard for the #205 review finding: analytics used to leak
    v4forecast_delete / v4wordstat_delete_report because both are analytics-area
    destructive tools and the profile had no disabled_groups."""
    destructive = {n for n in tool_names() if "destructive" in groups_for_tool(n)}
    assert destructive  # sanity: the set is non-empty
    for name in ("core", "analytics", "campaign-editor"):
        enabled = PROFILES[name].enabled_tool_names()
        leaked = destructive & enabled
        assert not leaked, f"profile {name} leaks destructive tools: {sorted(leaked)}"
