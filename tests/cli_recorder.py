"""CLI recorder for cassette-based testing.

Records subprocess calls to `direct` CLI and saves them as JSON cassettes.
Replays recorded cassettes in test mode.

Modes:
- Record (RECORD=true or pytest --record): calls real CLI, saves {args, stdout, stderr, returncode}
- Replay (default): patches subprocess.run, returns saved responses
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Any


class CassetteNotFoundError(Exception):
    """Raised when no matching cassette is found for replay."""

    pass


class CliRecorder:
    """Records and replays CLI subprocess calls as JSON cassettes."""

    def __init__(self, recordings_dir: Path, *, command: str = "direct") -> None:
        self._recordings_dir = recordings_dir
        self._command = command

    def record(self, args: list[str], env: dict[str, str] | None = None) -> dict[str, Any]:
        """Call the real CLI and save the result as a cassette.

        Args:
            args: Full CLI arguments including the command itself.
            env: Optional environment variables.

        Returns:
            The saved cassette dict.
        """
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )

        cassette = {
            "command": args[0] if args else self._command,
            "args": args[1:] if len(args) > 1 else [],
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

        self._save_cassette(cassette)
        return cassette

    def replay(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        """Find a matching cassette and return the recorded response.

        Args:
            args: Full CLI arguments to match against.

        Returns:
            CompletedProcess with recorded stdout/stderr.

        Raises:
            CassetteNotFoundError: If no matching cassette exists.
        """
        search_args = args[1:] if len(args) > 1 else []
        cassette = self._find_cassette(search_args)

        if cassette is None:
            raise CassetteNotFoundError(f"No cassette found for args: {search_args}. Record with: RECORD=true pytest")

        return subprocess.CompletedProcess(
            args=args,
            returncode=cassette["returncode"],
            stdout=cassette["stdout"],
            stderr=cassette["stderr"],
        )

    def _save_cassette(self, cassette: dict[str, Any]) -> Path:
        """Save a cassette to the recordings directory."""
        self._recordings_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename from subcommand
        args = cassette.get("args", [])
        subcmd = "general"
        for arg in args:
            if arg in ("campaigns", "ads", "keywords", "reports", "auth"):
                subcmd = arg
                break

        subcmd_dir = self._recordings_dir / subcmd
        subcmd_dir.mkdir(parents=True, exist_ok=True)

        # Find unique filename
        existing = len(list(subcmd_dir.glob("*.json")))
        filename = f"recording-{existing + 1:03d}.json"
        path = subcmd_dir / filename

        path.write_text(json.dumps(cassette, indent=2, ensure_ascii=False))
        return path

    def _find_cassette(self, args: list[str]) -> dict[str, Any] | None:
        """Search recordings for a cassette matching the given args."""
        # Look for exact args match in all cassette files
        for cassette_file in sorted(self._recordings_dir.rglob("*.json")):
            try:
                cassette = json.loads(cassette_file.read_text())
                if cassette.get("args") == args:
                    return cassette
            except (json.JSONDecodeError, KeyError):
                continue
        return None

    def is_recording(self) -> bool:
        """Check if we're in recording mode."""
        return os.environ.get("RECORD", "").lower() in ("true", "1", "yes")
