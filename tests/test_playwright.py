"""Tests for the opt-in Playwright diagnostics MCP helper."""

from __future__ import annotations

import inspect
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from server.tools.playwright import playwright_doctor

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_playwright_doctor_has_no_mcp_parameters() -> None:
    assert inspect.signature(playwright_doctor).parameters == {}


def test_playwright_doctor_returns_structured_lenient_json() -> None:
    result_data = {
        "ok": False,
        "checks": [
            {
                "name": "saved_session",
                "ok": False,
                "detail": "No saved session",
                "hint": "Run direct playwright login",
            }
        ],
    }
    runner = MagicMock()
    runner.run_json_lenient.return_value = result_data

    with patch("server.tools.playwright.get_browser_runner", return_value=runner):
        assert playwright_doctor() == result_data

    runner.run_json_lenient.assert_called_once_with(
        ["playwright", "doctor", "--format", "json"]
    )


def test_default_server_does_not_import_optional_thin_slice_modules() -> None:
    source = """
import json
import sys

import server.main

print(json.dumps({
    "playwright": "server.tools.playwright" in sys.modules,
    "trackingparams": "server.tools.trackingparams" in sys.modules,
    "trackingparams_legacy": "server.tools.trackingparams_legacy" in sys.modules,
}))
"""
    result = subprocess.run(
        [sys.executable, "-c", source],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )

    assert json.loads(result.stdout) == {
        "playwright": False,
        "trackingparams": False,
        "trackingparams_legacy": True,
    }
