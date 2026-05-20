"""Tests for creatives MCP tools."""

from unittest.mock import MagicMock, patch


from server.tools.creatives import creatives_add, creatives_list


def _mock_runner(return_value):
    """Create a mock get_runner that returns a runner with the given run_json result."""
    runner = MagicMock()
    runner.run_json.return_value = return_value
    return runner


class TestCreativesList:
    """Tests for creatives_list tool."""

    def test_creatives_list_basic(self):
        """Test listing creatives by IDs."""
        mock_result = {"creatives": [{"id": 1, "name": "Creative 1"}]}
        with patch(
            "server.tools.creatives.get_runner",
            return_value=_mock_runner(mock_result),
        ):
            result = creatives_list(ids="1")
            assert "creatives" in result

    def test_creatives_list_by_types(self):
        """Test listing creatives filtered by types."""
        runner = MagicMock()
        runner.run_json.return_value = []
        with patch("server.tools.creatives.get_runner", return_value=runner):
            creatives_list(types="VIDEO_EXTENSION_CREATIVE")
            call_args = runner.run_json.call_args[0][0]
            assert "--types" in call_args
            assert "VIDEO_EXTENSION_CREATIVE" in call_args

    def test_creatives_list_trims_filters(self):
        """Test creative filters are normalized before argv construction."""
        runner = MagicMock()
        runner.run_json.return_value = []
        with patch("server.tools.creatives.get_runner", return_value=runner):
            creatives_list(ids=" 1 ", types="VIDEO_EXTENSION_CREATIVE")

        runner.run_json.assert_called_once_with(
            [
                "creatives",
                "get",
                "--format",
                "json",
                "--ids",
                "1",
                "--types",
                "VIDEO_EXTENSION_CREATIVE",
            ]
        )

    def test_creatives_list_empty_result(self):
        """Test empty response returns empty list."""
        with patch(
            "server.tools.creatives.get_runner",
            return_value=_mock_runner([]),
        ):
            result = creatives_list()
            assert result == []

    def test_creatives_list_ignores_blank_ids(self):
        """Test blank ids behave like no filter."""
        runner = MagicMock()
        runner.run_json.return_value = []
        with patch("server.tools.creatives.get_runner", return_value=runner):
            creatives_list(ids="   ")
            call_args = runner.run_json.call_args[0][0]
            assert "--ids" not in call_args


class TestCreativesAdd:
    """Tests for creatives_add tool."""

    def test_creatives_add(self):
        runner = MagicMock()
        runner.run_json.return_value = {"Id": 10}
        with patch("server.tools.creatives.get_runner", return_value=runner):
            result = creatives_add(video_id="video-1")

        assert result == {"Id": 10}
        runner.run_json.assert_called_once_with(
            ["creatives", "add", "--video-id", "video-1"]
        )
