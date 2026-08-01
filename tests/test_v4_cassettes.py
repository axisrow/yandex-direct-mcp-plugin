"""Cassette-based tests for v4 Live readonly tools (issue #260, Phase 1 harness).

Phase 1 (this file): test harness with skip-on-missing-cassette, mirrors the
ads/adgroups mutate harness from #261 Phase 1 (tests/test_ads_mutate_cassettes.py,
merged in #264).
Phase 2 (after .env.test / a live OAuth token is available): record cassettes.

Only READONLY v4 Live tools are covered here. Mutating tools
(v4forecast_create/delete, v4wordstat_create/delete_report, v4adimage_set,
v4tags_update_campaigns/update_banners) and financial tools
(v4account_deposit/invoice/transfer_money/update_account) stay mock-only —
see tests/test_v4_mocks.py (or equivalent) for those.

Phase 2 target workflow:
    1. Fill .env.test with YANDEX_OAUTH_TOKEN (+ any TEST_*_ID needed)
    2. pytest tests/test_v4_cassettes.py --record
       (each test call hits the live API and cli_recorder saves a cassette)
    3. python -m tests.sanitize
    4. python -m tests.audit   # exit 0
    5. unset YANDEX_OAUTH_TOKEN && pytest tests/  # green (replay)

In replay mode (default) the ``cli_recorder`` fixture patches subprocess.run
to return the saved cassette, so no token and no network call occur — CI is
safe. Each tool call is wrapped by ``@handle_cli_errors``, so a missing
cassette does NOT raise ``CassetteNotFoundError`` up to the test — it comes
back as a normal ``{"error": "unknown", "message": "No cassette found..."}``
dict (see server/tools/__init__.py). ``_run_cassette`` below detects that
specific message and turns it into ``pytest.skip``, so this file is a no-op
harness until Phase 2 records cassettes.
"""

from __future__ import annotations

import pytest

from server.tools.balance import balance_get
from server.tools.v4account import v4account_get_accounts
from server.tools.v4adimage import v4adimage_get
from server.tools.v4events import v4events_get_events_log
from server.tools.v4forecast import v4forecast_get, v4forecast_list
from server.tools.v4goals import (
    v4goals_get_retargeting_goals,
    v4goals_get_stat_goals,
)
from server.tools.v4keywords import v4keywords_get_suggestion
from server.tools.v4tags import v4tags_get_banners, v4tags_get_campaigns
from server.tools.v4wordstat import v4wordstat_get_report, v4wordstat_list_reports


def _run_cassette(fn, /, *args, **kwargs):
    """Call a tool, skipping the test if no cassette has been recorded yet.

    ``@handle_cli_errors`` catches ``CassetteNotFoundError`` (a bare
    ``Exception`` subclass) and returns it as an ``{"error": "unknown", ...}``
    dict rather than letting it propagate, so we detect that shape here
    instead of catching the exception directly.
    """
    result = fn(*args, **kwargs)
    if (
        isinstance(result, dict)
        and result.get("error") == "unknown"
        and "No cassette found" in str(result.get("message", ""))
    ):
        pytest.skip(f"No cassette recorded yet for {fn.__name__} (Phase 2, issue #260)")
    return result


class TestV4AccountCassette:
    """Cassette replay for v4account_get_accounts."""

    def test_v4account_get_accounts(self, cli_recorder):
        result = _run_cassette(v4account_get_accounts)
        assert isinstance(result, (dict, list))


class TestV4ForecastCassettes:
    """Cassette replay for v4forecast readonly tools."""

    def test_v4forecast_list(self, cli_recorder):
        result = _run_cassette(v4forecast_list)
        assert isinstance(result, (dict, list))

    def test_v4forecast_get(self, cli_recorder):
        result = _run_cassette(v4forecast_get, forecast_id=1)
        assert isinstance(result, (dict, list))


class TestV4WordstatCassettes:
    """Cassette replay for v4wordstat readonly tools."""

    def test_v4wordstat_list_reports(self, cli_recorder):
        result = _run_cassette(v4wordstat_list_reports)
        assert isinstance(result, (dict, list))

    def test_v4wordstat_get_report(self, cli_recorder):
        result = _run_cassette(v4wordstat_get_report, report_id=1)
        assert isinstance(result, (dict, list))


class TestV4AdimageCassette:
    """Cassette replay for v4adimage_get."""

    def test_v4adimage_get(self, cli_recorder):
        result = _run_cassette(v4adimage_get)
        assert isinstance(result, (dict, list))


class TestV4GoalsCassettes:
    """Cassette replay for v4goals readonly tools."""

    def test_v4goals_get_stat_goals(self, cli_recorder):
        result = _run_cassette(v4goals_get_stat_goals, campaign_ids="1")
        assert isinstance(result, (dict, list))

    def test_v4goals_get_retargeting_goals(self, cli_recorder):
        result = _run_cassette(v4goals_get_retargeting_goals, campaign_ids="1")
        assert isinstance(result, (dict, list))


class TestV4TagsCassettes:
    """Cassette replay for v4tags readonly tools."""

    def test_v4tags_get_campaigns(self, cli_recorder):
        result = _run_cassette(v4tags_get_campaigns, campaign_ids="1")
        assert isinstance(result, (dict, list))

    def test_v4tags_get_banners(self, cli_recorder):
        result = _run_cassette(v4tags_get_banners, campaign_ids="1")
        assert isinstance(result, (dict, list))


class TestBalanceCassette:
    """Cassette replay for balance_get."""

    def test_balance_get(self, cli_recorder):
        result = _run_cassette(balance_get)
        assert isinstance(result, (dict, list))


class TestV4EventsCassette:
    """Cassette replay for v4events_get_events_log."""

    def test_v4events_get_events_log(self, cli_recorder):
        result = _run_cassette(
            v4events_get_events_log,
            timestamp_from="2026-01-01T00:00:00",
            timestamp_to="2026-01-02T00:00:00",
        )
        assert isinstance(result, (dict, list))


class TestV4KeywordsCassette:
    """Cassette replay for v4keywords_get_suggestion."""

    def test_v4keywords_get_suggestion(self, cli_recorder):
        result = _run_cassette(v4keywords_get_suggestion, keywords=["купить телефон"])
        assert isinstance(result, (dict, list))
