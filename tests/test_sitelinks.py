"""Tests for sitelinks MCP tools."""

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
    """Tests for sitelinks_add tool (CLI 0.3.8: repeatable --sitelink)."""

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

    def test_add_sitelinks_empty_list(self):
        result = sitelinks_add(sitelinks=[])
        assert result["error"] == "missing_sitelinks"

    def test_add_sitelinks_dry_run(self):
        runner = MagicMock()
        runner.run_json.return_value = {"_dry_run": True}
        with patch("server.tools.sitelinks.get_runner", return_value=runner):
            sitelinks_add(sitelinks=["A|https://a"], dry_run=True)
            assert "--dry-run" in runner.run_json.call_args[0][0]


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
