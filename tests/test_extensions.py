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

    def test_list_extensions_no_ids(self, mock_extensions):
        """Test listing all extensions with no ids."""
        with patch(
            "server.tools.adextensions.get_runner",
            return_value=_mock_runner(mock_extensions),
        ):
            result = adextensions_list()
            assert len(result) == 2

    def test_list_extensions_empty_ids_treated_as_missing_filter(self, mock_extensions):
        """Test empty ids behaves like no filter."""
        runner = MagicMock()
        runner.run_json.return_value = mock_extensions
        with patch(
            "server.tools.adextensions.get_runner",
            return_value=runner,
        ):
            result = adextensions_list(ids="   ")
            assert len(result) == 2
            call_args = runner.run_json.call_args[0][0]
            assert "--ids" not in call_args

    def test_list_extensions_with_types(self):
        """Test listing extensions filtered by types."""
        runner = MagicMock()
        runner.run_json.return_value = []
        with patch(
            "server.tools.adextensions.get_runner",
            return_value=runner,
        ):
            adextensions_list(types="CALLOUT,SITELINK")
            call_args = runner.run_json.call_args[0][0]
            assert "--types" in call_args
            assert "CALLOUT,SITELINK" in call_args

    def test_list_extensions_empty_result(self):
        """Test empty response returns empty list."""
        with patch(
            "server.tools.adextensions.get_runner",
            return_value=_mock_runner([]),
        ):
            result = adextensions_list(ids="999")
            assert result == []


class TestAdextensionsAdd:
    """Tests for adextensions_add tool."""

    def test_add_extension_success(self):
        """Test adding extension successfully."""
        mock_result = {"Id": 123, "Type": "Call"}
        extra_json = '{"PhoneNumber": "+79991112233"}'
        runner = MagicMock()
        runner.run_json.return_value = mock_result

        with patch(
            "server.tools.adextensions.get_runner",
            return_value=runner,
        ):
            result = adextensions_add(extension_type="Call", extra_json=extra_json)
            assert result["Id"] == 123
            assert result["Type"] == "Call"
            call_args = runner.run_json.call_args[0][0]
            assert "--type" in call_args
            assert "--json" in call_args

    def test_add_extension_invalid_type(self):
        """Test adding extension with non-standard type."""
        extra_json = '{"SomeField": "value"}'
        mock_result = {"Id": 124, "Type": "UnknownType"}

        with patch(
            "server.tools.adextensions.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = adextensions_add(
                extension_type="UnknownType", extra_json=extra_json
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
            result = adextensions_delete(ids="1")
            assert result["success"] is True

    def test_delete_extensions_rejects_empty_ids(self):
        """Test deleting extensions rejects empty ids."""
        with patch(
            "server.tools.adextensions.get_runner",
            return_value=_mock_runner({"success": True}),
        ):
            result = adextensions_delete(ids="   ")
            assert result["error"] == "missing_ids"
