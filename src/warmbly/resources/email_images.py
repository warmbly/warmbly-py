"""The ``email_images`` resource: the workspace image library for email bodies.

Maps to the ``/v1/email-images`` route group. Images uploaded here are stored
as public objects, because a recipient's mail client fetches them with no
session; the ``url`` on each :class:`EmailImage` is what an email body embeds.
These routes only manage the library, not the reads. Uploads count against the
workspace's storage quota.
"""

from __future__ import annotations

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions

__all__ = [
    "AsyncEmailImages",
    "EmailImage",
    "EmailImageDeleted",
    "EmailImages",
]


class EmailImage(BaseModel):
    """One image in the workspace's library.

    ``url`` is the public address to embed in an email body. ``filename`` is
    the display name (its extension always matches the sniffed type) and
    ``mime_type`` is decided from the bytes, never from the upload's declared
    type. ``user_id`` is absent when the uploader is unknown.
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

        Needs ``read_campaigns``.

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
        filename: str = "image.png",
        content_type: str = "image/png",
        options: RequestOptions | None = None,
    ) -> EmailImage:
        """Upload an image to the library.

        Needs ``write_campaigns``. PNG, JPEG, GIF or WebP (SVG is refused),
        at most 5 MB and 4000 pixels on each side. The format is decided from
        the bytes. An upload past the workspace's storage quota is refused.

        Args:
            file: The raw image bytes.
            filename: The display name; its extension is replaced to match the
                detected type.
            content_type: The image's MIME type for the multipart part.
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
        """Delete an image (``204 No Content``).

        Needs ``write_campaigns``. The bytes go with the row, so any email
        already sent with this image loses it. Repeating the call after the
        object is gone still removes the row.
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

        Needs ``read_campaigns``.

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
        filename: str = "image.png",
        content_type: str = "image/png",
        options: RequestOptions | None = None,
    ) -> EmailImage:
        """Upload an image to the library.

        Needs ``write_campaigns``. PNG, JPEG, GIF or WebP (SVG is refused),
        at most 5 MB and 4000 pixels on each side. The format is decided from
        the bytes. An upload past the workspace's storage quota is refused.

        Args:
            file: The raw image bytes.
            filename: The display name; its extension is replaced to match the
                detected type.
            content_type: The image's MIME type for the multipart part.
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
        """Delete an image (``204 No Content``).

        Needs ``write_campaigns``. The bytes go with the row, so any email
        already sent with this image loses it. Repeating the call after the
        object is gone still removes the row.
        """
        return await self._delete(
            f"/email-images/{image_id}", cast_to=EmailImageDeleted, options=options
        )
