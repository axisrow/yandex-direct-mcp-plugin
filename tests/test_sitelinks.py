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
            "Name": "Quick Links",
            "Links": [
                {"Title": "About", "Href": "https://example.com/about"},
                {"Title": "Contact", "Href": "https://example.com/contact"},
            ],
        },
        {
            "Id": 2,
            "Name": "Products",
            "Links": [
                {"Title": "Product A", "Href": "https://example.com/a"},
                {"Title": "Product B", "Href": "https://example.com/b"},
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
            result = sitelinks_list(ids="1,2")
            assert len(result) == 2
            assert result[0]["Id"] == 1

    def test_list_sitelinks_batch_limit(self):
        """Test batch limit validation for list."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = sitelinks_list(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_list_sitelinks_empty_result(self):
        """Test empty response returns empty list."""
        with patch("server.tools.sitelinks.get_runner", return_value=_mock_runner([])):
            result = sitelinks_list(ids="1")
            assert result == []


class TestSitelinksAdd:
    """Tests for sitelinks_add tool."""

    def test_add_sitelinks_success(self):
        """Test adding sitelinks successfully."""
        mock_result = {"Id": 123, "Name": "New Sitelinks"}
        sitelinks_data = '{"Name": "New Sitelinks", "Links": [{"Title": "Link", "Href": "https://example.com"}]}'

        with patch(
            "server.tools.sitelinks.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = sitelinks_add(sitelinks_data=sitelinks_data)
            assert result["Id"] == 123
            assert result["Name"] == "New Sitelinks"


class TestSitelinksDelete:
    """Tests for sitelinks_delete tool."""

    def test_delete_sitelinks_success(self):
        """Test deleting sitelinks successfully."""
        mock_result = {"success": True}

        with patch(
            "server.tools.sitelinks.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = sitelinks_delete(ids="1,2")
            assert result["success"] is True

    def test_delete_sitelinks_batch_limit(self):
        """Test batch limit validation for delete."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = sitelinks_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
