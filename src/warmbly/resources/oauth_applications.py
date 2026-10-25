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
:func:`warmbly.scopes_to_mask`. An app can request any permission except
``api_keys``, which stays with people and API keys.

Every route here needs the ``api_keys`` API permission. OAuth app tokens are
refused (``403`` ``oauth_token_not_allowed``), so an app can never register
apps, rotate secrets, or read webhook secrets; use an API key or a session.
Creating, editing, and deleting an app, rotating its secrets, and changing its
logo are recorded in the workspace audit log.
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
    "AsyncOAuthApplications",
    "OAuthAppListing",
    "OAuthApplication",
    "OAuthApplicationDeleted",
    "OAuthApplicationLogo",
    "OAuthApplications",
    "OAuthClientSecret",
    "OAuthDeveloperAccess",
    "OAuthWebhookDelivery",
    "OAuthWebhookEndpoint",
    "WebhookSecret",
]


class OAuthApplication(BaseModel):
    """A registered OAuth 2.1 application.

    ``is_public`` marks a PKCE-only client with no secret;
    ``dynamically_registered`` marks one created through RFC 7591 dynamic
    client registration rather than the dashboard. ``suspended_at`` and
    ``suspended_reason`` are set when the instance's operators suspended the
    app: it can no longer sign anyone in, its tokens stop working, and only an
    operator can lift the suspension.
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


class OAuthDeveloperAccess(BaseModel):
    """What the workspace may do with OAuth apps right now.

    When ``blocked`` is ``True``, registering or publishing an app answers
    ``403`` ``developer_access_blocked``; apps the workspace already has keep
    working unless they were suspended too. ``reason`` says why.
    """

    blocked: bool | None = None
    reason: str | None = None


class _OAuthApplicationList(BaseModel):
    applications: Sequence[OAuthApplication] = []
    developer_access: OAuthDeveloperAccess | None = None


class AppListing(BaseModel):
    """An app's page in the community directory.

    ``status`` is ``published`` (reachable by its link, listed in discovery once
    enough workspaces use it), ``featured`` (picked by an operator, always
    listed), or ``hidden`` (taken down by an operator, with ``status_note``
    saying why). ``category`` is one of ``crm``, ``automation``,
    ``notifications``, ``meetings``, ``data``, ``verification``, ``ai``, or
    ``other``.
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


class OAuthAppListing(BaseModel):
    """The ``{"listing": ...}`` envelope of the listing routes.

    ``listing`` is ``None`` when the app is not published.
    """

    listing: AppListing | None = None


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

        Registering is refused with ``403`` ``developer_access_blocked`` when an
        operator blocked the workspace or the caller from registering apps. The
        name follows the naming rules and cannot include Warmbly.

        Args:
            name: The application name shown on the consent screen.
            redirect_uris: The exact URIs an authorization code may return to.
            scopes: The scope bitmask the app may request (see
                :func:`warmbly.scopes_to_mask`).
            description: A short description for the consent screen.
            logo_url: A logo this instance hosted for your workspace (see
                :meth:`upload_logo`); any other address is refused with
                ``invalid_logo``.
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
        """Update an application's registration.

        The server replaces the whole registration, so send every field you want
        to keep (at least ``name``, ``redirect_uris`` and ``scopes``); a field
        you leave out is cleared, or refused when it is required. The one
        exception is ``logo_url``: an update without it keeps the current logo.
        Scopes outside what an app may hold (``api_keys``) are dropped.
        A suspended app cannot be updated (``409`` ``app_suspended``).
        """
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
        during registration, before an application id exists. The image is a
        PNG or JPG of at most 2 MB, between 32 and 1024 pixels on each side;
        the server re-encodes it so only the pixels are kept.

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

    def upload_application_logo(
        self,
        application_id: str,
        *,
        file: bytes,
        filename: str = "logo.png",
        content_type: str = "image/png",
        options: RequestOptions | None = None,
    ) -> OAuthApplication:
        """Upload a logo to an application; the server stores it and sets it.

        The image is a PNG or JPG of at most 2 MB, between 32 and 1024 pixels
        on each side; the server re-encodes it so only the pixels are kept, and
        the previous logo is deleted. Returns the updated application.

        Args:
            application_id: The application.
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

    def delete_application_logo(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthApplication:
        """Remove an application's logo. Returns the updated application."""
        return self._delete(
            f"/oauth/applications/{application_id}/logo",
            cast_to=OAuthApplication,
            options=options,
        )

    def developer_access(
        self, *, options: RequestOptions | None = None
    ) -> OAuthDeveloperAccess:
        """Report whether the workspace may register and publish OAuth apps.

        Read from the application list, which carries it next to the apps.
        """
        page = self._get(
            "/oauth/applications", cast_to=_OAuthApplicationList, options=options
        )
        return page.developer_access or OAuthDeveloperAccess()

    def get_listing(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthAppListing:
        """Retrieve an app's community-directory listing.

        ``listing`` is ``None`` when the app is not published.
        """
        return self._get(
            f"/oauth/applications/{application_id}/listing",
            cast_to=OAuthAppListing,
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
    ) -> OAuthAppListing:
        """Publish an app to the community directory, or edit its listing.

        Replaces the whole listing, so repeating the request is safe and an
        omitted optional field is cleared. Changing a ``featured`` listing, or
        the app's name, logo, website or scopes, returns it to ``published``.
        A refusal is ``400`` ``invalid_listing`` (the message names the field),
        ``400`` ``app_not_listable`` for a disabled or dynamically registered
        app, or ``409`` ``listing_slug_taken``.

        Args:
            application_id: The application.
            slug: The link: 3 to 48 lowercase letters, numbers or single
                dashes, starting and ending with a letter or number.
            tagline: One line, at most 120 characters.
            category: ``crm``, ``automation``, ``notifications``, ``meetings``,
                ``data``, ``verification``, ``ai``, or ``other``.
            install_url: Where Install takes people; must be ``https``.
            description: At most 2000 characters; line breaks are kept.
            support_url: An ``https`` support link.
            privacy_url: An ``https`` privacy-policy link.
        """
        return self._put(
            f"/oauth/applications/{application_id}/listing",
            cast_to=OAuthAppListing,
            body=drop_not_given(
                {
                    "slug": slug,
                    "tagline": tagline,
                    "category": category,
                    "install_url": install_url,
                    "description": description,
                    "support_url": support_url,
                    "privacy_url": privacy_url,
                }
            ),
            options=options,
        )

    def delete_listing(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthApplicationDeleted:
        """Unpublish an app. Workspaces that installed it keep their grants.

        Succeeds when there is no listing, so it is safe to retry. A listing an
        operator hid stays until they restore it (``409``).
        """
        return self._delete(
            f"/oauth/applications/{application_id}/listing",
            cast_to=OAuthApplicationDeleted,
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

        Registering is refused with ``403`` ``developer_access_blocked`` when an
        operator blocked the workspace or the caller from registering apps. The
        name follows the naming rules and cannot include Warmbly.

        Args:
            name: The application name shown on the consent screen.
            redirect_uris: The exact URIs an authorization code may return to.
            scopes: The scope bitmask the app may request (see
                :func:`warmbly.scopes_to_mask`).
            description: A short description for the consent screen.
            logo_url: A logo this instance hosted for your workspace (see
                :meth:`upload_logo`); any other address is refused with
                ``invalid_logo``.
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
        """Update an application's registration.

        The server replaces the whole registration, so send every field you want
        to keep (at least ``name``, ``redirect_uris`` and ``scopes``); a field
        you leave out is cleared, or refused when it is required. The one
        exception is ``logo_url``: an update without it keeps the current logo.
        Scopes outside what an app may hold (``api_keys``) are dropped.
        A suspended app cannot be updated (``409`` ``app_suspended``).
        """
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
        during registration, before an application id exists. The image is a
        PNG or JPG of at most 2 MB, between 32 and 1024 pixels on each side;
        the server re-encodes it so only the pixels are kept.

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

    async def upload_application_logo(
        self,
        application_id: str,
        *,
        file: bytes,
        filename: str = "logo.png",
        content_type: str = "image/png",
        options: RequestOptions | None = None,
    ) -> OAuthApplication:
        """Upload a logo to an application; the server stores it and sets it.

        The image is a PNG or JPG of at most 2 MB, between 32 and 1024 pixels
        on each side; the server re-encodes it so only the pixels are kept, and
        the previous logo is deleted. Returns the updated application.

        Args:
            application_id: The application.
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

    async def delete_application_logo(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthApplication:
        """Remove an application's logo. Returns the updated application."""
        return await self._delete(
            f"/oauth/applications/{application_id}/logo",
            cast_to=OAuthApplication,
            options=options,
        )

    async def developer_access(
        self, *, options: RequestOptions | None = None
    ) -> OAuthDeveloperAccess:
        """Report whether the workspace may register and publish OAuth apps.

        Read from the application list, which carries it next to the apps.
        """
        page = await self._get(
            "/oauth/applications", cast_to=_OAuthApplicationList, options=options
        )
        return page.developer_access or OAuthDeveloperAccess()

    async def get_listing(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthAppListing:
        """Retrieve an app's community-directory listing.

        ``listing`` is ``None`` when the app is not published.
        """
        return await self._get(
            f"/oauth/applications/{application_id}/listing",
            cast_to=OAuthAppListing,
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
    ) -> OAuthAppListing:
        """Publish an app to the community directory, or edit its listing.

        Replaces the whole listing, so repeating the request is safe and an
        omitted optional field is cleared. Changing a ``featured`` listing, or
        the app's name, logo, website or scopes, returns it to ``published``.
        A refusal is ``400`` ``invalid_listing`` (the message names the field),
        ``400`` ``app_not_listable`` for a disabled or dynamically registered
        app, or ``409`` ``listing_slug_taken``.

        Args:
            application_id: The application.
            slug: The link: 3 to 48 lowercase letters, numbers or single
                dashes, starting and ending with a letter or number.
            tagline: One line, at most 120 characters.
            category: ``crm``, ``automation``, ``notifications``, ``meetings``,
                ``data``, ``verification``, ``ai``, or ``other``.
            install_url: Where Install takes people; must be ``https``.
            description: At most 2000 characters; line breaks are kept.
            support_url: An ``https`` support link.
            privacy_url: An ``https`` privacy-policy link.
        """
        return await self._put(
            f"/oauth/applications/{application_id}/listing",
            cast_to=OAuthAppListing,
            body=drop_not_given(
                {
                    "slug": slug,
                    "tagline": tagline,
                    "category": category,
                    "install_url": install_url,
                    "description": description,
                    "support_url": support_url,
                    "privacy_url": privacy_url,
                }
            ),
            options=options,
        )

    async def delete_listing(
        self, application_id: str, *, options: RequestOptions | None = None
    ) -> OAuthApplicationDeleted:
        """Unpublish an app. Workspaces that installed it keep their grants.

        Succeeds when there is no listing, so it is safe to retry. A listing an
        operator hid stays until they restore it (``409``).
        """
        return await self._delete(
            f"/oauth/applications/{application_id}/listing",
            cast_to=OAuthApplicationDeleted,
            options=options,
        )
