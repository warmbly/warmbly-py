"""Tests for the pluggable OAuth2 token storage backends."""

from __future__ import annotations

import stat
from pathlib import Path

from warmbly.oauth import FileTokenStorage, MemoryTokenStorage, OAuth2Token


def _token(access: str = "wmat_x") -> OAuth2Token:
    return OAuth2Token(
        access_token=access,
        refresh_token="wmrt_y",
        expires_in=3600,
        scope="read_campaigns",
    )


# --------------------------------------------------------------------------
# MemoryTokenStorage
# --------------------------------------------------------------------------
def test_memory_round_trip() -> None:
    storage = MemoryTokenStorage()
    assert storage.load() is None

    token = _token()
    storage.save(token)
    loaded = storage.load()
    assert loaded is not None
    assert loaded.access_token == "wmat_x"
    assert loaded.refresh_token == "wmrt_y"


def test_memory_seeded_and_clear() -> None:
    storage = MemoryTokenStorage(_token("wmat_seed"))
    assert storage.load() is not None
    storage.clear()
    assert storage.load() is None


# --------------------------------------------------------------------------
# FileTokenStorage
# --------------------------------------------------------------------------
def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def test_file_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "subdir" / "token.json"
    storage = FileTokenStorage(path)
    assert storage.load() is None  # absent file

    token = _token()
    storage.save(token)
    assert path.exists()

    loaded = storage.load()
    assert loaded is not None
    assert loaded.access_token == "wmat_x"
    assert loaded.refresh_token == "wmrt_y"
    assert loaded.scope == "read_campaigns"
    # expires_at survives a JSON round-trip.
    assert loaded.expires_at == token.expires_at


def test_file_written_with_0600(tmp_path: Path) -> None:
    path = tmp_path / "token.json"
    storage = FileTokenStorage(path)
    storage.save(_token())
    assert _mode(path) == 0o600


def test_file_overwrite_tightens_loose_perms(tmp_path: Path) -> None:
    path = tmp_path / "token.json"
    # Pre-create the file world-readable to simulate a loose pre-existing file.
    path.write_text("{}", encoding="utf-8")
    path.chmod(0o644)
    assert _mode(path) == 0o644

    storage = FileTokenStorage(path)
    storage.save(_token())
    # Saving must re-assert the restrictive 0600 mode.
    assert _mode(path) == 0o600


def test_file_clear_removes_file(tmp_path: Path) -> None:
    path = tmp_path / "token.json"
    storage = FileTokenStorage(path)
    storage.save(_token())
    assert path.exists()
    storage.clear()
    assert not path.exists()
    # clear() on a missing file is a no-op.
    storage.clear()
    assert storage.load() is None


def test_file_empty_file_loads_none(tmp_path: Path) -> None:
    path = tmp_path / "token.json"
    path.write_text("   \n", encoding="utf-8")
    storage = FileTokenStorage(path)
    assert storage.load() is None
