"""Tests for advideos MCP tools."""

from unittest.mock import patch

from server.tools.advideos import advideos_add, advideos_get

from tests.helpers import mock_runner


def test_advideos_get():
    runner = mock_runner({"Videos": []})
    with patch("server.tools.advideos.get_runner", return_value=runner):
        result = advideos_get(ids="1,2")

    assert result == {"Videos": []}
    runner.run_json.assert_called_once_with(
        ["advideos", "get", "--format", "json", "--ids", "1,2"]
    )


def test_advideos_add_url():
    runner = mock_runner({"Id": 10})
    with patch("server.tools.advideos.get_runner", return_value=runner):
        result = advideos_add(url="https://example.com/video.mp4", name="Promo")

    assert result == {"Id": 10}
    runner.run_json.assert_called_once_with(
        ["advideos", "add", "--url", "https://example.com/video.mp4", "--name", "Promo"]
    )


def test_advideos_add_requires_exactly_one_source():
    result = advideos_add()
    assert result["error"] == "invalid_video_source"


def test_advideos_add_rejects_both_sources():
    result = advideos_add(url="https://example.com/video.mp4", video_data="abc123")
    assert result["error"] == "invalid_video_source"
