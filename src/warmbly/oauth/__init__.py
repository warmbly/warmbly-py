"""The Warmbly OAuth2 client subsystem.

This package implements the two OAuth2 grants Warmbly's authorization server
accepts — **authorization_code + PKCE (S256)** and **refresh_token** — plus
token revocation, secure token storage, and auto-refreshing token management.

There is no client-credentials grant: every token is bound to a user who
consented, so machine-to-machine access uses an API key instead.

Typical authorization-code flow::

    from warmbly.oauth import OAuth2Client

    oauth = OAuth2Client(
        client_id="wmcid_...",
        client_secret="wmcs_...",
        redirect_uri="https://app.example.com/callback",
    )
    url, state, verifier = oauth.authorization_url(scopes=["read_campaigns"])
    # ... redirect the user to `url`, capture `code` and `state` on callback ...
    token = oauth.exchange_code(
        code, code_verifier=verifier, state=state, expected_state=state
    )
    print(token.access_token)

This is the one subsystem permitted to use ``httpx`` directly; token-endpoint and
transport errors are surfaced as :class:`~warmbly.OAuthError`.
"""

from __future__ import annotations

from ._discovery import (
    AuthorizationServerMetadata,
    async_discover,
    clear_discovery_cache,
    discover,
)
from ._flow import AsyncOAuth2Client, OAuth2Client
from ._pkce import challenge_for_verifier, generate_pkce_pair, verify_pkce
from ._storage import (
    FileTokenStorage,
    KeyringTokenStorage,
    MemoryTokenStorage,
    TokenStorage,
)
from ._tokens import AsyncTokenManager, OAuth2Token, TokenManager

__all__ = [
    "AsyncOAuth2Client",
    "AsyncTokenManager",
    "AuthorizationServerMetadata",
    "FileTokenStorage",
    "KeyringTokenStorage",
    "MemoryTokenStorage",
    "OAuth2Client",
    "OAuth2Token",
    "TokenManager",
    "TokenStorage",
    "async_discover",
    "challenge_for_verifier",
    "clear_discovery_cache",
    "discover",
    "generate_pkce_pair",
    "verify_pkce",
]
