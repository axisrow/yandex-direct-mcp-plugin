"""Live safe smoke tests for existing read-only and auth MCP tools."""

import json
import os
from pathlib import Path

import pytest

from server.auth.storage import FileTokenStorage, TokenData
from server.tools.ads import ads_list
from server.tools.auth_tools import auth_setup, auth_status
from server.tools.campaigns import campaigns_list
from server.tools.keywords import keywords_list
from server.tools.reports import reports_get

pytestmark = [pytest.mark.integration, pytest.mark.live_safe]


def _find_campaign(campaigns: list[dict], campaign_id: str) -> dict | None:
    for campaign in campaigns:
        if str(campaign.get("Id")) == str(campaign_id):
            return campaign
    return None


@pytest.fixture()
def active_campaign(live_token_getter):
    """Return a live active campaign, preferring an explicitly configured ID."""
    campaigns = campaigns_list(state="ON")
    assert isinstance(campaigns, list), campaigns
    assert campaigns, "No active campaigns available for live tests"

    preferred_id = os.environ.get("TEST_ACTIVE_CAMPAIGN_ID")
    if preferred_id:
        campaign = _find_campaign(campaigns, preferred_id)
        assert campaign is not None, (
            f"TEST_ACTIVE_CAMPAIGN_ID={preferred_id} not found in active campaigns"
        )
        return campaign

    return campaigns[0]


def test_live_auth_status_returns_valid_dict(live_oauth_manager):
    result = auth_status()
    assert isinstance(result, dict)
    assert result["valid"] is True


def test_live_auth_setup_accepts_existing_direct_token(
    live_oauth_manager, live_plugin_data_dir: Path
):
    token_path = live_plugin_data_dir / "tokens.json"
    original_contents = token_path.read_text()
    original_data = json.loads(original_contents)
    access_token = original_data["access_token"]

    try:
        result = auth_setup(access_token)
        assert result["success"] is True
        assert result["method"] == "direct_token"
        assert result["access_token_prefix"] == access_token[:6] + "..."
        status = auth_status()
        assert status["valid"] is True
    finally:
        storage = FileTokenStorage(path=token_path)
        storage.save(TokenData(**original_data))


def test_live_campaigns_list_returns_active_campaigns(live_token_getter):
    campaigns = campaigns_list(state="ON")
    assert isinstance(campaigns, list), campaigns
    assert campaigns, "Expected at least one active campaign"
    assert all(campaign.get("State") == "ON" for campaign in campaigns)


def test_live_ads_list_reads_campaign(active_campaign, live_token_getter):
    result = ads_list(campaign_ids=str(active_campaign["Id"]))
    assert isinstance(result, list), result


def test_live_keywords_list_reads_campaign(active_campaign, live_token_getter):
    result = keywords_list(campaign_ids=str(active_campaign["Id"]))
    assert isinstance(result, list), result


def test_live_reports_get_returns_goal_metrics(live_token_getter):
    result = reports_get()
    assert isinstance(result, list), result
    assert result, "Expected at least one report row"
    first_row = result[0]
    assert "CampaignName" in first_row
    assert "Conversions" in first_row
    assert "CostPerConversion" in first_row
    assert "ConversionRate" in first_row
