"""The top-level :class:`Warmbly` and :class:`AsyncWarmbly` clients.

A single client object owns all configuration and a shared connection pool, and
exposes each API resource group as a lazily-instantiated attribute
(``client.api_keys``, ``client.campaigns``, ...). Swap ``Warmbly`` for
``AsyncWarmbly`` and ``await`` the methods for the async variant.
"""

from __future__ import annotations

import os
from functools import cached_property

import httpx

from ._base_client import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    AsyncAPIClient,
    SyncAPIClient,
)
from ._exceptions import WarmblyError
from ._types import Timeout
from .resources import (
    Analytics,
    ApiKeys,
    AsyncAnalytics,
    AsyncApiKeys,
    AsyncCampaigns,
    AsyncContacts,
    AsyncCrm,
    AsyncEmails,
    AsyncIntegrations,
    AsyncOAuthApplications,
    AsyncPlans,
    AsyncTeams,
    AsyncTemplates,
    AsyncTimezones,
    AsyncUnibox,
    AsyncWebhooks,
    Campaigns,
    Contacts,
    Crm,
    Emails,
    Integrations,
    OAuthApplications,
    Plans,
    Teams,
    Templates,
    Timezones,
    Unibox,
    Webhooks,
)

__all__ = ["PRODUCTION_BASE_URL", "AsyncWarmbly", "Warmbly"]

PRODUCTION_BASE_URL = "https://api.warmbly.com/v1"


def _resolve_api_key(api_key: str | None) -> str:
    if api_key is None:
        api_key = os.environ.get("WARMBLY_API_KEY")
    if not api_key:
        raise WarmblyError(
            "No API key provided. Pass api_key=... or set the WARMBLY_API_KEY "
            "environment variable."
        )
    return api_key


def _resolve_base_url(base_url: str | None) -> str:
    return base_url or os.environ.get("WARMBLY_BASE_URL", PRODUCTION_BASE_URL)


class Warmbly(SyncAPIClient):
    """Synchronous Warmbly API client.

    Args:
        api_key: A Warmbly API key (``wmbly_...``) or OAuth2 access token
            (``wmat_...``). Falls back to the ``WARMBLY_API_KEY`` env var.
        base_url: API base URL. Falls back to ``WARMBLY_BASE_URL`` then the
            production endpoint.
        timeout: Per-request timeout in seconds or an :class:`httpx.Timeout`.
        max_retries: Number of automatic retries for transient failures.
        http_client: An optional pre-configured :class:`httpx.Client`.
    """

    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | Timeout | None = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.api_key = _resolve_api_key(api_key)
        super().__init__(
            base_url=_resolve_base_url(base_url),
            timeout=timeout,
            max_retries=max_retries,
            http_client=http_client,
        )

    @property
    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    @cached_property
    def api_keys(self) -> ApiKeys:
        return ApiKeys(self)

    @cached_property
    def oauth_applications(self) -> OAuthApplications:
        return OAuthApplications(self)

    @cached_property
    def campaigns(self) -> Campaigns:
        return Campaigns(self)

    @cached_property
    def emails(self) -> Emails:
        return Emails(self)

    @cached_property
    def contacts(self) -> Contacts:
        return Contacts(self)

    @cached_property
    def webhooks(self) -> Webhooks:
        return Webhooks(self)

    @cached_property
    def analytics(self) -> Analytics:
        return Analytics(self)

    @cached_property
    def integrations(self) -> Integrations:
        return Integrations(self)

    @cached_property
    def templates(self) -> Templates:
        return Templates(self)

    @cached_property
    def crm(self) -> Crm:
        return Crm(self)

    @cached_property
    def teams(self) -> Teams:
        return Teams(self)

    @cached_property
    def plans(self) -> Plans:
        return Plans(self)

    @cached_property
    def timezones(self) -> Timezones:
        return Timezones(self)

    @cached_property
    def unibox(self) -> Unibox:
        return Unibox(self)


class AsyncWarmbly(AsyncAPIClient):
    """Asynchronous Warmbly API client.

    Mirrors :class:`Warmbly`; every resource method is a coroutine. Remember to
    ``await client.close()`` (or use ``async with AsyncWarmbly(...) as client``).
    """

    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | Timeout | None = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = _resolve_api_key(api_key)
        super().__init__(
            base_url=_resolve_base_url(base_url),
            timeout=timeout,
            max_retries=max_retries,
            http_client=http_client,
        )

    @property
    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    @cached_property
    def api_keys(self) -> AsyncApiKeys:
        return AsyncApiKeys(self)

    @cached_property
    def oauth_applications(self) -> AsyncOAuthApplications:
        return AsyncOAuthApplications(self)

    @cached_property
    def campaigns(self) -> AsyncCampaigns:
        return AsyncCampaigns(self)

    @cached_property
    def emails(self) -> AsyncEmails:
        return AsyncEmails(self)

    @cached_property
    def contacts(self) -> AsyncContacts:
        return AsyncContacts(self)

    @cached_property
    def webhooks(self) -> AsyncWebhooks:
        return AsyncWebhooks(self)

    @cached_property
    def analytics(self) -> AsyncAnalytics:
        return AsyncAnalytics(self)

    @cached_property
    def integrations(self) -> AsyncIntegrations:
        return AsyncIntegrations(self)

    @cached_property
    def templates(self) -> AsyncTemplates:
        return AsyncTemplates(self)

    @cached_property
    def crm(self) -> AsyncCrm:
        return AsyncCrm(self)

    @cached_property
    def teams(self) -> AsyncTeams:
        return AsyncTeams(self)

    @cached_property
    def plans(self) -> AsyncPlans:
        return AsyncPlans(self)

    @cached_property
    def timezones(self) -> AsyncTimezones:
        return AsyncTimezones(self)

    @cached_property
    def unibox(self) -> AsyncUnibox:
        return AsyncUnibox(self)
