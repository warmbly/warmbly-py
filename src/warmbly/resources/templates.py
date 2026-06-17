"""The ``templates`` resource: manage reusable email templates.

Maps to the ``/v1/templates`` route group. A template bundles a reusable
``subject`` and ``body`` (and a human-readable ``name``) that campaigns and
one-off sends can reference.
"""

from __future__ import annotations

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncTemplates",
    "Template",
    "TemplateDeleted",
    "Templates",
]


class Template(BaseModel):
    """A reusable email template."""

    id: str
    organization_id: str | None = None
    name: str | None = None
    subject: str | None = None
    body: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class TemplateDeleted(BaseModel):
    """The result of deleting a template."""

    id: str | None = None
    deleted: bool | None = None
    status: str | None = None


class Templates(SyncAPIResource):
    """Synchronous ``templates`` resource."""

    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[Template]:
        """List templates (auto-paginating)."""
        return self._get_api_list(
            "/templates",
            model=Template,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def create(
        self,
        *,
        name: str,
        subject: str,
        body: str,
        options: RequestOptions | None = None,
    ) -> Template:
        """Create a template.

        Args:
            name: A human-readable label for the template.
            subject: The email subject line.
            body: The email body (HTML or text).
        """
        request_body = drop_not_given(
            {
                "name": name,
                "subject": subject,
                "body": body,
            }
        )
        return self._post(
            "/templates", cast_to=Template, body=request_body, options=options
        )

    def retrieve(
        self, template_id: str, *, options: RequestOptions | None = None
    ) -> Template:
        """Retrieve a single template by id."""
        return self._get(f"/templates/{template_id}", cast_to=Template, options=options)

    def update(
        self,
        template_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Template:
        """Update a template's name, subject, or body."""
        request_body = drop_not_given(
            {
                "name": name,
                "subject": subject,
                "body": body,
            }
        )
        return self._patch(
            f"/templates/{template_id}",
            cast_to=Template,
            body=request_body,
            options=options,
        )

    def delete(
        self, template_id: str, *, options: RequestOptions | None = None
    ) -> TemplateDeleted:
        """Delete a template."""
        return self._delete(
            f"/templates/{template_id}", cast_to=TemplateDeleted, options=options
        )


class AsyncTemplates(AsyncAPIResource):
    """Asynchronous ``templates`` resource."""

    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[Template]:
        """List templates (auto-paginating)."""
        return self._get_api_list(
            "/templates",
            model=Template,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def create(
        self,
        *,
        name: str,
        subject: str,
        body: str,
        options: RequestOptions | None = None,
    ) -> Template:
        """Create a template.

        Args:
            name: A human-readable label for the template.
            subject: The email subject line.
            body: The email body (HTML or text).
        """
        request_body = drop_not_given(
            {
                "name": name,
                "subject": subject,
                "body": body,
            }
        )
        return await self._post(
            "/templates", cast_to=Template, body=request_body, options=options
        )

    async def retrieve(
        self, template_id: str, *, options: RequestOptions | None = None
    ) -> Template:
        """Retrieve a single template by id."""
        return await self._get(
            f"/templates/{template_id}", cast_to=Template, options=options
        )

    async def update(
        self,
        template_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Template:
        """Update a template's name, subject, or body."""
        request_body = drop_not_given(
            {
                "name": name,
                "subject": subject,
                "body": body,
            }
        )
        return await self._patch(
            f"/templates/{template_id}",
            cast_to=Template,
            body=request_body,
            options=options,
        )

    async def delete(
        self, template_id: str, *, options: RequestOptions | None = None
    ) -> TemplateDeleted:
        """Delete a template."""
        return await self._delete(
            f"/templates/{template_id}", cast_to=TemplateDeleted, options=options
        )
