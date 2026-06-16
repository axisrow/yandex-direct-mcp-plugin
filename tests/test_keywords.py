"""Tests for keyword MCP tools."""

from unittest.mock import call, patch

from server.tools.keywords import (
    keywords_list,
    keywords_update,
    keywords_add,
    keywords_delete,
    keywords_suspend,
    keywords_resume,
)

from tests.helpers import mock_runner

SAMPLE_KEYWORDS = [
    {"Id": 99999, "Keyword": "keyword_99999", "Bid": 12000000},
]


def test_keywords_list():
    """Test 14: List keywords."""
    with patch(
        "server.tools.keywords.get_runner", return_value=mock_runner(SAMPLE_KEYWORDS)
    ):
        result = keywords_list(campaign_ids="12345")
        assert len(result) == 1
        assert result[0]["Id"] == 99999


def test_keywords_list_trims_campaign_ids():
    """Test campaign IDs are normalized before argv construction."""
    runner = mock_runner(SAMPLE_KEYWORDS)
    with patch("server.tools.keywords.get_runner", return_value=runner):
        keywords_list(campaign_ids=" 12345 ")

    runner.run_json.assert_called_once_with(
        ["keywords", "get", "--format", "json", "--campaign-ids", "12345"]
    )


def test_keywords_list_blank_selector_rejected():
    """Blank/missing selectors must NOT silently widen to an account-wide query."""
    runner = mock_runner(SAMPLE_KEYWORDS)
    with patch("server.tools.keywords.get_runner", return_value=runner):
        result = keywords_list(campaign_ids="   ")
    assert isinstance(result, dict)
    assert result["error"] == "missing_selector"
    runner.run_json.assert_not_called()


def test_keywords_list_fetch_all_is_not_a_filter():
    """fetch_all paginates but is not a filter; direct-cli rejects empty
    SelectionCriteria, so fetch_all alone is rejected up front (#170-19)."""
    runner = mock_runner(SAMPLE_KEYWORDS)
    with patch("server.tools.keywords.get_runner", return_value=runner):
        result = keywords_list(fetch_all=True)
    assert result["error"] == "missing_selector"
    runner.run_json.assert_not_called()


def test_keywords_list_status_counts_as_filter():
    """A status/state filter alone is a valid SelectionCriteria (no IDs needed)."""
    runner = mock_runner(SAMPLE_KEYWORDS)
    with patch("server.tools.keywords.get_runner", return_value=runner):
        keywords_list(statuses="ACCEPTED", fetch_all=True)
    argv = runner.run_json.call_args[0][0]
    assert "--statuses" in argv
    assert "--fetch-all" in argv


def test_keywords_update():
    """Test updating keyword text."""
    with patch("server.tools.keywords.get_runner", return_value=mock_runner(None)):
        result = keywords_update(id=99999, keyword="new keyword text")
        assert result["success"] is True
        assert result["keyword"] == "new keyword text"


def test_keywords_update_argv_composition():
    """Test that update passes the expanded CLI surface (no --json in 0.3.8)."""
    runner = mock_runner(None)
    with patch("server.tools.keywords.get_runner", return_value=runner):
        result = keywords_update(
            id=99999,
            keyword="updated kw",
            user_param_1="val1",
            user_param_2="val2",
        )

    runner.run_json.assert_called_once_with(
        [
            "keywords",
            "update",
            "--id",
            "99999",
            "--keyword",
            "updated kw",
            "--user-param-1",
            "val1",
            "--user-param-2",
            "val2",
        ]
    )
    assert result["user_param_1"] == "val1"


def test_keywords_update_dry_run():
    """dry_run=True appends --dry-run to argv."""
    runner = mock_runner(None)
    with patch("server.tools.keywords.get_runner", return_value=runner):
        keywords_update(id=99999, keyword="x", dry_run=True)
        argv = runner.run_json.call_args[0][0]
        assert "--dry-run" in argv


def test_keywords_update_accepts_zero_bids():
    """Zero bid values are provided updates and must be stringified for CLI."""
    runner = mock_runner(None)
    with patch("server.tools.keywords.get_runner", return_value=runner):
        keywords_update(id=99999, bid=0, context_bid=0)

    runner.run_json.assert_called_once_with(
        [
            "keywords",
            "update",
            "--id",
            "99999",
            "--bid",
            "0",
            "--context-bid",
            "0",
        ]
    )


def test_keywords_update_requires_changes():
    """Test that empty updates are rejected before CLI call."""
    runner = mock_runner(None)
    with patch("server.tools.keywords.get_runner", return_value=runner):
        result = keywords_update(id=99999)

    assert result["error"] == "missing_update_fields"
    runner.run_json.assert_not_called()


class TestKeywordsCrudOperations:
    """Tests for keyword CRUD operations (add, delete, suspend, resume)."""

    def test_keywords_add(self):
        """Test adding a keyword to an ad group (no --json in CLI 0.3.8)."""
        runner = mock_runner({"success": True})
        with patch("server.tools.keywords.get_runner", return_value=runner):
            result = keywords_add(
                ad_group_id=1,
                keyword="buy shoes",
                bid=10000000,
                context_bid=5000000,
                user_param_1="summer",
                user_param_2="sale",
            )
            assert result["success"] is True
            runner.run_json.assert_called_once_with(
                [
                    "keywords",
                    "add",
                    "--adgroup-id",
                    "1",
                    "--keyword",
                    "buy shoes",
                    "--bid",
                    "10000000",
                    "--context-bid",
                    "5000000",
                    "--user-param-1",
                    "summer",
                    "--user-param-2",
                    "sale",
                ]
            )

    def test_keywords_add_dry_run(self):
        """dry_run=True appends --dry-run to argv."""
        runner = mock_runner({"success": True})
        with patch("server.tools.keywords.get_runner", return_value=runner):
            keywords_add(ad_group_id=1, keyword="x", dry_run=True)
            argv = runner.run_json.call_args[0][0]
            assert "--dry-run" in argv

    def test_keywords_add_passes_from_file(self):
        """CLI 0.3.9: JSONL batch via --from-file."""
        runner = mock_runner({"AddResults": [{"Id": 1}, {"Id": 2}]})
        with patch("server.tools.keywords.get_runner", return_value=runner):
            keywords_add(from_file="/tmp/k.jsonl")
            argv = runner.run_json.call_args[0][0]
            assert "--from-file" in argv
            assert "/tmp/k.jsonl" in argv
            assert "--keyword" not in argv
            assert "--keywords-json" not in argv

    def test_keywords_add_passes_keywords_json(self):
        """CLI 0.3.9: inline JSON batch via --keywords-json."""
        runner = mock_runner({"AddResults": [{"Id": 1}]})
        payload = '[{"AdGroupId":1,"Keyword":"foo"}]'
        with patch("server.tools.keywords.get_runner", return_value=runner):
            keywords_add(keywords_json=payload)
            argv = runner.run_json.call_args[0][0]
            assert "--keywords-json" in argv
            assert payload in argv

    def test_keywords_add_batch_with_default_adgroup_id(self):
        """ad_group_id is forwarded as default in batch mode."""
        runner = mock_runner({"AddResults": []})
        with patch("server.tools.keywords.get_runner", return_value=runner):
            keywords_add(
                ad_group_id=42,
                keywords_json='[{"Keyword":"x"}]',
            )
            argv = runner.run_json.call_args[0][0]
            assert "--adgroup-id" in argv
            assert "42" in argv
            assert "--keywords-json" in argv

    def test_keywords_add_rejects_single_item_flags_in_batch(self):
        """Per-keyword flags are single-item-only; CLI rejects them in batch
        mode, so the tool returns single_item_flags_in_batch first (#170-20)."""
        runner = mock_runner({"AddResults": []})
        with patch("server.tools.keywords.get_runner", return_value=runner):
            result = keywords_add(
                ad_group_id=42,
                keywords_json='[{"Keyword":"x"}]',
                bid=15000000,
                priority="HIGH",
            )
        assert result["error"] == "single_item_flags_in_batch"
        assert "bid" in result["message"]
        runner.run_json.assert_not_called()

    def test_keywords_add_batch_without_single_item_flags_ok(self):
        """Batch mode without per-keyword flags still builds the call."""
        runner = mock_runner({"AddResults": []})
        with patch("server.tools.keywords.get_runner", return_value=runner):
            keywords_add(ad_group_id=42, keywords_json='[{"Keyword":"x"}]')
            argv = runner.run_json.call_args[0][0]
            assert "--keywords-json" in argv
            assert "--bid" not in argv

    def test_keywords_add_rejects_no_mode(self):
        """Neither keyword nor batch flag → missing_mode, runner not invoked."""
        runner = mock_runner({"AddResults": []})
        with patch("server.tools.keywords.get_runner", return_value=runner):
            result = keywords_add(ad_group_id=1)
        assert isinstance(result, dict)
        assert result["error"] == "missing_mode"
        runner.run_json.assert_not_called()

    def test_keywords_add_rejects_conflicting_modes(self):
        """keyword + from_file → conflicting_modes, runner not invoked."""
        runner = mock_runner({"AddResults": []})
        with patch("server.tools.keywords.get_runner", return_value=runner):
            result = keywords_add(keyword="x", from_file="/tmp/k.jsonl")
        assert isinstance(result, dict)
        assert result["error"] == "conflicting_modes"
        runner.run_json.assert_not_called()

    def test_keywords_add_rejects_all_three_modes(self):
        """All three modes set → conflicting_modes."""
        runner = mock_runner({"AddResults": []})
        with patch("server.tools.keywords.get_runner", return_value=runner):
            result = keywords_add(
                keyword="x",
                from_file="/tmp/k.jsonl",
                keywords_json="[{}]",
            )
        assert result["error"] == "conflicting_modes"
        runner.run_json.assert_not_called()

    def test_keywords_delete_success(self):
        """Test deleting keywords successfully."""
        runner = mock_runner({"success": True})
        with patch("server.tools.keywords.get_runner", return_value=runner):
            result = keywords_delete(ids="111,222")
            assert result["success"] is True
            runner.run_json.assert_has_calls(
                [
                    call(["keywords", "delete", "--id", "111"]),
                    call(["keywords", "delete", "--id", "222"]),
                ]
            )

    def test_keywords_delete_batch_limit(self):
        """Test batch limit validation for delete."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = keywords_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_keywords_suspend_success(self):
        """Test suspending keywords."""
        runner = mock_runner({"success": True})
        with patch("server.tools.keywords.get_runner", return_value=runner):
            result = keywords_suspend(ids="111,222")
            assert result["success"] is True
            runner.run_json.assert_has_calls(
                [
                    call(["keywords", "suspend", "--id", "111"]),
                    call(["keywords", "suspend", "--id", "222"]),
                ]
            )

    def test_keywords_suspend_batch_limit(self):
        """Test batch limit validation for suspend."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = keywords_suspend(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_keywords_resume_success(self):
        """Test resuming suspended keywords."""
        runner = mock_runner({"success": True})
        with patch("server.tools.keywords.get_runner", return_value=runner):
            result = keywords_resume(ids="111,222")
            assert result["success"] is True
            runner.run_json.assert_has_calls(
                [
                    call(["keywords", "resume", "--id", "111"]),
                    call(["keywords", "resume", "--id", "222"]),
                ]
            )

    def test_keywords_resume_batch_limit(self):
        """Test batch limit validation for resume."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = keywords_resume(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
