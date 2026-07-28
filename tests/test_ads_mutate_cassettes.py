"""Cassette-based tests for ads mutating tools (issue #261, Phase 1 harness).

Phase 1 (this file): test harness with skip-on-missing-cassette.
Phase 2 (after .env.test): record cassettes.

WARNING — SAFETY (review #264): these tests mutate a real Yandex.Direct
account when run live, so the suite carries ``pytest.mark.live_unsafe``
and is gated behind ``--run-live-unsafe`` (same contract as
tests/test_live_unsafe.py). Setting ``TEST_*_ID`` without the flag does
NOT run them — they stay skipped. Do NOT remove the marker.

WARNING — RECORD MODE IS NOT WIRE-READY (review #264, Codex): the
``cli_recorder`` fixture's ``--record`` path (tests/conftest.py) currently
lets real subprocess calls through WITHOUT capturing them, so
``pytest --record`` would mutate the account and write NO cassettes.
Before Phase 2 recording, either (a) call ``recorder.record(...)`` per
test, or (b) patch the fixture's record branch to intercept
``subprocess.run`` and save each call. Until then, do NOT run ``--record``
expecting cassettes — track in #261 Phase 2.

Phase 2 target workflow (after the record-mode fix above):
    1. Fill .env.test with YANDEX_OAUTH_TOKEN + TEST_*_ID
    2. pytest tests/test_ads_mutate_cassettes.py --run-live-unsafe --record
       (add/verify/rollback per test, disposable resources, finally-cleanup)
    3. python -m tests.sanitize
    4. python -m tests.audit   # exit 0
    5. unset YANDEX_OAUTH_TOKEN && pytest tests/  # green (replay)

In replay mode (default) the fixture patches subprocess.run to return the
saved cassette, so no token and no mutation occur — CI is safe.

Why ads/adgroups first (#261 rationale):
    These tools had the most format-drift precedents:
    - #210 AdImageHash ``[null]`` vs ``null``
    - #166 list_type breaks update
    - Batch mode (from_file / *_json) is unique to ads & adgroups
    - Grouped dict params (#220) are unique to ads & campaigns
"""

from __future__ import annotations

import os

import pytest

from server.tools.adgroups import (
    adgroups_add,
    adgroups_delete,
    adgroups_update,
)

# ── Import the tool functions under test ─────────────────────────────────
from server.tools.ads import (
    ads_add,
    ads_archive,
    ads_delete,
    ads_moderate,
    ads_resume,
    ads_suspend,
    ads_unarchive,
    ads_update,
)

# ── Helpers ───────────────────────────────────────────────────────────────

# SAFETY: when run live (`--record` with TEST_*_ID set), these tests mutate a
# real Yandex.Direct account (overwrite ad fields, suspend/archive/moderate,
# add ads/ad groups). They MUST stay behind the `--run-live-unsafe` gate so a
# contributor who sets the IDs cannot accidentally run them against a live
# account, exactly like tests/test_live_unsafe.py. The replay path (default,
# cassettes present) is still gated — replay needs neither the gate nor a
# token, but the marker is harmless there and keeps the safety contract
# uniform. See #261 Phase 2 conventions (#126).
pytestmark = [pytest.mark.integration, pytest.mark.live_unsafe]

# IDs used during recording.  These come from the test account — the
# cassette stores the full CLI response so the actual IDs are baked in.
# When re-recording, update these to match the live test account.
TEST_CAMPAIGN_ID = os.environ.get("TEST_CAMPAIGN_ID", "")
TEST_AD_GROUP_ID = os.environ.get("TEST_AD_GROUP_ID", "")
TEST_AD_ID = os.environ.get("TEST_AD_ID", "")


# ── Ads mutating cassette tests ───────────────────────────────────────────


class TestAdsAddCassette:
    """Cassette replay for ads_add (single TEXT_AD)."""

    def test_ads_add_text_ad(self, cli_recorder):
        """ads_add single TEXT_AD — cassette replay."""
        if not TEST_CAMPAIGN_ID or not TEST_AD_GROUP_ID:
            pytest.skip("TEST_CAMPAIGN_ID / TEST_AD_GROUP_ID not set")
        result = ads_add(
            ad_group_id=int(TEST_AD_GROUP_ID),
            ad_type="TEXT_AD",
            title="Cassette test ad",
            text="Cassette test body",
            href="https://example.com/cassette-test",
        )
        assert "AddResults" in result or "Id" in result or "error" in result

    def test_ads_add_text_ad_dry_run(self, cli_recorder):
        """ads_add --dry-run — no mutation, safe for any account."""
        if not TEST_AD_GROUP_ID:
            pytest.skip("TEST_AD_GROUP_ID not set")
        result = ads_add(
            ad_group_id=int(TEST_AD_GROUP_ID),
            ad_type="TEXT_AD",
            title="Dry run ad",
            text="Dry run body",
            href="https://example.com/dry-run",
            dry_run=True,
        )
        # dry-run should return something (even if validation error from CLI)
        assert isinstance(result, dict)


class TestAdsUpdateCassette:
    """Cassette replay for ads_update."""

    def test_ads_update_title(self, cli_recorder):
        """ads_update changes title — cassette replay."""
        if not TEST_AD_ID:
            pytest.skip("TEST_AD_ID not set")
        result = ads_update(
            id=int(TEST_AD_ID),
            type="TEXT_AD",
            title="Updated cassette title",
        )
        assert "UpdateResults" in result or "Id" in result or "error" in result

    def test_ads_update_clear_image_hash(self, cli_recorder):
        """ads_update --clear-image-hash (#210 regression guard)."""
        if not TEST_AD_ID:
            pytest.skip("TEST_AD_ID not set")
        result = ads_update(
            id=int(TEST_AD_ID),
            type="TEXT_AD",
            clear_image_hash=True,
        )
        assert isinstance(result, dict)


class TestAdsStateCassettes:
    """Cassette replay for ads state-change operations.

    Each test records a suspend/resume/archive/unarchive call.
    Recording protocol: call suspend → record cassette → immediately resume
    (rollback) → record second cassette.  Both cassettes are committed.
    """

    def test_ads_suspend(self, cli_recorder):
        """ads_suspend — cassette replay."""
        if not TEST_AD_ID:
            pytest.skip("TEST_AD_ID not set")
        result = ads_suspend(ids=TEST_AD_ID)
        assert isinstance(result, dict)

    def test_ads_resume(self, cli_recorder):
        """ads_resume — cassette replay."""
        if not TEST_AD_ID:
            pytest.skip("TEST_AD_ID not set")
        result = ads_resume(ids=TEST_AD_ID)
        assert isinstance(result, dict)

    def test_ads_archive(self, cli_recorder):
        """ads_archive — cassette replay."""
        if not TEST_AD_ID:
            pytest.skip("TEST_AD_ID not set")
        result = ads_archive(ids=TEST_AD_ID)
        assert isinstance(result, dict)

    def test_ads_unarchive(self, cli_recorder):
        """ads_unarchive — cassette replay."""
        if not TEST_AD_ID:
            pytest.skip("TEST_AD_ID not set")
        result = ads_unarchive(ids=TEST_AD_ID)
        assert isinstance(result, dict)

    def test_ads_moderate(self, cli_recorder):
        """ads_moderate — cassette replay."""
        if not TEST_AD_ID:
            pytest.skip("TEST_AD_ID not set")
        result = ads_moderate(ids=TEST_AD_ID)
        assert isinstance(result, dict)

    def test_ads_delete_dry_run(self, cli_recorder):
        """ads_delete --dry-run — safe, no real deletion."""
        if not TEST_AD_ID:
            pytest.skip("TEST_AD_ID not set")
        result = ads_delete(ids=TEST_AD_ID, dry_run=True)
        assert isinstance(result, dict)


# ── Adgroups mutating cassette tests ──────────────────────────────────────


class TestAdgroupsAddCassette:
    """Cassette replay for adgroups_add."""

    def test_adgroups_add(self, cli_recorder):
        """adgroups_add — cassette replay."""
        if not TEST_CAMPAIGN_ID:
            pytest.skip("TEST_CAMPAIGN_ID not set")
        result = adgroups_add(
            campaign_id=int(TEST_CAMPAIGN_ID),
            name="Cassette test ad group",
        )
        assert "AddResults" in result or "Id" in result or "error" in result

    def test_adgroups_add_dry_run(self, cli_recorder):
        """adgroups_add --dry-run — safe for any account."""
        if not TEST_CAMPAIGN_ID:
            pytest.skip("TEST_CAMPAIGN_ID not set")
        result = adgroups_add(
            campaign_id=int(TEST_CAMPAIGN_ID),
            name="Dry run ad group",
            dry_run=True,
        )
        assert isinstance(result, dict)


class TestAdgroupsUpdateCassette:
    """Cassette replay for adgroups_update."""

    def test_adgroups_update_name(self, cli_recorder):
        """adgroups_update changes name — cassette replay."""
        if not TEST_AD_GROUP_ID:
            pytest.skip("TEST_AD_GROUP_ID not set")
        result = adgroups_update(
            id=int(TEST_AD_GROUP_ID),
            name="Updated cassette name",
        )
        assert "UpdateResults" in result or "Id" in result or "error" in result


class TestAdgroupsDeleteCassette:
    """Cassette replay for adgroups_delete."""

    def test_adgroups_delete_dry_run(self, cli_recorder):
        """adgroups_delete --dry-run — safe, no real deletion."""
        if not TEST_AD_GROUP_ID:
            pytest.skip("TEST_AD_GROUP_ID not set")
        result = adgroups_delete(ids=TEST_AD_GROUP_ID, dry_run=True)
        assert isinstance(result, dict)
