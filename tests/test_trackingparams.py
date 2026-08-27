"""Tests for the trackingparams MCP helper."""

from unittest.mock import patch

from server.tools.trackingparams import trackingparams_get
from server.tools.trackingparams_legacy import trackingparams
from tests.helpers import mock_runner


def test_trackingparams_requests_json_from_reference_command() -> None:
    result_data = [
        {
            "Parameter": "{campaign_id}",
            "Description": "Campaign ID",
            "Values": "number",
        }
    ]
    runner = mock_runner(result_data)

    with patch("server.tools.trackingparams_legacy.get_runner", return_value=runner):
        assert trackingparams() == result_data

    runner.run_json.assert_called_once_with(["trackingparams", "--format", "json"])


def test_trackingparams_get_requests_json_from_reference_command() -> None:
    result_data = [{"Parameter": "{campaign_id}", "Description": "Campaign ID"}]
    runner = mock_runner(result_data)

    with patch("server.tools.trackingparams.get_runner", return_value=runner):
        assert trackingparams_get() == result_data

    runner.run_json.assert_called_once_with(["trackingparams", "--format", "json"])
