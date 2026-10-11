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

Who may call these routes: an **API key** holding the ``api_keys`` scope, or a
dashboard session. A token issued to an **OAuth application** is refused on
every route in this group, reads included, with ``403`` and the code
``oauth_token_not_allowed``; an app cannot manage apps or credentials. Rotating
a secret additionally asks a dashboard session to have re-confirmed the account
holder recently (``reauth_required``, see
:attr:`warmbly.APIError.requires_reauth`); an API key is never asked to.
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
    "AsyncOAuthApplications",
    "OAuthAppListing",
    "OAuthAppListingDeleted",
    "OAuthAppListingResponse",
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
    client registration rather than the dashboard. ``suspended_at`` is set when
    an instance operator suspended the app; the owner cannot lift that, and
    edits to a suspended app (including its logo and listing) are refused with
    ``409`` and the code ``app_suspended``.
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
    suspended_at: str | None = None
    suspended_reason: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


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


class OAuthAppListing(BaseModel):
    """An application's page in the community app directory.

    ``status`` is ``"published"`` (reachable by its link), ``"featured"``
    (picked by an operator) or ``"hidden"`` (taken down by an operator;
    ``status_note`` may say why). ``category`` is one of ``crm``,
    ``automation``, ``notifications``, ``meetings``, ``data``,
    ``verification``, ``ai`` or ``other``.
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


class OAuthAppListingResponse(BaseModel):
    """The ``{"listing": ...}`` envelope of the listing routes.

    ``listing`` is ``None`` when the application is not published.
    """

    listing: OAuthAppListing | None = None


class OAuthAppListingDeleted(BaseModel):
    """The result of unpublishing an application."""

    deleted: bool | None = None


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
        """Rotate the client secret. The new secret is shown once.

        A dashboard session must have re-confirmed the account holder recently
        (``reauth_required``); an API key with the ``api_keys`` scope is never
        asked to. An OAuth app token is refused (``oauth_token_not_allowed``).
        """
        return self._post(
            f"/oauth/applications/{application_id}/rotate-secret",
            cast_to=OAuthClientSecret,
            options=options,
        )

    def webhook_secret(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> WebhookSecret:
        """Reveal the application-level webhook signing secret.

        Fresh-auth rules as for :meth:`rotate_secret`.
        """
        return self._get(
            f"/oauth/applications/{application_id}/webhook-secret",
            cast_to=WebhookSecret,
            options=options,
        )

    def rotate_webhook_secret(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> WebhookSecret:
        """Rotate the application-level webhook signing secret.

        Fresh-auth rules as for :meth:`rotate_secret`.
        """
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
        """Upload a logo and set it on an existing application.

        Unlike :meth:`upload_logo`, which only hosts the image, this stores it
        and updates the application in one call, then deletes the previous
        image once nothing points at it. Returns the updated application. The
        image must be a PNG or JPG, at most 2 MB and at least 32 pixels on each
        side; the server re-encodes it. Answers ``409`` (``app_suspended``) for
        a suspended app and ``403`` (``developer_access_blocked``) when the
        workspace may not publish apps.

        Requires the ``api_keys`` scope. An OAuth app token is refused
        (``oauth_token_not_allowed``).

        Args:
            application_id: The application to change.
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

    def remove_logo(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthApplication:
        """Clear an application's logo and return the updated application.

        Requires the ``api_keys`` scope. An OAuth app token is refused
        (``oauth_token_not_allowed``); a suspended app answers ``409``
        (``app_suspended``).
        """
        return self._delete(
            f"/oauth/applications/{application_id}/logo",
            cast_to=OAuthApplication,
            options=options,
        )

    def retrieve_listing(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthAppListingResponse:
        """Read the application's community-directory listing.

        The response's ``listing`` is ``None`` while the app is unpublished. A
        dynamically registered client cannot be listed (``400``,
        ``app_not_listable``). Requires the ``api_keys`` scope. An OAuth app
        token is refused (``oauth_token_not_allowed``).
        """
        return self._get(
            f"/oauth/applications/{application_id}/listing",
            cast_to=OAuthAppListingResponse,
            options=options,
        )

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
    ) -> OAuthAppListingResponse:
        """Publish the application, or replace its listing.

        The whole listing is written each time; saving identical content is a
        no-op. The app must be active and not suspended (``400``,
        ``app_not_listable``). A taken *slug* answers ``409``
        (``listing_slug_taken``); a rejected field answers ``400``
        (``invalid_listing``).

        Requires the ``api_keys`` scope. An OAuth app token is refused
        (``oauth_token_not_allowed``).

        Args:
            application_id: The application to publish.
            slug: The listing's link: 3 to 48 lowercase letters, digits or
                single dashes.
            tagline: One line, at most 120 characters.
            category: ``crm``, ``automation``, ``notifications``, ``meetings``,
                ``data``, ``verification``, ``ai`` or ``other``.
            install_url: The ``https`` address people start installing from.
            description: Plain text, at most 2000 characters.
            support_url: An ``https`` support address.
            privacy_url: An ``https`` privacy policy address.
        """
        return self._put(
            f"/oauth/applications/{application_id}/listing",
            cast_to=OAuthAppListingResponse,
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

    def delete_listing(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthAppListingDeleted:
        """Unpublish the application. Workspaces that installed it keep their
        grant until they revoke it.

        A listing an operator hid stays until they restore it (``409``,
        ``listing_hidden``). Requires the ``api_keys`` scope. An OAuth app
        token is refused (``oauth_token_not_allowed``).
        """
        return self._delete(
            f"/oauth/applications/{application_id}/listing",
            cast_to=OAuthAppListingDeleted,
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
        """Rotate the client secret. The new secret is shown once.

        A dashboard session must have re-confirmed the account holder recently
        (``reauth_required``); an API key with the ``api_keys`` scope is never
        asked to. An OAuth app token is refused (``oauth_token_not_allowed``).
        """
        return await self._post(
            f"/oauth/applications/{application_id}/rotate-secret",
            cast_to=OAuthClientSecret,
            options=options,
        )

    async def webhook_secret(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> WebhookSecret:
        """Reveal the application-level webhook signing secret.

        Fresh-auth rules as for :meth:`rotate_secret`.
        """
        return await self._get(
            f"/oauth/applications/{application_id}/webhook-secret",
            cast_to=WebhookSecret,
            options=options,
        )

    async def rotate_webhook_secret(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> WebhookSecret:
        """Rotate the application-level webhook signing secret.

        Fresh-auth rules as for :meth:`rotate_secret`.
        """
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
        """Upload a logo and set it on an existing application.

        Unlike :meth:`upload_logo`, which only hosts the image, this stores it
        and updates the application in one call, then deletes the previous
        image once nothing points at it. Returns the updated application. The
        image must be a PNG or JPG, at most 2 MB and at least 32 pixels on each
        side; the server re-encodes it. Answers ``409`` (``app_suspended``) for
        a suspended app and ``403`` (``developer_access_blocked``) when the
        workspace may not publish apps.

        Requires the ``api_keys`` scope. An OAuth app token is refused
        (``oauth_token_not_allowed``).

        Args:
            application_id: The application to change.
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

    async def remove_logo(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthApplication:
        """Clear an application's logo and return the updated application.

        Requires the ``api_keys`` scope. An OAuth app token is refused
        (``oauth_token_not_allowed``); a suspended app answers ``409``
        (``app_suspended``).
        """
        return await self._delete(
            f"/oauth/applications/{application_id}/logo",
            cast_to=OAuthApplication,
            options=options,
        )

    async def retrieve_listing(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthAppListingResponse:
        """Read the application's community-directory listing.

        The response's ``listing`` is ``None`` while the app is unpublished. A
        dynamically registered client cannot be listed (``400``,
        ``app_not_listable``). Requires the ``api_keys`` scope. An OAuth app
        token is refused (``oauth_token_not_allowed``).
        """
        return await self._get(
            f"/oauth/applications/{application_id}/listing",
            cast_to=OAuthAppListingResponse,
            options=options,
        )

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
    ) -> OAuthAppListingResponse:
        """Publish the application, or replace its listing.

        The whole listing is written each time; saving identical content is a
        no-op. The app must be active and not suspended (``400``,
        ``app_not_listable``). A taken *slug* answers ``409``
        (``listing_slug_taken``); a rejected field answers ``400``
        (``invalid_listing``).

        Requires the ``api_keys`` scope. An OAuth app token is refused
        (``oauth_token_not_allowed``).

        Args:
            application_id: The application to publish.
            slug: The listing's link: 3 to 48 lowercase letters, digits or
                single dashes.
            tagline: One line, at most 120 characters.
            category: ``crm``, ``automation``, ``notifications``, ``meetings``,
                ``data``, ``verification``, ``ai`` or ``other``.
            install_url: The ``https`` address people start installing from.
            description: Plain text, at most 2000 characters.
            support_url: An ``https`` support address.
            privacy_url: An ``https`` privacy policy address.
        """
        return await self._put(
            f"/oauth/applications/{application_id}/listing",
            cast_to=OAuthAppListingResponse,
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

    async def delete_listing(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthAppListingDeleted:
        """Unpublish the application. Workspaces that installed it keep their
        grant until they revoke it.

        A listing an operator hid stays until they restore it (``409``,
        ``listing_hidden``). Requires the ``api_keys`` scope. An OAuth app
        token is refused (``oauth_token_not_allowed``).
        """
        return await self._delete(
            f"/oauth/applications/{application_id}/listing",
            cast_to=OAuthAppListingDeleted,
            options=options,
        )
