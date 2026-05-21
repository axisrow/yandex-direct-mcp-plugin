"""Tests for ads MCP tool."""

from unittest.mock import MagicMock, call, patch


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


SAMPLE_ADS = [
    {
        "Id": 111,
        "Title": "Ad title placeholder",
        "Title2": "Ad title2 placeholder",
        "State": "ON",
    },
    {"Id": 222, "Title": "Ad title placeholder 2", "State": "OFF"},
]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


def test_ads_list_success():
    """Test 11: List ads in a campaign."""
    with patch("server.tools.ads.get_runner", return_value=_mock_runner(SAMPLE_ADS)):
        result = ads_list(campaign_ids="12345")
        assert len(result) == 2


def test_ads_list_ignores_blank_filters():
    """Test blank filters behave like no filter."""
    runner = MagicMock()
    runner.run_json.return_value = SAMPLE_ADS
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
    with patch("server.tools.ads.get_runner", return_value=_mock_runner([])):
        result = ads_list(campaign_ids="12345")
        assert result == []


class TestAdsCrudOperations:
    """Tests for ad CRUD operations (add, update, delete, moderate, suspend, resume)."""

    def test_ads_add(self):
        """Test adding a new ad."""
        mock_result = {"Id": 999, "Text": "New ad text"}
        runner = _mock_runner(mock_result)
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
        runner = _mock_runner({"Id": 9999})
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
        runner = _mock_runner({"_dry_run": True})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_add(ad_group_id=1, ad_type="TEXT_AD", title="t", dry_run=True)
            argv = runner.run_json.call_args[0][0]
            assert "--dry-run" in argv

    def test_ads_update(self):
        """Test updating an ad with new required type parameter."""
        mock_result = {"Id": 111}
        with patch(
            "server.tools.ads.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = ads_update(id=111, type="TEXT_AD", title="New title")
            assert result["Id"] == 111

    def test_ads_update_argv_composition(self):
        """Test that update passes --type and field flags correctly."""
        runner = _mock_runner({"Id": 111})
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

    def test_ads_update_mobile_app_argv(self):
        """MOBILE_APP_AD update accepts tracking_url / action / age_label / image_hash."""
        runner = _mock_runner({"Id": 222})
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
        runner = _mock_runner({"Id": 111})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_update(id=111, type="TEXT_AD")
            assert result["error"] == "missing_update_fields"
            runner.run_json.assert_not_called()

    def test_ads_update_dry_run(self):
        """dry_run=True appends --dry-run to argv."""
        runner = _mock_runner({"_dry_run": True})
        with patch("server.tools.ads.get_runner", return_value=runner):
            ads_update(id=111, type="TEXT_AD", title="x", dry_run=True)
            argv = runner.run_json.call_args[0][0]
            assert "--dry-run" in argv

    def test_ads_delete_success(self):
        """Test deleting ads successfully."""
        runner = _mock_runner({"success": True})
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
        runner = _mock_runner({"success": True})
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
        runner = _mock_runner({"success": True})
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
        runner = _mock_runner({"success": True})
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
        runner = _mock_runner({"success": True})
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
        runner = _mock_runner({"success": True})
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
        runner = _mock_runner({"Id": 1})
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
        runner = _mock_runner({"Id": 1})
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
        runner = _mock_runner({"Id": 1})
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
        runner = _mock_runner({"Id": 1})
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
        runner = _mock_runner({"Id": 1})
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
        runner = _mock_runner({"Id": 1})
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
        runner = _mock_runner({"Id": 1})
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
        runner = _mock_runner({"Id": 1})
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
        runner = _mock_runner({"Id": 555})
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
        runner = _mock_runner({"Id": 555})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_update(id=555, type="TEXT_AD", mobile="FOO")
        assert isinstance(result, dict)
        assert result["error"] == "invalid_mobile"
        runner.run_json.assert_not_called()

    def test_ads_update_typed_field_alone_satisfies_change_check(self):
        """title2 alone counts as a meaningful update — not 'missing_update_fields'."""
        runner = _mock_runner({"Id": 555})
        with patch("server.tools.ads.get_runner", return_value=runner):
            result = ads_update(id=555, type="TEXT_AD", title2="b")
        assert result["Id"] == 555
        argv = runner.run_json.call_args[0][0]
        assert "--title2" in argv
