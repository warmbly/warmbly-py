"""Exhaustive tests for warmbly.oauth._tokens (sync + async paths)."""

from __future__ import annotations

import pytest

from warmbly._exceptions import OAuthError
from warmbly.oauth._tokens import (
    DEFAULT_EXPIRY_SKEW,
    AsyncTokenManager,
    OAuth2Token,
    TokenManager,
)


class _StaticStorage:
    """Minimal TokenStorage: always returns the same token, records saves."""

    def __init__(self, token: OAuth2Token | None) -> None:
        self._token = token
        self.saved: list[OAuth2Token] = []

    def load(self) -> OAuth2Token | None:
        return self._token

    def save(self, token: OAuth2Token) -> None:
        self.saved.append(token)
        self._token = token


class _SequenceStorage:
    """TokenStorage whose load() yields a queued sequence of tokens.

    Used to drive the double-check-under-lock path: the first load() (outside
    the lock) returns an expired token, the second (inside the lock) returns a
    fresh one, as if another thread/task refreshed in between.
    """

    def __init__(self, tokens: list[OAuth2Token | None]) -> None:
        self._queue = list(tokens)
        self._last: OAuth2Token | None = None
        self.saved: list[OAuth2Token] = []

    def load(self) -> OAuth2Token | None:
        if self._queue:
            self._last = self._queue.pop(0)
        return self._last

    def save(self, token: OAuth2Token) -> None:
        self.saved.append(token)
        self._last = token


# --------------------------------------------------------------------------
# OAuth2Token.model_post_init / scopes
# --------------------------------------------------------------------------
def test_model_post_init_derives_expires_at(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("warmbly.oauth._tokens.time.time", lambda: 1000.0)
    token = OAuth2Token(access_token="wmat_x", expires_in=3600)
    assert token.expires_at == 1000.0 + 3600


def test_model_post_init_leaves_supplied_expires_at(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("warmbly.oauth._tokens.time.time", lambda: 1000.0)
    token = OAuth2Token(access_token="wmat_x", expires_in=3600, expires_at=42.0)
    assert token.expires_at == 42.0


def test_model_post_init_no_expires_in_keeps_none() -> None:
    token = OAuth2Token(access_token="wmat_x")
    assert token.expires_at is None


def test_scopes_splits_and_empty() -> None:
    assert OAuth2Token(access_token="x", scope="read write").scopes == [
        "read",
        "write",
    ]
    assert OAuth2Token(access_token="x", scope=None).scopes == []
    assert OAuth2Token(access_token="x").scopes == []


# --------------------------------------------------------------------------
# OAuth2Token.is_expired
# --------------------------------------------------------------------------
def test_is_expired_none_expires_at_is_false() -> None:
    assert OAuth2Token(access_token="x").is_expired() is False


def test_is_expired_fresh_token_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("warmbly.oauth._tokens.time.time", lambda: 1000.0)
    token = OAuth2Token(access_token="x", expires_at=5000.0)
    assert token.is_expired() is False


def test_is_expired_within_skew_true(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("warmbly.oauth._tokens.time.time", lambda: 1000.0)
    token = OAuth2Token(access_token="x", expires_at=1030.0)
    assert token.is_expired(skew=60) is True


def test_is_expired_default_skew(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("warmbly.oauth._tokens.time.time", lambda: 1000.0)
    token = OAuth2Token(access_token="x", expires_at=1000.0 + DEFAULT_EXPIRY_SKEW - 1)
    assert token.is_expired() is True


def test_is_expired_skew_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("warmbly.oauth._tokens.time.time", lambda: 1000.0)
    # expires_at - skew == now -> time.time() >= deadline -> True at boundary.
    at_boundary = OAuth2Token(access_token="x", expires_at=1060.0)
    assert at_boundary.is_expired(skew=60) is True
    # One second past the boundary the token is still fresh.
    just_fresh = OAuth2Token(access_token="x", expires_at=1061.0)
    assert just_fresh.is_expired(skew=60) is False


# --------------------------------------------------------------------------
# TokenManager (sync)
# --------------------------------------------------------------------------
def _expired(refresh_token: str | None = "wmrt_old") -> OAuth2Token:
    return OAuth2Token(
        access_token="wmat_old",
        refresh_token=refresh_token,
        expires_at=0.0,
    )


def test_sync_no_token_raises() -> None:
    storage = _StaticStorage(None)
    manager = TokenManager(storage, lambda rt: OAuth2Token(access_token="x"))
    with pytest.raises(OAuthError) as exc:
        manager.get_token()
    assert exc.value.error == "no_token"


def test_sync_fresh_token_no_refresh() -> None:
    fresh = OAuth2Token(access_token="wmat_fresh", expires_in=3600)
    storage = _StaticStorage(fresh)
    calls: list[str] = []

    def refresh(rt: str) -> OAuth2Token:
        calls.append(rt)
        raise AssertionError("must not refresh")

    manager = TokenManager(storage, refresh)
    assert manager.access_token() == "wmat_fresh"
    assert calls == []


def test_sync_expired_refreshes_and_saves() -> None:
    storage = _StaticStorage(_expired())
    calls: list[str] = []

    def refresh(rt: str) -> OAuth2Token:
        calls.append(rt)
        return OAuth2Token(
            access_token="wmat_new",
            refresh_token="wmrt_rot",
            expires_in=3600,
        )

    manager = TokenManager(storage, refresh)
    token = manager.get_token()
    assert calls == ["wmrt_old"]
    assert token.access_token == "wmat_new"
    assert len(storage.saved) == 1
    assert storage.load().refresh_token == "wmrt_rot"


def test_sync_expired_without_refresh_token_raises() -> None:
    storage = _StaticStorage(_expired(refresh_token=None))
    manager = TokenManager(storage, lambda rt: OAuth2Token(access_token="x"))
    with pytest.raises(OAuthError) as exc:
        manager.get_token()
    assert exc.value.error == "no_refresh_token"


def test_sync_double_check_under_lock_returns_fresh() -> None:
    fresh = OAuth2Token(access_token="wmat_fresh", expires_in=3600)
    storage = _SequenceStorage([_expired(), fresh])

    def refresh(rt: str) -> OAuth2Token:
        raise AssertionError("must not refresh when re-check finds fresh token")

    manager = TokenManager(storage, refresh)
    token = manager.get_token()
    assert token.access_token == "wmat_fresh"
    assert storage.saved == []


def test_sync_double_check_under_lock_none_raises() -> None:
    storage = _SequenceStorage([_expired(), None])
    manager = TokenManager(storage, lambda rt: OAuth2Token(access_token="x"))
    with pytest.raises(OAuthError) as exc:
        manager.get_token()
    assert exc.value.error == "no_token"


# --------------------------------------------------------------------------
# AsyncTokenManager
# --------------------------------------------------------------------------
@pytest.mark.anyio
async def test_async_no_token_raises() -> None:
    storage = _StaticStorage(None)

    async def refresh(rt: str) -> OAuth2Token:
        raise AssertionError("must not refresh")

    manager = AsyncTokenManager(storage, refresh)
    with pytest.raises(OAuthError) as exc:
        await manager.get_token()
    assert exc.value.error == "no_token"


@pytest.mark.anyio
async def test_async_fresh_token_no_refresh() -> None:
    fresh = OAuth2Token(access_token="wmat_fresh", expires_in=3600)
    storage = _StaticStorage(fresh)

    async def refresh(rt: str) -> OAuth2Token:
        raise AssertionError("must not refresh")

    manager = AsyncTokenManager(storage, refresh)
    assert await manager.access_token() == "wmat_fresh"


@pytest.mark.anyio
async def test_async_expired_refreshes_and_saves() -> None:
    storage = _StaticStorage(_expired())
    calls: list[str] = []

    async def refresh(rt: str) -> OAuth2Token:
        calls.append(rt)
        return OAuth2Token(
            access_token="wmat_new",
            refresh_token="wmrt_rot",
            expires_in=3600,
        )

    manager = AsyncTokenManager(storage, refresh)
    token = await manager.get_token()
    assert calls == ["wmrt_old"]
    assert token.access_token == "wmat_new"
    assert len(storage.saved) == 1
    assert storage.load().refresh_token == "wmrt_rot"


@pytest.mark.anyio
async def test_async_expired_without_refresh_token_raises() -> None:
    storage = _StaticStorage(_expired(refresh_token=None))

    async def refresh(rt: str) -> OAuth2Token:
        raise AssertionError("must not refresh")

    manager = AsyncTokenManager(storage, refresh)
    with pytest.raises(OAuthError) as exc:
        await manager.get_token()
    assert exc.value.error == "no_refresh_token"


@pytest.mark.anyio
async def test_async_double_check_under_lock_returns_fresh() -> None:
    fresh = OAuth2Token(access_token="wmat_fresh", expires_in=3600)
    storage = _SequenceStorage([_expired(), fresh])

    async def refresh(rt: str) -> OAuth2Token:
        raise AssertionError("must not refresh when re-check finds fresh token")

    manager = AsyncTokenManager(storage, refresh)
    token = await manager.get_token()
    assert token.access_token == "wmat_fresh"
    assert storage.saved == []


@pytest.mark.anyio
async def test_async_double_check_under_lock_none_raises() -> None:
    storage = _SequenceStorage([_expired(), None])

    async def refresh(rt: str) -> OAuth2Token:
        raise AssertionError("must not refresh")

    manager = AsyncTokenManager(storage, refresh)
    with pytest.raises(OAuthError) as exc:
        await manager.get_token()
    assert exc.value.error == "no_token"
