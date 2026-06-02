"""Public MCP contract metadata aligned to the `direct` CLI surface.

Tool count (derived from the structures below):
- Direct API tools: 139
- CLI helper tools:   3
- Plugin tools:       4
Total:              146
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# ``wsdl``: canonical SOAP/WSDL-backed Direct API operation.
# ``reports-spec``: canonical Reports API operation validated against reports spec.
# ``v4-live``: canonical Yandex Direct v4 Live operation exposed by the direct CLI.
# ``cli-extra``: public CLI helper intentionally outside the 1:1 API surface.
# ``plugin``: plugin-only auth/utility tool, not a Direct API operation.
ToolAuthority = Literal["wsdl", "reports-spec", "v4-live", "cli-extra", "plugin"]

# ``direct_api``: public Direct operation exposed through CLI transport.
# ``cli_helper``: public helper kept separate from the Direct API contract.
# ``plugin``: plugin-only tool unrelated to Direct service parity.
ToolClassification = Literal["direct_api", "cli_helper", "plugin"]

# ``aligned``: MCP name matches tapi/WSDL canonical; CLI transport confirmed.
# ``transport_blocked``: operation exists in WSDL/tapi surface but
#   ``direct`` has no matching subcommand yet; not exposed in MCP.
ToolDrift = Literal["aligned", "transport_blocked"]


@dataclass(frozen=True)
class ContractTool:
    public_name: str
    cli_service: str | None
    # MCP-normalised snake_case method name used to derive the public tool name
    # via ``{cli_service}_{cli_method}``.  This is *not* the raw CLI subcommand
    # string — use the ``cli_subcommand`` property for that (kebab-case).
    # E.g. cli_method="set_auto" → CLI subcommand "set-auto".
    cli_method: str | None
    authority: ToolAuthority
    classification: ToolClassification
    # Explicit tapi-yandex-direct canonical method name when it cannot be
    # derived automatically from cli_method.  None means the auto-derived
    # camelCase form (``tapi_canonical`` property) is correct.
    tapi_name: str | None = field(default=None)
    drift: ToolDrift = field(default="aligned")
    # Set when an MCP tool wraps a single action of a multi-action tapi
    # operation. AccountManagement is currently the only such case: five
    # discrete MCP tools (v4account_get_accounts, v4account_update_account,
    # v4account_deposit, v4account_invoice, v4account_transfer_money) each
    # declare their single ``supported_actions`` entry. ``None`` for the
    # usual 1:1 tool→method case. ``deferred_actions`` is the audit trail
    # for actions tracked by a follow-up issue until the CLI ships their
    # typed surface — currently empty.
    supported_actions: tuple[str, ...] | None = field(default=None)
    deferred_actions: tuple[str, ...] | None = field(default=None)

    @property
    def cli_subcommand(self) -> str | None:
        """Raw direct subcommand in kebab-case.

        Converts the stored snake_case ``cli_method`` to the kebab-case string
        expected by the ``direct`` binary, e.g. ``set_bids`` → ``set-bids``.
        Use this when constructing actual CLI invocations or validating parity
        against the CLI transport layer.
        """
        if self.cli_method is None:
            return None
        return self.cli_method.replace("_", "-")

    @property
    def tapi_canonical(self) -> str | None:
        """tapi-yandex-direct canonical method name (camelCase).

        Returns the explicit ``tapi_name`` when set, including CLI-backed v4
        tools with no subcommand method stored in ``cli_method``. Otherwise
        auto-derives it from ``cli_method`` by converting snake_case to
        camelCase, e.g. ``set_auto`` → ``setAuto``. Returns ``None`` for
        plugin tools with neither ``cli_method`` nor ``tapi_name``.
        """
        if self.cli_method is None and self.tapi_name is not None:
            return self.tapi_name
        if self.cli_method is None:
            return None
        if self.tapi_name is not None:
            return self.tapi_name
        parts = self.cli_method.split("_")
        return parts[0] + "".join(p.capitalize() for p in parts[1:])


@dataclass(frozen=True)
class BlockedV4Method:
    """v4 Live method intentionally not surfaced as an MCP tool.

    Two reasons coexist:
    - direct-cli does not yet expose a typed subcommand for the method.
    - direct-cli exposes the method but the plugin intentionally leaves it
      out of the public MCP surface (financial operations, manual review
      needed, etc.). The ``reason`` field distinguishes the two.
    """

    method: str
    group: str
    expected_cli_group: str | None
    expected_cli_subcommand: str | None
    reason: str = (
        "direct-cli does not expose a typed subcommand for this v4 Live method."
    )


DIRECT_API_SERVICE_METHODS: dict[str, tuple[str, ...]] = {
    "adextensions": ("get", "add", "delete"),
    "adgroups": ("get", "add", "update", "delete"),
    "adimages": ("get", "add", "delete"),
    "ads": (
        "get",
        "add",
        "update",
        "delete",
        "moderate",
        "suspend",
        "resume",
        "archive",
        "unarchive",
    ),
    "advideos": ("get", "add"),
    "agencyclients": (
        "get",
        "add",
        "update",
        "add_passport_organization",
        "add_passport_organization_member",
    ),
    "audiencetargets": ("get", "add", "delete", "suspend", "resume", "set_bids"),
    "bidmodifiers": ("get", "add", "set", "delete"),
    "bids": ("get", "set", "set_auto"),
    "businesses": ("get",),
    "campaigns": (
        "get",
        "update",
        "add",
        "delete",
        "archive",
        "unarchive",
        "suspend",
        "resume",
    ),
    "changes": ("check", "check_campaigns", "check_dictionaries"),
    "clients": ("get", "update"),
    "creatives": ("get", "add"),
    "dictionaries": ("get", "get_geo_regions"),
    "dynamicads": ("get", "add", "delete", "suspend", "resume", "set_bids"),
    "dynamicfeedadtargets": (
        "get",
        "add",
        "delete",
        "suspend",
        "resume",
        "set_bids",
    ),
    "feeds": ("get", "add", "update", "delete"),
    "keywordbids": ("get", "set", "set_auto"),
    "keywords": (
        "get",
        "update",
        "add",
        "delete",
        "suspend",
        "resume",
    ),
    "keywordsresearch": ("has_search_volume", "deduplicate"),
    "leads": ("get",),
    "negativekeywordsharedsets": ("get", "add", "update", "delete"),
    "reports": ("get",),
    "retargeting": ("get", "add", "update", "delete"),
    "sitelinks": ("get", "add", "delete"),
    "smartadtargets": (
        "get",
        "add",
        "update",
        "delete",
        "suspend",
        "resume",
        "set_bids",
    ),
    "strategies": ("get", "add", "update", "archive", "unarchive"),
    "turbopages": ("get",),
    "vcards": ("get", "add", "delete"),
}

CLI_HELPER_SERVICE_METHODS: dict[str, tuple[str, ...]] = {
    "agencyclients": ("delete",),
    "dictionaries": ("list_names",),
    "reports": ("list_types",),
}

# Reports-spec tools that share the same CLI subcommand (`direct reports get`)
# but expose a different MCP-side parameter shape. These cannot live in
# DIRECT_API_SERVICE_METHODS because that mapping auto-derives a kebab-case
# CLI subcommand from the method name (which would yield `reports custom`,
# a command that doesn't exist).
REPORTS_SPEC_EXTRA_TOOLS: tuple[ContractTool, ...] = (
    ContractTool(
        public_name="reports_custom",
        cli_service="reports",
        cli_method=None,
        authority="reports-spec",
        classification="direct_api",
        tapi_name="GetReport",
    ),
)

V4_LIVE_CLI_TOOLS: tuple[ContractTool, ...] = (
    ContractTool(
        public_name="balance_get",
        cli_service="balance",
        cli_method=None,
        authority="v4-live",
        classification="direct_api",
        tapi_name="AccountManagement",
        # balance_get wraps the Logins-selector path of AccountManagement Get
        # via the dedicated ``direct balance`` CLI command (no --account-ids
        # flag). For the full Get surface (logins OR account_ids) use
        # ``v4account_get_accounts``. ``supported_actions`` is left None here
        # because the full Get action is owned by the v4account_* tool family;
        # balance_get is treated as a convenience alias rather than a separate
        # action implementation.
    ),
    ContractTool(
        public_name="v4goals_get_stat_goals",
        cli_service="v4goals",
        cli_method="get_stat_goals",
        authority="v4-live",
        classification="direct_api",
        tapi_name="GetStatGoals",
    ),
    ContractTool(
        public_name="v4goals_get_retargeting_goals",
        cli_service="v4goals",
        cli_method="get_retargeting_goals",
        authority="v4-live",
        classification="direct_api",
        tapi_name="GetRetargetingGoals",
    ),
    ContractTool(
        public_name="v4tags_get_campaigns",
        cli_service="v4tags",
        cli_method="get_campaigns",
        authority="v4-live",
        classification="direct_api",
        tapi_name="GetCampaignsTags",
    ),
    ContractTool(
        public_name="v4tags_get_banners",
        cli_service="v4tags",
        cli_method="get_banners",
        authority="v4-live",
        classification="direct_api",
        tapi_name="GetBannersTags",
    ),
    ContractTool(
        public_name="v4tags_update_campaigns",
        cli_service="v4tags",
        cli_method="update_campaigns",
        authority="v4-live",
        classification="direct_api",
        tapi_name="UpdateCampaignsTags",
    ),
    ContractTool(
        public_name="v4tags_update_banners",
        cli_service="v4tags",
        cli_method="update_banners",
        authority="v4-live",
        classification="direct_api",
        tapi_name="UpdateBannersTags",
    ),
    ContractTool(
        public_name="v4forecast_create",
        cli_service="v4forecast",
        cli_method="create",
        authority="v4-live",
        classification="direct_api",
        tapi_name="CreateNewForecast",
    ),
    ContractTool(
        public_name="v4forecast_list",
        cli_service="v4forecast",
        cli_method="list",
        authority="v4-live",
        classification="direct_api",
        tapi_name="GetForecastList",
    ),
    ContractTool(
        public_name="v4forecast_get",
        cli_service="v4forecast",
        cli_method="get",
        authority="v4-live",
        classification="direct_api",
        tapi_name="GetForecast",
    ),
    ContractTool(
        public_name="v4forecast_delete",
        cli_service="v4forecast",
        cli_method="delete",
        authority="v4-live",
        classification="direct_api",
        tapi_name="DeleteForecastReport",
    ),
    # AccountManagement is a multi-action v4 Live method. direct-cli 0.3.11
    # surfaces it as a single CLI subcommand (``v4account account-management``)
    # switched by ``--action``, but the plugin splits the five actions into
    # discrete MCP tools so that mutating / financial operations get distinct
    # signatures with their own required parameters. ``cli_method`` is the
    # same for all five entries since they share the underlying CLI command.
    ContractTool(
        public_name="v4account_get_accounts",
        cli_service="v4account",
        cli_method="account_management",
        authority="v4-live",
        classification="direct_api",
        tapi_name="AccountManagement",
        supported_actions=("Get",),
    ),
    ContractTool(
        public_name="v4account_update_account",
        cli_service="v4account",
        cli_method="account_management",
        authority="v4-live",
        classification="direct_api",
        tapi_name="AccountManagement",
        supported_actions=("Update",),
    ),
    ContractTool(
        public_name="v4account_deposit",
        cli_service="v4account",
        cli_method="account_management",
        authority="v4-live",
        classification="direct_api",
        tapi_name="AccountManagement",
        supported_actions=("Deposit",),
    ),
    ContractTool(
        public_name="v4account_invoice",
        cli_service="v4account",
        cli_method="account_management",
        authority="v4-live",
        classification="direct_api",
        tapi_name="AccountManagement",
        supported_actions=("Invoice",),
    ),
    ContractTool(
        public_name="v4account_transfer_money",
        cli_service="v4account",
        cli_method="account_management",
        authority="v4-live",
        classification="direct_api",
        tapi_name="AccountManagement",
        supported_actions=("TransferMoney",),
    ),
    ContractTool(
        public_name="v4account_enable_shared_account",
        cli_service="v4account",
        cli_method="enable_shared_account",
        authority="v4-live",
        classification="direct_api",
        tapi_name="EnableSharedAccount",
    ),
    ContractTool(
        public_name="v4events_get_events_log",
        cli_service="v4events",
        cli_method="get_events_log",
        authority="v4-live",
        classification="direct_api",
        tapi_name="GetEventsLog",
    ),
    ContractTool(
        public_name="v4wordstat_create_report",
        cli_service="v4wordstat",
        cli_method="create_report",
        authority="v4-live",
        classification="direct_api",
        tapi_name="CreateNewWordstatReport",
    ),
    ContractTool(
        public_name="v4wordstat_list_reports",
        cli_service="v4wordstat",
        cli_method="list_reports",
        authority="v4-live",
        classification="direct_api",
        tapi_name="GetWordstatReportList",
    ),
    ContractTool(
        public_name="v4wordstat_get_report",
        cli_service="v4wordstat",
        cli_method="get_report",
        authority="v4-live",
        classification="direct_api",
        tapi_name="GetWordstatReport",
    ),
    ContractTool(
        public_name="v4wordstat_delete_report",
        cli_service="v4wordstat",
        cli_method="delete_report",
        authority="v4-live",
        classification="direct_api",
        tapi_name="DeleteWordstatReport",
    ),
    ContractTool(
        public_name="v4keywords_get_suggestion",
        cli_service="v4keywords",
        cli_method="get_suggestion",
        authority="v4-live",
        classification="direct_api",
        tapi_name="GetKeywordsSuggestion",
    ),
    # AdImageAssociation is a multi-action v4 Live method. direct-cli 0.4.1
    # surfaces it as two typed CLI subcommands (``v4adimage get`` for
    # Action=Get, ``v4adimage set`` for Action=Set); the plugin mirrors that
    # split with two discrete MCP tools, each owning its single action.
    ContractTool(
        public_name="v4adimage_get",
        cli_service="v4adimage",
        cli_method="get",
        authority="v4-live",
        classification="direct_api",
        tapi_name="AdImageAssociation",
        supported_actions=("Get",),
    ),
    ContractTool(
        public_name="v4adimage_set",
        cli_service="v4adimage",
        cli_method="set",
        authority="v4-live",
        classification="direct_api",
        tapi_name="AdImageAssociation",
        supported_actions=("Set",),
    ),
)

# Methods either not yet typed by direct-cli OR typed but intentionally not
# surfaced in MCP (e.g. financial operations needing manual review).
_FINANCIAL_REASON = (
    "Exposed by direct-cli 0.3.7+ as a typed command, but intentionally not "
    "surfaced in MCP — financial operations require manual review and master "
    "token issuance through the Direct UI."
)
_PENDING_TYPED_REASON = (
    "Exposed by direct-cli 0.3.7+ as a typed command, but not yet wrapped "
    "as an MCP tool — separate scoping needed before public exposure."
)
_NO_CLI_REASON = (
    "direct-cli does not expose a typed subcommand for this v4 Live method."
)

V4_LIVE_BLOCKED_METHODS: tuple[BlockedV4Method, ...] = (
    BlockedV4Method(
        "GetClientsUnits",
        "finance",
        "v4finance",
        "get-clients-units",
        _FINANCIAL_REASON,
    ),
    BlockedV4Method(
        "GetCreditLimits",
        "finance",
        "v4finance",
        "get-credit-limits",
        _FINANCIAL_REASON,
    ),
    BlockedV4Method(
        "TransferMoney",
        "finance",
        "v4finance",
        "transfer-money",
        _FINANCIAL_REASON,
    ),
    BlockedV4Method(
        "PayCampaigns",
        "finance",
        "v4finance",
        "pay-campaigns",
        _FINANCIAL_REASON,
    ),
    BlockedV4Method(
        "PayCampaignsByCard",
        "finance",
        "v4finance",
        "pay-campaigns-by-card",
        _FINANCIAL_REASON,
    ),
    BlockedV4Method(
        "CheckPayment",
        "finance",
        "v4finance",
        "check-payment",
        _FINANCIAL_REASON,
    ),
    BlockedV4Method(
        "CreateInvoice",
        "finance",
        "v4finance",
        "create-invoice",
        _FINANCIAL_REASON,
    ),
    BlockedV4Method(
        "DeleteOfflineReport",
        "offline_reports",
        None,
        "delete-offline-report",
        _NO_CLI_REASON,
    ),
    BlockedV4Method(
        "DeleteReport",
        "offline_reports",
        None,
        "delete-report",
        _NO_CLI_REASON,
    ),
    BlockedV4Method("PingAPI", "meta", "v4meta", "ping-api", _NO_CLI_REASON),
    BlockedV4Method("PingAPI_X", "meta", "v4meta", "ping-api-x", _NO_CLI_REASON),
    BlockedV4Method("GetVersion", "meta", "v4meta", "get-version", _NO_CLI_REASON),
    BlockedV4Method(
        "GetAvailableVersions",
        "meta",
        "v4meta",
        "get-available-versions",
        _NO_CLI_REASON,
    ),
)

# ``tool_help`` is a meta-tool: it serves the full docstring of any tool on
# demand so the other tools can expose only a short one-line description and
# keep the startup context small (progressive disclosure).
PLUGIN_TOOL_NAMES = ("auth_status", "auth_setup", "auth_login", "tool_help")

# Operations that exist in the WSDL/tapi surface but cannot be exposed
# in MCP because `direct` has no matching transport subcommand.
# When the CLI gap is closed these entries should move into
# DIRECT_API_SERVICE_METHODS.
#
# Format: { "<service>_<method>": "<reason>" }
TRANSPORT_BLOCKED_OPERATIONS: dict[str, str] = {
    "dynamicads_update": (
        "`direct` has no `dynamicads update` subcommand; "
        "the operation is WSDL-backed (DynamicTextAdTargets.update) but "
        "not yet wired in the CLI transport layer."
    ),
    "negativekeywords_*": (
        "`negativekeywords` is not a registered `direct` service. "
        "Per-adgroup negative keywords are part of the AdGroups WSDL payload "
        "(NegativeKeywords field) rather than a standalone service. "
        "The legacy `negative_keywords_*` MCP tools were removed because they "
        "had no valid CLI transport; manage them via the adgroups payload or "
        "via NegativeKeywordSharedSets."
    ),
    "bidmodifiers_toggle": (
        "`direct bidmodifiers toggle` removed in CLI 0.2.8; "
        "Yandex deprecated this API operation on 2025-11-13."
    ),
}

# Mapping of removed legacy public names to their canonical replacements.
# Used for generating migration docs and for asserting no regressions.
# ``None`` as a value means the old name was removed without a 1:1 replacement
# (transport-blocked or absorbed into another service's payload).
RENAMED_TOOL_MIGRATION: dict[str, str | None] = {
    "campaigns_list": "campaigns_get",
    "adgroups_list": "adgroups_get",
    "ads_list": "ads_get",
    "keyword_bids_list": "keywordbids_get",
    "keyword_bids_set": "keywordbids_set",
    "audience_targets_list": "audiencetargets_get",
    "audience_targets_add": "audiencetargets_add",
    "audience_targets_delete": "audiencetargets_delete",
    "audience_targets_suspend": "audiencetargets_suspend",
    "audience_targets_resume": "audiencetargets_resume",
    "agency_clients_list": "agencyclients_get",
    "agency_clients_add": "agencyclients_add",
    "agency_clients_delete": "agencyclients_delete",
    "businesses_list": "businesses_get",
    "changes_checkcamp": "changes_check_campaigns",
    "changes_checkdict": "changes_check_dictionaries",
    "creatives_list": "creatives_get",
    "dynamic_ads_list": "dynamicads_get",
    "dynamic_ads_add": "dynamicads_add",
    "dynamic_ads_update": None,  # transport-blocked; see TRANSPORT_BLOCKED_OPERATIONS
    "dynamic_ads_delete": "dynamicads_delete",
    "dynamic_targets_list": "dynamicads_get",
    "dynamic_targets_add": "dynamicads_add",
    "dynamic_targets_update": None,  # transport-blocked
    "dynamic_targets_delete": "dynamicads_delete",
    "feeds_list": "feeds_get",
    "keywords_has_volume": "keywordsresearch_has_search_volume",
    "keywords_deduplicate": "keywordsresearch_deduplicate",
    "leads_list": "leads_get",
    "negative_keyword_shared_sets_list": "negativekeywordsharedsets_get",
    "negative_keyword_shared_sets_add": "negativekeywordsharedsets_add",
    "negative_keyword_shared_sets_update": "negativekeywordsharedsets_update",
    "negative_keyword_shared_sets_delete": "negativekeywordsharedsets_delete",
    "negative_keywords_list": None,  # transport-blocked; see TRANSPORT_BLOCKED_OPERATIONS
    "negative_keywords_add": None,
    "negative_keywords_update": None,
    "negative_keywords_delete": None,
    "smart_ad_targets_list": "smartadtargets_get",
    "smart_ad_targets_add": "smartadtargets_add",
    "smart_ad_targets_update": "smartadtargets_update",
    "smart_ad_targets_delete": "smartadtargets_delete",
    "smart_targets_list": "smartadtargets_get",
    "smart_targets_add": "smartadtargets_add",
    "smart_targets_update": "smartadtargets_update",
    "smart_targets_delete": "smartadtargets_delete",
    "turbo_pages_list": "turbopages_get",
    "turbo_pages_add": None,  # no add subcommand in CLI
    "vcards_list": "vcards_get",
    "adimages_list": "adimages_get",
    "adextensions_list": "adextensions_get",
    "sitelinks_list": "sitelinks_get",
    "bidmodifiers_toggle": None,  # CLI 0.2.8 removed toggle; see TRANSPORT_BLOCKED_OPERATIONS
    # AccountManagement multi-action split (CLI 0.3.11): the single-action
    # alias kept only the Update half of the surface. Now five distinct
    # tools cover Get / Update / Deposit / Invoice / TransferMoney; the old
    # name maps to the Update replacement so existing keyword-argument
    # callers can switch with a tool-name rename only.
    "v4account_account_management": "v4account_update_account",
}

# Public tools whose parameter shape changed in a backwards-incompatible way.
# The replacement string describes the new signature so callers can migrate.
PARAMETER_BREAKING_CHANGES: dict[str, str] = {
    "bidmodifiers_set": (
        "Signature changed in CLI 0.3.8 alignment: now (id: int, value: int, "
        "dry_run: bool = False). Removed campaign_id, modifier_type, and "
        "free-form JSON updates; direct-cli exposes only typed flags for this "
        "operation. Use the Id returned by `bidmodifiers_add` to update an "
        "existing modifier."
    ),
    "v4account_account_management": (
        "Renamed to v4account_update_account in CLI 0.3.11 alignment. The "
        "AccountManagement method was split into five tools "
        "(v4account_get_accounts / v4account_update_account / "
        "v4account_deposit / v4account_invoice / v4account_transfer_money) "
        "so that financial actions get isolated signatures and finance / "
        "master tokens stay env-only (YANDEX_DIRECT_FINANCE_TOKEN, "
        "YANDEX_DIRECT_MASTER_TOKEN). The old name is mapped in "
        "RENAMED_TOOL_MIGRATION."
    ),
}

REMOVED_LEGACY_PUBLIC_NAMES = frozenset(RENAMED_TOOL_MIGRATION.keys())

# Changes timestamps follow the Yandex Direct API wire format and must include
# an explicit timezone. The plugin rejects bare local datetimes before invoking
# ``direct`` so callers cannot accidentally depend on server-local fallback.
EXPLICIT_TIMEZONE_TIMESTAMP_TOOLS = frozenset(
    {"changes_check", "changes_check_campaigns"}
)


def _tool_name(service: str, method: str) -> str:
    return f"{service}_{method}"


PUBLIC_CONTRACT: tuple[ContractTool, ...] = tuple(
    [
        *(
            ContractTool(
                public_name=_tool_name(service, method),
                cli_service=service,
                cli_method=method,
                authority="reports-spec" if service == "reports" else "wsdl",
                classification="direct_api",
            )
            for service, methods in DIRECT_API_SERVICE_METHODS.items()
            for method in methods
        ),
        *(
            ContractTool(
                public_name=_tool_name(service, method),
                cli_service=service,
                cli_method=method,
                authority="cli-extra",
                classification="cli_helper",
            )
            for service, methods in CLI_HELPER_SERVICE_METHODS.items()
            for method in methods
        ),
        *REPORTS_SPEC_EXTRA_TOOLS,
        *V4_LIVE_CLI_TOOLS,
        *(
            ContractTool(
                public_name=name,
                cli_service=None,
                cli_method=None,
                authority="plugin",
                classification="plugin",
            )
            for name in PLUGIN_TOOL_NAMES
        ),
    ]
)

PUBLIC_TOOL_NAMES = frozenset(tool.public_name for tool in PUBLIC_CONTRACT)
DIRECT_API_TOOL_NAMES = frozenset(
    tool.public_name for tool in PUBLIC_CONTRACT if tool.classification == "direct_api"
)
CLI_HELPER_TOOL_NAMES = frozenset(
    tool.public_name for tool in PUBLIC_CONTRACT if tool.classification == "cli_helper"
)
V4_LIVE_TOOL_NAMES = frozenset(tool.public_name for tool in V4_LIVE_CLI_TOOLS)
V4_LIVE_BLOCKED_METHOD_NAMES = frozenset(
    blocked.method for blocked in V4_LIVE_BLOCKED_METHODS
)


# Action-level audit trail for v4 Live tapi methods whose actions are split
# across multiple MCP tools. ``AccountManagement`` is the canonical example:
# Get / Update / Deposit / Invoice / TransferMoney are owned by individual
# v4account_* tools. Both maps are keyed by the canonical tapi method name so
# WSDL-diff tooling can join cleanly. Per-method, supported ∩ deferred is
# guaranteed empty (asserted in tests/test_v4_tools.py).
def _aggregate_actions(
    field_name: str,
) -> dict[str, frozenset[str]]:
    aggregated: dict[str, set[str]] = {}
    for tool in V4_LIVE_CLI_TOOLS:
        actions = getattr(tool, field_name)
        if actions and tool.tapi_canonical is not None:
            aggregated.setdefault(tool.tapi_canonical, set()).update(actions)
    return {name: frozenset(actions) for name, actions in aggregated.items()}


V4_LIVE_SUPPORTED_ACTIONS: dict[str, frozenset[str]] = _aggregate_actions(
    "supported_actions"
)
V4_LIVE_DEFERRED_ACTIONS: dict[str, frozenset[str]] = _aggregate_actions(
    "deferred_actions"
)
PLUGIN_ONLY_TOOL_NAMES = frozenset(
    tool.public_name for tool in PUBLIC_CONTRACT if tool.classification == "plugin"
)
