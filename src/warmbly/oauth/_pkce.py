"""PKCE (Proof Key for Code Exchange) helpers: RFC 7636, S256 only.

Public clients must protect the authorization code with a PKCE pair: a random
``code_verifier`` and its ``code_challenge`` (the base64url-encoded SHA-256 of
the verifier). Warmbly only supports the ``S256`` method; the legacy ``plain``
method is never produced or accepted here.
"""

from __future__ import annotations

import base64
import hashlib
import secrets

__all__ = ["challenge_for_verifier", "generate_pkce_pair", "verify_pkce"]

# RFC 7636 section 4.1 constrains the verifier length to 43-128 characters.
# Thirty-two random bytes encode to a 43-character base64url string (the minimum).
_VERIFIER_BYTES = 32


def _b64url_no_pad(raw: bytes) -> str:
    """Base64url-encode *raw* without trailing ``=`` padding (RFC 7636 §A)."""
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def challenge_for_verifier(verifier: str) -> str:
    """Return the ``S256`` code challenge for a given *verifier*.

    Args:
        verifier: A ``code_verifier`` string.

    Returns:
        The base64url-encoded (unpadded) SHA-256 digest of *verifier*.
    """
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return _b64url_no_pad(digest)


def generate_pkce_pair() -> tuple[str, str]:
    """Generate a fresh PKCE ``(verifier, challenge)`` pair using ``S256``.

    The verifier is 43 base64url characters of cryptographically random data;
    the challenge is the base64url-encoded (unpadded) SHA-256 of the verifier,
    per RFC 7636.

    Returns:
        A ``(code_verifier, code_challenge)`` tuple.
    """
    verifier = _b64url_no_pad(secrets.token_bytes(_VERIFIER_BYTES))
    return verifier, challenge_for_verifier(verifier)


def verify_pkce(verifier: str, challenge: str) -> bool:
    """Constant-time check that *challenge* is the ``S256`` challenge of *verifier*.

    Args:
        verifier: The ``code_verifier`` presented at the token endpoint.
        challenge: The ``code_challenge`` sent to the authorization endpoint.

    Returns:
        ``True`` if they correspond under ``S256``, otherwise ``False``.
    """
    return secrets.compare_digest(challenge_for_verifier(verifier), challenge)
