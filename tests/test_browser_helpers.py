"""Tests for environment-backed browser CLI options."""

import pytest

from server.tools.browser_helpers import browser_session_args


def test_browser_session_args_omits_unset_values() -> None:
    assert browser_session_args({}) == []


def test_browser_session_args_emits_normalized_values_in_cli_order() -> None:
    env = {
        "YANDEX_DIRECT_BROWSER_PROFILE_DIR": "  /tmp/direct-profile  ",
        "YANDEX_DIRECT_BROWSER_CHROME_PROFILE": "  Profile 2  ",
        "YANDEX_DIRECT_BROWSER_HEADFUL": "1",
    }

    assert browser_session_args(env) == [
        "--profile-dir",
        "/tmp/direct-profile",
        "--chrome-profile",
        "Profile 2",
        "--headful",
    ]


def test_browser_session_args_omits_blank_profile_values() -> None:
    env = {
        "YANDEX_DIRECT_BROWSER_PROFILE_DIR": "  ",
        "YANDEX_DIRECT_BROWSER_CHROME_PROFILE": "",
    }

    assert browser_session_args(env) == []


def test_browser_session_args_can_omit_headful_for_read_only_doctor() -> None:
    env = {
        "YANDEX_DIRECT_BROWSER_PROFILE_DIR": "/tmp/direct-profile",
        "YANDEX_DIRECT_BROWSER_CHROME_PROFILE": "Profile 2",
        "YANDEX_DIRECT_BROWSER_HEADFUL": "1",
    }

    assert browser_session_args(env, include_headful=False) == [
        "--profile-dir",
        "/tmp/direct-profile",
        "--chrome-profile",
        "Profile 2",
    ]


@pytest.mark.parametrize("value", ["0", "true", "yes", " 1 ", ""])
def test_browser_session_args_requires_exact_headful_opt_in(value: str) -> None:
    assert browser_session_args({"YANDEX_DIRECT_BROWSER_HEADFUL": value}) == []
