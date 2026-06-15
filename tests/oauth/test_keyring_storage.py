"""Tests for ``KeyringTokenStorage`` (keyring backend and file fallback)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from warmbly.oauth import KeyringTokenStorage, OAuth2Token


def _token(access: str = "wmat_x") -> OAuth2Token:
    return OAuth2Token(
        access_token=access,
        refresh_token="wmrt_y",
        expires_in=3600,
        scope="read_campaigns",
    )


class _FakeKeyring:
    """A minimal in-memory stand-in for the ``keyring`` module."""

    def __init__(self) -> None:
        self.store: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self.store.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self.store[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        del self.store[(service, username)]  # raises KeyError if absent


@pytest.fixture
def fake_keyring(monkeypatch: pytest.MonkeyPatch) -> _FakeKeyring:
    fake = _FakeKeyring()
    monkeypatch.setitem(sys.modules, "keyring", fake)
    return fake


def test_keyring_round_trip(fake_keyring: _FakeKeyring, tmp_path: Path) -> None:
    storage = KeyringTokenStorage(
        service="warmbly-test",
        username="alice",
        fallback_path=tmp_path / "fb.json",
    )
    assert storage.load() is None

    storage.save(_token())
    loaded = storage.load()
    assert loaded is not None
    assert loaded.access_token == "wmat_x"
    assert loaded.refresh_token == "wmrt_y"
    # It was stored in the keyring, not the file fallback.
    assert ("warmbly-test", "alice") in fake_keyring.store
    assert not (tmp_path / "fb.json").exists()


def test_keyring_clear(fake_keyring: _FakeKeyring, tmp_path: Path) -> None:
    storage = KeyringTokenStorage(
        service="warmbly-test",
        username="bob",
        fallback_path=tmp_path / "fb.json",
    )
    storage.save(_token())
    assert storage.load() is not None

    storage.clear()
    assert storage.load() is None
    # clear() on an already-empty entry is a no-op (suppressed KeyError).
    storage.clear()


def test_keyring_load_empty_returns_none(
    fake_keyring: _FakeKeyring, tmp_path: Path
) -> None:
    storage = KeyringTokenStorage(
        service="warmbly-test",
        username="empty",
        fallback_path=tmp_path / "fb.json",
    )
    # An empty-string password counts as no token.
    fake_keyring.set_password("warmbly-test", "empty", "")
    assert storage.load() is None


def test_default_fallback_path() -> None:
    storage = KeyringTokenStorage(service="svc", username="user")
    expected = Path.home() / ".warmbly" / "svc-user.json"
    assert storage._fallback.path == expected


def test_file_fallback_when_keyring_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Simulate keyring not being importable.
    monkeypatch.setitem(sys.modules, "keyring", None)
    fallback = tmp_path / "fb.json"
    storage = KeyringTokenStorage(
        service="warmbly-test",
        username="carol",
        fallback_path=fallback,
    )
    assert storage._keyring() is None

    assert storage.load() is None
    storage.save(_token("wmat_fallback"))
    # The token landed in the file fallback.
    assert fallback.exists()
    loaded = storage.load()
    assert loaded is not None
    assert loaded.access_token == "wmat_fallback"

    storage.clear()
    assert not fallback.exists()
    assert storage.load() is None
