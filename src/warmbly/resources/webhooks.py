"""The ``webhooks`` resource — register endpoints and inspect deliveries.

Maps to the ``/v1/webhooks`` route group. Outbound webhook requests are signed
with HMAC-SHA256 and carry the signature in the ``X-Warmbly-Signature`` header
using the ``sha256=<hexdigest>`` format. Verify it with the module-level
:func:`verify_webhook_signature` helper (aliased as :func:`verify_signature`).

The signing ``secret`` is returned **only** on the create and rotate-secret
responses; store it immediately, as it cannot be retrieved again.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Sequence
from typing import Any

from .._exceptions import WarmblyError
from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncWebhooks",
    "WebhookDelivery",
    "WebhookEndpoint",
    "WebhookEventType",
    "WebhookThrottleDrop",
    "WebhookVerification",
    "Webhooks",
    "verify_signature",
    "verify_webhook_signature",
]


class WebhookEndpoint(BaseModel):
    """A registered webhook endpoint.

    The plaintext signing ``secret`` is present only on the create and
    rotate-secret responses.
    """

    id: str
    organization_id: str | None = None
    url: str | None = None
    description: str | None = None
    event_types: Sequence[str] = []
    enabled: bool | None = None
    secret: str | None = None
    last_success_at: str | None = None
    last_failure_at: str | None = None
    consecutive_failures: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class WebhookDelivery(BaseModel):
    """A single delivery attempt of an event to an endpoint.

    The ``status`` is one of ``pending``, ``in_flight``, ``delivered``,
    ``failed``, or ``abandoned``.
    """

    id: str
    endpoint_id: str | None = None
    event_type: str | None = None
    status: str | None = None
    attempt_count: int | None = None
    response_status: int | None = None
    created_at: str | None = None


class WebhookEventType(BaseModel):
    """A webhook event type that endpoints may subscribe to."""

    name: str | None = None
    description: str | None = None
    category: str | None = None


class WebhookThrottleDrop(BaseModel):
    """An event that was dropped because an endpoint was being throttled."""

    id: str | None = None
    endpoint_id: str | None = None
    event_type: str | None = None
    reason: str | None = None
    dropped_at: str | None = None
    created_at: str | None = None


class WebhookVerification(BaseModel):
    """The result of a server-side endpoint verification (test ping)."""

    status: str | None = None
    delivery_id: str | None = None
    response_status: int | None = None
    message: str | None = None


class WebhookDeleted(BaseModel):
    """The result of deleting a webhook endpoint."""

    status: str | None = None


def verify_webhook_signature(
    *, payload: bytes | str, signature: str, secret: str
) -> dict[str, Any]:
    """Verify the HMAC-SHA256 signature of a webhook payload.

    Computes ``hmac.new(secret, payload, sha256).hexdigest()`` and compares it
    against the value supplied in the ``X-Warmbly-Signature`` header, using a
    constant-time comparison. The header value has the form
    ``sha256=<hexdigest>``; an optional ``sha256=`` prefix on *signature* is
    stripped before comparison.

    Args:
        payload: The raw request body, as received (``bytes`` or ``str``). It
            must not be re-serialized before verification, or the signature
            will not match.
        signature: The ``X-Warmbly-Signature`` header value, with or without
            the ``sha256=`` prefix.
        secret: The endpoint's signing secret (returned on create / rotate).

    Returns:
        The parsed JSON body as a ``dict``.

    Raises:
        WarmblyError: If the signature does not match the computed digest.
    """
    payload_bytes = payload.encode() if isinstance(payload, str) else payload
    expected = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
    provided = signature
    if provided.startswith("sha256="):
        provided = provided[len("sha256=") :]
    if not hmac.compare_digest(expected, provided):
        raise WarmblyError("Webhook signature verification failed.")
    parsed: dict[str, Any] = json.loads(payload_bytes)
    return parsed


# Convenience alias matching the documented ``client.webhooks.verify_signature``
# wording; both names refer to the same constant-time verifier.
verify_signature = verify_webhook_signature


class Webhooks(SyncAPIResource):
    """Synchronous ``webhooks`` resource."""

    def create(
        self,
        *,
        url: str,
        event_types: Sequence[str],
        description: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> WebhookEndpoint:
        """Register a webhook endpoint. The one-time ``secret`` is on the result.

        Args:
            url: The HTTPS URL that signed event payloads are POSTed to.
            event_types: The event types this endpoint subscribes to.
            description: An optional human-readable description.
        """
        body = drop_not_given(
            {
                "url": url,
                "event_types": event_types,
                "description": description,
            }
        )
        return self._post(
            "/webhooks", cast_to=WebhookEndpoint, body=body, options=options
        )

    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[WebhookEndpoint]:
        """List webhook endpoints (auto-paginating)."""
        return self._get_api_list(
            "/webhooks",
            model=WebhookEndpoint,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def event_types(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[WebhookEventType]:
        """List the event types endpoints may subscribe to (auto-paginating)."""
        return self._get_api_list(
            "/webhooks/event-types",
            model=WebhookEventType,
            options=options,
        )

    def deliveries(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[WebhookDelivery]:
        """List delivery attempts across all endpoints (auto-paginating)."""
        return self._get_api_list(
            "/webhooks/deliveries",
            model=WebhookDelivery,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def redeliver(
        self, delivery_id: str, *, options: RequestOptions | None = None
    ) -> WebhookDelivery:
        """Re-attempt a previously recorded delivery."""
        return self._post(
            f"/webhooks/deliveries/{delivery_id}/redeliver",
            cast_to=WebhookDelivery,
            options=options,
        )

    def throttle_drops(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[WebhookThrottleDrop]:
        """List events dropped due to endpoint throttling (auto-paginating)."""
        return self._get_api_list(
            "/webhooks/throttle-drops",
            model=WebhookThrottleDrop,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def update(
        self,
        webhook_id: str,
        *,
        url: NotGivenOr[str] = NOT_GIVEN,
        event_types: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> WebhookEndpoint:
        """Update an endpoint's URL, subscriptions, description, or enabled state."""
        body = drop_not_given(
            {
                "url": url,
                "event_types": event_types,
                "description": description,
                "enabled": enabled,
            }
        )
        return self._patch(
            f"/webhooks/{webhook_id}",
            cast_to=WebhookEndpoint,
            body=body,
            options=options,
        )

    def delete(
        self, webhook_id: str, *, options: RequestOptions | None = None
    ) -> WebhookDeleted:
        """Delete a webhook endpoint."""
        return self._delete(
            f"/webhooks/{webhook_id}", cast_to=WebhookDeleted, options=options
        )

    def rotate_secret(
        self, webhook_id: str, *, options: RequestOptions | None = None
    ) -> WebhookEndpoint:
        """Rotate an endpoint's signing secret. The new ``secret`` is on the result."""
        return self._post(
            f"/webhooks/{webhook_id}/rotate-secret",
            cast_to=WebhookEndpoint,
            options=options,
        )

    def verify(
        self, webhook_id: str, *, options: RequestOptions | None = None
    ) -> WebhookVerification:
        """Send a server-side test ping to verify an endpoint is reachable."""
        return self._post(
            f"/webhooks/{webhook_id}/verify",
            cast_to=WebhookVerification,
            options=options,
        )

    def endpoint_deliveries(
        self,
        webhook_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[WebhookDelivery]:
        """List delivery attempts for a single endpoint (auto-paginating)."""
        return self._get_api_list(
            f"/webhooks/{webhook_id}/deliveries",
            model=WebhookDelivery,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )


class AsyncWebhooks(AsyncAPIResource):
    """Asynchronous ``webhooks`` resource."""

    async def create(
        self,
        *,
        url: str,
        event_types: Sequence[str],
        description: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> WebhookEndpoint:
        """Register a webhook endpoint. The one-time ``secret`` is on the result.

        Args:
            url: The HTTPS URL that signed event payloads are POSTed to.
            event_types: The event types this endpoint subscribes to.
            description: An optional human-readable description.
        """
        body = drop_not_given(
            {
                "url": url,
                "event_types": event_types,
                "description": description,
            }
        )
        return await self._post(
            "/webhooks", cast_to=WebhookEndpoint, body=body, options=options
        )

    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[WebhookEndpoint]:
        """List webhook endpoints (auto-paginating)."""
        return self._get_api_list(
            "/webhooks",
            model=WebhookEndpoint,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def event_types(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[WebhookEventType]:
        """List the event types endpoints may subscribe to (auto-paginating)."""
        return self._get_api_list(
            "/webhooks/event-types",
            model=WebhookEventType,
            options=options,
        )

    def deliveries(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[WebhookDelivery]:
        """List delivery attempts across all endpoints (auto-paginating)."""
        return self._get_api_list(
            "/webhooks/deliveries",
            model=WebhookDelivery,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def redeliver(
        self, delivery_id: str, *, options: RequestOptions | None = None
    ) -> WebhookDelivery:
        """Re-attempt a previously recorded delivery."""
        return await self._post(
            f"/webhooks/deliveries/{delivery_id}/redeliver",
            cast_to=WebhookDelivery,
            options=options,
        )

    def throttle_drops(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[WebhookThrottleDrop]:
        """List events dropped due to endpoint throttling (auto-paginating)."""
        return self._get_api_list(
            "/webhooks/throttle-drops",
            model=WebhookThrottleDrop,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def update(
        self,
        webhook_id: str,
        *,
        url: NotGivenOr[str] = NOT_GIVEN,
        event_types: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> WebhookEndpoint:
        """Update an endpoint's URL, subscriptions, description, or enabled state."""
        body = drop_not_given(
            {
                "url": url,
                "event_types": event_types,
                "description": description,
                "enabled": enabled,
            }
        )
        return await self._patch(
            f"/webhooks/{webhook_id}",
            cast_to=WebhookEndpoint,
            body=body,
            options=options,
        )

    async def delete(
        self, webhook_id: str, *, options: RequestOptions | None = None
    ) -> WebhookDeleted:
        """Delete a webhook endpoint."""
        return await self._delete(
            f"/webhooks/{webhook_id}", cast_to=WebhookDeleted, options=options
        )

    async def rotate_secret(
        self, webhook_id: str, *, options: RequestOptions | None = None
    ) -> WebhookEndpoint:
        """Rotate an endpoint's signing secret. The new ``secret`` is on the result."""
        return await self._post(
            f"/webhooks/{webhook_id}/rotate-secret",
            cast_to=WebhookEndpoint,
            options=options,
        )

    async def verify(
        self, webhook_id: str, *, options: RequestOptions | None = None
    ) -> WebhookVerification:
        """Send a server-side test ping to verify an endpoint is reachable."""
        return await self._post(
            f"/webhooks/{webhook_id}/verify",
            cast_to=WebhookVerification,
            options=options,
        )

    def endpoint_deliveries(
        self,
        webhook_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[WebhookDelivery]:
        """List delivery attempts for a single endpoint (auto-paginating)."""
        return self._get_api_list(
            f"/webhooks/{webhook_id}/deliveries",
            model=WebhookDelivery,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )
