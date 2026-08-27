"""Live safe smoke tests for existing read-only and auth MCP tools."""

import os
from datetime import date, timedelta
from types import ModuleType

import pytest

from server.tools.ads import ads_list
from server.tools.auth_tools import auth_status
from server.tools.campaigns import campaigns_list
from server.tools.keywords import keywords_list
from server.tools.reports import reports_get
from tests.helpers import import_tool_module_without_registration

pytestmark = [pytest.mark.integration, pytest.mark.live_safe]

_BROWSER_ENV_ERRORS = {
    "browser_auth_required",
    "browser_captcha",
    "browser_error",
    "browser_profile_error",
}


def _find_campaign(campaigns: list[dict], campaign_id: str) -> dict | None:
    for campaign in campaigns:
        if str(campaign.get("Id")) == str(campaign_id):
            return campaign
    return None


def _skip_unavailable_browser(result):
    if isinstance(result, dict) and result.get("error") in _BROWSER_ENV_ERRORS:
        pytest.skip(f"Masters browser session unavailable: {result['error']}")
    return result


@pytest.fixture(scope="module")
def masters_tools() -> ModuleType:
    """Load optional tools without changing the process-wide default surface."""
    with import_tool_module_without_registration("server.tools.masters") as module:
        return module


@pytest.fixture(scope="module")
def masters_campaign_id(masters_tools: ModuleType) -> str:
    result = _skip_unavailable_browser(masters_tools.masters_list(status="all"))
    assert isinstance(result, list), result
    if not result:
        pytest.skip("No Campaign Wizard campaigns available for live tests")

    preferred_id = os.environ.get("TEST_MASTERS_CAMPAIGN_ID")
    if preferred_id is not None:
        return preferred_id

    campaign_id = result[0].get("CampaignId", result[0].get("campaign_id"))
    assert campaign_id is not None, result[0]
    return str(campaign_id)


@pytest.fixture()
def active_campaign(live_plugin_data_dir):
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


def test_live_auth_status_returns_valid_dict(live_plugin_data_dir):
    result = auth_status()
    assert isinstance(result, dict)
    assert result["valid"] is True


def test_live_campaigns_list_returns_active_campaigns(live_plugin_data_dir):
    campaigns = campaigns_list(state="ON")
    assert isinstance(campaigns, list), campaigns
    assert campaigns, "Expected at least one active campaign"
    assert all(campaign.get("State") == "ON" for campaign in campaigns)


def test_live_ads_list_reads_campaign(active_campaign, live_plugin_data_dir):
    result = ads_list(campaign_ids=str(active_campaign["Id"]))
    assert isinstance(result, list), result


def test_live_keywords_list_reads_campaign(active_campaign, live_plugin_data_dir):
    result = keywords_list(campaign_ids=str(active_campaign["Id"]))
    assert isinstance(result, list), result


def test_live_reports_get_returns_goal_metrics(live_plugin_data_dir):
    result = reports_get()
    assert isinstance(result, list), result
    assert result, "Expected at least one report row"
    first_row = result[0]
    assert "CampaignName" in first_row
    assert "Conversions" in first_row
    assert "CostPerConversion" in first_row
    assert "ConversionRate" in first_row


def test_live_history_get_reads_browser_history_or_skips_without_session():
    """Read one recent history row without turning missing browser state into CI red."""
    from server.main import mcp
    from server.tools.history import history_get

    # Optional-tool import gating is integrated separately by W-02. Keep this
    # direct live call from mutating the process-wide default registry.
    mcp._tool_manager._tools.pop("history_get", None)

    today = date.today()
    result = history_get(
        date_from=(today - timedelta(days=1)).isoformat(),
        date_to=today.isoformat(),
        limit=1,
    )
    if isinstance(result, dict) and result.get("error") in {
        "browser_auth_required",
        "browser_profile_error",
        "browser_error",
    }:
        pytest.skip(f"No usable browser session for history_get: {result['message']}")

    assert isinstance(result, list), result
    if result:
        assert {
            "Datetime",
            "Login",
            "ChangeSource",
            "Category",
            "EventType",
            "Gtid",
            "Event",
        } <= result[0].keys()


def test_live_masters_list_is_readable(masters_tools: ModuleType):
    result = _skip_unavailable_browser(masters_tools.masters_list())
    assert isinstance(result, list), result


def test_live_masters_get_is_readable(
    masters_tools: ModuleType, masters_campaign_id: str
):
    result = _skip_unavailable_browser(
        masters_tools.masters_get(str(masters_campaign_id))
    )
    assert isinstance(result, (dict, list)), result


@pytest.mark.parametrize(
    "tool_name",
    [
        "masters_adimages_get",
        "masters_targetactions_get",
        "masters_counters_get",
        "masters_audience_get",
    ],
)
def test_live_masters_nested_read_is_readable(
    masters_tools: ModuleType,
    masters_campaign_id: str,
    tool_name: str,
):
    result = _skip_unavailable_browser(
        getattr(masters_tools, tool_name)(masters_campaign_id)
    )
    assert isinstance(result, dict), result
