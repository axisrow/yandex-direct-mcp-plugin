"""direct-cli 0.3.12 option parity checks."""

from __future__ import annotations

import importlib
import inspect
import re
import tomllib
from collections.abc import Callable
from pathlib import Path
from unittest.mock import patch

import pytest
import direct_cli  # type: ignore[import-not-found, import-untyped]
from direct_cli.cli import cli  # type: ignore[import-not-found, import-untyped]

from server.cli.runner import MIN_DIRECT_VERSION
from server.tools.adgroups import adgroups_add, adgroups_update
from server.tools.ads import ads_add, ads_update
from server.tools.bidmodifiers import bidmodifiers_add
from server.tools.bids import bids_set
from server.tools.campaigns import campaigns_add, campaigns_update
from server.tools.changes import changes_check
from server.tools.clients import clients_update
from server.tools.dynamic_feed_ad_targets import dynamic_feed_ad_targets_add
from server.tools.feeds import feeds_add, feeds_update
from server.tools.keyword_bids import keyword_bids_set
from server.tools.keywords import keywords_add, keywords_update
from server.tools.retargeting import retargeting_add, retargeting_update
from server.tools.smart_ad_targets import smart_ad_targets_add, smart_ad_targets_update
from server.tools.strategies import strategies_add, strategies_update
from server.tools.vcards import vcards_add

from tests.helpers import mock_runner

TARGET_COMMANDS: tuple[tuple[str, str, str, str], ...] = (
    ("campaigns", "add", "server.tools.campaigns", "campaigns_add"),
    ("campaigns", "update", "server.tools.campaigns", "campaigns_update"),
    ("adgroups", "add", "server.tools.adgroups", "adgroups_add"),
    ("adgroups", "update", "server.tools.adgroups", "adgroups_update"),
    ("ads", "add", "server.tools.ads", "ads_add"),
    ("ads", "update", "server.tools.ads", "ads_update"),
    ("keywords", "add", "server.tools.keywords", "keywords_add"),
    ("keywords", "update", "server.tools.keywords", "keywords_update"),
    ("feeds", "add", "server.tools.feeds", "feeds_add"),
    ("feeds", "update", "server.tools.feeds", "feeds_update"),
    ("vcards", "add", "server.tools.vcards", "vcards_add"),
    ("sitelinks", "add", "server.tools.sitelinks", "sitelinks_add"),
    ("retargeting", "add", "server.tools.retargeting", "retargeting_add"),
    ("retargeting", "update", "server.tools.retargeting", "retargeting_update"),
    ("bidmodifiers", "add", "server.tools.bidmodifiers", "bidmodifiers_add"),
    ("audiencetargets", "add", "server.tools.audience", "audience_targets_add"),
    (
        "dynamicfeedadtargets",
        "add",
        "server.tools.dynamic_feed_ad_targets",
        "dynamic_feed_ad_targets_add",
    ),
    ("smartadtargets", "add", "server.tools.smart_ad_targets", "smart_ad_targets_add"),
    (
        "smartadtargets",
        "update",
        "server.tools.smart_ad_targets",
        "smart_ad_targets_update",
    ),
    ("bids", "set", "server.tools.bids", "bids_set"),
    ("keywordbids", "set", "server.tools.keyword_bids", "keyword_bids_set"),
    ("clients", "update", "server.tools.clients", "clients_update"),
    ("strategies", "add", "server.tools.strategies", "strategies_add"),
    ("strategies", "update", "server.tools.strategies", "strategies_update"),
    ("changes", "check", "server.tools.changes", "changes_check"),
)

IGNORED_CLI_PARAMS = {"output", "output_format", "format"}

# CLI options the plugin intentionally does NOT expose because the Direct API
# rejects them even though direct-cli still accepts the flag. Keyed by
# (group, subcommand) -> set of click param names.
INTENTIONALLY_UNEXPOSED_CLI_PARAMS = {
    # RetargetingLists.update rejects the Type field (API error 8000); a list's
    # type is fixed at creation, so retargeting_update drops list_type. See #166.
    ("retargeting", "update"): {"list_type"},
}

# CLI options that direct-cli 0.4.2 still DEFINES (so it can emit a friendly
# deprecation error) but REJECTS at runtime. The MCP plugin intentionally does
# not forward them — campaigns_add/update drop the free-form notification/
# time_targeting blob flags in favour of the typed --notification-*/
# --time-targeting-* flags (issue #170 finding #8) — so they are excluded from
# the "every CLI option must be exposed" parity guard.
DEPRECATED_REJECTED_CLI_PARAMS: dict[tuple[str, str], set[str]] = {
    ("campaigns", "add"): {"notification", "time_targeting"},
    ("campaigns", "update"): {"notification", "time_targeting"},
}
ALIASES = {
    ("campaigns", "update"): {"campaign_id": "id"},
    ("adgroups", "add"): {"group_type": "type"},
    ("adgroups", "update"): {"adgroup_id": "id"},
    ("ads", "add"): {"adgroup_id": "ad_group_id"},
    ("ads", "update"): {"ad_id": "id", "ad_type": "type"},
    ("keywords", "add"): {"adgroup_id": "ad_group_id"},
    ("keywords", "update"): {"keyword_id": "id"},
    ("feeds", "update"): {"feed_id": "id"},
    ("sitelinks", "add"): {
        "sitelinks_specs": "sitelinks",
        "sitelinks_json": "items",
        "sitelinks_from_file": "from_file",
    },
    ("retargeting", "update"): {"list_id": "id"},
    ("bidmodifiers", "add"): {"adgroup_id": "ad_group_id"},
    ("audiencetargets", "add"): {"adgroup_id": "ad_group_id"},
    ("dynamicfeedadtargets", "add"): {"adgroup_id": "ad_group_id"},
    ("smartadtargets", "add"): {"adgroup_id": "ad_group_id"},
    ("smartadtargets", "update"): {"target_id": "id"},
    ("bids", "set"): {"adgroup_id": "ad_group_id"},
    ("keywordbids", "set"): {"adgroup_id": "ad_group_id"},
    ("strategies", "add"): {"strategy_type": "type"},
    ("strategies", "update"): {"strategy_id": "id", "strategy_type": "type"},
}


def _direct_cli_version() -> tuple[int, int, int]:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", direct_cli.__version__)
    assert match is not None
    major, minor, patch = map(int, match.groups())
    return (major, minor, patch)


def _require_direct_cli_0312() -> None:
    if _direct_cli_version() < (0, 3, 12):
        pytest.skip("direct-cli 0.3.12 parity check waits for the PyPI release")


def test_runtime_and_package_require_direct_cli_0312_or_newer() -> None:
    """Issue #128: runtime and install contract must not regress below 0.3.12.

    Adapted for #223: pyproject.toml now exact-pins (``direct-cli==X.Y.Z``)
    instead of using a floor (``>=X.Y.Z``); the assertion still ensures the
    pinned version is ≥ both the historical 0.3.12 floor and the runtime
    probe in ``server/cli/runner.py``.
    """
    assert MIN_DIRECT_VERSION >= (0, 3, 12)

    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    dependencies = pyproject["project"]["dependencies"]
    direct_dependency = next(
        dep for dep in dependencies if dep.startswith("direct-cli")
    )

    match = re.search(r"==\s*(\d+)\.(\d+)\.(\d+)", direct_dependency)
    assert match is not None, (
        f"direct-cli dependency must be exact-pinned (==X.Y.Z); got {direct_dependency!r}"
    )
    pyproject_pin = tuple(map(int, match.groups()))
    assert pyproject_pin >= (0, 3, 12)
    assert pyproject_pin >= MIN_DIRECT_VERSION, (
        f"pyproject.toml pin {pyproject_pin} is below the runtime probe "
        f"{MIN_DIRECT_VERSION}; a fresh install could satisfy the package "
        "constraint and still be rejected by the runtime version probe."
    )


def _campaign_strategy_dict_param_names() -> set[str]:
    """CLI option names exposed via campaigns_* grouped strategy dicts.

    campaigns_add/update collapse the ~138 per-campaign-type bidding-strategy
    flags (and the 10 update-only *_budget_type flags) into nested dict params
    to cut tool-spec tokens (#154). They are still 1:1 reachable — just as dict
    keys, not flat signature params — so the parity guard treats them as exposed.
    """
    from server.tools.campaigns import (
        CAMPAIGN_UPDATE_ONLY_OPTIONS,
        _CAMPAIGN_FAMILY_DICT_REGISTRY,
        _STRATEGY_DICT_REGISTRY,
    )

    names = {opt.name for _, opts in _STRATEGY_DICT_REGISTRY for opt in opts}
    names |= {opt.name for opt in CAMPAIGN_UPDATE_ONLY_OPTIONS}
    # #220-B grouped the remaining flat families into dicts too; their member
    # names live on as dict keys, so they are still exposed.
    names |= {m for _, members in _CAMPAIGN_FAMILY_DICT_REGISTRY for m in members}
    return names


def _ads_extra_dict_param_names_by_subcommand() -> dict[str, set[str]]:
    """CLI option names exposed via ads_* grouped extension dicts (#220),
    scoped per subcommand.

    ads_add/ads_update collapse the price_extension / video_extension / callouts
    / creative / text-source flag families into nested dict params; the flat
    names live on as dict keys, so the parity guard treats them as exposed.
    Scoping per subcommand (rather than unioning both registries) avoids
    masking an accidentally-dropped flat param on one subcommand by a dict
    member name that exists only on the other.
    """
    from server.tools.ads import ADS_ADD_DICT_REGISTRY, ADS_UPDATE_DICT_REGISTRY

    return {
        "add": {m for _, members in ADS_ADD_DICT_REGISTRY for m in members},
        "update": {m for _, members in ADS_UPDATE_DICT_REGISTRY for m in members},
    }


def test_direct_cli_0312_options_are_exposed_by_mcp_signatures() -> None:
    _require_direct_cli_0312()

    strategy_dict_params = _campaign_strategy_dict_param_names()
    ads_dict_params_by_sub = _ads_extra_dict_param_names_by_subcommand()
    missing_by_command: dict[str, list[str]] = {}
    for group, subcommand, module_name, function_name in TARGET_COMMANDS:
        click_command = cli.commands[group].commands[subcommand]
        ignored = DEPRECATED_REJECTED_CLI_PARAMS.get((group, subcommand), set())
        cli_params = [
            param.name
            for param in click_command.params
            if hasattr(param, "opts")
            and param.name not in IGNORED_CLI_PARAMS
            and param.name not in ignored
        ]
        fn = getattr(importlib.import_module(module_name), function_name)
        mcp_params = set(inspect.signature(fn).parameters)
        # Strategy / extension options moved from flat params into grouped dicts;
        # they remain exposed (as dict keys), so count them as present.
        if group == "campaigns":
            mcp_params |= strategy_dict_params
        if group == "ads":
            mcp_params |= ads_dict_params_by_sub.get(subcommand, set())
        aliases = ALIASES.get((group, subcommand), {})
        unexposed = INTENTIONALLY_UNEXPOSED_CLI_PARAMS.get((group, subcommand), set())
        missing = [
            name
            for name in cli_params
            if name not in unexposed and aliases.get(name, name) not in mcp_params
        ]
        if missing:
            missing_by_command[f"{group} {subcommand}"] = missing

    assert missing_by_command == {}


def test_bidmodifier_type_choices_match_direct_cli() -> None:
    _require_direct_cli_0312()

    click_command = cli.commands["bidmodifiers"].commands["add"]
    modifier_type = next(
        param for param in click_command.params if param.name == "modifier_type"
    )
    from server.tools.bidmodifiers import _BIDMOD_TYPES

    assert set(_BIDMOD_TYPES) == set(modifier_type.type.choices)


def _assert_contains(argv: list[str], expected: list[str]) -> None:
    for item in expected:
        assert item in argv


def _run_with_runner(
    patch_target: str,
    fn: Callable[..., object],
    expected: list[str],
    **kwargs: object,
) -> None:
    runner = mock_runner({"ok": True})
    with patch(patch_target, return_value=runner):
        fn(**kwargs)
    _assert_contains(runner.run_json.call_args[0][0], expected)


def test_campaigns_0312_flags_are_forwarded() -> None:
    _run_with_runner(
        "server.tools.campaigns.get_runner",
        campaigns_add,
        [
            "--dynamic-placement-search-results",
            "YES",
            "--time-targeting-schedule",
            "1=10-18",
            "--frequency-cap-period-all",
            "--tracking-params",
            "utm_source=x",
        ],
        name="c",
        start_date="2026-01-01",
        dynamic_placement_search_results="YES",
        time_targeting_options={"time_targeting_schedule": ["1=10-18"]},
        frequency_cap_options={"frequency_cap_period_all": True},
        tracking_params="utm_source=x",
    )
    _run_with_runner(
        "server.tools.campaigns.get_runner",
        campaigns_update,
        ["--type", "TEXT_CAMPAIGN", "--package-platform-network", "YES"],
        id=1,
        campaign_type="TEXT_CAMPAIGN",
        package_platform_options={"package_platform_network": "YES"},
    )


def test_adgroups_and_ads_0312_flags_are_forwarded() -> None:
    _run_with_runner(
        "server.tools.adgroups.get_runner",
        adgroups_add,
        ["--autotargeting-category", "EXACT", "--tracking-params", "x=1"],
        campaign_id=1,
        name="g",
        region_ids="225",
        autotargeting_categories=["EXACT"],
        tracking_params="x=1",
    )
    # --dynamic-feed is is_flag=True in CLI 0.4.2: bare flag, no value.
    _run_with_runner(
        "server.tools.adgroups.get_runner",
        adgroups_update,
        ["--dynamic-feed", "--feed-category-ids", "1,2"],
        id=1,
        dynamic_feed=True,
        feed_category_ids="1,2",
    )
    _run_with_runner(
        "server.tools.ads.get_runner",
        ads_add,
        ["--mobile-app-feature", "PRICE=YES", "--feed-filter-condition", "x:eq:y"],
        ad_group_id=1,
        ad_type="SHOPPING_AD",
        mobile_app_features=["PRICE=YES"],
        feed_filter_conditions=["x:eq:y"],
    )
    _run_with_runner(
        "server.tools.ads.get_runner",
        ads_update,
        ["--callouts-set", "1,2", "--creative-erir-ad-description", "erir"],
        id=1,
        type="TEXT_AD",
        callouts_options={"callouts_set": "1,2"},
        creative_options={"creative_erir_ad_description": "erir"},
    )


def test_keyword_bid_and_target_0312_flags_are_forwarded() -> None:
    _run_with_runner(
        "server.tools.keywords.get_runner",
        keywords_add,
        ["--autotargeting-category", "EXACT", "--priority", "HIGH"],
        ad_group_id=1,
        keyword="foo",
        autotargeting_categories=["EXACT"],
        priority="HIGH",
    )
    # CLI 0.4.2 removed --bid/--context-bid/--status from `keywords update`;
    # only typed text/user-param/autotargeting fields are forwarded now.
    _run_with_runner(
        "server.tools.keywords.get_runner",
        keywords_update,
        ["--autotargeting-brand-option", "WITHOUT_BRANDS=YES"],
        id=1,
        autotargeting_brand_options=["WITHOUT_BRANDS=YES"],
    )
    _run_with_runner(
        "server.tools.bids.get_runner",
        bids_set,
        ["--campaign-id", "1", "--context-bid", "2000000", "--priority", "HIGH"],
        campaign_id=1,
        context_bid=2_000_000,
        priority="HIGH",
    )
    _run_with_runner(
        "server.tools.keyword_bids.get_runner",
        keyword_bids_set,
        ["--adgroup-id", "2", "--autotargeting-search-bid-is-auto", "YES"],
        ad_group_id=2,
        autotargeting_search_bid_is_auto="YES",
    )


def test_remaining_0312_flags_are_forwarded() -> None:
    _run_with_runner(
        "server.tools.feeds.get_runner",
        feeds_add,
        ["--file-feed-path", "/tmp/feed.xml", "--feed-login", "user"],
        name="feed",
        business_type="RETAIL",
        file_feed_path="/tmp/feed.xml",
        feed_login="user",
    )
    _run_with_runner(
        "server.tools.feeds.get_runner",
        feeds_update,
        ["--clear-feed-login", "--clear-feed-password"],
        id=1,
        clear_feed_login=True,
        clear_feed_password=True,
    )
    _run_with_runner(
        "server.tools.vcards.get_runner",
        vcards_add,
        ["--instant-messenger-client", "TELEGRAM", "--point-on-map-x", "1.1"],
        campaign_id=1,
        country="RU",
        city="Moscow",
        company_name="Co",
        work_time="0#4#10#18",
        phone_country_code="+7",
        phone_city_code="495",
        phone_number="1234567",
        instant_messenger_client="TELEGRAM",
        point_on_map_x="1.1",
    )
    _run_with_runner(
        "server.tools.retargeting.get_runner",
        retargeting_add,
        ["--description", "desc", "--rule", "ALL:1:30"],
        name="r",
        description="desc",
        rules=["ALL:1:30"],
    )
    _run_with_runner(
        "server.tools.retargeting.get_runner",
        retargeting_update,
        ["--description", "desc", "--rule", "ANY:2:7"],
        id=1,
        description="desc",
        rules=["ANY:2:7"],
    )
    _run_with_runner(
        "server.tools.bidmodifiers.get_runner",
        bidmodifiers_add,
        ["--operating-system-type", "IOS"],
        modifier_type="MOBILE_ADJUSTMENT",
        value=110,
        campaign_id=1,
        operating_system_type="IOS",
    )


def test_feed_smart_client_strategy_and_changes_0312_flags_are_forwarded() -> None:
    _run_with_runner(
        "server.tools.dynamic_feed_ad_targets.get_runner",
        dynamic_feed_ad_targets_add,
        ["--condition", "x:eq:y"],
        ad_group_id=1,
        name="t",
        conditions=["x:eq:y"],
    )
    _run_with_runner(
        "server.tools.smart_ad_targets.get_runner",
        smart_ad_targets_add,
        ["--condition", "x:eq:y"],
        ad_group_id=1,
        name="s",
        audience="PRODUCT_PAGE",
        conditions=["x:eq:y"],
    )
    _run_with_runner(
        "server.tools.smart_ad_targets.get_runner",
        smart_ad_targets_update,
        ["--condition", "x:eq:y"],
        id=1,
        conditions=["x:eq:y"],
    )
    _run_with_runner(
        "server.tools.clients.get_runner",
        clients_update,
        ["--erir-contract-number", "C-1", "--erir-contragent-tin", "123"],
        erir_contract_number="C-1",
        erir_contragent_tin="123",
    )
    _run_with_runner(
        "server.tools.strategies.get_runner",
        strategies_add,
        ["--custom-period-spend-limit", "1000000", "--minimum-exploration-budget", "5"],
        name="s",
        type="AverageCpc",
        custom_period_spend_limit=1_000_000,
        minimum_exploration_budget=5,
    )
    _run_with_runner(
        "server.tools.strategies.get_runner",
        strategies_update,
        ["--custom-period-auto-continue", "YES"],
        id=1,
        custom_period_auto_continue="YES",
    )
    _run_with_runner(
        "server.tools.changes.get_runner",
        changes_check,
        ["--fields", "CampaignIds", "--timestamp", "2026-01-01T00:00:00Z"],
        timestamp="2026-01-01T00:00:00Z",
        fields="CampaignIds",
        campaign_ids="1",
    )
