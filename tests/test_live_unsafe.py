"""Live unsafe tests for existing mutating MCP tools with rollback."""

import os
import warnings

import pytest

from server.tools.campaigns import campaigns_list, campaigns_update
from server.tools.keywords import keywords_list, keywords_update

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


def test_live_campaigns_update_rolls_back(live_token_getter):
    campaign_id = _require_env("TEST_OFF_CAMPAIGN_ID")
    original = _find_campaign(campaign_id)
    assert original.get("State") == "OFF", (
        f"TEST_OFF_CAMPAIGN_ID={campaign_id} must start in OFF state, "
        f"got {original.get('State')}"
    )

    try:
        update_result = campaigns_update(id=campaign_id, state="ON")
        assert update_result.get("success") is True, update_result

        updated = _find_campaign(campaign_id)
        assert updated.get("State") == "ON", updated
    finally:
        try:
            rollback = campaigns_update(id=campaign_id, state="OFF")
            assert rollback.get("success") is True, rollback
            restored = _find_campaign(campaign_id)
            assert restored.get("State") == "OFF", restored
        except Exception:
            warnings.warn(f"Rollback failed for campaign {campaign_id}", stacklevel=2)


def test_live_keywords_update_rolls_back(live_token_getter):
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
        update_result = keywords_update(id=keyword_id, bid=str(temp_bid_value))
        assert update_result.get("success") is True, update_result

        updated = _find_keyword(campaign_id, keyword_id)
        assert int(updated["Bid"]) == temp_bid_value, updated
    finally:
        try:
            rollback = keywords_update(id=keyword_id, bid=str(original_bid))
            assert rollback.get("success") is True, rollback
            restored = _find_keyword(campaign_id, keyword_id)
            assert int(restored["Bid"]) == original_bid, restored
        except Exception:
            warnings.warn(f"Rollback failed for keyword {keyword_id}", stacklevel=2)
