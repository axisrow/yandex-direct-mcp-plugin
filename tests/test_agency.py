"""Tests for agency MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.agency import (
    agency_clients_list,
    agency_clients_add,
    agency_clients_delete,
)


@pytest.fixture(autouse=True)
def setup_token_getter():
    """Configure a mock token getter for all tests."""
    server.tools.set_token_getter(lambda: "test-token")


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestAgencyClientsList:
    """Test scenarios for agency_clients_list."""

    def test_list_all_agency_clients(self):
        """Test listing all agency clients."""
        mock_result = {
            "Clients": [
                {"Login": "client1", "FirstName": "John"},
                {"Login": "client2", "FirstName": "Jane"},
            ]
        }
        with patch(
            "server.tools.agency.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = agency_clients_list()
            assert result == mock_result

    def test_list_agency_clients_with_login(self):
        """Test listing agency clients filtered by login."""
        mock_result = {"Clients": [{"Login": "client1", "FirstName": "John"}]}
        runner = MagicMock()
        runner.run_json.return_value = mock_result

        with patch("server.tools.agency.get_runner", return_value=runner):
            result = agency_clients_list(login="agency1")
            runner.run_json.assert_called_once()
            call_args = runner.run_json.call_args[0][0]
            assert "--login" in call_args
            assert "agency1" in call_args
            assert result == mock_result

    def test_list_empty_agency_clients(self):
        """Test with no agency clients."""
        mock_result = {"Clients": []}
        with patch(
            "server.tools.agency.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = agency_clients_list()
            assert result == mock_result


class TestAgencyClientsAdd:
    """Test scenarios for agency_clients_add."""

    def test_add_client_to_agency(self):
        """Test adding a client to an agency."""
        mock_result = {
            "Login": "new_client",
            "FirstName": "Alice",
            "LastName": "Johnson",
        }
        with patch(
            "server.tools.agency.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            client_info = '{"FirstName": "Alice", "LastName": "Johnson"}'
            result = agency_clients_add(login="agency1", client_info=client_info)
            assert result == mock_result

    def test_add_client_with_grants(self):
        """Test adding client with specific grants."""
        mock_result = {
            "Login": "new_client",
            "Grants": ["CampaignManagement", "ReportManagement"],
        }
        with patch(
            "server.tools.agency.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            client_info = '{"Grants": ["CampaignManagement", "ReportManagement"]}'
            result = agency_clients_add(login="agency1", client_info=client_info)
            assert result == mock_result

    def test_add_client_minimal_info(self):
        """Test adding client with minimal information."""
        mock_result = {"Login": "new_client"}
        with patch(
            "server.tools.agency.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            client_info = "{}"
            result = agency_clients_add(login="agency1", client_info=client_info)
            assert result == mock_result


class TestAgencyClientsDelete:
    """Test scenarios for agency_clients_delete."""

    def test_delete_client_from_agency(self):
        """Test removing a client from an agency."""
        mock_result = {"Success": True, "Login": "client1"}
        with patch(
            "server.tools.agency.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = agency_clients_delete(login="agency1", client_login="client1")
            assert result == mock_result

    def test_delete_client_with_result(self):
        """Test deletion with detailed result."""
        mock_result = {
            "Success": True,
            "Login": "client1",
            "AgencyLogin": "agency1",
        }
        with patch(
            "server.tools.agency.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = agency_clients_delete(login="agency1", client_login="client1")
            assert result == mock_result
            assert result["Success"] is True
