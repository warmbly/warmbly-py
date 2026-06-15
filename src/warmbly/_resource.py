"""Base classes for API resources.

A resource is a thin, typed facade over the transport: it binds the client's
request helpers so each method reads as a single ``self._post(...)`` /
``self._get_api_list(...)`` call. Every resource group (``api_keys``,
``campaigns``, ...) subclasses one of these.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._base_client import AsyncAPIClient, SyncAPIClient

__all__ = ["AsyncAPIResource", "SyncAPIResource"]


class SyncAPIResource:
    """Base class for synchronous resource groups."""

    def __init__(self, client: SyncAPIClient) -> None:
        self._client = client
        self._get = client.get
        self._post = client.post
        self._patch = client.patch
        self._put = client.put
        self._delete = client.delete
        self._get_api_list = client.get_api_list


class AsyncAPIResource:
    """Base class for asynchronous resource groups."""

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client
        self._get = client.get
        self._post = client.post
        self._patch = client.patch
        self._put = client.put
        self._delete = client.delete
        self._get_api_list = client.get_api_list
