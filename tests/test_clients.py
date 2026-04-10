"""Tests for clients MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.clients import clients_get, clients_update


@pytest.fixture(autouse=True)
def setup_token_getter():
    """Configure a mock token getter for all tests."""
    server.tools.set_token_getter(lambda: "test-token")


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
    """Test scenarios for clients_update."""

    def test_update_client(self):
        """Test updating client information."""
        mock_result = {
            "Login": "client1",
            "FirstName": "John",
            "LastName": "Smith",
        }
        runner = MagicMock()
        runner.run_json.return_value = mock_result
        with patch("server.tools.clients.get_runner", return_value=runner):
            extra_json = '{"FirstName": "John", "LastName": "Smith"}'
            result = clients_update(client_id="123", extra_json=extra_json)
            assert result == mock_result
            call_args = runner.run_json.call_args[0][0]
            assert "--client-id" in call_args
            assert "123" in call_args
            assert "--json" in call_args

    def test_update_client_with_grants(self):
        """Test updating client with grants."""
        mock_result = {
            "Login": "client1",
            "Grants": ["CampaignManagement"],
        }
        with patch(
            "server.tools.clients.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            extra_json = '{"Grants": ["CampaignManagement"]}'
            result = clients_update(client_id="123", extra_json=extra_json)
            assert result == mock_result

    def test_update_client_argv_composition(self):
        """Test update passes correct argv to CLI."""
        runner = MagicMock()
        runner.run_json.return_value = {"Login": "client1"}
        with patch("server.tools.clients.get_runner", return_value=runner):
            clients_update(client_id="123", extra_json='{"FirstName":"Bob"}')

        runner.run_json.assert_called_once_with(
            [
                "clients",
                "update",
                "--client-id",
                "123",
                "--json",
                '{"FirstName":"Bob"}',
            ]
        )

    def test_get_client_ignores_blank_ids(self):
        """Test blank ids behave like no filter."""
        runner = MagicMock()
        runner.run_json.return_value = {"Clients": []}
        with patch("server.tools.clients.get_runner", return_value=runner):
            clients_get(ids="   ")
            call_args = runner.run_json.call_args[0][0]
            assert "--ids" not in call_args
