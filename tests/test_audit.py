"""Tests for cassette audit."""

import json

from tests.audit import audit


def test_clean_cassette(tmp_path):
    """Clean cassette returns 0."""
    cassette = tmp_path / "clean.json"
    cassette.write_text(
        json.dumps(
            {
                "args": ["campaigns", "get"],
                "stdout": '[{"Id": 12345, "Name": "Campaign_XXXXX"}]',
                "stderr": "",
                "returncode": 0,
            }
        )
    )

    result = audit(tmp_path)
    assert result == 0


def test_critical_leak(tmp_path):
    """Cassette with OAuth token returns 2."""
    cassette = tmp_path / "leaked.json"
    cassette.write_text(
        json.dumps(
            {
                "args": [],
                "stdout": f'{{"access_token": "AQAAAA{"X" * 30}"}}',
                "stderr": "",
                "returncode": 0,
            }
        )
    )

    result = audit(tmp_path)
    assert result == 2


def test_warning_leak(tmp_path):
    """Cassette with real domain returns 1."""
    cassette = tmp_path / "warn.json"
    cassette.write_text(
        json.dumps(
            {
                "args": [],
                "stdout": '{"url": "https://pizza-shop.ru"}',
                "stderr": "",
                "returncode": 0,
            }
        )
    )

    result = audit(tmp_path)
    assert result == 1
