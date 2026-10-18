"""The ``oauth_applications`` resource: register OAuth 2.1 apps.

Maps to the ``/v1/oauth/applications`` route group. An application is the
identity a third-party integration authenticates as: it owns a ``client_id``,
a set of redirect URIs, the scope bitmask it may request, and optionally an
app-level webhook subscription that fires for every organization that
authorizes it.

Two secrets are shown exactly once and never again: the ``client_secret`` on
create and rotate, and the app webhook secret on rotate. Capture them at the
call site.

Scopes travel as a ``uint64`` bitmask; build one from readable names with
:func:`warmbly.scopes_to_mask`.
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
    "AppListing",
    "AppListingDeleted",
    "AppListingEnvelope",
    "AsyncOAuthApplications",
    "OAuthApplication",
    "OAuthApplicationDeleted",
    "OAuthApplicationLogo",
    "OAuthApplications",
    "OAuthClientSecret",
    "OAuthWebhookDelivery",
    "OAuthWebhookEndpoint",
    "WebhookSecret",
]


class OAuthApplication(BaseModel):
    """A registered OAuth 2.1 application.

    ``is_public`` marks a PKCE-only client with no secret;
    ``dynamically_registered`` marks one created through RFC 7591 dynamic
    client registration rather than the dashboard.
    """

    id: str
    organization_id: str | None = None
    created_by: str | None = None
    name: str | None = None
    description: str | None = None
    logo_url: str | None = None
    website_url: str | None = None
    client_id: str | None = None
    client_secret: str | None = None  # present only on create
    redirect_uris: Sequence[str] = []
    allowed_webhook_domains: Sequence[str] = []
    webhook_url: str | None = None
    webhook_events: Sequence[str] = []
    scopes: int | None = None
    status: str | None = None
    is_public: bool | None = None
    dynamically_registered: bool | None = None
    #: Set when an operator suspended the app; only an operator can lift it.
    suspended_at: str | None = None
    suspended_reason: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class AppListing(BaseModel):
    """An OAuth app's page in the community directory.

    ``status`` is ``published`` (reachable by link), ``featured`` (always
    listed) or ``hidden`` (taken down by an operator; see ``status_note``).
    """

    application_id: str | None = None
    organization_id: str | None = None
    slug: str | None = None
    tagline: str | None = None
    description: str | None = None
    category: str | None = None
    install_url: str | None = None
    support_url: str | None = None
    privacy_url: str | None = None
    status: str | None = None
    status_note: str | None = None
    status_at: str | None = None
    submitted_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class AppListingEnvelope(BaseModel):
    """The ``{"listing": ...}`` wrapper; ``listing`` is null when unpublished."""

    listing: AppListing | None = None


class AppListingDeleted(BaseModel):
    """The result of unpublishing an application's listing."""

    deleted: bool | None = None


class OAuthApplicationDeleted(BaseModel):
    """The result of deleting an application."""

    deleted: bool | None = None


class OAuthClientSecret(BaseModel):
    """A freshly rotated client secret. Shown once."""

    client_secret: str | None = None


class WebhookSecret(BaseModel):
    """An application's webhook signing secret."""

    webhook_secret: str | None = None


class OAuthApplicationLogo(BaseModel):
    """The hosted URL of an uploaded application logo."""

    logo_url: str | None = None


class OAuthWebhookEndpoint(BaseModel):
    """A per-organization endpoint materialized from an app's webhook config."""

    id: str
    organization_id: str | None = None
    oauth_application_id: str | None = None
    url: str | None = None
    event_types: Sequence[str] = []
    enabled: bool | None = None
    verified_at: str | None = None
    consecutive_failures: int | None = None
    auto_disabled_at: str | None = None
    disabled_reason: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class OAuthWebhookDelivery(BaseModel):
    """A delivery attempt against one of an application's endpoints."""

    id: str
    endpoint_id: str | None = None
    organization_id: str | None = None
    event_type: str | None = None
    event_id: str | None = None
    payload: dict[str, Any] | None = None
    status: str | None = None
    attempt_count: int | None = None
    response_status: int | None = None
    error_reason: str | None = None
    created_at: str | None = None


def _application_body(
    *,
    name: NotGivenOr[str],
    description: NotGivenOr[str],
    logo_url: NotGivenOr[str],
    website_url: NotGivenOr[str],
    redirect_uris: NotGivenOr[Sequence[str]],
    allowed_webhook_domains: NotGivenOr[Sequence[str]],
    webhook_url: NotGivenOr[str],
    webhook_events: NotGivenOr[Sequence[str]],
    scopes: NotGivenOr[int],
) -> dict[str, Any]:
    return drop_not_given(
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


class OAuthApplications(SyncAPIResource):
    """Synchronous ``oauth_applications`` resource."""

    def list(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[OAuthApplication]:
        """List the organization's applications. Returned in full, unpaginated."""
        return self._get_api_list(
            "/oauth/applications",
            model=OAuthApplication,
            data_key="applications",
            options=options,
        )

    def create(
        self,
        *,
        name: str,
        redirect_uris: Sequence[str],
        scopes: int,
        description: NotGivenOr[str] = NOT_GIVEN,
        logo_url: NotGivenOr[str] = NOT_GIVEN,
        website_url: NotGivenOr[str] = NOT_GIVEN,
        allowed_webhook_domains: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        webhook_url: NotGivenOr[str] = NOT_GIVEN,
        webhook_events: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> OAuthApplication:
        """Register an application. The ``client_secret`` is shown once.

        Args:
            name: The application name shown on the consent screen.
            redirect_uris: The exact URIs an authorization code may return to.
            scopes: The scope bitmask the app may request (see
                :func:`warmbly.scopes_to_mask`).
            description: A short description for the consent screen.
            logo_url: A hosted logo (see :meth:`upload_logo`).
            website_url: The app's homepage.
            allowed_webhook_domains: Hosts an authorizing organization's
                webhook endpoints must fall within.
            webhook_url: An app-level webhook URL, materialized once per
                authorizing organization.
            webhook_events: The event types that webhook subscribes to.
        """
        return self._post(
            "/oauth/applications",
            cast_to=OAuthApplication,
            body=_application_body(
                name=name,
                description=description,
                logo_url=logo_url,
                website_url=website_url,
                redirect_uris=redirect_uris,
                allowed_webhook_domains=allowed_webhook_domains,
                webhook_url=webhook_url,
                webhook_events=webhook_events,
                scopes=scopes,
            ),
            options=options,
        )

    def retrieve(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthApplication:
        """Retrieve a single application by id."""
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
        """Update an application's registration."""
        return self._patch(
            f"/oauth/applications/{application_id}",
            cast_to=OAuthApplication,
            body=_application_body(
                name=name,
                description=description,
                logo_url=logo_url,
                website_url=website_url,
                redirect_uris=redirect_uris,
                allowed_webhook_domains=allowed_webhook_domains,
                webhook_url=webhook_url,
                webhook_events=webhook_events,
                scopes=scopes,
            ),
            options=options,
        )

    def delete(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthApplicationDeleted:
        """Delete an application and revoke every token issued for it."""
        return self._delete(
            f"/oauth/applications/{application_id}",
            cast_to=OAuthApplicationDeleted,
            options=options,
        )

    def rotate_secret(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthClientSecret:
        """Rotate the client secret. The new secret is shown once."""
        return self._post(
            f"/oauth/applications/{application_id}/rotate-secret",
            cast_to=OAuthClientSecret,
            options=options,
        )

    def webhook_secret(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> WebhookSecret:
        """Reveal the application-level webhook signing secret."""
        return self._get(
            f"/oauth/applications/{application_id}/webhook-secret",
            cast_to=WebhookSecret,
            options=options,
        )

    def rotate_webhook_secret(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> WebhookSecret:
        """Rotate the application-level webhook signing secret."""
        return self._post(
            f"/oauth/applications/{application_id}/webhook-secret/rotate",
            cast_to=WebhookSecret,
            options=options,
        )

    def webhook_endpoints(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[OAuthWebhookEndpoint]:
        """List the per-organization endpoints this application owns."""
        return self._get_api_list(
            f"/oauth/applications/{application_id}/webhook-endpoints",
            model=OAuthWebhookEndpoint,
            data_key="endpoints",
            options=options,
        )

    def webhook_deliveries(
        self,
        application_id: str,
        *,
        status: NotGivenOr[str] = NOT_GIVEN,
        event_type: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[OAuthWebhookDelivery]:
        """List delivery attempts across every organization that authorized it.

        Args:
            status: Restrict to one delivery status.
            event_type: Restrict to one event type.
            limit: Page size.
        """
        return self._get_api_list(
            f"/oauth/applications/{application_id}/webhook-deliveries",
            model=OAuthWebhookDelivery,
            query={
                "status": status,
                "event_type": event_type,
                "limit": limit,
                "cursor": cursor,
            },
            options=options,
        )

    def upload_logo(
        self,
        *,
        file: bytes,
        filename: str = "logo.png",
        content_type: str = "image/png",
        options: RequestOptions | None = None,
    ) -> OAuthApplicationLogo:
        """Upload an application logo and return its hosted URL.

        Sits outside ``/applications/{id}`` on purpose, so it can be called
        during registration, before an application id exists.

        Args:
            file: The raw image bytes.
            filename: The filename to send in the multipart part.
            content_type: The image's MIME type.
        """
        return self._client.request(
            cast_to=OAuthApplicationLogo,
            method="POST",
            path="/oauth/application-logo",
            files={"file": (filename, file, content_type)},
            options=options,
        )

    def set_logo(
        self,
        application_id: str,
        *,
        file: bytes,
        filename: str = "logo.png",
        content_type: str = "image/png",
        options: RequestOptions | None = None,
    ) -> OAuthApplication:
        """Upload an image and set it as the application's logo.

        The server stores a re-encoded copy (PNG or JPG, at most 2 MB, 32 to
        1,024 pixels per side) and deletes the previous logo. Requires the
        ``api_keys`` scope. A suspended application refuses the change.

        Args:
            application_id: The application to update.
            file: The raw image bytes.
            filename: The filename to send in the multipart part.
            content_type: The image's MIME type.
        """
        return self._client.request(
            cast_to=OAuthApplication,
            method="POST",
            path=f"/oauth/applications/{application_id}/logo",
            files={"file": (filename, file, content_type)},
            options=options,
        )

    def delete_logo(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthApplication:
        """Remove the application's logo. Requires the ``api_keys`` scope."""
        return self._delete(
            f"/oauth/applications/{application_id}/logo",
            cast_to=OAuthApplication,
            options=options,
        )

    def retrieve_listing(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> AppListing | None:
        """Return the application's community-directory listing.

        Returns ``None`` when the application is not published. Requires the
        ``api_keys`` scope.
        """
        data = self._get(
            f"/oauth/applications/{application_id}/listing",
            cast_to=AppListingEnvelope,
            options=options,
        )
        return data.listing

    def put_listing(
        self,
        application_id: str,
        *,
        slug: str,
        tagline: str,
        category: str,
        install_url: str,
        description: NotGivenOr[str] = NOT_GIVEN,
        support_url: NotGivenOr[str] = NOT_GIVEN,
        privacy_url: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AppListing:
        """Publish or replace the application's community-directory listing.

        Replaces the whole listing, so repeating the call is safe. Requires the
        ``api_keys`` scope.

        Args:
            application_id: The application to publish.
            slug: The link, 3 to 48 lowercase letters, numbers or dashes.
            tagline: One line, at most 120 characters.
            category: One of ``crm``, ``automation``, ``notifications``,
                ``meetings``, ``data``, ``verification``, ``ai`` or ``other``.
            install_url: Where Install sends people (HTTPS).
            description: Optional text, at most 2,000 characters.
            support_url: Optional HTTPS support link.
            privacy_url: Optional HTTPS privacy policy link.
        """
        data = self._put(
            f"/oauth/applications/{application_id}/listing",
            cast_to=AppListingEnvelope,
            body=drop_not_given(
                {
                    "slug": slug,
                    "tagline": tagline,
                    "description": description,
                    "category": category,
                    "install_url": install_url,
                    "support_url": support_url,
                    "privacy_url": privacy_url,
                }
            ),
            options=options,
        )
        return data.listing or AppListing()

    def delete_listing(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> AppListingDeleted:
        """Unpublish the application. Succeeds when nothing is published."""
        return self._delete(
            f"/oauth/applications/{application_id}/listing",
            cast_to=AppListingDeleted,
            options=options,
        )


class AsyncOAuthApplications(AsyncAPIResource):
    """Asynchronous ``oauth_applications`` resource."""

    def list(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[OAuthApplication]:
        """List the organization's applications. Returned in full, unpaginated."""
        return self._get_api_list(
            "/oauth/applications",
            model=OAuthApplication,
            data_key="applications",
            options=options,
        )

    async def create(
        self,
        *,
        name: str,
        redirect_uris: Sequence[str],
        scopes: int,
        description: NotGivenOr[str] = NOT_GIVEN,
        logo_url: NotGivenOr[str] = NOT_GIVEN,
        website_url: NotGivenOr[str] = NOT_GIVEN,
        allowed_webhook_domains: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        webhook_url: NotGivenOr[str] = NOT_GIVEN,
        webhook_events: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> OAuthApplication:
        """Register an application. The ``client_secret`` is shown once.

        Args:
            name: The application name shown on the consent screen.
            redirect_uris: The exact URIs an authorization code may return to.
            scopes: The scope bitmask the app may request (see
                :func:`warmbly.scopes_to_mask`).
            description: A short description for the consent screen.
            logo_url: A hosted logo (see :meth:`upload_logo`).
            website_url: The app's homepage.
            allowed_webhook_domains: Hosts an authorizing organization's
                webhook endpoints must fall within.
            webhook_url: An app-level webhook URL, materialized once per
                authorizing organization.
            webhook_events: The event types that webhook subscribes to.
        """
        return await self._post(
            "/oauth/applications",
            cast_to=OAuthApplication,
            body=_application_body(
                name=name,
                description=description,
                logo_url=logo_url,
                website_url=website_url,
                redirect_uris=redirect_uris,
                allowed_webhook_domains=allowed_webhook_domains,
                webhook_url=webhook_url,
                webhook_events=webhook_events,
                scopes=scopes,
            ),
            options=options,
        )

    async def retrieve(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthApplication:
        """Retrieve a single application by id."""
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
        """Update an application's registration."""
        return await self._patch(
            f"/oauth/applications/{application_id}",
            cast_to=OAuthApplication,
            body=_application_body(
                name=name,
                description=description,
                logo_url=logo_url,
                website_url=website_url,
                redirect_uris=redirect_uris,
                allowed_webhook_domains=allowed_webhook_domains,
                webhook_url=webhook_url,
                webhook_events=webhook_events,
                scopes=scopes,
            ),
            options=options,
        )

    async def delete(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthApplicationDeleted:
        """Delete an application and revoke every token issued for it."""
        return await self._delete(
            f"/oauth/applications/{application_id}",
            cast_to=OAuthApplicationDeleted,
            options=options,
        )

    async def rotate_secret(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthClientSecret:
        """Rotate the client secret. The new secret is shown once."""
        return await self._post(
            f"/oauth/applications/{application_id}/rotate-secret",
            cast_to=OAuthClientSecret,
            options=options,
        )

    async def webhook_secret(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> WebhookSecret:
        """Reveal the application-level webhook signing secret."""
        return await self._get(
            f"/oauth/applications/{application_id}/webhook-secret",
            cast_to=WebhookSecret,
            options=options,
        )

    async def rotate_webhook_secret(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> WebhookSecret:
        """Rotate the application-level webhook signing secret."""
        return await self._post(
            f"/oauth/applications/{application_id}/webhook-secret/rotate",
            cast_to=WebhookSecret,
            options=options,
        )

    def webhook_endpoints(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[OAuthWebhookEndpoint]:
        """List the per-organization endpoints this application owns."""
        return self._get_api_list(
            f"/oauth/applications/{application_id}/webhook-endpoints",
            model=OAuthWebhookEndpoint,
            data_key="endpoints",
            options=options,
        )

    def webhook_deliveries(
        self,
        application_id: str,
        *,
        status: NotGivenOr[str] = NOT_GIVEN,
        event_type: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[OAuthWebhookDelivery]:
        """List delivery attempts across every organization that authorized it.

        Args:
            status: Restrict to one delivery status.
            event_type: Restrict to one event type.
            limit: Page size.
        """
        return self._get_api_list(
            f"/oauth/applications/{application_id}/webhook-deliveries",
            model=OAuthWebhookDelivery,
            query={
                "status": status,
                "event_type": event_type,
                "limit": limit,
                "cursor": cursor,
            },
            options=options,
        )

    async def upload_logo(
        self,
        *,
        file: bytes,
        filename: str = "logo.png",
        content_type: str = "image/png",
        options: RequestOptions | None = None,
    ) -> OAuthApplicationLogo:
        """Upload an application logo and return its hosted URL.

        Sits outside ``/applications/{id}`` on purpose, so it can be called
        during registration, before an application id exists.

        Args:
            file: The raw image bytes.
            filename: The filename to send in the multipart part.
            content_type: The image's MIME type.
        """
        return await self._client.request(
            cast_to=OAuthApplicationLogo,
            method="POST",
            path="/oauth/application-logo",
            files={"file": (filename, file, content_type)},
            options=options,
        )

    async def set_logo(
        self,
        application_id: str,
        *,
        file: bytes,
        filename: str = "logo.png",
        content_type: str = "image/png",
        options: RequestOptions | None = None,
    ) -> OAuthApplication:
        """Upload an image and set it as the application's logo.

        The server stores a re-encoded copy (PNG or JPG, at most 2 MB, 32 to
        1,024 pixels per side) and deletes the previous logo. Requires the
        ``api_keys`` scope. A suspended application refuses the change.

        Args:
            application_id: The application to update.
            file: The raw image bytes.
            filename: The filename to send in the multipart part.
            content_type: The image's MIME type.
        """
        return await self._client.request(
            cast_to=OAuthApplication,
            method="POST",
            path=f"/oauth/applications/{application_id}/logo",
            files={"file": (filename, file, content_type)},
            options=options,
        )

    async def delete_logo(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthApplication:
        """Remove the application's logo. Requires the ``api_keys`` scope."""
        return await self._delete(
            f"/oauth/applications/{application_id}/logo",
            cast_to=OAuthApplication,
            options=options,
        )

    async def retrieve_listing(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> AppListing | None:
        """Return the application's community-directory listing.

        Returns ``None`` when the application is not published. Requires the
        ``api_keys`` scope.
        """
        data = await self._get(
            f"/oauth/applications/{application_id}/listing",
            cast_to=AppListingEnvelope,
            options=options,
        )
        return data.listing

    async def put_listing(
        self,
        application_id: str,
        *,
        slug: str,
        tagline: str,
        category: str,
        install_url: str,
        description: NotGivenOr[str] = NOT_GIVEN,
        support_url: NotGivenOr[str] = NOT_GIVEN,
        privacy_url: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AppListing:
        """Publish or replace the application's community-directory listing.

        Replaces the whole listing, so repeating the call is safe. Requires the
        ``api_keys`` scope.

        Args:
            application_id: The application to publish.
            slug: The link, 3 to 48 lowercase letters, numbers or dashes.
            tagline: One line, at most 120 characters.
            category: One of ``crm``, ``automation``, ``notifications``,
                ``meetings``, ``data``, ``verification``, ``ai`` or ``other``.
            install_url: Where Install sends people (HTTPS).
            description: Optional text, at most 2,000 characters.
            support_url: Optional HTTPS support link.
            privacy_url: Optional HTTPS privacy policy link.
        """
        data = await self._put(
            f"/oauth/applications/{application_id}/listing",
            cast_to=AppListingEnvelope,
            body=drop_not_given(
                {
                    "slug": slug,
                    "tagline": tagline,
                    "description": description,
                    "category": category,
                    "install_url": install_url,
                    "support_url": support_url,
                    "privacy_url": privacy_url,
                }
            ),
            options=options,
        )
        return data.listing or AppListing()

    async def delete_listing(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> AppListingDeleted:
        """Unpublish the application. Succeeds when nothing is published."""
        return await self._delete(
            f"/oauth/applications/{application_id}/listing",
            cast_to=AppListingDeleted,
            options=options,
        )
