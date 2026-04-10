"""Tests for sitelinks MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.sitelinks import sitelinks_list, sitelinks_add, sitelinks_delete


@pytest.fixture(autouse=True)
def setup_token_getter():
    """Configure a mock token getter for all tests."""
    server.tools.set_token_getter(lambda: "test-token")


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


class TestSitelinksAdd:
    """Tests for sitelinks_add tool."""

    def test_add_sitelinks_success(self):
        """Test adding sitelinks successfully."""
        mock_result = {"Id": 123}
        links = '[{"Title":"About","Href":"https://example.com/about"}]'
        runner = MagicMock()
        runner.run_json.return_value = mock_result

        with patch(
            "server.tools.sitelinks.get_runner",
            return_value=runner,
        ):
            result = sitelinks_add(links=links)
            assert result["Id"] == 123
            call_args = runner.run_json.call_args[0][0]
            assert "--links" in call_args


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
