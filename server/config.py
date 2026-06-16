"""Tool-surface configuration: group taxonomy + enable/disable resolution (#149).

This module is **pure data + logic**. It maps every public tool to its groups
and resolves whether a tool is enabled under a given :class:`ToolSurfaceConfig`.
It does NOT touch tool registration — wiring this into ``server/main.py`` is a
separate step (issue #190).

Two kinds of groups:

* **service groups** — the ``cli_service`` from :mod:`server.contract`
  (``campaigns``, ``ads``, …) plus ``plugin`` for the auth / ``tool_help``
  utilities.
* **scenario groups** — cross-cutting, product-oriented:

  * *action*: ``read`` | ``mutate`` | ``destructive`` (every tool has exactly one)
  * *area*: ``analytics`` | ``campaign_management`` | ``bidding_budget`` |
    ``assets_creatives`` | ``targeting_audience``

A tool belongs to its service group, its single action group, and (if its
service maps to one) one area group. ``groups_for_tool`` returns that union, so
a user can toggle a tool by service (``campaigns``), by action (``destructive``)
or by product area (``campaign_management``).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from server.contract import PLUGIN_TOOL_NAMES, PUBLIC_CONTRACT

# --- action classification (read / mutate / destructive) --------------------
# Keyed by cli_method. Anything not destructive/mutate is read (get/list/check/
# has_search_volume/deduplicate/get_suggestion/reports_custom/balance_get/…).
_DESTRUCTIVE_METHODS = frozenset(
    {"delete", "archive", "unarchive", "suspend", "resume", "moderate", "delete_report"}
)
_MUTATE_METHODS = frozenset(
    {
        "add",
        "update",
        "set",
        "set_bids",
        "set_auto",
        "create",
        "create_report",
        "add_passport_organization",
        "add_passport_organization_member",
        "update_campaigns",
        "update_banners",
        "enable_shared_account",
    }
)
# Tools whose cli_method does not encode the action (cli_method is None or a
# shared dispatch verb); classify them by name.
_MUTATE_TOOLS = frozenset({"auth_setup", "auth_login"})

# --- product area from service ----------------------------------------------
_SERVICE_AREA: dict[str, str] = {
    # campaign_management
    "campaigns": "campaign_management",
    "adgroups": "campaign_management",
    "ads": "campaign_management",
    "keywords": "campaign_management",
    "v4tags": "campaign_management",
    # bidding_budget
    "bids": "bidding_budget",
    "keywordbids": "bidding_budget",
    "bidmodifiers": "bidding_budget",
    "strategies": "bidding_budget",
    "balance": "bidding_budget",
    "v4account": "bidding_budget",
    # assets_creatives
    "creatives": "assets_creatives",
    "adimages": "assets_creatives",
    "advideos": "assets_creatives",
    "sitelinks": "assets_creatives",
    "vcards": "assets_creatives",
    "adextensions": "assets_creatives",
    "feeds": "assets_creatives",
    "turbopages": "assets_creatives",
    "v4adimage": "assets_creatives",
    # targeting_audience
    "retargeting": "targeting_audience",
    "audiencetargets": "targeting_audience",
    "smartadtargets": "targeting_audience",
    "dynamicads": "targeting_audience",
    "dynamicfeedadtargets": "targeting_audience",
    "negativekeywordsharedsets": "targeting_audience",
    # analytics
    "reports": "analytics",
    "changes": "analytics",
    "dictionaries": "analytics",
    "keywordsresearch": "analytics",
    "leads": "analytics",
    "v4forecast": "analytics",
    "v4wordstat": "analytics",
    "v4goals": "analytics",
    "v4keywords": "analytics",
    "v4events": "analytics",
    # agencyclients / clients / businesses / plugin: account/admin, no area group
}

ACTION_GROUPS = frozenset({"read", "mutate", "destructive"})
AREA_GROUPS = frozenset(set(_SERVICE_AREA.values()))
SCENARIO_GROUPS = ACTION_GROUPS | AREA_GROUPS


def _action_group(name: str, cli_method: str | None) -> str:
    if cli_method in _DESTRUCTIVE_METHODS:
        return "destructive"
    if cli_method == "account_management":
        # AccountManagement is one CLI verb split across action-scoped tools.
        return "read" if name.endswith("get_accounts") else "mutate"
    if cli_method in _MUTATE_METHODS or name in _MUTATE_TOOLS:
        return "mutate"
    return "read"


@lru_cache(maxsize=1)
def _tool_records() -> dict[str, tuple[str | None, str | None]]:
    """name -> (cli_service, cli_method) for every public tool."""
    return {ct.public_name: (ct.cli_service, ct.cli_method) for ct in PUBLIC_CONTRACT}


def tool_names() -> frozenset[str]:
    """All public tool names known to the contract."""
    return frozenset(_tool_records())


@lru_cache(maxsize=None)
def groups_for_tool(name: str) -> frozenset[str]:
    """Service group + action group + area group (if any) for one tool."""
    service, cli_method = _tool_records().get(name, (None, None))
    groups: set[str] = set()
    service_group = service or ("plugin" if name in PLUGIN_TOOL_NAMES else None)
    if service_group:
        groups.add(service_group)
        area = _SERVICE_AREA.get(service_group)
        if area:
            groups.add(area)
    groups.add(_action_group(name, cli_method))
    return frozenset(groups)


@lru_cache(maxsize=1)
def all_groups() -> frozenset[str]:
    """Every valid group name (service + scenario), for config validation."""
    groups: set[str] = set()
    for name in tool_names():
        groups |= groups_for_tool(name)
    return frozenset(groups)


@dataclass(frozen=True)
class ToolSurfaceConfig:
    """Declarative include/exclude rules for the MCP tool surface.

    Resolution precedence (most specific wins, deterministic):

        tool disabled > tool enabled > group disabled > group enabled > default

    ``default_enabled=True`` is the ``full`` surface (deny-list mode);
    ``default_enabled=False`` is allow-list mode (only what's explicitly enabled).
    """

    enabled_groups: frozenset[str] = frozenset()
    disabled_groups: frozenset[str] = frozenset()
    enabled_tools: frozenset[str] = frozenset()
    disabled_tools: frozenset[str] = frozenset()
    default_enabled: bool = True

    def is_enabled(self, name: str) -> bool:
        if name in self.disabled_tools:
            return False
        if name in self.enabled_tools:
            return True
        groups = groups_for_tool(name)
        if groups & self.disabled_groups:
            return False
        if groups & self.enabled_groups:
            return True
        return self.default_enabled

    def enabled_tool_names(self) -> frozenset[str]:
        return frozenset(name for name in tool_names() if self.is_enabled(name))

    def unknown_groups(self) -> frozenset[str]:
        """Configured group names that match no real group (typo guard)."""
        configured = self.enabled_groups | self.disabled_groups
        return frozenset(configured - all_groups())
