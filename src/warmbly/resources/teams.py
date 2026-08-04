"""The ``teams`` resource: named groups of organization members.

Maps to the ``/v1/teams`` route group. A team groups people who already belong
to the organization so CRM ownership and routing can address them as a unit.
Membership is managed on the team (``POST /teams/{id}/members``), not on the
member: inviting a *new* person to the organization is a separate,
session-only flow that an API key cannot reach.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncTeams",
    "Team",
    "TeamDeleted",
    "TeamMember",
    "TeamMemberRemoved",
    "Teams",
]


class TeamMember(BaseModel):
    """A member of a team (permissive)."""

    user_id: str | None = None
    team_id: str | None = None
    email: str | None = None
    name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    avatar: str | None = None
    role: str | None = None
    created_at: str | None = None


class Team(BaseModel):
    """A team within the organization."""

    id: str
    organization_id: str | None = None
    name: str | None = None
    description: str | None = None
    color: str | None = None
    members: Sequence[TeamMember] = []
    member_count: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class TeamDeleted(BaseModel):
    """The result of deleting a team.

    ``DELETE /teams/{id}`` answers ``204 No Content``, so every field is
    ``None`` on a successful delete; the object exists so the call has a
    uniform return type.
    """

    id: str | None = None
    deleted: bool | None = None
    status: str | None = None


class TeamMemberRemoved(BaseModel):
    """The result of removing a member from a team.

    ``DELETE /teams/{id}/members/{user_id}`` answers ``204 No Content``, so
    every field is ``None`` on success.
    """

    team_id: str | None = None
    user_id: str | None = None
    removed: bool | None = None


class Teams(SyncAPIResource):
    """Synchronous ``teams`` resource."""

    def list(
        self,
        *,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[Team]:
        """List the organization's teams.

        The endpoint returns every team in one response, so the returned page
        never has a next page.
        """
        return self._get_api_list("/teams", model=Team, options=options)

    def create(
        self,
        *,
        name: str,
        description: NotGivenOr[str] = NOT_GIVEN,
        color: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Team:
        """Create a team.

        Args:
            name: The team name.
            description: An optional longer description.
            color: An optional display colour.
        """
        body: dict[str, Any] = drop_not_given(
            {"name": name, "description": description, "color": color}
        )
        return self._post("/teams", cast_to=Team, body=body, options=options)

    def retrieve(self, team_id: str, *, options: RequestOptions | None = None) -> Team:
        """Retrieve a single team (with its members) by id."""
        return self._get(f"/teams/{team_id}", cast_to=Team, options=options)

    def update(
        self,
        team_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        color: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Team:
        """Update a team's name, description, or colour."""
        body = drop_not_given(
            {"name": name, "description": description, "color": color}
        )
        return self._patch(
            f"/teams/{team_id}", cast_to=Team, body=body, options=options
        )

    def delete(
        self, team_id: str, *, options: RequestOptions | None = None
    ) -> TeamDeleted:
        """Delete a team. Its members keep their organization membership."""
        return self._delete(f"/teams/{team_id}", cast_to=TeamDeleted, options=options)

    def add_member(
        self, team_id: str, *, user_id: str, options: RequestOptions | None = None
    ) -> Team:
        """Add an existing organization member to a team.

        Args:
            team_id: The team to add to.
            user_id: The id of a user who already belongs to the organization.

        Returns:
            The team, refreshed with its new membership.
        """
        return self._post(
            f"/teams/{team_id}/members",
            cast_to=Team,
            body={"user_id": user_id},
            options=options,
        )

    def remove_member(
        self, team_id: str, user_id: str, *, options: RequestOptions | None = None
    ) -> TeamMemberRemoved:
        """Remove a member from a team."""
        return self._delete(
            f"/teams/{team_id}/members/{user_id}",
            cast_to=TeamMemberRemoved,
            options=options,
        )


class AsyncTeams(AsyncAPIResource):
    """Asynchronous ``teams`` resource."""

    def list(
        self,
        *,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[Team]:
        """List the organization's teams.

        The endpoint returns every team in one response, so the returned page
        never has a next page.
        """
        return self._get_api_list("/teams", model=Team, options=options)

    async def create(
        self,
        *,
        name: str,
        description: NotGivenOr[str] = NOT_GIVEN,
        color: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Team:
        """Create a team.

        Args:
            name: The team name.
            description: An optional longer description.
            color: An optional display colour.
        """
        body: dict[str, Any] = drop_not_given(
            {"name": name, "description": description, "color": color}
        )
        return await self._post("/teams", cast_to=Team, body=body, options=options)

    async def retrieve(
        self, team_id: str, *, options: RequestOptions | None = None
    ) -> Team:
        """Retrieve a single team (with its members) by id."""
        return await self._get(f"/teams/{team_id}", cast_to=Team, options=options)

    async def update(
        self,
        team_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        color: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Team:
        """Update a team's name, description, or colour."""
        body = drop_not_given(
            {"name": name, "description": description, "color": color}
        )
        return await self._patch(
            f"/teams/{team_id}", cast_to=Team, body=body, options=options
        )

    async def delete(
        self, team_id: str, *, options: RequestOptions | None = None
    ) -> TeamDeleted:
        """Delete a team. Its members keep their organization membership."""
        return await self._delete(
            f"/teams/{team_id}", cast_to=TeamDeleted, options=options
        )

    async def add_member(
        self, team_id: str, *, user_id: str, options: RequestOptions | None = None
    ) -> Team:
        """Add an existing organization member to a team.

        Args:
            team_id: The team to add to.
            user_id: The id of a user who already belongs to the organization.

        Returns:
            The team, refreshed with its new membership.
        """
        return await self._post(
            f"/teams/{team_id}/members",
            cast_to=Team,
            body={"user_id": user_id},
            options=options,
        )

    async def remove_member(
        self, team_id: str, user_id: str, *, options: RequestOptions | None = None
    ) -> TeamMemberRemoved:
        """Remove a member from a team."""
        return await self._delete(
            f"/teams/{team_id}/members/{user_id}",
            cast_to=TeamMemberRemoved,
            options=options,
        )
