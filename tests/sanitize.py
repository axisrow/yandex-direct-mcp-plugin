"""Cassette sanitization -- strip secrets and commercial data.

Usage: python -m tests.sanitize

Processes all JSON files in tests/recordings/, replacing:
- Secrets (tokens, credentials) with REDACTED placeholders
- Commercial data (names, keywords, costs) with anonymized values
"""

import json
import re
import sys
from pathlib import Path

RECORDINGS_DIR = Path(__file__).parent / "recordings"

SANITIZE_RULES: list[tuple[str, str]] = [
    # Secrets -- full replacement
    (r'"access_token"\s*:\s*"[^"]+"', '"access_token": "ACCESS_TOKEN_REDACTED"'),
    (r'"refresh_token"\s*:\s*"[^"]+"', '"refresh_token": "REFRESH_TOKEN_REDACTED"'),
    (r"Bearer [A-Za-z0-9_-]+", "Bearer ACCESS_TOKEN_REDACTED"),
    (r'"client_secret"\s*:\s*"[^"]+"', '"client_secret": "CLIENT_SECRET_REDACTED"'),
    (r'"client_id"\s*:\s*"[^"]+"', '"client_id": "CLIENT_ID_REDACTED"'),
    # Commercial data -- anonymization
    (r'"Name"\s*:\s*"[^"]+"', '"Name": "Campaign_XXXXX"'),
    (r'"Title"\s*:\s*"[^"]+"', '"Title": "Ad title placeholder"'),
    (r'"Title2"\s*:\s*"[^"]+"', '"Title2": "Ad title2 placeholder"'),
    (r'"Keyword"\s*:\s*"[^"]+"', '"Keyword": "keyword_XXXXX"'),
    (r'"Login"\s*:\s*"[^"]+"', '"Login": "test_account"'),
    (r'"Cost"\s*:\s*[\d.]+', '"Cost": 1000.00'),
    (r'"Href"\s*:\s*"https?://[^"]+"', '"Href": "https://example.com"'),
    (r"\+7\s*\(?\d{3}\)?\s*\d{3}[\s-]?\d{2}[\s-]?\d{2}", "+7 (000) 000-00-00"),
]


def _sanitize_string(text: str) -> str:
    """Apply sanitization rules to a single string value."""
    for pattern, replacement in SANITIZE_RULES:
        text = re.sub(pattern, replacement, text)
    return text


SECRET_FLAGS = {"--token", "--client-secret", "--client-id", "--password"}


def _sanitize_args(args: list) -> list:
    """Redact values following secret flags in the args list."""
    result = []
    skip_next = False
    for arg in args:
        if skip_next:
            result.append("REDACTED")
            skip_next = False
        elif arg in SECRET_FLAGS:
            result.append(arg)
            skip_next = True
        else:
            result.append(arg)
    return result


def sanitize(recordings_dir: Path = RECORDINGS_DIR) -> int:
    """Sanitize all cassettes in the recordings directory.

    Parses each cassette as JSON, sanitizes the stdout and stderr string
    fields using regex rules, then re-serializes to JSON.

    Returns:
        Number of cassettes processed.
    """
    count = 0
    for cassette in sorted(recordings_dir.rglob("*.json")):
        try:
            data = json.loads(cassette.read_text())
        except json.JSONDecodeError:
            print(f"  SKIP (invalid JSON): {cassette.relative_to(recordings_dir)}")
            continue

        # Sanitize string fields that may contain CLI output with sensitive data
        for field in ("stdout", "stderr"):
            if isinstance(data.get(field), str):
                data[field] = _sanitize_string(data[field])

        # Sanitize args array — redact values after secret flags
        if isinstance(data.get("args"), list):
            data["args"] = _sanitize_args(data["args"])

        cassette.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        count += 1
        print(f"  Sanitized: {cassette.relative_to(recordings_dir)}")

    print(f"\nDone: {count} cassettes sanitized")
    return count


if __name__ == "__main__":
    sanitize()  # Always exit 0 — count is informational, not an error code

