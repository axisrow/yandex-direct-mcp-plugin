"""Shared environment-backed options for browser CLI commands."""

from collections.abc import Mapping

from server.tools.helpers import normalize_optional_str

ENV_BROWSER_PROFILE_DIR = "YANDEX_DIRECT_BROWSER_PROFILE_DIR"
ENV_BROWSER_CHROME_PROFILE = "YANDEX_DIRECT_BROWSER_CHROME_PROFILE"
ENV_BROWSER_HEADFUL = "YANDEX_DIRECT_BROWSER_HEADFUL"


def browser_session_args(env: Mapping[str, str]) -> list[str]:
    """Build browser-session CLI arguments from deployment environment values."""
    args: list[str] = []
    profile_dir = normalize_optional_str(env.get(ENV_BROWSER_PROFILE_DIR))
    chrome_profile = normalize_optional_str(env.get(ENV_BROWSER_CHROME_PROFILE))

    if profile_dir is not None:
        args.extend(["--profile-dir", profile_dir])
    if chrome_profile is not None:
        args.extend(["--chrome-profile", chrome_profile])
    if env.get(ENV_BROWSER_HEADFUL) == "1":
        args.append("--headful")
    return args
