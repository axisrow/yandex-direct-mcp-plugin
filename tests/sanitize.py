"""Cassette sanitization -- strip secrets and commercial data.

Usage: python -m tests.sanitize

Processes all JSON files in tests/recordings/, replacing:
- Secrets (tokens, credentials) with REDACTED placeholders
- Commercial data (names, keywords, costs) with anonymized values
- Numeric IDs, ad texts, dates, bids — structural replacement via JSON parsing
"""

import json
import re
from pathlib import Path
from typing import Any

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

# Fields with numeric IDs — replaced consistently via id_map
_ID_FIELDS = {
    "Id",
    "CampaignId",
    "AdGroupId",
    "KeywordId",
    "AdId",
    "SitelinkSetId",
    "VCardId",
    "AdImageHash",
    "AdExtensionId",
    "AudienceTargetId",
    "RetargetingListId",
    "DynamicTargetId",
    "NegativeKeywordSharedSetId",
    "SmartTargetId",
    "FeedId",
    "CreativeId",
    "TurboPageId",
    "ClientId",
}

# Text fields replaced with fixed placeholders
_TEXT_REPLACEMENTS: dict[str, str] = {
    "Text": "Текст объявления XXXXX",
    "Body": "Текст XXXXX",
    "Title": "Ad title placeholder",
    "Title2": "Ad title2 placeholder",
    "DisplayUrlPath": "example-path",
}

# Date fields replaced with fixed dates
_DATE_REPLACEMENTS: dict[str, str] = {
    "StartDate": "2024-01-01",
    "EndDate": "2024-12-31",
}

# Numeric fields replaced with fixed values (micro-units: 1 RUB = 1 000 000)
_NUMBER_REPLACEMENTS: dict[str, int] = {
    "Bid": 1_000_000,
    "ContextBid": 1_000_000,
    "Amount": 10_000_000,
}


def _anonymize_node(node: Any, id_map: dict[int, int]) -> Any:
    """Recursively anonymize a parsed JSON node."""
    if isinstance(node, list):
        return [_anonymize_node(item, id_map) for item in node]

    if isinstance(node, dict):
        result: dict[str, Any] = {}
        for key, value in node.items():
            if key in _ID_FIELDS and isinstance(value, int) and value > 100_000:
                if value not in id_map:
                    id_map[value] = 10_000_000 + len(id_map) + 1
                result[key] = id_map[value]
            elif key in _TEXT_REPLACEMENTS and isinstance(value, str):
                result[key] = _TEXT_REPLACEMENTS[key]
            elif key in _DATE_REPLACEMENTS and isinstance(value, str) and value:
                result[key] = _DATE_REPLACEMENTS[key]
            elif key in _NUMBER_REPLACEMENTS and isinstance(value, (int, float)):
                result[key] = _NUMBER_REPLACEMENTS[key]
            else:
                result[key] = _anonymize_node(value, id_map)
        return result

    return node


def _anonymize_stdout(stdout: str, id_map: dict[int, int]) -> str:
    """Parse stdout as JSON, anonymize commercial fields, re-serialize."""
    stripped = stdout.strip()
    if not stripped or stripped in ("[]", "{}"):
        return stripped
    try:
        parsed = json.loads(stripped)
        anonymized = _anonymize_node(parsed, id_map)
        return json.dumps(anonymized, indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        return stripped  # not valid JSON — leave as-is


def _sanitize_string(text: str) -> str:
    """Apply sanitization rules to a single string value."""
    for pattern, replacement in SANITIZE_RULES:
        text = re.sub(pattern, replacement, text)
    return text


SECRET_FLAGS = {"--token", "--client-secret", "--client-id", "--password"}


def _sanitize_args(args: list, id_map: dict[int, int]) -> list:
    """Redact values following secret flags and remap numeric IDs in args."""
    result = []
    skip_next = False
    for arg in args:
        if skip_next:
            result.append("REDACTED")
            skip_next = False
        elif arg in SECRET_FLAGS:
            result.append(arg)
            skip_next = True
        elif isinstance(arg, str):
            # Remap numeric IDs found in comma-separated arg values (e.g. --campaign-ids)
            parts = arg.split(",")
            if len(parts) > 1 and all(p.strip().isdigit() for p in parts):
                remapped = [
                    str(id_map.get(int(p.strip()), int(p.strip()))) for p in parts
                ]
                result.append(",".join(remapped))
            else:
                result.append(arg)
        else:
            result.append(arg)
    return result


def sanitize(recordings_dir: Path = RECORDINGS_DIR) -> int:
    """Sanitize all cassettes in the recordings directory.

    Parses each cassette as JSON, sanitizes the stdout and stderr string
    fields using regex rules and structural JSON anonymization,
    then re-serializes to JSON.

    Returns:
        Number of cassettes processed.
    """
    # Shared ID map across all cassettes for cross-cassette consistency
    id_map: dict[int, int] = {}

    count = 0
    for cassette in sorted(recordings_dir.rglob("*.json")):
        try:
            data = json.loads(cassette.read_text())
        except json.JSONDecodeError:
            print(f"  SKIP (invalid JSON): {cassette.relative_to(recordings_dir)}")
            continue

        # Structural anonymization of stdout JSON first (IDs, texts, dates, bids)
        # Must run before regex to avoid breaking JSON with partial replacements
        if isinstance(data.get("stdout"), str):
            data["stdout"] = _anonymize_stdout(data["stdout"], id_map)

        # Regex sanitization (secrets, names, keywords, URLs) on already-structured output
        for field in ("stdout", "stderr"):
            if isinstance(data.get(field), str):
                data[field] = _sanitize_string(data[field])

        # Sanitize args array — redact values after secret flags
        if isinstance(data.get("args"), list):
            data["args"] = _sanitize_args(data["args"], id_map)

        cassette.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        count += 1
        print(f"  Sanitized: {cassette.relative_to(recordings_dir)}")

    print(f"\nDone: {count} cassettes sanitized")
    return count


if __name__ == "__main__":
    sanitize()  # Always exit 0 — count is informational, not an error code
