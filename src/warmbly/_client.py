"""The top-level :class:`Warmbly` and :class:`AsyncWarmbly` clients.

A single client object owns all configuration and a shared connection pool, and
exposes each API resource group as a lazily-instantiated attribute
(``client.api_keys``, ``client.oauth_applications``, ...). Swap ``Warmbly`` for
``AsyncWarmbly`` and ``await`` the methods for the async variant.
"""

from __future__ import annotations

import os
from functools import cached_property

import httpx

from ._base_client import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    AsyncAPIClient,
    SyncAPIClient,
)
from ._exceptions import WarmblyError
from ._types import Timeout
from .resources import (
    ApiKeys,
    AsyncApiKeys,
    AsyncOAuthApplications,
    OAuthApplications,
)

__all__ = ["Warmbly", "AsyncWarmbly", "PRODUCTION_BASE_URL"]

PRODUCTION_BASE_URL = "https://api.warmbly.com/v1"


def _resolve_api_key(api_key: str | None) -> str:
    if api_key is None:
        api_key = os.environ.get("WARMBLY_API_KEY")
    if not api_key:
        raise WarmblyError(
            "No API key provided. Pass api_key=... or set the WARMBLY_API_KEY "
            "environment variable."
        )
    return api_key


def _resolve_base_url(base_url: str | None) -> str:
    return base_url or os.environ.get("WARMBLY_BASE_URL", PRODUCTION_BASE_URL)


class Warmbly(SyncAPIClient):
    """Synchronous Warmbly API client.

    Args:
        api_key: A Warmbly API key (``wmbly_...``) or OAuth2 access token
            (``wmat_...``). Falls back to the ``WARMBLY_API_KEY`` env var.
        base_url: API base URL. Falls back to ``WARMBLY_BASE_URL`` then the
            production endpoint.
        timeout: Per-request timeout in seconds or an :class:`httpx.Timeout`.
        max_retries: Number of automatic retries for transient failures.
        http_client: An optional pre-configured :class:`httpx.Client`.
    """

    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | Timeout | None = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.api_key = _resolve_api_key(api_key)
        super().__init__(
            base_url=_resolve_base_url(base_url),
            timeout=timeout,
            max_retries=max_retries,
            http_client=http_client,
        )

    @property
    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    @cached_property
    def api_keys(self) -> ApiKeys:
        return ApiKeys(self)

    @cached_property
    def oauth_applications(self) -> OAuthApplications:
        return OAuthApplications(self)


class AsyncWarmbly(AsyncAPIClient):
    """Asynchronous Warmbly API client.

    Mirrors :class:`Warmbly`; every resource method is a coroutine. Remember to
    ``await client.close()`` (or use ``async with AsyncWarmbly(...) as client``).
    """

    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | Timeout | None = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = _resolve_api_key(api_key)
        super().__init__(
            base_url=_resolve_base_url(base_url),
            timeout=timeout,
            max_retries=max_retries,
            http_client=http_client,
        )

    @property
    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    @cached_property
    def api_keys(self) -> AsyncApiKeys:
        return AsyncApiKeys(self)

    @cached_property
    def oauth_applications(self) -> AsyncOAuthApplications:
        return AsyncOAuthApplications(self)
