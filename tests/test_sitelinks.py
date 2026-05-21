"""Tests for sitelinks MCP tools."""

import json
from unittest.mock import MagicMock, patch

import pytest

from server.tools.sitelinks import sitelinks_list, sitelinks_add, sitelinks_delete


@pytest.fixture
def mock_sitelinks():
    """Sample sitelinks data."""
    return [
        {
            "Id": 1,
            "Sitelinks": [
                {"Title": "About", "Href": "https://example.com/about"},
                {"Title": "Contact", "Href": "https://example.com/contact"},
            ],
        },
    ]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestSitelinksList:
    """Tests for sitelinks_list tool."""

    def test_list_sitelinks_success(self, mock_sitelinks):
        """Test listing sitelinks successfully."""
        with patch(
            "server.tools.sitelinks.get_runner",
            return_value=_mock_runner(mock_sitelinks),
        ):
            result = sitelinks_list(ids="1")
            assert len(result) == 1
            assert result[0]["Id"] == 1

    def test_list_sitelinks_no_ids(self, mock_sitelinks):
        """Test listing sitelinks with no IDs returns all."""
        with patch(
            "server.tools.sitelinks.get_runner",
            return_value=_mock_runner(mock_sitelinks),
        ):
            result = sitelinks_list()
            assert len(result) == 1

    def test_list_sitelinks_batch_limit(self):
        """Test batch limit validation for list."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = sitelinks_list(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_list_sitelinks_trims_ids_before_cli(self, mock_sitelinks):
        """Test sitelink IDs are normalized before argv construction."""
        runner = MagicMock()
        runner.run_json.return_value = mock_sitelinks
        with patch("server.tools.sitelinks.get_runner", return_value=runner):
            sitelinks_list(ids=" 1 ")

        runner.run_json.assert_called_once_with(
            ["sitelinks", "get", "--format", "json", "--ids", "1"]
        )


class TestSitelinksAdd:
    """Tests for sitelinks_add tool (CLI 0.3.10: three input modes)."""

    def test_add_sitelinks_success(self):
        """Each sitelink spec becomes a separate --sitelink argument."""
        mock_result = {"Id": 123}
        runner = MagicMock()
        runner.run_json.return_value = mock_result

        with patch("server.tools.sitelinks.get_runner", return_value=runner):
            result = sitelinks_add(
                sitelinks=[
                    "About|https://example.com/about|Learn more",
                    "Pricing|https://example.com/pricing",
                ]
            )
            assert result["Id"] == 123
            runner.run_json.assert_called_once_with(
                [
                    "sitelinks",
                    "add",
                    "--sitelink",
                    "About|https://example.com/about|Learn more",
                    "--sitelink",
                    "Pricing|https://example.com/pricing",
                ]
            )

    def test_add_sitelinks_items_serialized_to_camelcase_json(self):
        runner = MagicMock()
        runner.run_json.return_value = {"Id": 456}
        with patch("server.tools.sitelinks.get_runner", return_value=runner):
            sitelinks_add(
                items=[
                    {
                        "title": "Главная",
                        "href": "https://example.com/?utm=cid|{cid}",
                        "description": "На главную",
                    },
                    {"title": "Прайс", "href": "https://example.com/p"},
                ]
            )

        called_args = runner.run_json.call_args[0][0]
        assert called_args[0:2] == ["sitelinks", "add"]
        assert "--sitelink-json" in called_args
        json_idx = called_args.index("--sitelink-json")
        payload = json.loads(called_args[json_idx + 1])
        assert payload == [
            {
                "Title": "Главная",
                "Href": "https://example.com/?utm=cid|{cid}",
                "Description": "На главную",
            },
            {"Title": "Прайс", "Href": "https://example.com/p"},
        ]

    def test_add_sitelinks_items_unknown_field(self):
        result = sitelinks_add(items=[{"title": "X", "url": "https://x"}])
        assert result["error"] == "unknown_field"
        assert "url" in result["message"]

    def test_add_sitelinks_from_file(self):
        runner = MagicMock()
        runner.run_json.return_value = {"Id": 789}
        with patch("server.tools.sitelinks.get_runner", return_value=runner):
            sitelinks_add(from_file="/tmp/sitelinks.jsonl")

        runner.run_json.assert_called_once_with(
            [
                "sitelinks",
                "add",
                "--sitelinks-from-file",
                "/tmp/sitelinks.jsonl",
            ]
        )

    def test_add_sitelinks_missing_mode(self):
        result = sitelinks_add()
        assert result["error"] == "missing_mode"

    def test_add_sitelinks_conflicting_modes(self):
        result = sitelinks_add(
            sitelinks=["A|https://a"],
            items=[{"title": "B", "href": "https://b"}],
        )
        assert result["error"] == "conflicting_modes"

    def test_add_sitelinks_dry_run(self):
        runner = MagicMock()
        runner.run_json.return_value = {"_dry_run": True}
        with patch("server.tools.sitelinks.get_runner", return_value=runner):
            sitelinks_add(sitelinks=["A|https://a"], dry_run=True)
            assert "--dry-run" in runner.run_json.call_args[0][0]

    def test_add_sitelinks_empty_list_rejected(self):
        """sitelinks=[] is a chosen mode with no data — must fail before CLI call."""
        result = sitelinks_add(sitelinks=[])
        assert result["error"] == "empty_mode"

    def test_add_sitelinks_empty_items_rejected(self):
        result = sitelinks_add(items=[])
        assert result["error"] == "empty_mode"

    def test_add_sitelinks_empty_from_file_rejected(self):
        result = sitelinks_add(from_file="")
        assert result["error"] == "empty_mode"

    def test_add_sitelinks_empty_plus_nonempty_is_conflict(self):
        """sitelinks=[] + items=[...] must NOT silently drop items.

        Regression for the bug where mode detection used truthiness while
        dispatch used `is not None` — the empty sitelinks would take the
        dispatch branch and produce a CLI call with no --sitelink args.
        """
        result = sitelinks_add(
            sitelinks=[],
            items=[{"title": "X", "href": "https://x"}],
        )
        assert result["error"] == "conflicting_modes"

    def test_add_sitelinks_empty_items_plus_from_file_is_conflict(self):
        result = sitelinks_add(items=[], from_file="/tmp/x.jsonl")
        assert result["error"] == "conflicting_modes"


class TestSitelinksDelete:
    """Tests for sitelinks_delete tool."""

    def test_delete_sitelinks_success(self):
        """Test deleting sitelinks successfully."""
        mock_result = {"success": True}

        with patch(
            "server.tools.sitelinks.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = sitelinks_delete(ids="1")
            assert result["success"] is True

    def test_delete_sitelinks_batch_limit(self):
        """Test batch limit validation for delete."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = sitelinks_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
