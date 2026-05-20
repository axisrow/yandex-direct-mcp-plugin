"""Tests for clients MCP tools."""

from unittest.mock import MagicMock, patch


from server.tools.clients import clients_get, clients_update


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestClientsGet:
    """Test scenarios for clients_get."""

    def test_get_all_clients(self):
        """Test getting all clients."""
        mock_result = {
            "Clients": [
                {"Login": "client1", "FirstName": "John"},
                {"Login": "client2", "FirstName": "Jane"},
            ]
        }
        with patch(
            "server.tools.clients.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = clients_get()
            assert result == mock_result

    def test_get_client_by_ids(self):
        """Test getting specific client by IDs."""
        mock_result = {"Clients": [{"Login": "client1", "FirstName": "John"}]}
        runner = MagicMock()
        runner.run_json.return_value = mock_result

        with patch("server.tools.clients.get_runner", return_value=runner):
            result = clients_get(ids="123")
            runner.run_json.assert_called_once()
            call_args = runner.run_json.call_args[0][0]
            assert "--ids" in call_args
            assert "123" in call_args
            assert result == mock_result

    def test_get_client_trims_ids(self):
        """Test client IDs are normalized before argv construction."""
        runner = MagicMock()
        runner.run_json.return_value = {"Clients": []}

        with patch("server.tools.clients.get_runner", return_value=runner):
            clients_get(ids=" 123 ")

        runner.run_json.assert_called_once_with(
            ["clients", "get", "--format", "json", "--ids", "123"]
        )

    def test_get_empty_clients(self):
        """Test with no clients."""
        mock_result = {"Clients": []}
        with patch(
            "server.tools.clients.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = clients_get()
            assert result == mock_result


class TestClientsUpdate:
    """Test scenarios for clients_update (CLI 0.3.8 typed flags)."""

    def test_update_client(self):
        """Test updating client information."""
        mock_result = {"Login": "client1"}
        runner = MagicMock()
        runner.run_json.return_value = mock_result
        with patch("server.tools.clients.get_runner", return_value=runner):
            result = clients_update(
                client_info="John Smith",
                phone="+71234567890",
                notification_email="js@example.com",
            )
            assert result == mock_result
            runner.run_json.assert_called_once_with(
                [
                    "clients",
                    "update",
                    "--client-info",
                    "John Smith",
                    "--phone",
                    "+71234567890",
                    "--notification-email",
                    "js@example.com",
                ]
            )

    def test_update_client_settings_repeated(self):
        """List parameters produce repeated CLI flags."""
        runner = MagicMock()
        runner.run_json.return_value = {"Login": "client1"}
        with patch("server.tools.clients.get_runner", return_value=runner):
            clients_update(
                settings=["AccountNews=YES", "Warnings=NO"],
                email_subscriptions=["Promo=YES"],
            )
        argv = runner.run_json.call_args[0][0]
        assert argv.count("--setting") == 2
        assert argv.count("--email-subscription") == 1

    def test_update_client_requires_changes(self):
        result = clients_update()
        assert result["error"] == "missing_update_fields"

    def test_update_client_dry_run(self):
        runner = MagicMock()
        runner.run_json.return_value = {"_dry_run": True}
        with patch("server.tools.clients.get_runner", return_value=runner):
            clients_update(phone="+1", dry_run=True)
            assert "--dry-run" in runner.run_json.call_args[0][0]

    def test_get_client_ignores_blank_ids(self):
        """Test blank ids behave like no filter."""
        runner = MagicMock()
        runner.run_json.return_value = {"Clients": []}
        with patch("server.tools.clients.get_runner", return_value=runner):
            clients_get(ids="   ")
            call_args = runner.run_json.call_args[0][0]
            assert "--ids" not in call_args
