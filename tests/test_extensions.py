"""Tests for ad extensions MCP tools."""

from unittest.mock import patch

import pytest

from server.tools.adextensions import (
    adextensions_list,
    adextensions_add,
    adextensions_delete,
)

from tests.helpers import mock_runner


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


class TestAdextensionsList:
    """Tests for adextensions_list tool."""

    def test_list_extensions_success(self, mock_extensions):
        """Test listing extensions successfully."""
        with patch(
            "server.tools.adextensions.get_runner",
            return_value=mock_runner(mock_extensions),
        ):
            result = adextensions_list(ids="1,2")
            assert len(result) == 2
            assert result[0]["Id"] == 1

    def test_list_extensions_no_ids(self, mock_extensions):
        """Test listing all extensions with no ids."""
        with patch(
            "server.tools.adextensions.get_runner",
            return_value=mock_runner(mock_extensions),
        ):
            result = adextensions_list()
            assert len(result) == 2

    def test_list_extensions_empty_ids_treated_as_missing_filter(self, mock_extensions):
        """Test empty ids behaves like no filter."""
        runner = mock_runner(mock_extensions)
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
        runner = mock_runner([])
        with patch(
            "server.tools.adextensions.get_runner",
            return_value=runner,
        ):
            adextensions_list(types="CALLOUT,SITELINK")
            call_args = runner.run_json.call_args[0][0]
            assert "--types" in call_args
            assert "CALLOUT,SITELINK" in call_args

    def test_list_extensions_trims_ids_and_types(self):
        """Test list filters are normalized before argv construction."""
        runner = mock_runner([])
        with patch("server.tools.adextensions.get_runner", return_value=runner):
            adextensions_list(ids=" 1,2 ", types=" CALLOUT,SITELINK ")

        runner.run_json.assert_called_once_with(
            [
                "adextensions",
                "get",
                "--format",
                "json",
                "--ids",
                "1,2",
                "--types",
                "CALLOUT,SITELINK",
            ]
        )

    def test_list_extensions_with_callout_field_names(self):
        """Test CalloutFieldNames are passed through 1:1 via the CLI flag."""
        runner = mock_runner([])
        with patch("server.tools.adextensions.get_runner", return_value=runner):
            adextensions_list(
                types="CALLOUT",
                fields="Id,Type,State,Status",
                callout_field_names="CalloutText",
            )

        runner.run_json.assert_called_once_with(
            [
                "adextensions",
                "get",
                "--format",
                "json",
                "--types",
                "CALLOUT",
                "--fields",
                "Id,Type,State,Status",
                "--callout-field-names",
                "CalloutText",
            ]
        )

    def test_list_extensions_empty_result(self):
        """Test empty response returns empty list."""
        with patch(
            "server.tools.adextensions.get_runner",
            return_value=mock_runner([]),
        ):
            result = adextensions_list(ids="999")
            assert result == []

    def test_list_extensions_batch_limit(self):
        """Test batch limit validation for adextensions_list."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = adextensions_list(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"


class TestAdextensionsAdd:
    """Tests for adextensions_add tool (CLI 0.3.8: callout-only typed)."""

    def test_add_callout_extension_success(self):
        """Test adding a callout extension successfully."""
        mock_result = {"Id": 123}
        runner = mock_runner(mock_result)

        with patch("server.tools.adextensions.get_runner", return_value=runner):
            result = adextensions_add(callout_text="Free shipping")
            assert result["Id"] == 123
            runner.run_json.assert_called_once_with(
                ["adextensions", "add", "--callout-text", "Free shipping"]
            )

    def test_add_callout_extension_dry_run(self):
        runner = mock_runner({"_dry_run": True})
        with patch("server.tools.adextensions.get_runner", return_value=runner):
            adextensions_add(callout_text="X", dry_run=True)
            assert "--dry-run" in runner.run_json.call_args[0][0]


class TestAdextensionsDelete:
    """Tests for adextensions_delete tool."""

    def test_delete_extensions_success(self):
        """Test deleting extensions successfully."""
        mock_result = {"success": True}

        with patch(
            "server.tools.adextensions.get_runner",
            return_value=mock_runner(mock_result),
        ):
            result = adextensions_delete(ids="1")
            assert result["success"] is True

    def test_delete_extensions_rejects_empty_ids(self):
        """Test deleting extensions rejects empty ids."""
        with patch(
            "server.tools.adextensions.get_runner",
            return_value=mock_runner({"success": True}),
        ):
            result = adextensions_delete(ids="   ")
            assert result["error"] == "missing_ids"
