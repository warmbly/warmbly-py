"""The ``email_images`` resource: images hosted for use in email bodies.

Maps to the ``/v1/email-images`` route group. An uploaded image gets a public
``url`` that a recipient's mail client fetches with no session, so place that
URL in an ``<img src>`` in a template or message body. Uploads count against
the workspace's storage quota.
"""

from __future__ import annotations

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions

__all__ = ["AsyncEmailImages", "EmailImage", "EmailImageDeleted", "EmailImages"]


class EmailImage(BaseModel):
    """One image in the workspace's library for email bodies.

    ``url`` is the public address to embed. ``width`` and ``height`` are 0 for
    a WebP, whose dimensions the server does not read. ``mime_type`` is the
    sniffed type (``image/png``, ``image/jpeg``, ``image/gif`` or
    ``image/webp``), not the one the upload declared.
    """

    id: str
    organization_id: str | None = None
    user_id: str | None = None
    filename: str | None = None
    mime_type: str | None = None
    size: int | None = None
    width: int | None = None
    height: int | None = None
    url: str | None = None
    created_at: str | None = None


class EmailImageDeleted(BaseModel):
    """The result of deleting an image (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class EmailImages(SyncAPIResource):
    """Synchronous ``email_images`` resource."""

    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[EmailImage]:
        """List the workspace's images, newest first (auto-paginating).

        Requires the ``READ_CAMPAIGNS`` permission.

        Args:
            limit: Page size, 1 to 100 (default 40).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/email-images",
            model=EmailImage,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def upload(
        self,
        *,
        file: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        options: RequestOptions | None = None,
    ) -> EmailImage:
        """Upload an image to the library (multipart).

        Requires the ``WRITE_CAMPAIGNS`` permission. The image must be a PNG,
        JPG, GIF or WebP of at most 5 MB and 4000 px on each side; the server
        decides the type from the bytes, not from *content_type*. A workspace
        over its storage quota is refused.

        Args:
            file: The raw image bytes.
            filename: The upload filename, kept as the image's display name.
            content_type: The image's MIME type.
        """
        return self._client.request(
            cast_to=EmailImage,
            method="POST",
            path="/email-images",
            files={"file": (filename, file, content_type)},
            options=options,
        )

    def delete(
        self, image_id: str, *, options: RequestOptions | None = None
    ) -> EmailImageDeleted:
        """Delete an image and its hosted bytes.

        Requires the ``WRITE_CAMPAIGNS`` permission. Any email already sent
        with this image loses it.
        """
        return self._delete(
            f"/email-images/{image_id}", cast_to=EmailImageDeleted, options=options
        )


class AsyncEmailImages(AsyncAPIResource):
    """Asynchronous ``email_images`` resource."""

    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[EmailImage]:
        """List the workspace's images, newest first (auto-paginating).

        Requires the ``READ_CAMPAIGNS`` permission.

        Args:
            limit: Page size, 1 to 100 (default 40).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/email-images",
            model=EmailImage,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def upload(
        self,
        *,
        file: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        options: RequestOptions | None = None,
    ) -> EmailImage:
        """Upload an image to the library (multipart).

        Requires the ``WRITE_CAMPAIGNS`` permission. The image must be a PNG,
        JPG, GIF or WebP of at most 5 MB and 4000 px on each side; the server
        decides the type from the bytes, not from *content_type*. A workspace
        over its storage quota is refused.

        Args:
            file: The raw image bytes.
            filename: The upload filename, kept as the image's display name.
            content_type: The image's MIME type.
        """
        return await self._client.request(
            cast_to=EmailImage,
            method="POST",
            path="/email-images",
            files={"file": (filename, file, content_type)},
            options=options,
        )

    async def delete(
        self, image_id: str, *, options: RequestOptions | None = None
    ) -> EmailImageDeleted:
        """Delete an image and its hosted bytes.

        Requires the ``WRITE_CAMPAIGNS`` permission. Any email already sent
        with this image loses it.
        """
        return await self._delete(
            f"/email-images/{image_id}", cast_to=EmailImageDeleted, options=options
        )
