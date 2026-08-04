"""The ``ai_skills`` resource: reusable instructions for the AI assistant.

Maps to the ``/v1/ai/skills`` route group. A skill is a named block of
instructions that is prepended to every AI generation for the organization when
``enabled`` — house style, banned phrases, product facts. Disabling a skill
keeps it around without applying it.
"""

from __future__ import annotations

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AISkill",
    "AISkillDeleted",
    "AISkills",
    "AsyncAISkills",
]


class AISkill(BaseModel):
    """A reusable instruction block for the AI assistant."""

    id: str
    org_id: str | None = None
    name: str | None = None
    description: str | None = None
    content: str | None = None
    enabled: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None


class AISkillDeleted(BaseModel):
    """The result of deleting a skill."""

    deleted: bool | None = None


class AISkills(SyncAPIResource):
    """Synchronous ``ai_skills`` resource."""

    def list(self, *, options: RequestOptions | None = None) -> SyncCursorPage[AISkill]:
        """List the organization's skills. Returned in full, unpaginated."""
        return self._get_api_list("/ai/skills", model=AISkill, options=options)

    def create(
        self,
        *,
        name: str,
        content: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AISkill:
        """Create a skill.

        Args:
            name: A short label.
            content: The instruction text applied to AI generations.
            description: A human-readable note about what the skill is for.
            enabled: Whether to apply it immediately.
        """
        return self._post(
            "/ai/skills",
            cast_to=AISkill,
            body=drop_not_given(
                {
                    "name": name,
                    "content": content,
                    "description": description,
                    "enabled": enabled,
                }
            ),
            options=options,
        )

    def update(
        self,
        skill_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        content: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AISkill:
        """Update a skill, or toggle it on and off with *enabled*."""
        return self._patch(
            f"/ai/skills/{skill_id}",
            cast_to=AISkill,
            body=drop_not_given(
                {
                    "name": name,
                    "content": content,
                    "description": description,
                    "enabled": enabled,
                }
            ),
            options=options,
        )

    def delete(
        self, skill_id: str, *, options: RequestOptions | None = None
    ) -> AISkillDeleted:
        """Delete a skill."""
        return self._delete(
            f"/ai/skills/{skill_id}", cast_to=AISkillDeleted, options=options
        )


class AsyncAISkills(AsyncAPIResource):
    """Asynchronous ``ai_skills`` resource."""

    def list(self, *, options: RequestOptions | None = None) -> AsyncPaginator[AISkill]:
        """List the organization's skills. Returned in full, unpaginated."""
        return self._get_api_list("/ai/skills", model=AISkill, options=options)

    async def create(
        self,
        *,
        name: str,
        content: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AISkill:
        """Create a skill.

        Args:
            name: A short label.
            content: The instruction text applied to AI generations.
            description: A human-readable note about what the skill is for.
            enabled: Whether to apply it immediately.
        """
        return await self._post(
            "/ai/skills",
            cast_to=AISkill,
            body=drop_not_given(
                {
                    "name": name,
                    "content": content,
                    "description": description,
                    "enabled": enabled,
                }
            ),
            options=options,
        )

    async def update(
        self,
        skill_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        content: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AISkill:
        """Update a skill, or toggle it on and off with *enabled*."""
        return await self._patch(
            f"/ai/skills/{skill_id}",
            cast_to=AISkill,
            body=drop_not_given(
                {
                    "name": name,
                    "content": content,
                    "description": description,
                    "enabled": enabled,
                }
            ),
            options=options,
        )

    async def delete(
        self, skill_id: str, *, options: RequestOptions | None = None
    ) -> AISkillDeleted:
        """Delete a skill."""
        return await self._delete(
            f"/ai/skills/{skill_id}", cast_to=AISkillDeleted, options=options
        )
