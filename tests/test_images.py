"""Tests for ad images MCP tools."""

from unittest.mock import patch

import pytest

from server.tools.images import adimages_list, adimages_add, adimages_delete

from tests.helpers import mock_runner


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


class TestAdimagesList:
    """Tests for adimages_list tool."""

    def test_list_images_success(self, mock_images):
        """Test listing images successfully."""
        with patch(
            "server.tools.images.get_runner",
            return_value=mock_runner(mock_images),
        ):
            result = adimages_list(ids="1,2")
            assert len(result) == 2
            assert result[0]["Id"] == 1

    def test_list_images_no_ids(self, mock_images):
        """Test listing all images with no ids."""
        with patch(
            "server.tools.images.get_runner",
            return_value=mock_runner(mock_images),
        ):
            result = adimages_list()
            assert len(result) == 2

    def test_list_images_empty_ids_treated_as_missing_filter(self, mock_images):
        """Test empty ids behaves like no filter."""
        runner = mock_runner(mock_images)
        with patch("server.tools.images.get_runner", return_value=runner):
            result = adimages_list(ids="   ")
            assert len(result) == 2
            call_args = runner.run_json.call_args[0][0]
            assert "--ids" not in call_args

    def test_list_images_empty_result(self):
        """Test empty response returns empty list."""
        with patch("server.tools.images.get_runner", return_value=mock_runner([])):
            result = adimages_list(ids="999")
            assert result == []

    def test_list_images_trims_ids_before_cli(self, mock_images):
        """Test image IDs are normalized before argv construction."""
        runner = mock_runner(mock_images)
        with patch("server.tools.images.get_runner", return_value=runner):
            adimages_list(ids=" 1,2 ")

        runner.run_json.assert_called_once_with(
            ["adimages", "get", "--format", "json", "--ids", "1,2"]
        )


class TestAdimagesAdd:
    """Tests for adimages_add tool (CLI 0.3.8 typed flags)."""

    def test_add_image_with_data(self):
        """Test adding image with base64 image_data."""
        mock_result = {"Id": 123, "Name": "new_image.jpg"}
        runner = mock_runner(mock_result)

        with patch("server.tools.images.get_runner", return_value=runner):
            result = adimages_add(name="new_image.jpg", image_data="base64data")
            assert result["Id"] == 123
            runner.run_json.assert_called_once_with(
                [
                    "adimages",
                    "add",
                    "--name",
                    "new_image.jpg",
                    "--image-data",
                    "base64data",
                ]
            )

    def test_add_image_with_file(self):
        """Test adding image with file path."""
        runner = mock_runner({"Id": 124})
        with patch("server.tools.images.get_runner", return_value=runner):
            adimages_add(name="img", image_file="/tmp/img.jpg", type="REGULAR")
        argv = runner.run_json.call_args[0][0]
        assert "--image-file" in argv
        assert "/tmp/img.jpg" in argv
        assert "--type" in argv

    def test_add_image_requires_source(self):
        result = adimages_add(name="x")
        assert result["error"] == "missing_image_source"

    def test_add_image_rejects_conflicting_source(self):
        result = adimages_add(name="x", image_data="d", image_file="/p")
        assert result["error"] == "conflicting_image_source"


class TestAdimagesDelete:
    """Tests for adimages_delete tool."""

    def test_delete_image_by_hash(self):
        """Test deleting an image by hash."""
        mock_result = {"success": True}
        runner = mock_runner(mock_result)

        with patch("server.tools.images.get_runner", return_value=runner):
            result = adimages_delete(hash_value="abc123")
            assert result["success"] is True
            call_args = runner.run_json.call_args[0][0]
            assert "--hash" in call_args
            assert "abc123" in call_args
