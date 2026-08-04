"""The ``me`` resource: who this credential is.

Maps to ``GET /v1/me``. No scope gates it, so any valid credential can resolve
its own identity — which makes it the natural way to validate a key at setup
time and to label the connection in a UI.

``scopes`` is populated for API keys and OAuth tokens, and empty for browser
sessions, which are governed by organization roles rather than a scope bitmask.
"""

from __future__ import annotations

from collections.abc import Sequence

from .._models import BaseModel
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import RequestOptions

__all__ = [
    "AsyncMe",
    "Identity",
    "Me",
]


class Identity(BaseModel):
    """The caller's identity and what its credential may do.

    ``auth_type`` is ``"api_key"``, ``"oauth"``, or ``"jwt"``.
    """

    user_id: str | None = None
    email: str | None = None
    name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    organization_id: str | None = None
    organization_name: str | None = None
    auth_type: str | None = None
    scopes: Sequence[str] = []


class Me(SyncAPIResource):
    """Synchronous ``me`` resource (read-only)."""

    def retrieve(self, *, options: RequestOptions | None = None) -> Identity:
        """Resolve the caller's identity, organization, and granted scopes."""
        return self._get("/me", cast_to=Identity, options=options)


class AsyncMe(AsyncAPIResource):
    """Asynchronous ``me`` resource (read-only)."""

    async def retrieve(self, *, options: RequestOptions | None = None) -> Identity:
        """Resolve the caller's identity, organization, and granted scopes."""
        return await self._get("/me", cast_to=Identity, options=options)
