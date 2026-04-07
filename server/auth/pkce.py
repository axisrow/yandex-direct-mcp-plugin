"""PKCE (Proof Key for Code Exchange) support for Yandex OAuth."""

import base64
import hashlib
import secrets


def generate_code_verifier() -> str:
    """Generate a random code_verifier (43-128 chars, URL-safe)."""
    return secrets.token_urlsafe(96)[:128]


def generate_code_challenge(verifier: str) -> str:
    """Compute S256 code_challenge: BASE64URL(SHA256(verifier))."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
