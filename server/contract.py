"""Public MCP contract metadata aligned to the `direct` CLI surface.

Tool count (derived from the structures below):
- Direct API tools: 118
- CLI helper tools:   3
- Plugin tools:       3
Total:              124
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# ``wsdl``: canonical SOAP/WSDL-backed Direct API operation.
# ``reports-spec``: canonical Reports API operation validated against reports spec.
# ``v4-live``: canonical Yandex Direct v4 Live operation exposed by direct-cli.
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

    @property
    def cli_subcommand(self) -> str | None:
        """Raw direct-cli subcommand in kebab-case.

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

        Returns the explicit ``tapi_name`` when set; otherwise auto-derives it
        from ``cli_method`` by converting snake_case to camelCase, e.g.
        ``set_auto`` → ``setAuto``, ``has_search_volume`` → ``hasSearchVolume``.
        Returns ``None`` when there is no CLI method (plugin tools).
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
    """Known v4 Live method that direct-cli does not expose as a command yet."""

    method: str
    group: str
    expected_cli_group: str | None
    expected_cli_subcommand: str | None
    reason: str = (
        "direct 0.3.1 does not expose a typed CLI command for this v4 Live method."
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
        "archive",
        "unarchive",
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

V4_LIVE_CLI_TOOLS: tuple[ContractTool, ...] = (
    ContractTool(
        public_name="balance_get",
        cli_service="balance",
        cli_method=None,
        authority="v4-live",
        classification="direct_api",
        tapi_name="AccountManagement",
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
)

# Methods present in direct_cli.v4_contracts but intentionally not exposed as
# MCP tools until direct-cli publishes typed commands for them.
V4_LIVE_BLOCKED_METHODS: tuple[BlockedV4Method, ...] = (
    BlockedV4Method("GetClientsUnits", "finance", "v4finance", "get-clients-units"),
    BlockedV4Method("GetCreditLimits", "finance", "v4finance", "get-credit-limits"),
    BlockedV4Method("TransferMoney", "finance", "v4finance", "transfer-money"),
    BlockedV4Method("PayCampaigns", "finance", "v4finance", "pay-campaigns"),
    BlockedV4Method(
        "PayCampaignsByCard", "finance", "v4finance", "pay-campaigns-by-card"
    ),
    BlockedV4Method("CheckPayment", "finance", "v4finance", "check-payment"),
    BlockedV4Method("CreateInvoice", "finance", "v4finance", "create-invoice"),
    BlockedV4Method(
        "EnableSharedAccount",
        "shared_account",
        "v4account",
        "enable-shared-account",
    ),
    BlockedV4Method("GetEventsLog", "events", "v4events", "get-events-log"),
    BlockedV4Method(
        "CreateNewWordstatReport",
        "wordstat",
        "v4wordstat",
        "create-new-wordstat-report",
    ),
    BlockedV4Method(
        "GetWordstatReportList",
        "wordstat",
        "v4wordstat",
        "get-wordstat-report-list",
    ),
    BlockedV4Method(
        "GetWordstatReport", "wordstat", "v4wordstat", "get-wordstat-report"
    ),
    BlockedV4Method(
        "DeleteWordstatReport",
        "wordstat",
        "v4wordstat",
        "delete-wordstat-report",
    ),
    BlockedV4Method(
        "CreateNewForecast", "forecast", "v4forecast", "create-new-forecast"
    ),
    BlockedV4Method("GetForecastList", "forecast", "v4forecast", "get-forecast-list"),
    BlockedV4Method("GetForecast", "forecast", "v4forecast", "get-forecast"),
    BlockedV4Method(
        "DeleteForecastReport",
        "forecast",
        "v4forecast",
        "delete-forecast-report",
    ),
    BlockedV4Method(
        "DeleteOfflineReport", "offline_reports", None, "delete-offline-report"
    ),
    BlockedV4Method("DeleteReport", "offline_reports", None, "delete-report"),
    BlockedV4Method("GetBannersTags", "tags", None, "get-banners-tags"),
    BlockedV4Method("GetCampaignsTags", "tags", None, "get-campaigns-tags"),
    BlockedV4Method("UpdateBannersTags", "tags", None, "update-banners-tags"),
    BlockedV4Method("UpdateCampaignsTags", "tags", None, "update-campaigns-tags"),
    BlockedV4Method("AdImageAssociation", "ad_image", None, "ad-image-association"),
    BlockedV4Method(
        "GetKeywordsSuggestion", "keywords", None, "get-keywords-suggestion"
    ),
    BlockedV4Method("PingAPI", "meta", "v4meta", "ping-api"),
    BlockedV4Method("PingAPI_X", "meta", "v4meta", "ping-api-x"),
    BlockedV4Method("GetVersion", "meta", "v4meta", "get-version"),
    BlockedV4Method("GetAvailableVersions", "meta", "v4meta", "get-available-versions"),
)

PLUGIN_TOOL_NAMES = ("auth_status", "auth_setup", "auth_login")

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
}

# Public tools whose parameter shape changed in a backwards-incompatible way.
# The replacement string describes the new signature so callers can migrate.
PARAMETER_BREAKING_CHANGES: dict[str, str] = {
    "bidmodifiers_set": (
        "Signature changed in CLI 0.2.10 alignment: now (id: int, value: int, "
        "extra_json?). Removed campaign_id and modifier_type — those were the "
        "legacy form which CLI itself documents as 'broken by design' "
        "(API rejects with 'required field Id is omitted'). Use the Id "
        "returned by `bidmodifiers_add` to update an existing modifier."
    ),
}

REMOVED_LEGACY_PUBLIC_NAMES = frozenset(RENAMED_TOOL_MIGRATION.keys())


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
PLUGIN_ONLY_TOOL_NAMES = frozenset(
    tool.public_name for tool in PUBLIC_CONTRACT if tool.classification == "plugin"
)
