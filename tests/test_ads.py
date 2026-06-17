"""Tests for ads MCP tool."""

import asyncio

from unittest.mock import call, patch

from server.main import mcp
from server.tools.ads import (
    ads_list,
    ads_add,
    ads_update,
    ads_delete,
    ads_moderate,
    ads_suspend,
    ads_resume,
    ads_archive,
    ads_unarchive,
)

from tests.helpers import mock_runner

SAMPLE_ADS = [
    {
        "Id": 111,
        "Title": "Ad title placeholder",
        "Title2": "Ad title2 placeholder",
        "State": "ON",
    },
    {"Id": 222, "Title": "Ad title placeholder 2", "State": "OFF"},
]


def test_ads_list_success():
    """Test 11: List ads in a campaign."""
    with patch("server.tools.ads.get_runner", return_value=mock_runner(SAMPLE_ADS)):
        result = ads_list(campaign_ids="12345")
        assert len(result) == 2


def test_ads_list_ignores_blank_filters():
    """Test blank filters behave like no filter."""
    runner = mock_runner(SAMPLE_ADS)
    with patch("server.tools.ads.get_runner", return_value=runner):
        result = ads_list(campaign_ids="   ", ad_group_ids="   ", ids="   ")
        assert len(result) == 2
        call_args = runner.run_json.call_args[0][0]
        assert "--campaign-ids" not in call_args
        assert "--adgroup-ids" not in call_args
        assert "--ids" not in call_args


def test_ads_batch_limit():
    """Test 13: Too many IDs."""
    ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
    result = ads_list(campaign_ids=ids)
    assert "error" in result
    assert result["error"] == "batch_limit"


def test_ads_empty():
    """Empty result."""
    with patch("server.tools.ads.get_runner", return_value=mock_runner([])):
        result = ads_list(campaign_ids="12345")
        assert result == []


class TestAdsCrudOperations:
    """Tests for ad CRUD operations (add, update, delete, moderate, suspend, resume)."""

    def test_ads_add(self):
        """Test adding a new ad."""
        mock_result = {"Id": 999, "Text": "New ad text"}
        runner = mock_runner(mock_result)
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_add(
                ad_group_id=1,
                ad_type="TEXT_AD",
                title="Title",
                text="New ad text",
                href="https://example.com",
            )
            assert result["Id"] == 999
            runner.run_json.assert_called_once_with(
                [
                    "ads",
                    "add",
                    "--adgroup-id",
                    "1",
                    "--type",
                    "TEXT_AD",
                    "--title",
                    "Title",
                    "--text",
                    "New ad text",
                    "--href",
                    "https://example.com",
                ]
            )

    def test_ads_add_mobile_app(self):
        """MOBILE_APP_AD: tracking_url, action, age_label, image_hash pass through."""
        runner = mock_runner({"Id": 9999})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_add(
                ad_group_id=1,
                ad_type="MOBILE_APP_AD",
                title="Install now",
                text="Free game",
                image_hash="abc123",
                tracking_url="https://track.example/click",
                action="INSTALL",
                age_label="AGE_0_PLUS",
            )
            runner.run_json.assert_called_once_with(
                [
                    "ads",
                    "add",
                    "--adgroup-id",
                    "1",
                    "--type",
                    "MOBILE_APP_AD",
                    "--title",
                    "Install now",
                    "--text",
                    "Free game",
                    "--image-hash",
                    "abc123",
                    "--tracking-url",
                    "https://track.example/click",
                    "--action",
                    "INSTALL",
                    "--age-label",
                    "AGE_0_PLUS",
                ]
            )

    def test_ads_add_dry_run(self):
        """dry_run=True appends --dry-run to argv."""
        runner = mock_runner({"_dry_run": True})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_add(ad_group_id=1, ad_type="TEXT_AD", title="t", dry_run=True)
            argv = runner.run_json.call_args[0][0]
            assert "--dry-run" in argv

    def test_ads_update(self):
        """Test updating an ad with new required type parameter."""
        mock_result = {"Id": 111}
        with patch(
            "server.tools.ads.get_runner", return_value=mock_runner(mock_result)
        ):
            result = ads_update(id=111, type="TEXT_AD", title="New title")
            assert result["Id"] == 111

    def test_ads_update_argv_composition(self):
        """Test that update passes --type and field flags correctly."""
        runner = mock_runner({"Id": 111})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_update(
                id=111,
                type="TEXT_AD",
                title="New title",
                text="New body",
                href="https://example.com/new",
            )
            runner.run_json.assert_called_once_with(
                [
                    "ads",
                    "update",
                    "--id",
                    "111",
                    "--type",
                    "TEXT_AD",
                    "--title",
                    "New title",
                    "--text",
                    "New body",
                    "--href",
                    "https://example.com/new",
                ]
            )

    def test_ads_update_rejects_status(self):
        """direct-cli 0.4.2 rejects `ads update --status`; the tool redirects.

        Ad status is changed via ads_suspend/resume/archive/unarchive, so a
        status update is intercepted before any CLI call.
        """
        runner = mock_runner({"Id": 111})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_update(id=111, status="SUSPENDED")
        assert result["error"] == "status_not_updatable"
        runner.run_json.assert_not_called()

    def test_ads_update_mobile_app_argv(self):
        """MOBILE_APP_AD update accepts tracking_url / action / age_label / image_hash."""
        runner = mock_runner({"Id": 222})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_update(
                id=222,
                type="MOBILE_APP_AD",
                image_hash="hash123",
                tracking_url="https://t.example",
                action="INSTALL",
                age_label="AGE_0_PLUS",
            )
            argv = runner.run_json.call_args[0][0]
            assert "--type" in argv and "MOBILE_APP_AD" in argv
            assert "--tracking-url" in argv
            assert "--action" in argv
            assert "--age-label" in argv

    def test_ads_update_requires_changes(self):
        """Test that empty updates (type only) are rejected before CLI call."""
        runner = mock_runner({"Id": 111})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_update(id=111, type="TEXT_AD")
            assert result["error"] == "missing_update_fields"
            runner.run_json.assert_not_called()

    def test_ads_update_dry_run(self):
        """dry_run=True appends --dry-run to argv."""
        runner = mock_runner({"_dry_run": True})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_update(id=111, type="TEXT_AD", title="x", dry_run=True)
            argv = runner.run_json.call_args[0][0]
            assert "--dry-run" in argv

    def test_ads_update_clear_image_hash(self):
        """clear_image_hash=True appends --clear-image-hash (CLI #552/#553)."""
        runner = mock_runner({"Id": 111})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_update(id=111, type="TEXT_AD", clear_image_hash=True)
            argv = runner.run_json.call_args[0][0]
            assert "--clear-image-hash" in argv
            assert "--image-hash" not in argv

    def test_ads_update_clear_and_set_image_hash_conflict(self):
        """image_hash + clear_image_hash is rejected before the CLI call."""
        runner = mock_runner({"Id": 111})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_update(
                id=111, type="TEXT_AD", image_hash="abc", clear_image_hash=True
            )
        assert result["error"] == "conflicting_image_hash"
        runner.run_json.assert_not_called()

    def test_ads_add_from_file(self):
        """Batch add via from_file emits --from-file, no single-item flags (CLI #562)."""
        runner = mock_runner({"AddResults": [{"Id": 1}, {"Id": 2}]})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_add(from_file="/tmp/ads.jsonl")
            runner.run_json.assert_called_once_with(
                ["ads", "add", "--from-file", "/tmp/ads.jsonl"]
            )

    def test_ads_add_ads_json_with_default_adgroup(self):
        """ads_json batch forwards --adgroup-id default + --ads-json."""
        payload = '[{"type":"TEXT_AD","title":"x"}]'
        runner = mock_runner({"AddResults": [{"Id": 1}]})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_add(ad_group_id=42, ads_json=payload)
            argv = runner.run_json.call_args[0][0]
            assert argv == ["ads", "add", "--adgroup-id", "42", "--ads-json", payload]

    def test_ads_add_rejects_no_mode(self):
        """Neither ad_group_id nor batch flag → missing_mode."""
        runner = mock_runner({"AddResults": []})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_add()
        assert result["error"] == "missing_mode"
        runner.run_json.assert_not_called()

    def test_ads_add_rejects_conflicting_batch_modes(self):
        """from_file + ads_json → conflicting_modes."""
        runner = mock_runner({"AddResults": []})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_add(from_file="/tmp/a.jsonl", ads_json="[]")
        assert result["error"] == "conflicting_modes"
        runner.run_json.assert_not_called()

    def test_ads_update_from_file(self):
        """Batch update via from_file emits --from-file (CLI #563)."""
        runner = mock_runner({"UpdateResults": [{"Id": 1}]})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_update(from_file="/tmp/ads.jsonl")
            runner.run_json.assert_called_once_with(
                ["ads", "update", "--from-file", "/tmp/ads.jsonl"]
            )

    def test_ads_update_ads_json(self):
        """Batch update via ads_json emits --ads-json."""
        payload = '[{"id":1,"type":"TEXT_AD","title":"x"}]'
        runner = mock_runner({"UpdateResults": [{"Id": 1}]})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_update(ads_json=payload)
            argv = runner.run_json.call_args[0][0]
            assert argv == ["ads", "update", "--ads-json", payload]

    def test_ads_update_rejects_no_mode(self):
        """Neither id nor batch flag → missing_mode."""
        runner = mock_runner({"UpdateResults": []})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_update()
        assert result["error"] == "missing_mode"
        runner.run_json.assert_not_called()

    def test_ads_update_rejects_id_with_batch(self):
        """id + batch flag → conflicting_modes."""
        runner = mock_runner({"UpdateResults": []})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_update(id=1, ads_json="[]")
        assert result["error"] == "conflicting_modes"
        runner.run_json.assert_not_called()

    def test_ads_delete_success(self):
        """Test deleting ads successfully."""
        runner = mock_runner({"success": True})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_delete(ids="111,222")
            assert result["success"] is True
            runner.run_json.assert_has_calls(
                [
                    call(["ads", "delete", "--id", "111"]),
                    call(["ads", "delete", "--id", "222"]),
                ]
            )

    def test_ads_delete_batch_limit(self):
        """Test batch limit validation for delete."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = ads_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_ads_moderate_success(self):
        """Test submitting ads for moderation."""
        runner = mock_runner({"success": True})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_moderate(ids="111,222")
            assert result["success"] is True
            runner.run_json.assert_has_calls(
                [
                    call(["ads", "moderate", "--id", "111"]),
                    call(["ads", "moderate", "--id", "222"]),
                ]
            )

    def test_ads_moderate_batch_limit(self):
        """Test batch limit validation for moderate."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = ads_moderate(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_ads_suspend_success(self):
        """Test suspending ads."""
        runner = mock_runner({"success": True})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_suspend(ids="111,222")
            assert result["success"] is True
            runner.run_json.assert_has_calls(
                [
                    call(["ads", "suspend", "--id", "111"]),
                    call(["ads", "suspend", "--id", "222"]),
                ]
            )

    def test_ads_suspend_batch_limit(self):
        """Test batch limit validation for suspend."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = ads_suspend(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_ads_resume_success(self):
        """Test resuming suspended ads."""
        runner = mock_runner({"success": True})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_resume(ids="111,222")
            assert result["success"] is True
            runner.run_json.assert_has_calls(
                [
                    call(["ads", "resume", "--id", "111"]),
                    call(["ads", "resume", "--id", "222"]),
                ]
            )

    def test_ads_resume_batch_limit(self):
        """Test batch limit validation for resume."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = ads_resume(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_ads_archive_success(self):
        """Test archiving ads."""
        runner = mock_runner({"success": True})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_archive(ids="111,222")
            assert result["success"] is True
            runner.run_json.assert_has_calls(
                [
                    call(["ads", "archive", "--id", "111"]),
                    call(["ads", "archive", "--id", "222"]),
                ]
            )

    def test_ads_archive_batch_limit(self):
        """Test batch limit validation for archive."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = ads_archive(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_ads_unarchive_success(self):
        """Test unarchiving ads."""
        runner = mock_runner({"success": True})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_unarchive(ids="111,222")
            assert result["success"] is True
            runner.run_json.assert_has_calls(
                [
                    call(["ads", "unarchive", "--id", "111"]),
                    call(["ads", "unarchive", "--id", "222"]),
                ]
            )

    def test_ads_unarchive_batch_limit(self):
        """Test batch limit validation for unarchive."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = ads_unarchive(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"


class TestAdsTypedTextAdFields:
    """CLI 0.3.9: typed TextAd fields (title2, sitelinks, ad_extensions, etc)."""

    def test_ads_add_passes_title2(self):
        runner = mock_runner({"Id": 1})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_add(
                ad_group_id=1,
                ad_type="TEXT_AD",
                title="t",
                text="x",
                href="https://x",
                title2="Second headline",
            )
        argv = runner.run_json.call_args[0][0]
        assert "--title2" in argv
        assert "Second headline" in argv

    def test_ads_add_passes_display_url_path(self):
        runner = mock_runner({"Id": 1})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_add(
                ad_group_id=1,
                ad_type="TEXT_AD",
                title="t",
                text="x",
                href="https://x",
                display_url_path="catalog/items",
            )
        argv = runner.run_json.call_args[0][0]
        assert "--display-url-path" in argv
        assert "catalog/items" in argv

    def test_ads_add_passes_mobile_yes(self):
        runner = mock_runner({"Id": 1})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_add(
                ad_group_id=1,
                ad_type="TEXT_AD",
                title="t",
                text="x",
                href="https://x",
                mobile="YES",
            )
        argv = runner.run_json.call_args[0][0]
        assert "--mobile" in argv
        assert "YES" in argv

    def test_ads_add_rejects_mobile_invalid_value(self):
        runner = mock_runner({"Id": 1})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_add(
                ad_group_id=1,
                ad_type="TEXT_AD",
                title="t",
                mobile="FOO",
            )
        assert isinstance(result, dict)
        assert result["error"] == "invalid_mobile"
        runner.run_json.assert_not_called()

    def test_ads_add_passes_vcard_id(self):
        runner = mock_runner({"Id": 1})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_add(
                ad_group_id=1,
                ad_type="TEXT_AD",
                title="t",
                text="x",
                href="https://x",
                vcard_id=42,
            )
        argv = runner.run_json.call_args[0][0]
        assert "--vcard-id" in argv
        assert "42" in argv

    def test_ads_add_passes_sitelink_set_id(self):
        runner = mock_runner({"Id": 1})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_add(
                ad_group_id=1,
                ad_type="TEXT_AD",
                title="t",
                text="x",
                href="https://x",
                sitelink_set_id=7,
            )
        argv = runner.run_json.call_args[0][0]
        assert "--sitelink-set-id" in argv
        assert "7" in argv

    def test_ads_add_passes_turbo_page_id(self):
        runner = mock_runner({"Id": 1})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_add(
                ad_group_id=1,
                ad_type="TEXT_AD",
                title="t",
                text="x",
                href="https://x",
                turbo_page_id=12345,
            )
        argv = runner.run_json.call_args[0][0]
        assert "--turbo-page-id" in argv
        assert "12345" in argv

    def test_ads_add_passes_ad_extensions(self):
        runner = mock_runner({"Id": 1})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_add(
                ad_group_id=1,
                ad_type="TEXT_AD",
                title="t",
                text="x",
                href="https://x",
                ad_extensions="111,222,333",
            )
        argv = runner.run_json.call_args[0][0]
        assert "--ad-extensions" in argv
        assert "111,222,333" in argv

    def test_ads_update_passes_typed_text_ad_fields(self):
        runner = mock_runner({"Id": 555})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_update(
                id=555,
                type="TEXT_AD",
                title2="b",
                display_url_path="path",
                mobile="NO",
                vcard_id=1,
                sitelink_set_id=2,
                turbo_page_id=3,
                ad_extensions="100,200",
            )
        argv = runner.run_json.call_args[0][0]
        for flag, value in (
            ("--title2", "b"),
            ("--display-url-path", "path"),
            ("--mobile", "NO"),
            ("--vcard-id", "1"),
            ("--sitelink-set-id", "2"),
            ("--turbo-page-id", "3"),
            ("--ad-extensions", "100,200"),
        ):
            assert flag in argv, f"{flag} missing from argv"
            assert value in argv, f"{value} missing from argv"

    def test_ads_update_rejects_mobile_invalid_value(self):
        runner = mock_runner({"Id": 555})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_update(id=555, type="TEXT_AD", mobile="FOO")
        assert isinstance(result, dict)
        assert result["error"] == "invalid_mobile"
        runner.run_json.assert_not_called()

    def test_ads_update_typed_field_alone_satisfies_change_check(self):
        """title2 alone counts as a meaningful update — not 'missing_update_fields'."""
        runner = mock_runner({"Id": 555})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_update(id=555, type="TEXT_AD", title2="b")
        assert result["Id"] == 555
        argv = runner.run_json.call_args[0][0]
        assert "--title2" in argv


def test_ads_update_schema_has_no_required_fields_issue_181():
    """Regression guard for #181: ads_update must expose NO required parameters.

    The original bug (#181) was that ads_update declared ``id: int`` (required),
    so when an MCP host sent empty arguments ``{}`` the FastMCP validation layer
    raised ``id Field required [input_value={}]`` instead of a helpful message.
    PR #202 made ``id`` optional and added a ``missing_mode`` guard. If ``id``
    (or any field) becomes schema-required again, an empty host call resurrects
    the confusing pydantic crash — lock the fix at the schema level here.
    """
    tools = asyncio.run(mcp.list_tools())
    schema = next(t.inputSchema for t in tools if t.name == "ads_update")
    assert schema.get("required", []) == [], (
        "ads_update must have no required fields so an empty {} call yields the "
        "graceful missing_mode guard, not a pydantic 'id required' crash (#181)."
    )


def test_ads_update_empty_args_yield_missing_mode_via_dispatch_issue_181():
    """#181: through the FastMCP dispatch layer, ads_update({}) is graceful.

    Calls the tool the way an MCP host does — name + empty arguments — and
    asserts the response is the ``missing_mode`` guard, never a validation error.
    """
    result = asyncio.run(mcp.call_tool("ads_update", {}))
    assert "missing_mode" in str(result)


class TestAdsDictGrouping:
    """Grouped extension dict params expand to byte-identical CLI argv (#220)."""

    def _argv(self, fn, **kwargs):
        runner = mock_runner({"ok": True})
        with patch("server.tools.ads.get_runner", return_value=runner):
            fn(**kwargs)
        return runner.run_json.call_args[0][0]

    def test_add_price_video_text_dicts_expand_to_flags(self):
        argv = self._argv(
            ads_add,
            ad_group_id=1,
            ad_type="TEXT_AD",
            price_extension_options={
                "price_extension_price": "100",
                "price_extension_price_currency": "RUB",
            },
            video_extension_options={"video_extension_ids": "7,8"},
            text_source_options={"title_sources": "A", "default_texts": "D"},
        )
        assert argv[argv.index("--price-extension-price") + 1] == "100"
        assert argv[argv.index("--price-extension-price-currency") + 1] == "RUB"
        assert argv[argv.index("--video-extension-ids") + 1] == "7,8"
        assert argv[argv.index("--title-sources") + 1] == "A"
        assert argv[argv.index("--default-texts") + 1] == "D"
        # the dict param name itself never reaches argv
        assert "price_extension_options" not in argv

    def test_update_callouts_creative_dicts_expand_to_flags(self):
        argv = self._argv(
            ads_update,
            id=5,
            type="TEXT_AD",
            callouts_options={"callouts_add": "c1", "callouts_set": "c2"},
            creative_options={
                "creative_id": 99,
                "creative_erir_ad_description": "erir",
            },
        )
        assert argv[argv.index("--callouts-add") + 1] == "c1"
        assert argv[argv.index("--callouts-set") + 1] == "c2"
        assert argv[argv.index("--creative-id") + 1] == "99"
        assert argv[argv.index("--creative-erir-ad-description") + 1] == "erir"

    def test_non_dict_group_param_rejected(self):
        runner = mock_runner({"ok": True})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_update(id=5, type="TEXT_AD", price_extension_options="bad")
        assert result["error"] == "invalid_param"
        runner.run_json.assert_not_called()

    def test_empty_group_dict_does_not_satisfy_update_guard(self):
        runner = mock_runner({"ok": True})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_update(id=5, type="TEXT_AD", price_extension_options={})
        assert result["error"] == "missing_update_fields"
        runner.run_json.assert_not_called()

    def test_unknown_group_key_silently_ignored(self):
        argv = self._argv(
            ads_update,
            id=5,
            type="TEXT_AD",
            price_extension_options={"price_extension_price": "1", "nope": "x"},
        )
        assert "--price-extension-price" in argv
        assert "nope" not in argv
        assert "--nope" not in argv

    def test_add_has_no_grouped_flat_params(self):
        import inspect

        params = inspect.signature(ads_add).parameters
        for gone in ("price_extension_price", "video_extension_ids", "title_sources"):
            assert gone not in params
        for grouped in (
            "price_extension_options",
            "video_extension_options",
            "text_source_options",
        ):
            assert grouped in params
