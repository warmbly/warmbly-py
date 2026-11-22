"""The ``email_images`` resource: the workspace image library for email bodies.

Maps to the ``/v1/email-images`` route group. An uploaded image is stored as a
public object, because a recipient's mail client fetches it with no session of
ours: the row keeps the ``url`` you put in an ``<img src>``. Uploads count
against the same storage quota as campaign attachments.

Reading needs the ``READ_CAMPAIGNS`` permission, uploading and deleting need
``WRITE_CAMPAIGNS``.
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
    """One image in the library.

    ``mime_type`` is decided from the uploaded bytes, never from the declared
    content type. ``size`` is in bytes, ``width`` and ``height`` in pixels.
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
        """List the library, newest first (auto-paginating).

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
        filename: str = "image.png",
        content_type: str = "image/png",
        options: RequestOptions | None = None,
    ) -> EmailImage:
        """Upload an image and return its row, with the public ``url``.

        Requires the ``WRITE_CAMPAIGNS`` permission. The server accepts PNG,
        JPG, GIF and WebP up to 5 MB and 4000 pixels on a side, and judges the
        format from the bytes.

        Args:
            file: The raw image bytes.
            filename: The filename to send in the multipart part.
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
        """Delete an image and its stored bytes.

        Mail already sent with the image stops loading it. A storage failure
        answers ``503`` and changes nothing, so the call can be retried.

        Requires the ``WRITE_CAMPAIGNS`` permission.
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
        """List the library, newest first (auto-paginating).

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
        filename: str = "image.png",
        content_type: str = "image/png",
        options: RequestOptions | None = None,
    ) -> EmailImage:
        """Upload an image and return its row, with the public ``url``.

        Requires the ``WRITE_CAMPAIGNS`` permission. The server accepts PNG,
        JPG, GIF and WebP up to 5 MB and 4000 pixels on a side, and judges the
        format from the bytes.

        Args:
            file: The raw image bytes.
            filename: The filename to send in the multipart part.
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
        """Delete an image and its stored bytes.

        Mail already sent with the image stops loading it. A storage failure
        answers ``503`` and changes nothing, so the call can be retried.

        Requires the ``WRITE_CAMPAIGNS`` permission.
        """
        return await self._delete(
            f"/email-images/{image_id}", cast_to=EmailImageDeleted, options=options
        )
