"""Tests for OAuth2Token expiry and the (Async)TokenManager refresh logic."""

from __future__ import annotations

import time

import pytest

from warmbly import OAuthError
from warmbly.oauth import (
    AsyncTokenManager,
    MemoryTokenStorage,
    OAuth2Token,
    TokenManager,
)


# --------------------------------------------------------------------------
# OAuth2Token expiry
# --------------------------------------------------------------------------
def test_expires_at_computed_from_expires_in() -> None:
    before = time.time()
    token = OAuth2Token(access_token="wmat_x", expires_in=3600)
    after = time.time()
    assert token.expires_at is not None
    assert before + 3600 <= token.expires_at <= after + 3600


def test_expires_at_respected_when_supplied() -> None:
    explicit = time.time() + 999
    token = OAuth2Token(access_token="wmat_x", expires_in=3600, expires_at=explicit)
    assert token.expires_at == explicit


def test_no_expires_in_means_no_expires_at_and_not_expired() -> None:
    token = OAuth2Token(access_token="wmat_x")
    assert token.expires_at is None
    assert token.is_expired() is False


def test_is_expired_true_for_past_token() -> None:
    token = OAuth2Token(access_token="wmat_x", expires_at=time.time() - 10)
    assert token.is_expired(skew=0) is True


def test_is_expired_accounts_for_skew() -> None:
    # Expires in 30s, but with a 60s skew it should already be considered stale.
    token = OAuth2Token(access_token="wmat_x", expires_at=time.time() + 30)
    assert token.is_expired(skew=60) is True
    assert token.is_expired(skew=0) is False


def test_scopes_split_from_scope_string() -> None:
    token = OAuth2Token(access_token="wmat_x", scope="a b c")
    assert token.scopes == ["a", "b", "c"]
    assert OAuth2Token(access_token="wmat_x").scopes == []


# --------------------------------------------------------------------------
# TokenManager (sync)
# --------------------------------------------------------------------------
def test_manager_returns_valid_token_without_refresh() -> None:
    token = OAuth2Token(access_token="wmat_valid", expires_in=3600)
    storage = MemoryTokenStorage(token)
    calls: list[str] = []

    def refresh(rt: str) -> OAuth2Token:
        calls.append(rt)
        raise AssertionError("should not refresh a valid token")

    manager = TokenManager(storage, refresh)
    assert manager.access_token() == "wmat_valid"
    assert calls == []


def test_manager_refreshes_expired_and_persists_rotated_refresh_token() -> None:
    expired = OAuth2Token(
        access_token="wmat_old",
        refresh_token="wmrt_old",
        expires_at=time.time() - 1,
    )
    storage = MemoryTokenStorage(expired)
    seen: list[str] = []

    def refresh(rt: str) -> OAuth2Token:
        seen.append(rt)
        return OAuth2Token(
            access_token="wmat_new",
            refresh_token="wmrt_rotated",
            expires_in=3600,
        )

    manager = TokenManager(storage, refresh)
    token = manager.get_token()

    assert seen == ["wmrt_old"]
    assert token.access_token == "wmat_new"
    # The rotated refresh token must be persisted back to storage.
    persisted = storage.load()
    assert persisted is not None
    assert persisted.refresh_token == "wmrt_rotated"
    assert persisted.access_token == "wmat_new"


def test_manager_invalid_grant_on_refresh_propagates() -> None:
    expired = OAuth2Token(
        access_token="wmat_old",
        refresh_token="wmrt_old",
        expires_at=time.time() - 1,
    )
    storage = MemoryTokenStorage(expired)

    def refresh(rt: str) -> OAuth2Token:
        raise OAuthError("invalid_grant", "refresh token revoked")

    manager = TokenManager(storage, refresh)
    with pytest.raises(OAuthError) as excinfo:
        manager.get_token()
    assert excinfo.value.error == "invalid_grant"
    # The stored (now-invalid) token is left untouched for the caller to clear.
    assert storage.load() is not None


def test_manager_no_token_raises() -> None:
    storage = MemoryTokenStorage()
    manager = TokenManager(storage, lambda rt: OAuth2Token(access_token="x"))
    with pytest.raises(OAuthError) as excinfo:
        manager.get_token()
    assert excinfo.value.error == "no_token"


def test_manager_expired_without_refresh_token_raises() -> None:
    expired = OAuth2Token(access_token="wmat_old", expires_at=time.time() - 1)
    storage = MemoryTokenStorage(expired)
    manager = TokenManager(storage, lambda rt: OAuth2Token(access_token="x"))
    with pytest.raises(OAuthError) as excinfo:
        manager.get_token()
    assert excinfo.value.error == "no_refresh_token"


# --------------------------------------------------------------------------
# AsyncTokenManager
# --------------------------------------------------------------------------
@pytest.mark.anyio
async def test_async_manager_returns_valid_token_without_refresh() -> None:
    token = OAuth2Token(access_token="wmat_valid", expires_in=3600)
    storage = MemoryTokenStorage(token)

    async def refresh(rt: str) -> OAuth2Token:
        raise AssertionError("should not refresh")

    manager = AsyncTokenManager(storage, refresh)
    assert await manager.access_token() == "wmat_valid"


@pytest.mark.anyio
async def test_async_manager_refreshes_and_persists() -> None:
    expired = OAuth2Token(
        access_token="wmat_old",
        refresh_token="wmrt_old",
        expires_at=time.time() - 1,
    )
    storage = MemoryTokenStorage(expired)
    seen: list[str] = []

    async def refresh(rt: str) -> OAuth2Token:
        seen.append(rt)
        return OAuth2Token(
            access_token="wmat_new",
            refresh_token="wmrt_rotated",
            expires_in=3600,
        )

    manager = AsyncTokenManager(storage, refresh)
    token = await manager.get_token()

    assert seen == ["wmrt_old"]
    assert token.access_token == "wmat_new"
    persisted = storage.load()
    assert persisted is not None
    assert persisted.refresh_token == "wmrt_rotated"


@pytest.mark.anyio
async def test_async_manager_invalid_grant_propagates() -> None:
    expired = OAuth2Token(
        access_token="wmat_old",
        refresh_token="wmrt_old",
        expires_at=time.time() - 1,
    )
    storage = MemoryTokenStorage(expired)

    async def refresh(rt: str) -> OAuth2Token:
        raise OAuthError("invalid_grant", "revoked")

    manager = AsyncTokenManager(storage, refresh)
    with pytest.raises(OAuthError) as excinfo:
        await manager.get_token()
    assert excinfo.value.error == "invalid_grant"
