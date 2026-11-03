"""Interactive direct auth setup for cassette recording.

Run:
    python -m tests.setup
"""

import subprocess
import sys


def main() -> int:
    """Delegate live test authentication to `direct`."""
    # `auth login` is a group (direct-cli #951); the API-token login the
    # cassette recording needs is the `api` subcommand.
    return subprocess.call(["direct", "auth", "login", "api"])


if __name__ == "__main__":
    sys.exit(main())
