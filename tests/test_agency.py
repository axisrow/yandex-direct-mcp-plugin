"""Tests for agency MCP tools."""

from unittest.mock import MagicMock, patch


from server.tools.agency import (
    agency_clients_list,
    agency_clients_add,
    agency_clients_add_passport_organization,
    agency_clients_add_passport_organization_member,
    agency_clients_delete,
    agency_clients_update,
)


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
            result = agency_clients_list(logins="login1,login2")
            runner.run_json.assert_called_once()
            call_args = runner.run_json.call_args[0][0]
            assert "--logins" in call_args
            assert "login1,login2" in call_args
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
            agency_clients_list(logins=" login1,login2 ")

        runner.run_json.assert_called_once_with(
            ["agencyclients", "get", "--format", "json", "--logins", "login1,login2"]
        )


class TestAgencyClientsAdd:
    """Test scenarios for agency_clients_add (CLI 0.3.8 typed flags)."""

    def test_add_client_typed(self):
        """Test adding a client with typed flags."""
        mock_result = {"Login": "new_client"}
        runner = _mock_runner(mock_result)
        with patch("server.tools.agency.get_runner", return_value=runner):
            result = agency_clients_add(
                login="new_client",
                first_name="Alice",
                last_name="Johnson",
                currency="RUB",
                notification_email="alice@example.com",
                send_account_news=True,
                send_warnings=False,
            )
            assert result == mock_result
            runner.run_json.assert_called_once_with(
                [
                    "agencyclients",
                    "add",
                    "--login",
                    "new_client",
                    "--first-name",
                    "Alice",
                    "--last-name",
                    "Johnson",
                    "--currency",
                    "RUB",
                    "--notification-email",
                    "alice@example.com",
                    "--send-account-news",
                    "--no-send-warnings",
                ]
            )

    def test_add_client_dry_run(self):
        runner = _mock_runner({"_dry_run": True})
        with patch("server.tools.agency.get_runner", return_value=runner):
            agency_clients_add(
                login="c", first_name="F", last_name="L", currency="RUB", dry_run=True
            )
            assert "--dry-run" in runner.run_json.call_args[0][0]


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
    """Test scenarios for agency_clients_update (CLI 0.3.8)."""

    def test_update_client(self):
        runner = _mock_runner({"success": True})
        with patch("server.tools.agency.get_runner", return_value=runner):
            result = agency_clients_update(
                client_id=123,
                notification_email="test@example.com",
                clear_grants=True,
            )

        assert result["success"] is True
        runner.run_json.assert_called_once_with(
            [
                "agencyclients",
                "update",
                "--client-id",
                "123",
                "--notification-email",
                "test@example.com",
                "--clear-grants",
            ]
        )

    def test_update_client_grants_list(self):
        runner = _mock_runner({"success": True})
        with patch("server.tools.agency.get_runner", return_value=runner):
            agency_clients_update(
                client_id=123,
                grants=["CampaignManagement=YES", "ReportManagement=NO"],
            )
        argv = runner.run_json.call_args[0][0]
        # Each grant should be a separate --grant argument
        assert argv.count("--grant") == 2

    def test_update_client_conflicting_grants(self):
        result = agency_clients_update(
            client_id=123,
            grants=["X=YES"],
            clear_grants=True,
        )
        assert result["error"] == "conflicting_grants"

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
