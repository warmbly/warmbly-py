"""Pluggable persistence for OAuth2 token sets.

Three backends are provided:

* :class:`MemoryTokenStorage` — process-local, non-persistent (good for tests
  and short-lived scripts).
* :class:`FileTokenStorage` — a JSON file written with ``0600`` permissions so
  only the owning user can read the stored secrets.
* :class:`KeyringTokenStorage` — the OS secret store (Keychain / Credential
  Locker / Secret Service) via the optional ``keyring`` dependency, falling back
  to a :class:`FileTokenStorage` when ``keyring`` is not installed.

All backends implement the :class:`TokenStorage` protocol, so they are
interchangeable wherever a storage is accepted.
"""

from __future__ import annotations

import contextlib
import json
import os
import stat
from pathlib import Path
from typing import Protocol, runtime_checkable

from .._utils import logger
from ._tokens import OAuth2Token

__all__ = [
    "FileTokenStorage",
    "KeyringTokenStorage",
    "MemoryTokenStorage",
    "TokenStorage",
]

_FILE_MODE = stat.S_IRUSR | stat.S_IWUSR  # 0o600


@runtime_checkable
class TokenStorage(Protocol):
    """Persistence contract for a single OAuth2 token set.

    Implementations store at most one :class:`OAuth2Token` and must round-trip
    it faithfully (including the rotated ``refresh_token``).
    """

    def load(self) -> OAuth2Token | None:
        """Return the stored token, or ``None`` if nothing is stored."""
        ...

    def save(self, token: OAuth2Token) -> None:
        """Persist *token*, replacing any previously stored value."""
        ...

    def clear(self) -> None:
        """Remove any stored token."""
        ...


def _serialize(token: OAuth2Token) -> str:
    return token.to_json(indent=None)


def _deserialize(raw: str) -> OAuth2Token:
    return OAuth2Token.model_validate(json.loads(raw))


class MemoryTokenStorage:
    """In-memory, process-local token storage (not persisted to disk)."""

    def __init__(self, token: OAuth2Token | None = None) -> None:
        """Initialize, optionally seeding with an existing *token*."""
        self._token = token

    def load(self) -> OAuth2Token | None:
        """Return the in-memory token, or ``None``."""
        return self._token

    def save(self, token: OAuth2Token) -> None:
        """Replace the in-memory token."""
        self._token = token

    def clear(self) -> None:
        """Drop the in-memory token."""
        self._token = None


class FileTokenStorage:
    """Token storage backed by a JSON file with ``0600`` permissions."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        """Initialize with the *path* of the backing file.

        The parent directory is created on first :meth:`save`; the file itself
        is always (re)written with owner-only read/write permissions.
        """
        self._path = Path(path)

    @property
    def path(self) -> Path:
        """The filesystem path of the backing file."""
        return self._path

    def load(self) -> OAuth2Token | None:
        """Return the persisted token, or ``None`` if the file is absent/empty."""
        try:
            raw = self._path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        if not raw.strip():
            return None
        return _deserialize(raw)

    def save(self, token: OAuth2Token) -> None:
        """Write *token* to disk with owner-only (``0600``) permissions."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # Create with restrictive perms from the start, then write, so the
        # secret is never momentarily world-readable.
        fd = os.open(self._path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, _FILE_MODE)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(_serialize(token))
        finally:
            # Re-assert perms in case the file pre-existed with a wider mode.
            self._path.chmod(_FILE_MODE)

    def clear(self) -> None:
        """Delete the backing file if it exists."""
        self._path.unlink(missing_ok=True)


class KeyringTokenStorage:
    """Token storage in the OS secret store, with a file fallback.

    Uses the optional ``keyring`` package. If ``keyring`` is not importable, all
    operations transparently delegate to a :class:`FileTokenStorage` so the SDK
    keeps working without the extra dependency.
    """

    def __init__(
        self,
        *,
        service: str = "warmbly",
        username: str = "default",
        fallback_path: str | os.PathLike[str] | None = None,
    ) -> None:
        """Initialize the keyring-backed storage.

        Args:
            service: The keyring service name under which the token is stored.
            username: The keyring entry name (use distinct values to store
                tokens for multiple accounts).
            fallback_path: Path for the :class:`FileTokenStorage` used when
                ``keyring`` is unavailable. Defaults to
                ``~/.warmbly/<service>-<username>.json``.
        """
        self._service = service
        self._username = username
        if fallback_path is None:
            fallback_path = Path.home() / ".warmbly" / f"{service}-{username}.json"
        self._fallback = FileTokenStorage(fallback_path)

    def _keyring(self) -> object | None:
        try:
            import keyring
        except ImportError:
            logger.debug("keyring not installed; using file fallback for tokens")
            return None
        return keyring

    def load(self) -> OAuth2Token | None:
        """Return the stored token from the keyring (or the file fallback)."""
        keyring = self._keyring()
        if keyring is None:
            return self._fallback.load()
        raw = keyring.get_password(self._service, self._username)  # type: ignore[attr-defined]
        if not raw:
            return None
        return _deserialize(raw)

    def save(self, token: OAuth2Token) -> None:
        """Persist *token* in the keyring (or the file fallback)."""
        keyring = self._keyring()
        if keyring is None:
            self._fallback.save(token)
            return
        keyring.set_password(  # type: ignore[attr-defined]
            self._service, self._username, _serialize(token)
        )

    def clear(self) -> None:
        """Remove the stored token from the keyring (or the file fallback)."""
        keyring = self._keyring()
        if keyring is None:
            self._fallback.clear()
            return
        # keyring raises if the entry is absent; deleting a missing token is a no-op.
        with contextlib.suppress(Exception):
            keyring.delete_password(self._service, self._username)  # type: ignore[attr-defined]
