"""File-based token storage for OAuth credentials."""

import json
import os
import tempfile
from pathlib import Path
from typing import TypedDict


class TokenData(TypedDict, total=False):
    """OAuth token data stored on disk."""

    access_token: str
    refresh_token: str
    expires_at: float
    scope: str
    login: str


class FileTokenStorage:
    """File-based token storage in CLAUDE_PLUGIN_DATA directory."""

    def __init__(self, path: Path | None = None) -> None:
        if path is not None:
            self._path = path
        else:
            plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
            if plugin_data:
                self._path = Path(plugin_data) / "tokens.json"
            else:
                # Fallback: store relative to plugin root (predictable for manual runs)
                self._path = (
                    Path(__file__).parent.parent.parent / "data" / "tokens.json"
                )

    @property
    def path(self) -> Path:
        """Return the path to the token file."""
        return self._path

    def load(self) -> TokenData | None:
        """Load tokens from disk. Returns None if file is missing or corrupt."""
        if not self._path.exists():
            return None
        try:
            data = json.loads(self._path.read_text())
            return TokenData(**data)
        except (json.JSONDecodeError, TypeError, UnicodeDecodeError, OSError):
            return None

    def save(self, data: TokenData) -> None:
        """Atomically save tokens to disk via temp file + rename."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(dir=self._path.parent, suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, self._path)
        except Exception:
            Path(tmp_path).unlink(missing_ok=True)
            raise
