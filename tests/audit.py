"""Cassette audit -- detect leaked secrets and commercial data.

Usage: python -m tests.audit

Exit codes:
  0 -- All cassettes clean
  1 -- WARNING: commercial data found
  2 -- CRITICAL: secrets found
"""

import json
import re
import sys
from pathlib import Path

RECORDINGS_DIR = Path(__file__).parent / "recordings"

CRITICAL_PATTERNS: list[tuple[str, str]] = [
    (r"AQAAAA[A-Za-z0-9_-]{20,}", "OAuth token"),
    (r"Bearer\s+[A-Za-z0-9_-]{20,}", "Bearer token"),
    (r"\d+:[A-Za-z0-9_-]{10,}:", "Refresh token"),
    (r'"client_secret"\s*:\s*"[^"]{6,}"', "Client secret"),
    (r"Basic\s+[A-Za-z0-9+/=]{20,}", "Base64 credentials"),
]

WARNING_PATTERNS: list[tuple[str, str]] = [
    (r"https?://(?!example\.com)[a-z0-9.-]+\.[a-z]{2,}", "Real domain"),
    (r"\+7\s*\(?\d{3}\)?\s*\d{3}[\s-]?\d{2}[\s-]?\d{2}", "Phone number"),
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "Email address"),
]


def audit(recordings_dir: Path = RECORDINGS_DIR) -> int:
    """Audit all cassettes for leaked data.

    Returns:
        Exit code: 0 (clean), 1 (warnings), 2 (critical).
    """
    if not recordings_dir.exists():
        print(f"Recordings directory not found: {recordings_dir}")
        return 0

    critical = 0
    warnings = 0

    print(f"Scanning {recordings_dir}/...")

    for cassette in sorted(recordings_dir.rglob("*.json")):
        text = cassette.read_text()
        rel = cassette.relative_to(recordings_dir)
        file_critical = 0
        file_warnings = 0

        # Structural validation
        try:
            data = json.loads(text)
            for key in ("args", "stdout", "returncode"):
                if key not in data:
                    print(f"  {rel}  INFO: Missing key '{key}'")
        except json.JSONDecodeError as e:
            print(f"  {rel}  INFO: Invalid JSON -- {e}")

        # Check for secrets
        for pattern, label in CRITICAL_PATTERNS:
            match = re.search(pattern, text)
            if match:
                print(f"  {rel}  CRITICAL: {label} found (pos {match.start()})")
                critical += 1
                file_critical += 1

        # Check for commercial data
        for pattern, label in WARNING_PATTERNS:
            match = re.search(pattern, text)
            if match:
                print(f'  {rel}  WARNING: {label} "{match.group()[:40]}" found')
                warnings += 1
                file_warnings += 1

        if not file_critical and not file_warnings:
            print(f"  {rel}  clean")

    print(f"\nResult: {critical} CRITICAL, {warnings} WARNING")

    if critical:
        print("Commit blocked. Run: python -m tests.sanitize")
        return 2
    if warnings:
        print("Commit blocked. Run: python -m tests.sanitize")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(audit())
