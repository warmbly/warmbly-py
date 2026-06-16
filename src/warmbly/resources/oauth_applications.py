"""The ``oauth_applications`` resource: register and manage OAuth2 clients.

Maps to the ``/v1/oauth/applications`` route group. The plaintext
``client_secret`` is returned **only** on create and ``rotate_secret``.
"""

from __future__ import annotations

from collections.abc import Sequence

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncOAuthApplications",
    "OAuthApplication",
    "OAuthApplications",
    "OAuthClientSecret",
    "WebhookSecret",
]


class OAuthApplication(BaseModel):
    """A registered OAuth2 application (client)."""

    id: str
    name: str
    organization_id: str | None = None
    created_by: str | None = None
    description: str | None = None
    logo_url: str | None = None
    website_url: str | None = None
    client_id: str | None = None
    client_secret: str | None = None  # present only on create / rotate
    redirect_uris: Sequence[str] = []
    allowed_webhook_domains: Sequence[str] = []
    webhook_url: str | None = None
    webhook_events: Sequence[str] = []
    scopes: int = 0
    status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class OAuthClientSecret(BaseModel):
    """The result of rotating a client secret."""

    client_secret: str | None = None


class WebhookSecret(BaseModel):
    """An application's webhook signing secret."""

    webhook_secret: str | None = None


class OAuthApplications(SyncAPIResource):
    """Synchronous ``oauth_applications`` resource."""

    def create(
        self,
        *,
        name: str,
        scopes: int,
        redirect_uris: Sequence[str],
        description: NotGivenOr[str] = NOT_GIVEN,
        logo_url: NotGivenOr[str] = NOT_GIVEN,
        website_url: NotGivenOr[str] = NOT_GIVEN,
        allowed_webhook_domains: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        webhook_url: NotGivenOr[str] = NOT_GIVEN,
        webhook_events: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> OAuthApplication:
        """Register an OAuth2 application. ``client_secret`` is on the result."""
        body = drop_not_given(
            {
                "name": name,
                "scopes": scopes,
                "redirect_uris": redirect_uris,
                "description": description,
                "logo_url": logo_url,
                "website_url": website_url,
                "allowed_webhook_domains": allowed_webhook_domains,
                "webhook_url": webhook_url,
                "webhook_events": webhook_events,
            }
        )
        return self._post(
            "/oauth/applications", cast_to=OAuthApplication, body=body, options=options
        )

    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[OAuthApplication]:
        """List registered OAuth2 applications (auto-paginating)."""
        return self._get_api_list(
            "/oauth/applications",
            model=OAuthApplication,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def retrieve(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthApplication:
        """Retrieve an OAuth2 application by id."""
        return self._get(
            f"/oauth/applications/{application_id}",
            cast_to=OAuthApplication,
            options=options,
        )

    def update(
        self,
        application_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        logo_url: NotGivenOr[str] = NOT_GIVEN,
        website_url: NotGivenOr[str] = NOT_GIVEN,
        redirect_uris: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        allowed_webhook_domains: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        webhook_url: NotGivenOr[str] = NOT_GIVEN,
        webhook_events: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        scopes: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> OAuthApplication:
        """Update an OAuth2 application."""
        body = drop_not_given(
            {
                "name": name,
                "description": description,
                "logo_url": logo_url,
                "website_url": website_url,
                "redirect_uris": redirect_uris,
                "allowed_webhook_domains": allowed_webhook_domains,
                "webhook_url": webhook_url,
                "webhook_events": webhook_events,
                "scopes": scopes,
            }
        )
        return self._patch(
            f"/oauth/applications/{application_id}",
            cast_to=OAuthApplication,
            body=body,
            options=options,
        )

    def delete(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> None:
        """Delete an OAuth2 application."""
        return self._delete(
            f"/oauth/applications/{application_id}", cast_to=type(None), options=options
        )

    def rotate_secret(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthClientSecret:
        """Rotate (regenerate) the application's client secret."""
        return self._post(
            f"/oauth/applications/{application_id}/rotate-secret",
            cast_to=OAuthClientSecret,
            options=options,
        )

    def webhook_secret(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> WebhookSecret:
        """Retrieve the application's webhook signing secret."""
        return self._get(
            f"/oauth/applications/{application_id}/webhook-secret",
            cast_to=WebhookSecret,
            options=options,
        )

    def rotate_webhook_secret(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> WebhookSecret:
        """Rotate the application's webhook signing secret."""
        return self._post(
            f"/oauth/applications/{application_id}/webhook-secret/rotate",
            cast_to=WebhookSecret,
            options=options,
        )


class AsyncOAuthApplications(AsyncAPIResource):
    """Asynchronous ``oauth_applications`` resource."""

    async def create(
        self,
        *,
        name: str,
        scopes: int,
        redirect_uris: Sequence[str],
        description: NotGivenOr[str] = NOT_GIVEN,
        logo_url: NotGivenOr[str] = NOT_GIVEN,
        website_url: NotGivenOr[str] = NOT_GIVEN,
        allowed_webhook_domains: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        webhook_url: NotGivenOr[str] = NOT_GIVEN,
        webhook_events: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> OAuthApplication:
        """Register an OAuth2 application. ``client_secret`` is on the result."""
        body = drop_not_given(
            {
                "name": name,
                "scopes": scopes,
                "redirect_uris": redirect_uris,
                "description": description,
                "logo_url": logo_url,
                "website_url": website_url,
                "allowed_webhook_domains": allowed_webhook_domains,
                "webhook_url": webhook_url,
                "webhook_events": webhook_events,
            }
        )
        return await self._post(
            "/oauth/applications", cast_to=OAuthApplication, body=body, options=options
        )

    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[OAuthApplication]:
        """List registered OAuth2 applications (auto-paginating)."""
        return self._get_api_list(
            "/oauth/applications",
            model=OAuthApplication,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def retrieve(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthApplication:
        """Retrieve an OAuth2 application by id."""
        return await self._get(
            f"/oauth/applications/{application_id}",
            cast_to=OAuthApplication,
            options=options,
        )

    async def update(
        self,
        application_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        logo_url: NotGivenOr[str] = NOT_GIVEN,
        website_url: NotGivenOr[str] = NOT_GIVEN,
        redirect_uris: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        allowed_webhook_domains: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        webhook_url: NotGivenOr[str] = NOT_GIVEN,
        webhook_events: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        scopes: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> OAuthApplication:
        """Update an OAuth2 application."""
        body = drop_not_given(
            {
                "name": name,
                "description": description,
                "logo_url": logo_url,
                "website_url": website_url,
                "redirect_uris": redirect_uris,
                "allowed_webhook_domains": allowed_webhook_domains,
                "webhook_url": webhook_url,
                "webhook_events": webhook_events,
                "scopes": scopes,
            }
        )
        return await self._patch(
            f"/oauth/applications/{application_id}",
            cast_to=OAuthApplication,
            body=body,
            options=options,
        )

    async def delete(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> None:
        """Delete an OAuth2 application."""
        return await self._delete(
            f"/oauth/applications/{application_id}", cast_to=type(None), options=options
        )

    async def rotate_secret(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthClientSecret:
        """Rotate (regenerate) the application's client secret."""
        return await self._post(
            f"/oauth/applications/{application_id}/rotate-secret",
            cast_to=OAuthClientSecret,
            options=options,
        )

    async def webhook_secret(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> WebhookSecret:
        """Retrieve the application's webhook signing secret."""
        return await self._get(
            f"/oauth/applications/{application_id}/webhook-secret",
            cast_to=WebhookSecret,
            options=options,
        )

    async def rotate_webhook_secret(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> WebhookSecret:
        """Rotate the application's webhook signing secret."""
        return await self._post(
            f"/oauth/applications/{application_id}/webhook-secret/rotate",
            cast_to=WebhookSecret,
            options=options,
        )
