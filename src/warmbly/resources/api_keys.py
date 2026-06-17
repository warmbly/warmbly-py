"""The ``api_keys`` resource: create, manage, and audit API keys.

Maps to the ``/v1/api-keys`` route group. The plaintext ``secret`` is returned
**only** on the create response; store it immediately, as it cannot be
retrieved again.
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
    "ApiKey",
    "ApiKeyDeleted",
    "ApiKeyPermissions",
    "ApiKeyUsageSummary",
    "ApiKeys",
    "AsyncApiKeys",
]


class ApiKey(BaseModel):
    """An API key. ``secret`` is present only on the create response."""

    id: str
    name: str
    organization_id: str | None = None
    user_id: str | None = None
    description: str | None = None
    key_prefix: str | None = None
    key_suffix: str | None = None
    secret: str | None = None
    permissions: int = 0
    allowed_ips: Sequence[str] = []
    allowed_email_accounts: Sequence[str] = []
    rate_limit_per_minute: int | None = None
    status: str | None = None
    last_used_at: str | None = None
    last_request_ip: str | None = None
    expires_at: str | None = None
    revoked_at: str | None = None
    revoked_reason: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ApiKeyDeleted(BaseModel):
    """The result of revoking an API key."""

    status: str | None = None


class PermissionInfo(BaseModel):
    name: str | None = None
    value: int | None = None
    description: str | None = None
    category: str | None = None


class ApiKeyPermissions(BaseModel):
    """The catalog of available permissions and convenience presets."""

    permissions: Sequence[PermissionInfo] = []
    presets: dict[str, int] = {}


class ApiKeyUsageSummary(BaseModel):
    active_keys: int | None = None
    revoked_keys: int | None = None
    expired_keys: int | None = None
    requests_24h: int | None = None
    errors_24h: int | None = None
    avg_latency_ms_24h: float | None = None
    last_call_at: str | None = None


class ApiKeyUsageAnalytics(BaseModel):
    api_key_id: str | None = None
    from_: str | None = None
    to: str | None = None
    interval: str | None = None
    buckets: Sequence[dict[str, Any]] = []
    endpoints: Sequence[dict[str, Any]] = []
    total: int | None = None
    errors: int | None = None


class ApiKeyUsageLog(BaseModel):
    id: str
    api_key_id: str | None = None
    endpoint: str | None = None
    method: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    response_code: int | None = None
    response_time_ms: int | None = None
    created_at: str | None = None


class ApiKeys(SyncAPIResource):
    """Synchronous ``api_keys`` resource."""

    def create(
        self,
        *,
        name: str,
        permissions: int,
        description: NotGivenOr[str] = NOT_GIVEN,
        allowed_ips: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        allowed_email_accounts: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        rate_limit_per_minute: NotGivenOr[int] = NOT_GIVEN,
        expires_at: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApiKey:
        """Create an API key. The one-time ``secret`` is on the returned object.

        Args:
            name: A human-readable label for the key.
            permissions: The permission bitmask (see
                :func:`warmbly.scopes_to_mask`).
            description: An optional longer description.
            allowed_ips: Optional IP / CIDR allowlist.
            allowed_email_accounts: Optional mailbox-id allowlist.
            rate_limit_per_minute: Optional per-key rate limit.
            expires_at: Optional RFC3339 expiry timestamp.
        """
        body = drop_not_given(
            {
                "name": name,
                "permissions": permissions,
                "description": description,
                "allowed_ips": allowed_ips,
                "allowed_email_accounts": allowed_email_accounts,
                "rate_limit_per_minute": rate_limit_per_minute,
                "expires_at": expires_at,
            }
        )
        return self._post("/api-keys", cast_to=ApiKey, body=body, options=options)

    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[ApiKey]:
        """List API keys (auto-paginating)."""
        return self._get_api_list(
            "/api-keys",
            model=ApiKey,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def retrieve(
        self, api_key_id: str, *, options: RequestOptions | None = None
    ) -> ApiKey:
        """Retrieve a single API key by id."""
        return self._get(f"/api-keys/{api_key_id}", cast_to=ApiKey, options=options)

    def update(
        self,
        api_key_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        permissions: NotGivenOr[int] = NOT_GIVEN,
        allowed_ips: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        allowed_email_accounts: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        rate_limit_per_minute: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApiKey:
        """Update a key's metadata, permissions, or limits."""
        body = drop_not_given(
            {
                "name": name,
                "description": description,
                "permissions": permissions,
                "allowed_ips": allowed_ips,
                "allowed_email_accounts": allowed_email_accounts,
                "rate_limit_per_minute": rate_limit_per_minute,
            }
        )
        return self._patch(
            f"/api-keys/{api_key_id}", cast_to=ApiKey, body=body, options=options
        )

    def delete(
        self,
        api_key_id: str,
        *,
        reason: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApiKeyDeleted:
        """Revoke an API key."""
        query = drop_not_given({"reason": reason})
        return self._delete(
            f"/api-keys/{api_key_id}",
            cast_to=ApiKeyDeleted,
            query=query,
            options=options,
        )

    def permissions(
        self, *, options: RequestOptions | None = None
    ) -> ApiKeyPermissions:
        """List the available permissions and presets."""
        return self._get(
            "/api-keys/permissions", cast_to=ApiKeyPermissions, options=options
        )

    def usage_summary(
        self, *, options: RequestOptions | None = None
    ) -> ApiKeyUsageSummary:
        """Org-level API usage summary."""
        return self._get(
            "/api-keys/usage/summary", cast_to=ApiKeyUsageSummary, options=options
        )

    def usage_analytics(
        self,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        interval: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApiKeyUsageAnalytics:
        """Time-bucketed org-level usage analytics."""
        query = drop_not_given({"from": from_, "to": to, "interval": interval})
        return self._get(
            "/api-keys/usage/analytics",
            cast_to=ApiKeyUsageAnalytics,
            query=query,
            options=options,
        )

    def analytics(
        self, api_key_id: str, *, options: RequestOptions | None = None
    ) -> ApiKeyUsageAnalytics:
        """Per-key usage analytics."""
        return self._get(
            f"/api-keys/{api_key_id}/analytics",
            cast_to=ApiKeyUsageAnalytics,
            options=options,
        )

    def logs(
        self,
        api_key_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[ApiKeyUsageLog]:
        """Raw per-key request logs (auto-paginating)."""
        return self._get_api_list(
            f"/api-keys/{api_key_id}/logs",
            model=ApiKeyUsageLog,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )


class AsyncApiKeys(AsyncAPIResource):
    """Asynchronous ``api_keys`` resource."""

    async def create(
        self,
        *,
        name: str,
        permissions: int,
        description: NotGivenOr[str] = NOT_GIVEN,
        allowed_ips: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        allowed_email_accounts: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        rate_limit_per_minute: NotGivenOr[int] = NOT_GIVEN,
        expires_at: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApiKey:
        """Create an API key. The one-time ``secret`` is on the returned object."""
        body = drop_not_given(
            {
                "name": name,
                "permissions": permissions,
                "description": description,
                "allowed_ips": allowed_ips,
                "allowed_email_accounts": allowed_email_accounts,
                "rate_limit_per_minute": rate_limit_per_minute,
                "expires_at": expires_at,
            }
        )
        return await self._post("/api-keys", cast_to=ApiKey, body=body, options=options)

    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[ApiKey]:
        """List API keys (auto-paginating)."""
        return self._get_api_list(
            "/api-keys",
            model=ApiKey,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def retrieve(
        self, api_key_id: str, *, options: RequestOptions | None = None
    ) -> ApiKey:
        """Retrieve a single API key by id."""
        return await self._get(
            f"/api-keys/{api_key_id}", cast_to=ApiKey, options=options
        )

    async def update(
        self,
        api_key_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        permissions: NotGivenOr[int] = NOT_GIVEN,
        allowed_ips: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        allowed_email_accounts: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        rate_limit_per_minute: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApiKey:
        """Update a key's metadata, permissions, or limits."""
        body = drop_not_given(
            {
                "name": name,
                "description": description,
                "permissions": permissions,
                "allowed_ips": allowed_ips,
                "allowed_email_accounts": allowed_email_accounts,
                "rate_limit_per_minute": rate_limit_per_minute,
            }
        )
        return await self._patch(
            f"/api-keys/{api_key_id}", cast_to=ApiKey, body=body, options=options
        )

    async def delete(
        self,
        api_key_id: str,
        *,
        reason: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApiKeyDeleted:
        """Revoke an API key."""
        query = drop_not_given({"reason": reason})
        return await self._delete(
            f"/api-keys/{api_key_id}",
            cast_to=ApiKeyDeleted,
            query=query,
            options=options,
        )

    async def permissions(
        self, *, options: RequestOptions | None = None
    ) -> ApiKeyPermissions:
        """List the available permissions and presets."""
        return await self._get(
            "/api-keys/permissions", cast_to=ApiKeyPermissions, options=options
        )

    async def usage_summary(
        self, *, options: RequestOptions | None = None
    ) -> ApiKeyUsageSummary:
        """Org-level API usage summary."""
        return await self._get(
            "/api-keys/usage/summary", cast_to=ApiKeyUsageSummary, options=options
        )

    async def usage_analytics(
        self,
        *,
        from_: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[str] = NOT_GIVEN,
        interval: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApiKeyUsageAnalytics:
        """Time-bucketed org-level usage analytics."""
        query = drop_not_given({"from": from_, "to": to, "interval": interval})
        return await self._get(
            "/api-keys/usage/analytics",
            cast_to=ApiKeyUsageAnalytics,
            query=query,
            options=options,
        )

    async def analytics(
        self, api_key_id: str, *, options: RequestOptions | None = None
    ) -> ApiKeyUsageAnalytics:
        """Per-key usage analytics."""
        return await self._get(
            f"/api-keys/{api_key_id}/analytics",
            cast_to=ApiKeyUsageAnalytics,
            options=options,
        )

    def logs(
        self,
        api_key_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[ApiKeyUsageLog]:
        """Raw per-key request logs (auto-paginating)."""
        return self._get_api_list(
            f"/api-keys/{api_key_id}/logs",
            model=ApiKeyUsageLog,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )
