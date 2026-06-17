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

  * *action*: ``read`` | ``mutate`` | ``destructive`` | ``lifecycle`` (every
    tool has exactly one). ``destructive`` is now *only* irreversible removal
    (delete); reversible state changes (suspend/resume/archive/unarchive/
    moderate) are the separate ``lifecycle`` action — so disabling
    ``destructive`` no longer also strips the ability to *undo* a state change
    (#205-A).
  * *area*: ``analytics`` | ``campaign_management`` | ``bidding_budget`` |
    ``assets_creatives`` | ``targeting_audience``
  * *risk*: ``financial`` — an extra deny axis layered *on top of* the action
    group for money-movement tools (``v4account_deposit`` / ``invoice`` /
    ``transfer_money``). It is not an action group: these tools keep their
    ``mutate`` action and additionally carry ``financial`` so a profile can
    deny money movement with one group (#205-B).

A tool belongs to its service group, its single action group, (if its service
maps to one) one area group, and (for money-movement tools) the ``financial``
risk group. ``groups_for_tool`` returns that union, so a user can toggle a tool
by service (``campaigns``), by action (``destructive`` / ``lifecycle``), by
product area (``campaign_management``) or by risk (``financial``).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from functools import lru_cache

from server.contract import PLUGIN_TOOL_NAMES, PUBLIC_CONTRACT

# --- action classification (read / mutate / destructive / lifecycle) --------
# Keyed by cli_method. Anything not destructive/lifecycle/mutate is read (get/
# list/check/has_search_volume/deduplicate/get_suggestion/reports_custom/…).
#
# destructive = irreversible removal only. lifecycle = reversible state changes
# (suspend/resume/archive/unarchive/moderate): disabling "destructive" must not
# also strip the ability to undo a state change (#205-A).
_DESTRUCTIVE_METHODS = frozenset({"delete", "delete_report"})
_LIFECYCLE_METHODS = frozenset(
    {"archive", "unarchive", "suspend", "resume", "moderate"}
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

# --- financial risk axis ----------------------------------------------------
# Money-movement tools. AccountManagement is one CLI verb (cli_method=
# "account_management") split across action-scoped tools, so these cannot be
# selected by a cli_method frozenset — they are pinned by public name. They keep
# their "mutate" action and additionally carry the "financial" risk group, so a
# profile can deny money movement with one group instead of a tool list (#205-B).
# update_account adjusts shared-account settings (day budget / spend mode), not a
# transfer, so it stays mutate-only and is NOT financial.
_FINANCIAL_TOOLS = frozenset(
    {"v4account_deposit", "v4account_invoice", "v4account_transfer_money"}
)

ACTION_GROUPS = frozenset({"read", "mutate", "destructive", "lifecycle"})
RISK_GROUPS = frozenset({"financial"})
AREA_GROUPS = frozenset(set(_SERVICE_AREA.values()))
SCENARIO_GROUPS = ACTION_GROUPS | AREA_GROUPS | RISK_GROUPS


def _action_group(name: str, cli_method: str | None) -> str:
    if cli_method in _DESTRUCTIVE_METHODS:
        return "destructive"
    if cli_method in _LIFECYCLE_METHODS:
        return "lifecycle"
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
    if name in _FINANCIAL_TOOLS:
        groups.add("financial")
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


# --- preset profiles --------------------------------------------------------
# "full" is the default 146-tool surface (backward compatible). The scenario
# profiles are allow-list configs (default_enabled=False). Auth / tool_help are
# always included as tool-level enables so any profile can still authenticate
# and look up docs (tool-level beats group-level, so they survive a disabled
# "mutate" group).
_ALWAYS_ON = frozenset({"auth_status", "auth_setup", "auth_login", "tool_help"})

PROFILES: dict[str, ToolSurfaceConfig] = {
    # Everything — the historical default surface.
    "full": ToolSurfaceConfig(),
    # Minimal read-only campaign diagnostics.
    "core": ToolSurfaceConfig(
        default_enabled=False,
        enabled_groups=frozenset({"campaign_management"}),
        disabled_groups=frozenset({"mutate", "destructive", "lifecycle"}),
        enabled_tools=_ALWAYS_ON,
    ),
    # Reporting / dictionaries / forecasting — no campaign-object mutations.
    "analytics": ToolSurfaceConfig(
        default_enabled=False,
        enabled_groups=frozenset({"analytics"}),
        enabled_tools=_ALWAYS_ON,
    ),
    # Read + mutate the core campaign objects, but not removal (destructive), not
    # reversible state churn (lifecycle), and not money movement (financial).
    "campaign-editor": ToolSurfaceConfig(
        default_enabled=False,
        enabled_groups=frozenset({"campaign_management", "bidding_budget"}),
        disabled_groups=frozenset({"destructive", "lifecycle", "financial"}),
        enabled_tools=_ALWAYS_ON,
    ),
}

# env var names (kept together so docs and code stay in sync)
ENV_PROFILE = "YANDEX_DIRECT_TOOL_PROFILE"
ENV_ENABLED_GROUPS = "YANDEX_DIRECT_ENABLED_GROUPS"
ENV_DISABLED_GROUPS = "YANDEX_DIRECT_DISABLED_GROUPS"
ENV_ENABLED_TOOLS = "YANDEX_DIRECT_ENABLED_TOOLS"
ENV_DISABLED_TOOLS = "YANDEX_DIRECT_DISABLED_TOOLS"


def _split_csv(value: str | None) -> frozenset[str]:
    if not value:
        return frozenset()
    return frozenset(item.strip() for item in value.split(",") if item.strip())


def config_from_env(env: Mapping[str, str]) -> ToolSurfaceConfig:
    """Build a :class:`ToolSurfaceConfig` from environment variables.

    Semantics:

    * ``YANDEX_DIRECT_TOOL_PROFILE`` picks a :data:`PROFILES` base (unknown name
      falls back to ``full``).
    * otherwise, if any ``ENABLED_*`` var is set, the surface is allow-list mode
      (``default_enabled=False`` — only what's explicitly enabled);
    * otherwise it is the ``full`` surface and ``DISABLED_*`` vars subtract.

    ``ENABLED_*`` / ``DISABLED_*`` vars are always merged on top of the base, so
    they refine a profile too.
    """
    profile = (env.get(ENV_PROFILE) or "").strip().lower()
    enabled_groups = _split_csv(env.get(ENV_ENABLED_GROUPS))
    disabled_groups = _split_csv(env.get(ENV_DISABLED_GROUPS))
    enabled_tools = _split_csv(env.get(ENV_ENABLED_TOOLS))
    disabled_tools = _split_csv(env.get(ENV_DISABLED_TOOLS))

    if profile:
        base = PROFILES.get(profile, ToolSurfaceConfig())
    elif enabled_groups or enabled_tools:
        base = ToolSurfaceConfig(default_enabled=False)
    else:
        base = ToolSurfaceConfig(default_enabled=True)

    return replace(
        base,
        enabled_groups=base.enabled_groups | enabled_groups,
        disabled_groups=base.disabled_groups | disabled_groups,
        enabled_tools=base.enabled_tools | enabled_tools,
        disabled_tools=base.disabled_tools | disabled_tools,
    )


def env_config_warnings(env: Mapping[str, str], config: ToolSurfaceConfig) -> list[str]:
    """Human-readable warnings for a parsed env config (unknown profile/groups/tools)."""
    warnings: list[str] = []
    profile = (env.get(ENV_PROFILE) or "").strip().lower()
    if profile and profile not in PROFILES:
        warnings.append(
            f"unknown {ENV_PROFILE}={profile!r}; known: {sorted(PROFILES)}. "
            "Falling back to the full surface."
        )
    unknown_groups = config.unknown_groups()
    if unknown_groups:
        warnings.append(f"unknown tool groups ignored: {sorted(unknown_groups)}")
    known_tools = tool_names()
    unknown_tools = (config.enabled_tools | config.disabled_tools) - known_tools
    if unknown_tools:
        warnings.append(f"unknown tool names ignored: {sorted(unknown_tools)}")
    # Allow-list mode that names nothing valid would disable the whole surface;
    # apply_tool_surface keeps the full surface in that case, so flag the typo.
    if not config.default_enabled and not any(
        config.is_enabled(name) for name in known_tools
    ):
        warnings.append(
            "tool-surface config enables zero tools (likely an allow-list typo); "
            "keeping the full surface instead of an empty server."
        )
    return warnings


def apply_tool_surface(mcp, config: ToolSurfaceConfig) -> list[str]:
    """Remove disabled tools from a FastMCP instance; return removed names.

    Uses the public ``remove_tool``. A ``full`` config removes nothing, so the
    default 146-tool surface is untouched.

    Fail-safe: if the config would remove *every* registered tool — almost
    always a typo in an allow-list env var (e.g. ``YANDEX_DIRECT_ENABLED_GROUPS``
    or ``...ENABLED_TOOLS`` naming nothing that matches) — the removal is
    abandoned and the full surface is kept. An empty MCP server is never a
    useful outcome, so a startup typo must not silently wipe the surface.
    """
    manager = getattr(mcp, "_tool_manager", None)
    registered = list(getattr(manager, "_tools", {}).keys())
    removed = [name for name in registered if not config.is_enabled(name)]
    if registered and len(removed) == len(registered):
        # Would disable everything — treat as misconfiguration, keep full surface.
        return []
    for name in removed:
        mcp.remove_tool(name)
    return removed
