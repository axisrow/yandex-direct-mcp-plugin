"""Tests for vCards MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.vcards import vcards_list, vcards_add, vcards_delete


@pytest.fixture(autouse=True)
def setup_token_getter():
    """Configure a mock token getter for all tests."""
    server.tools.set_token_getter(lambda: "test-token")


@pytest.fixture
def mock_vcards():
    """Sample vCard data."""
    return [
        {
            "Id": 1,
            "CampaignName": "Campaign 1",
            "CompanyAddress": "123 Main St",
            "ContactPhone": "+79991234567",
        },
        {
            "Id": 2,
            "CampaignName": "Campaign 2",
            "CompanyAddress": "456 Oak Ave",
            "ContactPhone": "+79997654321",
        },
    ]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestVcardsList:
    """Tests for vcards_list tool."""

    def test_list_vcards_success(self, mock_vcards):
        """Test listing vCards successfully."""
        with patch(
            "server.tools.vcards.get_runner",
            return_value=_mock_runner(mock_vcards),
        ):
            result = vcards_list(ids="1,2")
            assert len(result) == 2
            assert result[0]["Id"] == 1

    def test_list_vcards_batch_limit(self):
        """Test batch limit validation for list."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = vcards_list(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_list_vcards_empty_result(self):
        """Test empty response returns empty list."""
        with patch("server.tools.vcards.get_runner", return_value=_mock_runner([])):
            result = vcards_list(ids="1")
            assert result == []


class TestVcardsAdd:
    """Tests for vcards_add tool."""

    def test_add_vcard_success(self):
        """Test adding vCard successfully."""
        mock_result = {"Id": 123, "CompanyAddress": "789 Pine Rd"}
        vcard_data = '{"CompanyAddress": "789 Pine Rd", "ContactPhone": "+79991112233"}'

        with patch(
            "server.tools.vcards.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = vcards_add(vcard_data=vcard_data)
            assert result["Id"] == 123
            assert result["CompanyAddress"] == "789 Pine Rd"


class TestVcardsDelete:
    """Tests for vcards_delete tool."""

    def test_delete_vcards_success(self):
        """Test deleting vCards successfully."""
        mock_result = {"success": True}

        with patch(
            "server.tools.vcards.get_runner", return_value=_mock_runner(mock_result)
        ):
            result = vcards_delete(ids="1,2")
            assert result["success"] is True

    def test_delete_vcards_batch_limit(self):
        """Test batch limit validation for delete."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = vcards_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
