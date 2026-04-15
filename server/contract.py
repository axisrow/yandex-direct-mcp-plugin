"""Public MCP contract metadata aligned to the direct-cli surface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ToolAuthority = Literal["wsdl", "reports-spec", "cli-extra", "plugin"]
ToolClassification = Literal["direct_api", "cli_helper", "plugin"]


@dataclass(frozen=True)
class ContractTool:
    public_name: str
    cli_service: str | None
    cli_method: str | None
    authority: ToolAuthority
    classification: ToolClassification


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
    "turbopages": ("get",),
    "vcards": ("get", "add", "delete"),
}

CLI_HELPER_SERVICE_METHODS: dict[str, tuple[str, ...]] = {
    "agencyclients": ("delete",),
    "bidmodifiers": ("toggle",),
    "dictionaries": ("list_names",),
    "reports": ("list_types",),
}

PLUGIN_TOOL_NAMES = ("auth_status", "auth_setup", "auth_login")

REMOVED_LEGACY_PUBLIC_NAMES = frozenset(
    {
        "campaigns_list",
        "adgroups_list",
        "ads_list",
        "keyword_bids_list",
        "keyword_bids_set",
        "audience_targets_list",
        "audience_targets_add",
        "audience_targets_delete",
        "audience_targets_suspend",
        "audience_targets_resume",
        "agency_clients_list",
        "agency_clients_add",
        "agency_clients_delete",
        "businesses_list",
        "changes_checkcamp",
        "changes_checkdict",
        "creatives_list",
        "dynamic_ads_list",
        "dynamic_ads_add",
        "dynamic_ads_update",
        "dynamic_ads_delete",
        "dynamic_targets_list",
        "dynamic_targets_add",
        "dynamic_targets_update",
        "dynamic_targets_delete",
        "feeds_list",
        "keywords_has_volume",
        "keywords_deduplicate",
        "leads_list",
        "negative_keyword_shared_sets_list",
        "negative_keyword_shared_sets_add",
        "negative_keyword_shared_sets_update",
        "negative_keyword_shared_sets_delete",
        "negative_keywords_list",
        "negative_keywords_add",
        "negative_keywords_update",
        "negative_keywords_delete",
        "smart_ad_targets_list",
        "smart_ad_targets_add",
        "smart_ad_targets_update",
        "smart_ad_targets_delete",
        "smart_targets_list",
        "smart_targets_add",
        "smart_targets_update",
        "smart_targets_delete",
        "turbo_pages_list",
        "turbo_pages_add",
        "vcards_list",
        "adimages_list",
        "adextensions_list",
        "sitelinks_list",
    }
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
    tool.public_name
    for tool in PUBLIC_CONTRACT
    if tool.classification == "direct_api"
)
CLI_HELPER_TOOL_NAMES = frozenset(
    tool.public_name
    for tool in PUBLIC_CONTRACT
    if tool.classification == "cli_helper"
)
PLUGIN_ONLY_TOOL_NAMES = frozenset(
    tool.public_name for tool in PUBLIC_CONTRACT if tool.classification == "plugin"
)
