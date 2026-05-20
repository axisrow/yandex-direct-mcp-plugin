"""Tests for keyword research MCP tools (CLI 0.3.8 — --region-ids required)."""

from unittest.mock import MagicMock, patch


from server.tools.research import keywords_has_volume, keywords_deduplicate


def _mock_runner(return_value):
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestKeywordsHasVolume:
    """Tests for keywords_has_volume tool."""

    def test_keywords_has_volume_basic(self):
        mock_result = {"keyword1": True, "keyword2": False}
        with patch(
            "server.tools.research.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = keywords_has_volume(keywords="keyword1,keyword2", region_ids="0")
            assert result["keyword1"] is True

    def test_keywords_has_volume_argv(self):
        runner = MagicMock()
        runner.run_json.return_value = {"k1": True}
        with patch("server.tools.research.get_runner", return_value=runner):
            keywords_has_volume(keywords="k1,k2", region_ids="213")
        runner.run_json.assert_called_once_with(
            [
                "keywordsresearch",
                "has-search-volume",
                "--keywords",
                "k1,k2",
                "--region-ids",
                "213",
                "--format",
                "json",
            ]
        )

    def test_keywords_has_volume_requires_keywords(self):
        result = keywords_has_volume(keywords="  ", region_ids="0")
        assert result["error"] == "missing_keywords"

    def test_keywords_has_volume_requires_region_ids(self):
        result = keywords_has_volume(keywords="k", region_ids="  ")
        assert result["error"] == "missing_region_ids"


class TestKeywordsDeduplicate:
    """Tests for keywords_deduplicate tool."""

    def test_keywords_deduplicate_basic(self):
        mock_result = {
            "original": ["keyword1", "keyword2", "keyword1"],
            "deduplicated": ["keyword1", "keyword2"],
        }
        with patch(
            "server.tools.research.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = keywords_deduplicate(keywords="keyword1,keyword2,keyword1")
            assert result["deduplicated"] == ["keyword1", "keyword2"]

    def test_keywords_deduplicate_argv(self):
        runner = MagicMock()
        runner.run_json.return_value = {"original": [], "deduplicated": []}
        with patch("server.tools.research.get_runner", return_value=runner):
            keywords_deduplicate(keywords="k1,k2")
        runner.run_json.assert_called_once_with(
            [
                "keywordsresearch",
                "deduplicate",
                "--keywords",
                "k1,k2",
                "--format",
                "json",
            ]
        )
