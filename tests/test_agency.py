"""Tests for agency MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.agency import (
    agency_clients_list,
    agency_clients_add,
    agency_clients_add_passport_organization,
    agency_clients_add_passport_organization_member,
    agency_clients_delete,
    agency_clients_update,
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

    def test_list_agency_clients_with_ids(self):
        """Test listing agency clients filtered by IDs."""
        mock_result = {"Clients": [{"Login": "client1", "FirstName": "John"}]}
        runner = MagicMock()
        runner.run_json.return_value = mock_result

        with patch("server.tools.agency.get_runner", return_value=runner):
            result = agency_clients_list(ids="123,456")
            runner.run_json.assert_called_once()
            call_args = runner.run_json.call_args[0][0]
            assert "--ids" in call_args
            assert "123,456" in call_args
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

    def test_list_agency_clients_trims_ids_before_cli(self):
        """Test client IDs are normalized before argv construction."""
        runner = MagicMock()
        runner.run_json.return_value = {"Clients": []}
        with patch("server.tools.agency.get_runner", return_value=runner):
            agency_clients_list(ids=" 123,456 ")

        runner.run_json.assert_called_once_with(
            ["agencyclients", "get", "--format", "json", "--ids", "123,456"]
        )


class TestAgencyClientsAdd:
    """Test scenarios for agency_clients_add."""

    def test_add_client_to_agency(self):
        """Test adding a client to an agency."""
        mock_result = {
            "Login": "new_client",
            "FirstName": "Alice",
            "LastName": "Johnson",
        }
        runner = MagicMock()
        runner.run_json.return_value = mock_result
        with patch("server.tools.agency.get_runner", return_value=runner):
            client_json = '{"FirstName": "Alice", "LastName": "Johnson"}'
            result = agency_clients_add(client_json=client_json)
            assert result == mock_result
            call_args = runner.run_json.call_args[0][0]
            assert "--json" in call_args

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
            client_json = '{"Grants": ["CampaignManagement"]}'
            result = agency_clients_add(client_json=client_json)
            assert result == mock_result

    def test_add_client_argv_composition(self):
        """Test add passes correct argv to CLI."""
        runner = MagicMock()
        runner.run_json.return_value = {"Login": "client"}
        with patch("server.tools.agency.get_runner", return_value=runner):
            agency_clients_add(client_json='{"Login":"test"}')

        runner.run_json.assert_called_once_with(
            ["agencyclients", "add", "--json", '{"Login":"test"}']
        )


class TestAgencyClientsDelete:
    """Test scenarios for agency_clients_delete."""

    def test_delete_client_from_agency(self):
        """Test removing a client from an agency."""
        mock_result = {"Success": True}
        runner = MagicMock()
        runner.run_json.return_value = mock_result
        with patch("server.tools.agency.get_runner", return_value=runner):
            result = agency_clients_delete(id=123)
            assert result == mock_result
            call_args = runner.run_json.call_args[0][0]
            assert "--id" in call_args
            assert "123" in call_args


class TestAgencyClientsUpdate:
    """Test scenarios for agency_clients_update."""

    def test_update_client(self):
        runner = MagicMock()
        runner.run_json.return_value = {"success": True}
        with patch("server.tools.agency.get_runner", return_value=runner):
            result = agency_clients_update(
                client_id=123,
                email="test@example.com",
                clear_grants=True,
            )

        assert result["success"] is True
        runner.run_json.assert_called_once_with(
            [
                "agencyclients",
                "update",
                "--client-id",
                "123",
                "--email",
                "test@example.com",
                "--clear-grants",
            ]
        )

    def test_update_client_requires_changes(self):
        result = agency_clients_update(client_id=123)
        assert result["error"] == "missing_update_fields"


class TestAgencyClientsPassportOrganization:
    """Test passport organization helper wrappers."""

    def test_add_passport_organization(self):
        runner = MagicMock()
        runner.run_json.return_value = {"success": True}
        with patch("server.tools.agency.get_runner", return_value=runner):
            result = agency_clients_add_passport_organization(
                name="Org",
                currency="RUB",
                send_account_news=True,
                send_warnings=False,
            )

        assert result["success"] is True
        runner.run_json.assert_called_once_with(
            [
                "agencyclients",
                "add-passport-organization",
                "--name",
                "Org",
                "--currency",
                "RUB",
                "--send-account-news",
                "--no-send-warnings",
            ]
        )

    def test_add_passport_organization_member(self):
        runner = MagicMock()
        runner.run_json.return_value = {"success": True}
        with patch("server.tools.agency.get_runner", return_value=runner):
            result = agency_clients_add_passport_organization_member(
                passport_organization_login="org-login",
                role="ADMIN",
                invite_email="member@example.com",
            )

        assert result["success"] is True
        runner.run_json.assert_called_once_with(
            [
                "agencyclients",
                "add-passport-organization-member",
                "--passport-organization-login",
                "org-login",
                "--role",
                "ADMIN",
                "--invite-email",
                "member@example.com",
            ]
        )
