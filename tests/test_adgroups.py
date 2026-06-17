"""Tests for ad group MCP tools."""

from unittest.mock import patch

from server.tools.adgroups import (
    adgroups_list,
    adgroups_add,
    adgroups_update,
    adgroups_delete,
)

from tests.helpers import mock_runner

SAMPLE_ADGROUPS = [
    {"Id": 1, "Name": "Ad Group 1", "CampaignId": 12345},
    {"Id": 2, "Name": "Ad Group 2", "CampaignId": 12345},
]


class TestAdgroupsList:
    """Tests for adgroups_list tool."""

    def test_adgroups_list_by_campaign(self):
        """Test listing ad groups by campaign."""
        with patch(
            "server.tools.adgroups.get_runner",
            return_value=mock_runner(SAMPLE_ADGROUPS),
        ):
            result = adgroups_list(campaign_ids="12345")
            assert len(result) == 2
            assert result[0]["Id"] == 1

    def test_adgroups_list_ignores_blank_campaign_ids(self):
        """Test blank campaign IDs behave like no filter."""
        runner = mock_runner(SAMPLE_ADGROUPS)
        with patch("server.tools.adgroups.get_runner", return_value=runner):
            result = adgroups_list(campaign_ids="   ")
            assert len(result) == 2
            call_args = runner.run_json.call_args[0][0]
            assert "--campaign-ids" not in call_args

    def test_adgroups_list_empty(self):
        """Test empty ad groups list."""
        with patch(
            "server.tools.adgroups.get_runner",
            return_value=mock_runner([]),
        ):
            result = adgroups_list(campaign_ids="12345")
            assert result == []

    def test_adgroups_list_batch_limit(self):
        """Test batch limit validation."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = adgroups_list(campaign_ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"


class TestAdgroupsAdd:
    """Tests for adgroups_add tool."""

    def test_adgroups_add_success(self):
        """Test adding an ad group successfully."""
        mock_result = {"Id": 123, "Name": "New Ad Group"}
        with patch(
            "server.tools.adgroups.get_runner",
            return_value=mock_runner(mock_result),
        ):
            result = adgroups_add(campaign_id=12345, name="New Ad Group")
            assert result["Id"] == 123

    def test_adgroups_add_with_type(self):
        """Test adding ad group with type parameter."""
        runner = mock_runner({"Id": 124})
        with patch(
            "server.tools.adgroups.get_runner",
            return_value=runner,
        ):
            adgroups_add(
                campaign_id=12345,
                name="Test",
                type="MOBILE_AD_GROUP",
            )
            call_args = runner.run_json.call_args[0][0]
            assert "--type" in call_args
            assert "MOBILE_AD_GROUP" in call_args

    def test_adgroups_add_from_file(self):
        """Batch add via from_file emits --from-file only (CLI #564)."""
        runner = mock_runner({"AddResults": [{"Id": 1}]})
        with patch("server.tools.adgroups.get_runner", return_value=runner):
            adgroups_add(from_file="/tmp/ag.jsonl")
            runner.run_json.assert_called_once_with(
                ["adgroups", "add", "--from-file", "/tmp/ag.jsonl"]
            )

    def test_adgroups_add_json_with_default_campaign(self):
        """adgroups_json batch forwards --campaign-id default + --adgroups-json."""
        payload = '[{"name":"g","region-ids":"225"}]'
        runner = mock_runner({"AddResults": [{"Id": 1}]})
        with patch("server.tools.adgroups.get_runner", return_value=runner):
            adgroups_add(campaign_id=7, adgroups_json=payload)
            argv = runner.run_json.call_args[0][0]
            assert argv == [
                "adgroups",
                "add",
                "--campaign-id",
                "7",
                "--adgroups-json",
                payload,
            ]

    def test_adgroups_add_rejects_no_mode(self):
        """Neither campaign_id+name nor batch flag → missing_mode."""
        runner = mock_runner({"AddResults": []})
        with patch("server.tools.adgroups.get_runner", return_value=runner):
            result = adgroups_add(campaign_id=7)  # name missing, no batch
        assert result["error"] == "missing_mode"
        runner.run_json.assert_not_called()

    def test_adgroups_add_rejects_conflicting_batch_modes(self):
        """from_file + adgroups_json → conflicting_modes."""
        runner = mock_runner({"AddResults": []})
        with patch("server.tools.adgroups.get_runner", return_value=runner):
            result = adgroups_add(from_file="/tmp/a.jsonl", adgroups_json="[]")
        assert result["error"] == "conflicting_modes"
        runner.run_json.assert_not_called()


class TestAdgroupsUpdate:
    """Tests for adgroups_update tool."""

    def test_adgroups_update_name(self):
        """Test updating an ad group name."""
        mock_result = {"Id": 123, "Name": "Updated Name"}
        with patch(
            "server.tools.adgroups.get_runner",
            return_value=mock_runner(mock_result),
        ):
            result = adgroups_update(id=123, name="Updated Name")
            assert result["Id"] == 123

    def test_adgroups_update_requires_fields(self):
        """Test that updating with no fields returns error."""
        result = adgroups_update(id=123)
        assert "error" in result
        assert result["error"] == "missing_update_fields"

    def test_adgroups_update_accepts_empty_string_field(self):
        """Empty strings are provided values; CLI owns semantic validation."""
        runner = mock_runner({"Id": 123})
        with patch("server.tools.adgroups.get_runner", return_value=runner):
            adgroups_update(id=123, name="")

        runner.run_json.assert_called_once_with(
            ["adgroups", "update", "--id", "123", "--name", ""]
        )

    def test_adgroups_update_with_status(self):
        """Test updating with status."""
        runner = mock_runner({"Id": 123})
        with patch(
            "server.tools.adgroups.get_runner",
            return_value=runner,
        ):
            adgroups_update(id=123, status="SUSPENDED")
            call_args = runner.run_json.call_args[0][0]
            assert "--status" in call_args
            assert "SUSPENDED" in call_args

    def test_adgroups_update_from_file(self):
        """Batch update via from_file emits --from-file only (CLI #565)."""
        runner = mock_runner({"UpdateResults": [{"Id": 1}]})
        with patch("server.tools.adgroups.get_runner", return_value=runner):
            adgroups_update(from_file="/tmp/ag.jsonl")
            runner.run_json.assert_called_once_with(
                ["adgroups", "update", "--from-file", "/tmp/ag.jsonl"]
            )

    def test_adgroups_update_json(self):
        """Batch update via adgroups_json emits --adgroups-json."""
        payload = '[{"id":1,"name":"g2"}]'
        runner = mock_runner({"UpdateResults": [{"Id": 1}]})
        with patch("server.tools.adgroups.get_runner", return_value=runner):
            adgroups_update(adgroups_json=payload)
            argv = runner.run_json.call_args[0][0]
            assert argv == ["adgroups", "update", "--adgroups-json", payload]

    def test_adgroups_update_rejects_no_mode(self):
        """Neither id nor batch flag → missing_mode."""
        runner = mock_runner({"UpdateResults": []})
        with patch("server.tools.adgroups.get_runner", return_value=runner):
            result = adgroups_update()
        assert result["error"] == "missing_mode"
        runner.run_json.assert_not_called()

    def test_adgroups_update_rejects_id_with_batch(self):
        """id + batch flag → conflicting_modes."""
        runner = mock_runner({"UpdateResults": []})
        with patch("server.tools.adgroups.get_runner", return_value=runner):
            result = adgroups_update(id=1, adgroups_json="[]")
        assert result["error"] == "conflicting_modes"
        runner.run_json.assert_not_called()


class TestAdgroupsDelete:
    """Tests for adgroups_delete tool."""

    def test_adgroups_delete_success(self):
        """Test deleting ad groups successfully."""
        mock_result = {"success": True}
        with patch(
            "server.tools.adgroups.get_runner",
            return_value=mock_runner(mock_result),
        ):
            result = adgroups_delete(ids="1")
            assert result["success"] is True

    def test_adgroups_delete_batch_limit(self):
        """Test batch limit validation."""
        ids = ",".join(str(i) for i in range(1, 12))
        result = adgroups_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
