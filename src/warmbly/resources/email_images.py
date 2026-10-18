"""The ``email_images`` resource: images hosted for use in email bodies.

Maps to the ``/v1/email-images`` route group.
"""

from __future__ import annotations

from .._resource import AsyncAPIResource, SyncAPIResource

__all__ = ["AsyncEmailImages", "EmailImages"]


class EmailImages(SyncAPIResource):
    """Synchronous ``email_images`` resource."""


class AsyncEmailImages(AsyncAPIResource):
    """Asynchronous ``email_images`` resource."""
