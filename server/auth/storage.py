"""Token storage protocol for OAuth token persistence."""

from typing import Protocol, TypedDict


class TokenData(TypedDict, total=False):
    """OAuth token data structure."""

    access_token: str
    refresh_token: str
    expires_at: float  # Unix timestamp
    scope: str
    login: str


class TokenStorage(Protocol):
    """Protocol for storing and retrieving OAuth tokens."""

    def load(self) -> TokenData | None:
        """Load stored token data. Returns None if no tokens exist."""
        ...

    def save(self, data: TokenData) -> None:
        """Save token data persistently."""
        ...
