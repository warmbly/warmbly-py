"""The ``teams`` resource: members, invitations, and roles.

Maps to the ``/v1/teams`` route group. Members are managed via
``/teams/members`` and ``/teams/invitations``; the available roles are listed
via ``/teams/roles``. The exact member/invitation/role payloads are not fully
enumerated in the contract, so the models below are permissive
(``extra="allow"`` via :class:`~warmbly._models.BaseModel`).
"""

from __future__ import annotations

from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncTeams",
    "Invitation",
    "MemberRemoved",
    "Role",
    "TeamMember",
    "Teams",
]


class TeamMember(BaseModel):
    """An organization member (permissive)."""

    id: str
    organization_id: str | None = None
    user_id: str | None = None
    email: str | None = None
    name: str | None = None
    role: str | None = None
    permissions: int | None = None
    status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class MemberRemoved(BaseModel):
    """The result of removing a team member."""

    id: str | None = None
    removed: bool | None = None
    status: str | None = None


class Invitation(BaseModel):
    """A pending team invitation (permissive)."""

    id: str
    organization_id: str | None = None
    email: str | None = None
    role: str | None = None
    status: str | None = None
    invited_by: str | None = None
    expires_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class Role(BaseModel):
    """A team role and its associated permissions (permissive)."""

    id: str | None = None
    name: str | None = None
    description: str | None = None
    permissions: int | None = None
    is_default: bool | None = None
    metadata: dict[str, Any] = {}


class Teams(SyncAPIResource):
    """Synchronous ``teams`` resource (members, invitations, roles)."""

    def list_members(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[TeamMember]:
        """List team members (auto-paginating)."""
        return self._get_api_list(
            "/teams/members",
            model=TeamMember,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def invite(
        self,
        *,
        email: str,
        role: str,
        options: RequestOptions | None = None,
    ) -> Invitation:
        """Invite a new member to the team.

        Args:
            email: The invitee's email address.
            role: The role to grant the invitee.
        """
        body = drop_not_given({"email": email, "role": role})
        return self._post(
            "/teams/invitations", cast_to=Invitation, body=body, options=options
        )

    def remove_member(
        self, member_id: str, *, options: RequestOptions | None = None
    ) -> MemberRemoved:
        """Remove a member from the team."""
        return self._delete(
            f"/teams/members/{member_id}", cast_to=MemberRemoved, options=options
        )

    def list_roles(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[Role]:
        """List the available team roles (auto-paginating)."""
        return self._get_api_list(
            "/teams/roles",
            model=Role,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )


class AsyncTeams(AsyncAPIResource):
    """Asynchronous ``teams`` resource (members, invitations, roles)."""

    def list_members(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[TeamMember]:
        """List team members (auto-paginating)."""
        return self._get_api_list(
            "/teams/members",
            model=TeamMember,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def invite(
        self,
        *,
        email: str,
        role: str,
        options: RequestOptions | None = None,
    ) -> Invitation:
        """Invite a new member to the team.

        Args:
            email: The invitee's email address.
            role: The role to grant the invitee.
        """
        body = drop_not_given({"email": email, "role": role})
        return await self._post(
            "/teams/invitations", cast_to=Invitation, body=body, options=options
        )

    async def remove_member(
        self, member_id: str, *, options: RequestOptions | None = None
    ) -> MemberRemoved:
        """Remove a member from the team."""
        return await self._delete(
            f"/teams/members/{member_id}", cast_to=MemberRemoved, options=options
        )

    def list_roles(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[Role]:
        """List the available team roles (auto-paginating)."""
        return self._get_api_list(
            "/teams/roles",
            model=Role,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )
