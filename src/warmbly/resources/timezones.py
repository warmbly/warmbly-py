"""The ``timezones`` resource — read-only IANA timezone catalog.

Maps to ``GET /v1/timezones``. The endpoint returns a flat list of supported
timezones (used when scheduling campaign sends). It is modelled as a permissive
:class:`~warmbly._models.BaseModel` so both the wrapped list and any additional
metadata the backend returns are preserved.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pydantic import model_validator

from .._models import BaseModel
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import RequestOptions

__all__ = [
    "AsyncTimezones",
    "TimezoneList",
    "Timezones",
]


class TimezoneList(BaseModel):
    """The catalog of supported timezones.

    The backend returns a bare JSON list; it is exposed here under
    :attr:`data`. Each entry is left as a raw mapping (e.g.
    ``{"name": "America/New_York", "offset": "-05:00"}``) because the exact
    per-entry shape may evolve.

    Attributes:
        data: The supported timezone entries.
    """

    data: Sequence[dict[str, Any]] = []

    @model_validator(mode="before")
    @classmethod
    def _wrap_bare_list(cls, value: Any) -> Any:
        """Accept either a bare list or a ``{"data": [...]}`` envelope."""
        if isinstance(value, list):
            return {"data": value}
        return value


class Timezones(SyncAPIResource):
    """Synchronous ``timezones`` resource (read-only)."""

    def list(self, *, options: RequestOptions | None = None) -> TimezoneList:
        """List all supported timezones.

        Args:
            options: Optional per-request overrides.
        """
        return self._get("/timezones", cast_to=TimezoneList, options=options)


class AsyncTimezones(AsyncAPIResource):
    """Asynchronous ``timezones`` resource (read-only)."""

    async def list(self, *, options: RequestOptions | None = None) -> TimezoneList:
        """List all supported timezones.

        Args:
            options: Optional per-request overrides.
        """
        return await self._get("/timezones", cast_to=TimezoneList, options=options)
