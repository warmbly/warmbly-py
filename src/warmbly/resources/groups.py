"""The ``folders``, ``tags``, and ``categories`` resources.

Maps to the ``/v1/folders``, ``/v1/tags``, and ``/v1/categories`` route groups,
which share one shape: a titled, coloured, ordered label. They differ only in
what they organize — folders group campaigns, tags group mailboxes, and
categories group contacts and unibox conversations.

There is no list endpoint: groups arrive embedded in the resources they
organize (a campaign's ``folders``, a mailbox's ``tags``, a contact's
``categories``).
"""

from __future__ import annotations

from .._models import BaseModel
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncCategories",
    "AsyncFolders",
    "AsyncGroups",
    "AsyncTags",
    "Categories",
    "Folders",
    "Group",
    "GroupDeleted",
    "GroupOrder",
    "Groups",
    "Tags",
]


class Group(BaseModel):
    """A folder, tag, or category."""

    id: str
    title: str | None = None
    color: str | None = None
    position: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class GroupOrder(BaseModel):
    """One group's new position, as returned by a move."""

    id: str | None = None
    position: int | None = None


class GroupDeleted(BaseModel):
    """The result of deleting a group (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class Groups(SyncAPIResource):
    """Synchronous resource for one group kind.

    Instantiated by the client as ``folders``, ``tags``, and ``categories``;
    the *name* argument picks the route prefix.
    """

    _name: str

    def __init__(self, client: object, name: str) -> None:
        super().__init__(client)  # type: ignore[arg-type]
        self._name = name

    def create(
        self,
        *,
        title: str,
        color: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Group:
        """Create a group.

        Args:
            title: The label, 1-50 characters.
            color: A display colour.
        """
        return self._post(
            f"/{self._name}",
            cast_to=Group,
            body=drop_not_given({"title": title, "color": color}),
            options=options,
        )

    def update(
        self,
        group_id: str,
        *,
        title: NotGivenOr[str] = NOT_GIVEN,
        color: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Group:
        """Rename or recolour a group."""
        return self._patch(
            f"/{self._name}/{group_id}",
            cast_to=Group,
            body=drop_not_given({"title": title, "color": color}),
            options=options,
        )

    def move(
        self, group_id: str, *, position: int, options: RequestOptions | None = None
    ) -> list[GroupOrder]:
        """Move a group to *position*.

        Returns:
            Every group's resulting ``(id, position)``, so a client can reorder
            its local list without refetching.
        """
        return self._patch(
            f"/{self._name}/{group_id}/move",
            cast_to=list[GroupOrder],
            body={"position": position},
            options=options,
        )

    def delete(
        self, group_id: str, *, options: RequestOptions | None = None
    ) -> GroupDeleted:
        """Delete a group. The resources it organized are not deleted."""
        return self._delete(
            f"/{self._name}/{group_id}", cast_to=GroupDeleted, options=options
        )


class AsyncGroups(AsyncAPIResource):
    """Asynchronous resource for one group kind."""

    _name: str

    def __init__(self, client: object, name: str) -> None:
        super().__init__(client)  # type: ignore[arg-type]
        self._name = name

    async def create(
        self,
        *,
        title: str,
        color: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Group:
        """Create a group.

        Args:
            title: The label, 1-50 characters.
            color: A display colour.
        """
        return await self._post(
            f"/{self._name}",
            cast_to=Group,
            body=drop_not_given({"title": title, "color": color}),
            options=options,
        )

    async def update(
        self,
        group_id: str,
        *,
        title: NotGivenOr[str] = NOT_GIVEN,
        color: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Group:
        """Rename or recolour a group."""
        return await self._patch(
            f"/{self._name}/{group_id}",
            cast_to=Group,
            body=drop_not_given({"title": title, "color": color}),
            options=options,
        )

    async def move(
        self, group_id: str, *, position: int, options: RequestOptions | None = None
    ) -> list[GroupOrder]:
        """Move a group to *position*.

        Returns:
            Every group's resulting ``(id, position)``, so a client can reorder
            its local list without refetching.
        """
        return await self._patch(
            f"/{self._name}/{group_id}/move",
            cast_to=list[GroupOrder],
            body={"position": position},
            options=options,
        )

    async def delete(
        self, group_id: str, *, options: RequestOptions | None = None
    ) -> GroupDeleted:
        """Delete a group. The resources it organized are not deleted."""
        return await self._delete(
            f"/{self._name}/{group_id}", cast_to=GroupDeleted, options=options
        )


class Folders(Groups):
    """Campaign folders (``/v1/folders``)."""

    def __init__(self, client: object) -> None:
        super().__init__(client, "folders")


class AsyncFolders(AsyncGroups):
    """Campaign folders (``/v1/folders``)."""

    def __init__(self, client: object) -> None:
        super().__init__(client, "folders")


class Tags(Groups):
    """Mailbox tags (``/v1/tags``)."""

    def __init__(self, client: object) -> None:
        super().__init__(client, "tags")


class AsyncTags(AsyncGroups):
    """Mailbox tags (``/v1/tags``)."""

    def __init__(self, client: object) -> None:
        super().__init__(client, "tags")


class Categories(Groups):
    """Contact and conversation categories (``/v1/categories``)."""

    def __init__(self, client: object) -> None:
        super().__init__(client, "categories")


class AsyncCategories(AsyncGroups):
    """Contact and conversation categories (``/v1/categories``)."""

    def __init__(self, client: object) -> None:
        super().__init__(client, "categories")
