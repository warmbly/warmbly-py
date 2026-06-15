"""Shared pytest fixtures for the warmbly-py test suite."""

from __future__ import annotations

import pytest

BASE_URL = "https://api.warmbly.com/v1"


@pytest.fixture
def anyio_backend() -> str:
    """Run AnyIO-marked async tests on asyncio."""
    return "asyncio"


@pytest.fixture
def base_url() -> str:
    return BASE_URL
