"""Tests for cassette sanitization."""

import json

from tests.sanitize import sanitize


def test_sanitizes_access_token(tmp_path):
    """Access tokens are replaced with REDACTED."""
    cassette = tmp_path / "test.json"
    cassette.write_text(
        json.dumps(
            {
                "args": [],
                "stdout": '{"access_token": "AQAAAACy1C6ZAAAAfa6vDLuXYZ1234567890"}',
                "stderr": "",
                "returncode": 0,
            }
        )
    )

    sanitize(tmp_path)

    data = json.loads(cassette.read_text())
    assert "REDACTED" in data["stdout"]
    assert "AQAAAACy" not in data["stdout"]


def test_sanitizes_campaign_names(tmp_path):
    """Campaign names are anonymized."""
    cassette = tmp_path / "test.json"
    cassette.write_text(
        json.dumps(
            {
                "args": [],
                "stdout": '{"Name": "\u0414\u043e\u0441\u0442\u0430\u0432\u043a\u0430 \u043f\u0438\u0446\u0446\u044b \u041c\u043e\u0441\u043a\u0432\u0430"}',
                "stderr": "",
                "returncode": 0,
            }
        )
    )

    sanitize(tmp_path)

    data = json.loads(cassette.read_text())
    assert "Campaign_XXXXX" in data["stdout"]
    assert "\u0414\u043e\u0441\u0442\u0430\u0432\u043a\u0430" not in data["stdout"]
