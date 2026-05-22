"""Interactive direct auth setup for cassette recording.

Run:
    python -m tests.setup
"""

import subprocess
import sys


def main() -> int:
    """Delegate live test authentication to `direct`."""
    return subprocess.call(["direct", "auth", "login"])


if __name__ == "__main__":
    sys.exit(main())
