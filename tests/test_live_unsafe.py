"""Live unsafe tests for existing mutating MCP tools with rollback."""

import os
import warnings
from collections.abc import Iterator
from types import ModuleType

import pytest

from server.tools.campaigns import campaigns_list, campaigns_update
from server.tools.keyword_bids import keyword_bids_set
from server.tools.keywords import keywords_list
from tests.helpers import import_tool_module_without_registration

pytestmark = [pytest.mark.integration, pytest.mark.live_unsafe]


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        pytest.skip(f"{name} is required for live unsafe tests")
    return value


def _find_campaign(campaign_id: str) -> dict:
    campaigns = campaigns_list()
    assert isinstance(campaigns, list), campaigns
    for campaign in campaigns:
        if str(campaign.get("Id")) == str(campaign_id):
            return campaign
    raise AssertionError(f"Campaign {campaign_id} not found")


def _find_keyword(campaign_id: str, keyword_id: str) -> dict:
    keywords = keywords_list(campaign_ids=str(campaign_id))
    assert isinstance(keywords, list), keywords
    for keyword in keywords:
        if str(keyword.get("Id")) == str(keyword_id):
            return keyword
    raise AssertionError(f"Keyword {keyword_id} not found in campaign {campaign_id}")


@pytest.fixture()
def masters_tools() -> Iterator[ModuleType]:
    """Load optional Masters tools without changing the global tool surface."""
    with import_tool_module_without_registration("server.tools.masters") as module:
        yield module


def _master_status(masters_tools: ModuleType, campaign_id: str) -> str:
    result = masters_tools.masters_get(campaign_id)
    if isinstance(result, list):
        assert len(result) == 1, result
        result = result[0]
    assert isinstance(result, dict), result
    status = result.get("Status")
    assert isinstance(status, str), result
    return status


def test_live_campaigns_update_rolls_back(live_plugin_data_dir):
    campaign_id = _require_env("TEST_OFF_CAMPAIGN_ID")
    original = _find_campaign(campaign_id)
    assert original.get("State") == "OFF", (
        f"TEST_OFF_CAMPAIGN_ID={campaign_id} must start in OFF state, "
        f"got {original.get('State')}"
    )

    try:
        update_result = campaigns_update(id=campaign_id, status="ON")
        assert update_result.get("success") is True, update_result

        updated = _find_campaign(campaign_id)
        assert updated.get("State") == "ON", updated
    finally:
        try:
            rollback = campaigns_update(id=campaign_id, status="OFF")
            assert rollback.get("success") is True, rollback
            restored = _find_campaign(campaign_id)
            assert restored.get("State") == "OFF", restored
        except Exception:
            warnings.warn(f"Rollback failed for campaign {campaign_id}", stacklevel=2)


def test_live_keyword_bids_set_rolls_back(live_plugin_data_dir):
    campaign_id = _require_env("TEST_KEYWORD_CAMPAIGN_ID")
    keyword_id = _require_env("TEST_KEYWORD_ID")
    temp_bid = _require_env("TEST_KEYWORD_BID_TEMP")

    original = _find_keyword(campaign_id, keyword_id)
    original_bid = int(original["Bid"])
    assert original_bid > 0

    temp_bid_value = int(temp_bid)
    assert temp_bid_value > 0
    assert temp_bid_value != original_bid, (
        "TEST_KEYWORD_BID_TEMP must differ from the current bid"
    )

    try:
        update_result = keyword_bids_set(
            keyword_id=int(keyword_id),
            search_bid=temp_bid_value,
        )
        assert update_result.get("success") is True, update_result

        updated = _find_keyword(campaign_id, keyword_id)
        assert int(updated["Bid"]) == temp_bid_value, updated
    finally:
        try:
            rollback = keyword_bids_set(
                keyword_id=int(keyword_id),
                search_bid=original_bid,
            )
            assert rollback.get("success") is True, rollback
            restored = _find_keyword(campaign_id, keyword_id)
            assert int(restored["Bid"]) == original_bid, restored
        except Exception:
            warnings.warn(f"Rollback failed for keyword {keyword_id}", stacklevel=2)


def test_live_masters_resume_then_suspend_rolls_back(
    masters_tools: ModuleType,
) -> None:
    campaign_id = _require_env("TEST_MASTERS_SUSPENDED_CAMPAIGN_ID")
    assert _master_status(masters_tools, campaign_id) == "SUSPENDED", (
        f"TEST_MASTERS_SUSPENDED_CAMPAIGN_ID={campaign_id} must start SUSPENDED"
    )

    try:
        resumed = masters_tools.masters_resume(campaign_id)
        assert isinstance(resumed, dict), resumed
        assert resumed.get("Status") in {"ACTIVE", "MODERATION"}, resumed
        assert _master_status(masters_tools, campaign_id) in {
            "ACTIVE",
            "MODERATION",
        }
    finally:
        try:
            rollback = masters_tools.masters_suspend(campaign_id)
            assert isinstance(rollback, dict), rollback
            assert rollback.get("Status") == "SUSPENDED", rollback
            assert _master_status(masters_tools, campaign_id) == "SUSPENDED"
        except Exception:
            warnings.warn(
                f"Rollback failed for Masters campaign {campaign_id}",
                stacklevel=2,
            )
