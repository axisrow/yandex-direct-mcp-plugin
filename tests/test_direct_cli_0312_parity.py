"""direct-cli 0.3.12 option parity checks."""

from __future__ import annotations

import importlib
import inspect
import re
import tomllib
from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock, patch

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
    """Issue #128: runtime and install contract must not regress below 0.3.12."""
    assert MIN_DIRECT_VERSION >= (0, 3, 12)

    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    dependencies = pyproject["project"]["dependencies"]
    direct_dependency = next(
        dep for dep in dependencies if dep.startswith("direct-cli")
    )

    match = re.search(r">=\s*(\d+)\.(\d+)\.(\d+)", direct_dependency)
    assert match is not None
    assert tuple(map(int, match.groups())) >= (0, 3, 12)


def test_direct_cli_0312_options_are_exposed_by_mcp_signatures() -> None:
    _require_direct_cli_0312()

    missing_by_command: dict[str, list[str]] = {}
    for group, subcommand, module_name, function_name in TARGET_COMMANDS:
        click_command = cli.commands[group].commands[subcommand]
        cli_params = [
            param.name
            for param in click_command.params
            if hasattr(param, "opts") and param.name not in IGNORED_CLI_PARAMS
        ]
        fn = getattr(importlib.import_module(module_name), function_name)
        mcp_params = set(inspect.signature(fn).parameters)
        aliases = ALIASES.get((group, subcommand), {})
        missing = [
            name for name in cli_params if aliases.get(name, name) not in mcp_params
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


def _mock_runner() -> MagicMock:
    runner = MagicMock()
    runner.run_json.return_value = {"ok": True}
    return runner


def _assert_contains(argv: list[str], expected: list[str]) -> None:
    for item in expected:
        assert item in argv


def _run_with_runner(
    patch_target: str,
    fn: Callable[..., object],
    expected: list[str],
    **kwargs: object,
) -> None:
    runner = _mock_runner()
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
        time_targeting_schedule=["1=10-18"],
        frequency_cap_period_all=True,
        tracking_params="utm_source=x",
    )
    _run_with_runner(
        "server.tools.campaigns.get_runner",
        campaigns_update,
        ["--type", "TEXT_CAMPAIGN", "--package-platform-network", "YES"],
        id=1,
        campaign_type="TEXT_CAMPAIGN",
        package_platform_network="YES",
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
    _run_with_runner(
        "server.tools.adgroups.get_runner",
        adgroups_update,
        ["--dynamic-feed", "YES", "--feed-category-ids", "1,2"],
        id=1,
        dynamic_feed="YES",
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
        callouts_set="1,2",
        creative_erir_ad_description="erir",
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
    _run_with_runner(
        "server.tools.keywords.get_runner",
        keywords_update,
        ["--autotargeting-brand-option", "WITHOUT_BRANDS=YES", "--status", "ON"],
        id=1,
        autotargeting_brand_options=["WITHOUT_BRANDS=YES"],
        status="ON",
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
