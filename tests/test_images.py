"""Tests for ad images MCP tools."""

from unittest.mock import MagicMock, patch

import pytest

import server.tools
from server.tools.images import adimages_list, adimages_add, adimages_delete


@pytest.fixture(autouse=True)
def setup_token_getter():
    """Configure a mock token getter for all tests."""
    server.tools.set_token_getter(lambda: "test-token")


@pytest.fixture
def mock_images():
    """Sample ad images data."""
    return [
        {
            "Id": 1,
            "Name": "banner1.jpg",
            "Type": "Image",
            "Width": 300,
            "Height": 250,
        },
        {
            "Id": 2,
            "Name": "logo.png",
            "Type": "Image",
            "Width": 200,
            "Height": 200,
        },
    ]


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestAdimagesList:
    """Tests for adimages_list tool."""

    def test_list_images_success(self, mock_images):
        """Test listing images successfully."""
        with patch(
            "server.tools.images.get_runner",
            return_value=_mock_runner(mock_images),
        ):
            result = adimages_list(ids="1,2")
            assert len(result) == 2
            assert result[0]["Id"] == 1

    def test_list_images_no_ids(self, mock_images):
        """Test listing all images with no ids."""
        with patch(
            "server.tools.images.get_runner",
            return_value=_mock_runner(mock_images),
        ):
            result = adimages_list()
            assert len(result) == 2

    def test_list_images_empty_ids_treated_as_missing_filter(self, mock_images):
        """Test empty ids behaves like no filter."""
        runner = MagicMock()
        runner.run_json.return_value = mock_images
        with patch("server.tools.images.get_runner", return_value=runner):
            result = adimages_list(ids="   ")
            assert len(result) == 2
            call_args = runner.run_json.call_args[0][0]
            assert "--ids" not in call_args

    def test_list_images_empty_result(self):
        """Test empty response returns empty list."""
        with patch("server.tools.images.get_runner", return_value=_mock_runner([])):
            result = adimages_list(ids="999")
            assert result == []


class TestAdimagesAdd:
    """Tests for adimages_add tool."""

    def test_add_image_success(self):
        """Test adding image successfully."""
        mock_result = {"Id": 123, "Name": "new_image.jpg"}
        image_json = '{"Name": "new_image.jpg", "Data": "base64data"}'
        runner = MagicMock()
        runner.run_json.return_value = mock_result

        with patch("server.tools.images.get_runner", return_value=runner):
            result = adimages_add(image_json=image_json)
            assert result["Id"] == 123
            call_args = runner.run_json.call_args[0][0]
            assert "--json" in call_args


class TestAdimagesDelete:
    """Tests for adimages_delete tool."""

    def test_delete_image_by_hash(self):
        """Test deleting an image by hash."""
        mock_result = {"success": True}
        runner = MagicMock()
        runner.run_json.return_value = mock_result

        with patch("server.tools.images.get_runner", return_value=runner):
            result = adimages_delete(hash_value="abc123")
            assert result["success"] is True
            call_args = runner.run_json.call_args[0][0]
            assert "--hash" in call_args
            assert "abc123" in call_args
