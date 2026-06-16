"""Tests for the tool-surface group taxonomy and config resolution (#149)."""

from server.config import (
    ACTION_GROUPS,
    AREA_GROUPS,
    SCENARIO_GROUPS,
    ToolSurfaceConfig,
    all_groups,
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
    assert groups_for_tool("campaigns_delete") == frozenset(
        {"campaigns", "campaign_management", "destructive"}
    )
    assert groups_for_tool("reports_get") == frozenset({"reports", "analytics", "read"})
    assert groups_for_tool("v4account_deposit") == frozenset(
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
    assert "ads_archive" not in enabled
    assert "campaigns_get" in enabled  # read tool stays


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
