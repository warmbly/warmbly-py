"""The OAuth2 token model and the auto-refreshing token manager.

:class:`OAuth2Token` mirrors the RFC 6749 token-endpoint response and adds a
computed :attr:`~OAuth2Token.expires_at` absolute deadline so callers can reason
about staleness without re-reading wall-clock semantics.

:class:`TokenManager` and :class:`AsyncTokenManager` keep a valid access token
available: they refresh ahead of expiry (with a configurable skew), serialize
concurrent refreshes behind a lock (refresh tokens rotate, so two parallel
refreshes would invalidate each other), and persist the rotated refresh token
back to the provided :class:`~warmbly.oauth._storage.TokenStorage`.
"""

from __future__ import annotations

import asyncio
import threading
import time
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from .._exceptions import OAuthError
from .._models import BaseModel

if TYPE_CHECKING:
    from ._storage import TokenStorage

__all__ = [
    "DEFAULT_EXPIRY_SKEW",
    "AsyncTokenManager",
    "OAuth2Token",
    "TokenManager",
]

# Refresh this many seconds before the token's nominal expiry, so a token is
# never used in the window where it might expire mid-flight.
DEFAULT_EXPIRY_SKEW = 60.0


class OAuth2Token(BaseModel):
    """An OAuth2 token set returned by the token endpoint.

    Attributes:
        access_token: The bearer access token (``wmat_`` prefix). Send it as
            ``Authorization: Bearer <access_token>``.
        token_type: The token type; always ``"Bearer"`` for Warmbly.
        expires_in: Lifetime of ``access_token`` in seconds from issuance
            (``3600`` for Warmbly access tokens).
        refresh_token: The refresh token (``wmrt_`` prefix), if granted. It
            **rotates**: each refresh returns a new one and invalidates the old.
        scope: Space-delimited granted scopes, when the server narrows them.
        expires_at: Absolute Unix timestamp at which ``access_token`` expires,
            computed from ``expires_in`` at construction time. ``None`` if the
            server omitted ``expires_in``.
    """

    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    scope: str | None = None
    expires_at: float | None = None

    def model_post_init(self, __context: object) -> None:
        """Derive :attr:`expires_at` from :attr:`expires_in` if not supplied."""
        if self.expires_at is None and self.expires_in is not None:
            self.expires_at = time.time() + self.expires_in

    @property
    def scopes(self) -> list[str]:
        """The granted scopes as a list (empty if the server omitted ``scope``)."""
        return self.scope.split() if self.scope else []

    def is_expired(self, *, skew: float = DEFAULT_EXPIRY_SKEW) -> bool:
        """Return whether the access token is expired (or within *skew* of it).

        Args:
            skew: Seconds of safety margin treated as already-expired.

        Returns:
            ``True`` if the token should be refreshed before use. A token with
            no known ``expires_at`` is treated as not expired.
        """
        if self.expires_at is None:
            return False
        return time.time() >= self.expires_at - skew


# A refresh function takes the current refresh token and returns a fresh token
# set. The sync variant returns the token directly; the async variant awaits.
RefreshFn = Callable[[str], "OAuth2Token"]
AsyncRefreshFn = Callable[[str], Awaitable["OAuth2Token"]]


class TokenManager:
    """Keeps a valid access token available, refreshing as needed (sync).

    The manager loads the persisted token, and when it is expired (within
    ``skew`` seconds) it refreshes under a :class:`threading.Lock` so that
    concurrent callers do not race rotating refresh tokens. The rotated token is
    persisted back to *storage*.
    """

    def __init__(
        self,
        storage: TokenStorage,
        refresh_fn: RefreshFn,
        *,
        skew: float = DEFAULT_EXPIRY_SKEW,
    ) -> None:
        """Initialize the manager.

        Args:
            storage: Where the current token set is read from and written to.
            refresh_fn: Callable that exchanges a refresh token for a new
                :class:`OAuth2Token`. It must raise :class:`OAuthError` on
                ``invalid_grant`` so callers can trigger re-authentication.
            skew: Seconds before expiry at which a refresh is forced.
        """
        self._storage = storage
        self._refresh_fn = refresh_fn
        self._skew = skew
        self._lock = threading.Lock()

    def access_token(self) -> str:
        """Return a currently-valid access token, refreshing if necessary.

        Raises:
            OAuthError: If no token is stored (``no_token``), the stored token
                is expired but has no refresh token (``no_refresh_token``), or
                the refresh itself fails (e.g. ``invalid_grant``).
        """
        return self.get_token().access_token

    def get_token(self) -> OAuth2Token:
        """Return the current token set, refreshing it if expired.

        Raises:
            OAuthError: As described in :meth:`access_token`.
        """
        token = self._storage.load()
        if token is None:
            raise OAuthError("no_token", "No token stored; authenticate first.")
        if not token.is_expired(skew=self._skew):
            return token
        with self._lock:
            # Re-check under the lock: another thread may have refreshed already.
            token = self._storage.load()
            if token is None:
                raise OAuthError("no_token", "No token stored; authenticate first.")
            if not token.is_expired(skew=self._skew):
                return token
            if not token.refresh_token:
                raise OAuthError(
                    "no_refresh_token",
                    "Access token expired and no refresh token is available.",
                )
            refreshed = self._refresh_fn(token.refresh_token)
            self._storage.save(refreshed)
            return refreshed


class AsyncTokenManager:
    """Keeps a valid access token available, refreshing as needed (async).

    Mirrors :class:`TokenManager` but serializes refreshes with an
    :class:`asyncio.Lock` and awaits an async refresh callable.
    """

    def __init__(
        self,
        storage: TokenStorage,
        refresh_fn: AsyncRefreshFn,
        *,
        skew: float = DEFAULT_EXPIRY_SKEW,
    ) -> None:
        """Initialize the manager.

        Args:
            storage: Where the current token set is read from and written to.
            refresh_fn: Awaitable callable that exchanges a refresh token for a
                new :class:`OAuth2Token`; must raise :class:`OAuthError` on
                ``invalid_grant``.
            skew: Seconds before expiry at which a refresh is forced.
        """
        self._storage = storage
        self._refresh_fn = refresh_fn
        self._skew = skew
        self._lock = asyncio.Lock()

    async def access_token(self) -> str:
        """Return a currently-valid access token, refreshing if necessary.

        Raises:
            OAuthError: As described in :meth:`TokenManager.access_token`.
        """
        token = await self.get_token()
        return token.access_token

    async def get_token(self) -> OAuth2Token:
        """Return the current token set, refreshing it if expired.

        Raises:
            OAuthError: As described in :meth:`TokenManager.access_token`.
        """
        token = self._storage.load()
        if token is None:
            raise OAuthError("no_token", "No token stored; authenticate first.")
        if not token.is_expired(skew=self._skew):
            return token
        async with self._lock:
            token = self._storage.load()
            if token is None:
                raise OAuthError("no_token", "No token stored; authenticate first.")
            if not token.is_expired(skew=self._skew):
                return token
            if not token.refresh_token:
                raise OAuthError(
                    "no_refresh_token",
                    "Access token expired and no refresh token is available.",
                )
            refreshed = await self._refresh_fn(token.refresh_token)
            self._storage.save(refreshed)
            return refreshed
