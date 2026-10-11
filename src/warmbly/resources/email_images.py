"""The ``email_images`` resource: the workspace image library for email bodies.

Maps to the ``/v1/email-images`` route group. An uploaded image is stored as a
*public* object, because a recipient's mail client fetches it with no session,
so its ``url`` can be placed straight into a campaign or template body. These
routes only manage the library; they never serve the bytes. Uploads count
against the plan's storage quota, the same one attachments draw on.
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
    """An image in the workspace library.

    ``url`` is a public, absolute link that stays valid until the image is
    deleted. ``width`` and ``height`` are ``0`` for a WebP, whose dimensions the
    server does not read.
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

        Requires the ``read_campaigns`` scope.

        Args:
            limit: Page size (1-100; the server defaults to 40).
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
        content_type: str = "image/png",
        options: RequestOptions | None = None,
    ) -> EmailImage:
        """Upload an image (multipart, max 5 MB, at most 4000 px a side).

        The server decides the format from the bytes, not from *content_type*:
        PNG, JPEG, GIF and WebP are accepted; SVG is refused. A ``400`` with
        identifier ``storage_limit_reached`` means the plan's storage quota would
        be exceeded. Requires the ``write_campaigns`` scope.

        Args:
            file: The raw image bytes.
            filename: The display name kept in the library (the extension is
                corrected to match the real format).
            content_type: The file's MIME type.
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
        """Delete an image and its bytes.

        Any email already sent with this image loses it, so only delete images
        no live copy still depends on. Requires the ``write_campaigns`` scope.
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

        Requires the ``read_campaigns`` scope.

        Args:
            limit: Page size (1-100; the server defaults to 40).
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
        content_type: str = "image/png",
        options: RequestOptions | None = None,
    ) -> EmailImage:
        """Upload an image (multipart, max 5 MB, at most 4000 px a side).

        See :meth:`EmailImages.upload`. Requires the ``write_campaigns`` scope.
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
        """Delete an image and its bytes.

        See :meth:`EmailImages.delete`. Requires the ``write_campaigns`` scope.
        """
        return await self._delete(
            f"/email-images/{image_id}", cast_to=EmailImageDeleted, options=options
        )
