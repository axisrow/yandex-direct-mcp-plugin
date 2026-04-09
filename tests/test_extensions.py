"""Tests for ad extensions MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.adextensions import (
    adextensions_list,
    adextensions_add,
    adextensions_delete,
)


@pytest.fixture(autouse=True)
def setup_token_getter():
    """Configure a mock token getter for all tests."""
    server.tools.set_token_getter(lambda: "test-token")


@pytest.fixture
def mock_extensions():
    """Sample ad extensions data."""
    return [
        {
            "Id": 1,
            "Type": "Call",
            "PhoneNumber": "+79991234567",
        },
        {
            "Id": 2,
            "Type": "Message",
            "MessengerType": "Telegram",
        },
    ]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestAdextensionsList:
    """Tests for adextensions_list tool."""

    def test_list_extensions_success(self, mock_extensions):
        """Test listing extensions successfully."""
        with patch(
            "server.tools.adextensions.get_runner",
            return_value=_mock_runner(mock_extensions),
        ):
            result = adextensions_list(ids="1,2")
            assert len(result) == 2
            assert result[0]["Id"] == 1

    def test_list_extensions_empty_ids(self, mock_extensions):
        """Test listing all extensions with empty ids string."""
        with patch(
            "server.tools.adextensions.get_runner",
            return_value=_mock_runner(mock_extensions),
        ):
            result = adextensions_list(ids="")
            assert len(result) == 2

    def test_list_extensions_empty_result(self):
        """Test empty response returns empty list."""
        with patch(
            "server.tools.adextensions.get_runner", return_value=_mock_runner([])
        ):
            result = adextensions_list(ids="999")
            assert result == []


class TestAdextensionsAdd:
    """Tests for adextensions_add tool."""

    def test_add_extension_success(self):
        """Test adding extension successfully."""
        mock_result = {"Id": 123, "Type": "Call"}
        extension_data = '{"PhoneNumber": "+79991112233"}'

        with patch(
            "server.tools.adextensions.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = adextensions_add(
                extension_type="Call", extension_data=extension_data
            )
            assert result["Id"] == 123
            assert result["Type"] == "Call"

    def test_add_extension_invalid_type(self):
        """Test adding extension with invalid type."""
        # This test verifies the tool accepts any type string
        # Validation will happen at the CLI level
        extension_data = '{"SomeField": "value"}'
        mock_result = {"Id": 124, "Type": "UnknownType"}

        with patch(
            "server.tools.adextensions.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = adextensions_add(
                extension_type="UnknownType", extension_data=extension_data
            )
            assert result["Id"] == 124


class TestAdextensionsDelete:
    """Tests for adextensions_delete tool."""

    def test_delete_extensions_success(self):
        """Test deleting extensions successfully."""
        mock_result = {"success": True}

        with patch(
            "server.tools.adextensions.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = adextensions_delete(ids="1,2")
            assert result["success"] is True
