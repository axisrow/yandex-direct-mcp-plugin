"""Tests for vCards MCP tools."""

from unittest.mock import patch

import pytest

from server.tools.vcards import vcards_list, vcards_add, vcards_delete

from tests.helpers import mock_runner


@pytest.fixture
def mock_vcards():
    """Sample vCard data."""
    return [
        {
            "Id": 1,
            "CampaignName": "Campaign 1",
            "CompanyAddress": "123 Main St",
            "ContactPhone": "+79991234567",
        },
        {
            "Id": 2,
            "CampaignName": "Campaign 2",
            "CompanyAddress": "456 Oak Ave",
            "ContactPhone": "+79997654321",
        },
    ]


class TestVcardsList:
    """Tests for vcards_list tool."""

    def test_list_vcards_success(self, mock_vcards):
        """Test listing vCards successfully."""
        with patch(
            "server.tools.vcards.get_runner",
            return_value=mock_runner(mock_vcards),
        ):
            result = vcards_list(ids="1,2")
            assert len(result) == 2
            assert result[0]["Id"] == 1

    def test_list_vcards_no_ids(self, mock_vcards):
        """Test listing all vCards with no IDs."""
        with patch(
            "server.tools.vcards.get_runner",
            return_value=mock_runner(mock_vcards),
        ):
            result = vcards_list()
            assert len(result) == 2

    def test_list_vcards_batch_limit(self):
        """Test batch limit validation for list."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = vcards_list(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"

    def test_list_vcards_trims_ids_before_cli(self, mock_vcards):
        """Test vCard IDs are normalized before argv construction."""
        runner = mock_runner(mock_vcards)
        with patch("server.tools.vcards.get_runner", return_value=runner):
            vcards_list(ids=" 1,2 ")

        runner.run_json.assert_called_once_with(
            ["vcards", "get", "--format", "json", "--ids", "1,2"]
        )


class TestVcardsAdd:
    """Tests for vcards_add tool (CLI 0.3.8 typed flags)."""

    def test_add_vcard_required_fields(self):
        """Test adding vCard with all required typed flags."""
        mock_result = {"Id": 123}
        runner = mock_runner(mock_result)

        with patch("server.tools.vcards.get_runner", return_value=runner):
            result = vcards_add(
                campaign_id=42,
                country="RU",
                city="Москва",
                company_name="ООО Рога и Копыта",
                work_time="0#6#9#00#18#00",
                phone_country_code="+7",
                phone_city_code="495",
                phone_number="1234567",
            )
            assert result["Id"] == 123
            argv = runner.run_json.call_args[0][0]
            assert "--campaign-id" in argv and "42" in argv
            assert "--country" in argv and "RU" in argv
            assert "--phone-number" in argv

    def test_add_vcard_optional_fields(self):
        runner = mock_runner({"Id": 124})
        with patch("server.tools.vcards.get_runner", return_value=runner):
            vcards_add(
                campaign_id=42,
                country="RU",
                city="Москва",
                company_name="X",
                work_time="0#6#9#00#18#00",
                phone_country_code="+7",
                phone_city_code="495",
                phone_number="1234567",
                street="Тверская",
                contact_email="hi@example.com",
                metro_station_id=42,
                dry_run=True,
            )
        argv = runner.run_json.call_args[0][0]
        assert "--street" in argv
        assert "--contact-email" in argv
        assert "--metro-station-id" in argv and "42" in argv
        assert "--dry-run" in argv


class TestVcardsDelete:
    """Tests for vcards_delete tool."""

    def test_delete_vcards_success(self):
        """Test deleting vCards successfully."""
        mock_result = {"success": True}

        with patch(
            "server.tools.vcards.get_runner",
            return_value=mock_runner(mock_result),
        ):
            result = vcards_delete(ids="1")
            assert result["success"] is True

    def test_delete_vcards_batch_limit(self):
        """Test batch limit validation for delete."""
        ids = ",".join(str(i) for i in range(1, 12))  # 11 IDs
        result = vcards_delete(ids=ids)
        assert "error" in result
        assert result["error"] == "batch_limit"
