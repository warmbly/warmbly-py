"""The ``outreach`` resource: organization-wide sending guardrails.

Maps to the ``/v1/outreach/settings`` routes. These settings are what turn a
bounce into a suppression, pause a campaign whose complaint rate spikes, decide
how many attempts a send task gets, and choose which preflight checks block a
launch. Campaigns inherit them and can override individual branches through
``client.campaigns.update_advanced()``.

The tree is passed through as plain dictionaries: it is a nested settings
document, and typing every branch would ossify a surface that grows.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._models import BaseModel
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import RequestOptions

__all__ = [
    "AsyncOutreach",
    "Outreach",
    "OutreachSettings",
]


class OutreachSettings(BaseModel):
    """The organization's outreach settings.

    Each attribute is one branch of the settings tree: bounce handling, task
    reliability, A/B defaults, reply-intent keywords, send-time optimization,
    preflight checks, and which dashboard panels are shown.
    """

    bounce_pipeline: dict[str, Any] | None = None
    task_reliability: dict[str, Any] | None = None
    ab_testing: dict[str, Any] | None = None
    reply_intent: dict[str, Any] | None = None
    send_time_optimization: dict[str, Any] | None = None
    preflight: dict[str, Any] | None = None
    dashboard: dict[str, Any] | None = None
    custom: dict[str, Any] | None = None


class Outreach(SyncAPIResource):
    """Synchronous ``outreach`` resource."""

    def settings(self, *, options: RequestOptions | None = None) -> OutreachSettings:
        """Read the organization's outreach settings."""
        return self._get(
            "/outreach/settings", cast_to=OutreachSettings, options=options
        )

    def update_settings(
        self,
        *,
        settings: Mapping[str, Any],
        options: RequestOptions | None = None,
    ) -> None:
        """Replace the organization's outreach settings.

        This is a whole-document write, not a merge: read
        :meth:`settings` first, change the branch you care about, and send the
        result back.

        Args:
            settings: The full settings tree.
        """
        return self._patch(
            "/outreach/settings",
            cast_to=type(None),
            body={"settings": dict(settings)},
            options=options,
        )


class AsyncOutreach(AsyncAPIResource):
    """Asynchronous ``outreach`` resource."""

    async def settings(
        self, *, options: RequestOptions | None = None
    ) -> OutreachSettings:
        """Read the organization's outreach settings."""
        return await self._get(
            "/outreach/settings", cast_to=OutreachSettings, options=options
        )

    async def update_settings(
        self,
        *,
        settings: Mapping[str, Any],
        options: RequestOptions | None = None,
    ) -> None:
        """Replace the organization's outreach settings.

        This is a whole-document write, not a merge: read
        :meth:`settings` first, change the branch you care about, and send the
        result back.

        Args:
            settings: The full settings tree.
        """
        return await self._patch(
            "/outreach/settings",
            cast_to=type(None),
            body={"settings": dict(settings)},
            options=options,
        )
