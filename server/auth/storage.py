"""Token storage for OAuth credentials."""

from __future__ import annotations

from typing import TypedDict


class TokenData(TypedDict):
    """OAuth token data stored on disk."""

    access_token: str
    refresh_token: str
    expires_at: float


class FileTokenStorage:
    """Store and retrieve OAuth tokens from a JSON file."""

    def __init__(self, path: str) -> None:
        """Initialize storage with the given file path.

        Args:
            path: Absolute path to the token JSON file.
        """
        self._path = path

    def load(self) -> TokenData | None:
        """Load tokens from disk. Returns None if file missing or invalid."""
        ...

    def save(self, data: TokenData) -> None:
        """Persist token data to disk."""
        ...
