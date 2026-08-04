"""The ``webhooks`` resource: register endpoints and inspect deliveries.

Maps to the ``/v1/webhooks`` route group. Outbound webhook requests carry three
headers: ``X-Warmbly-Event`` (the event type, so you can route without parsing
the body), ``X-Warmbly-Event-Id`` (stable across retries, so it doubles as an
idempotency key), and ``X-Warmbly-Signature``.

The signature is Stripe-style: ``t=<unix>,v1=<hex>``, where the digest is
``HMAC-SHA256(secret, f"{t}.{raw_body}")``. Verify it with the module-level
:func:`verify_webhook_signature` (aliased as :func:`verify_signature`), which
also enforces a timestamp tolerance so a captured request cannot be replayed
indefinitely.

The signing ``secret`` is returned **only** on the create and rotate-secret
responses; store it immediately, as it cannot be retrieved again.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from collections.abc import Sequence
from typing import Any

from .._exceptions import WarmblyError
from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "CHALLENGE_HEADER",
    "DEFAULT_TOLERANCE",
    "EVENT_HEADER",
    "EVENT_ID_HEADER",
    "SIGNATURE_HEADER",
    "AsyncWebhooks",
    "WebhookDeleted",
    "WebhookDelivery",
    "WebhookEndpoint",
    "WebhookEventType",
    "WebhookRedelivery",
    "WebhookSecret",
    "WebhookThrottleDrop",
    "WebhookVerification",
    "Webhooks",
    "verify_signature",
    "verify_webhook_signature",
]

#: The header carrying ``t=<unix>,v1=<hex>`` on every outbound webhook.
SIGNATURE_HEADER = "X-Warmbly-Signature"

#: The header carrying the event type.
EVENT_HEADER = "X-Warmbly-Event"

#: The header carrying the retry-stable event id (use it to dedupe).
EVENT_ID_HEADER = "X-Warmbly-Event-Id"

#: The header a receiver may echo to answer a verification challenge.
CHALLENGE_HEADER = "X-Warmbly-Webhook-Challenge"

#: Default replay window, in seconds, accepted by :func:`verify_webhook_signature`.
DEFAULT_TOLERANCE = 300


class WebhookEndpoint(BaseModel):
    """A registered webhook endpoint.

    The plaintext signing ``secret`` is present only on the create response.
    An endpoint that fails repeatedly is auto-disabled; ``disabled_reason``
    explains why.
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
    last_failure_reason: str | None = None
    consecutive_failures: int | None = None
    oauth_application_id: str | None = None
    created_by: str | None = None
    verified_at: str | None = None
    ownership_confirmed: bool | None = None
    auto_disabled_at: str | None = None
    disabled_reason: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class WebhookSecret(BaseModel):
    """A freshly rotated signing secret. Shown once."""

    secret: str | None = None


class WebhookDelivery(BaseModel):
    """A single delivery attempt of an event to an endpoint.

    ``status`` is one of ``pending``, ``in_flight``, ``delivered``, ``failed``,
    or ``abandoned``.
    """

    id: str
    endpoint_id: str | None = None
    organization_id: str | None = None
    event_type: str | None = None
    event_id: str | None = None
    payload: dict[str, Any] | None = None
    status: str | None = None
    attempt_count: int | None = None
    max_attempts: int | None = None
    next_attempt_at: str | None = None
    last_attempt_at: str | None = None
    response_status: int | None = None
    response_body_excerpt: str | None = None
    error_reason: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class WebhookEventType(BaseModel):
    """An event type endpoints may subscribe to.

    ``firehose`` marks high-volume events that are opt-in for a reason.
    """

    type: str | None = None
    category: str | None = None
    description: str | None = None
    firehose: bool | None = None


class WebhookThrottleDrop(BaseModel):
    """A day's worth of events the dispatch throttle dropped."""

    event_type: str | None = None
    day: str | None = None
    dropped_windows: int | None = None
    last_dropped_at: str | None = None


class WebhookVerification(BaseModel):
    """The result of asking the server to re-verify an endpoint.

    The challenge is sent asynchronously; the endpoint flips to verified once
    it echoes the challenge value.
    """

    status: str | None = None


class WebhookRedelivery(BaseModel):
    """The result of queueing a delivery for another attempt."""

    status: str | None = None


class WebhookDeleted(BaseModel):
    """The result of deleting a webhook endpoint (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


def _parse_signature_header(signature: str) -> tuple[int, list[str]]:
    """Split ``t=<unix>,v1=<hex>[,v1=<hex>]`` into a timestamp and digests.

    More than one ``v1`` may be present during a secret rotation, so every
    candidate digest is returned.

    Raises:
        WarmblyError: If the header is missing its timestamp or any digest.
    """
    timestamp: int | None = None
    digests: list[str] = []
    for part in signature.split(","):
        key, _, value = part.strip().partition("=")
        if key == "t":
            try:
                timestamp = int(value)
            except ValueError:
                raise WarmblyError(
                    "Webhook signature header has a malformed timestamp."
                ) from None
        elif key == "v1":
            digests.append(value)
    if timestamp is None or not digests:
        raise WarmblyError(
            "Webhook signature header is malformed: expected 't=<unix>,v1=<hex>'."
        )
    return timestamp, digests


def verify_webhook_signature(
    *,
    payload: bytes | str,
    signature: str,
    secret: str,
    tolerance: int | None = DEFAULT_TOLERANCE,
) -> dict[str, Any]:
    """Verify the ``X-Warmbly-Signature`` header on a webhook request.

    Recomputes ``HMAC-SHA256(secret, f"{t}.{payload}")`` and compares it
    against the header's ``v1`` digest in constant time.

    Args:
        payload: The raw request body, exactly as received (``bytes`` or
            ``str``). It must not be re-serialized before verification, or the
            digest will not match.
        signature: The ``X-Warmbly-Signature`` header value.
        secret: The endpoint's signing secret (returned on create / rotate).
        tolerance: Maximum age of the signed timestamp, in seconds, before the
            request is rejected as a replay. Pass ``None`` to skip the check.

    Returns:
        The parsed JSON body as a ``dict``.

    Raises:
        WarmblyError: If the header is malformed, the timestamp is outside
            *tolerance*, or no digest matches.
    """
    payload_bytes = payload.encode() if isinstance(payload, str) else payload
    timestamp, digests = _parse_signature_header(signature)

    if tolerance is not None and abs(time.time() - timestamp) > tolerance:
        raise WarmblyError(
            f"Webhook timestamp is outside the {tolerance}s tolerance window."
        )

    signed = f"{timestamp}.".encode() + payload_bytes
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, digest) for digest in digests):
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
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> WebhookEndpoint:
        """Register a webhook endpoint. The one-time ``secret`` is on the result.

        Args:
            url: The HTTPS URL that signed event payloads are POSTed to.
            event_types: The event types this endpoint subscribes to (see
                :meth:`event_types`).
            description: An optional human-readable description.
            enabled: Whether to start delivering immediately.
        """
        body = drop_not_given(
            {
                "url": url,
                "event_types": list(event_types),
                "description": description,
                "enabled": enabled,
            }
        )
        return self._post(
            "/webhooks", cast_to=WebhookEndpoint, body=body, options=options
        )

    def list(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[WebhookEndpoint]:
        """List webhook endpoints. Returned in full, unpaginated."""
        return self._get_api_list(
            "/webhooks",
            model=WebhookEndpoint,
            data_key="endpoints",
            options=options,
        )

    def event_types(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[WebhookEventType]:
        """List every event type endpoints may subscribe to."""
        return self._get_api_list(
            "/webhooks/event-types",
            model=WebhookEventType,
            data_key="event_types",
            options=options,
        )

    def deliveries(
        self,
        *,
        endpoint_id: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        event_type: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[WebhookDelivery]:
        """List delivery attempts across all endpoints (auto-paginating).

        Args:
            endpoint_id: Restrict to one endpoint.
            status: Restrict to one delivery status.
            event_type: Restrict to one event type.
            limit: Page size (1-200; the server defaults to 50).
        """
        return self._get_api_list(
            "/webhooks/deliveries",
            model=WebhookDelivery,
            query={
                "endpoint_id": endpoint_id,
                "status": status,
                "event_type": event_type,
                "limit": limit,
                "cursor": cursor,
            },
            options=options,
        )

    def redeliver(
        self, delivery_id: str, *, options: RequestOptions | None = None
    ) -> WebhookRedelivery:
        """Queue a recorded delivery for a fresh attempt cycle."""
        return self._post(
            f"/webhooks/deliveries/{delivery_id}/redeliver",
            cast_to=WebhookRedelivery,
            options=options,
        )

    def throttle_drops(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[WebhookThrottleDrop]:
        """List events the dispatch throttle dropped over the last 30 days."""
        return self._get_api_list(
            "/webhooks/throttle-drops",
            model=WebhookThrottleDrop,
            data_key="drops",
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
        """Update an endpoint's URL, subscriptions, description, or enabled state.

        Changing the URL clears verification: the endpoint must echo a fresh
        challenge before events resume.
        """
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
    ) -> WebhookSecret:
        """Rotate an endpoint's signing secret. The new secret is shown once."""
        return self._post(
            f"/webhooks/{webhook_id}/rotate-secret",
            cast_to=WebhookSecret,
            options=options,
        )

    def verify(
        self, webhook_id: str, *, options: RequestOptions | None = None
    ) -> WebhookVerification:
        """Send a signed verification challenge to the endpoint.

        The endpoint becomes verified once it echoes the ``challenge`` value,
        either in its response body or the ``X-Warmbly-Webhook-Challenge``
        header.
        """
        return self._post(
            f"/webhooks/{webhook_id}/verify",
            cast_to=WebhookVerification,
            options=options,
        )

    def endpoint_deliveries(
        self,
        webhook_id: str,
        *,
        status: NotGivenOr[str] = NOT_GIVEN,
        event_type: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[WebhookDelivery]:
        """List delivery attempts for a single endpoint (auto-paginating)."""
        return self._get_api_list(
            f"/webhooks/{webhook_id}/deliveries",
            model=WebhookDelivery,
            query={
                "status": status,
                "event_type": event_type,
                "limit": limit,
                "cursor": cursor,
            },
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
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> WebhookEndpoint:
        """Register a webhook endpoint. The one-time ``secret`` is on the result.

        Args:
            url: The HTTPS URL that signed event payloads are POSTed to.
            event_types: The event types this endpoint subscribes to (see
                :meth:`event_types`).
            description: An optional human-readable description.
            enabled: Whether to start delivering immediately.
        """
        body = drop_not_given(
            {
                "url": url,
                "event_types": list(event_types),
                "description": description,
                "enabled": enabled,
            }
        )
        return await self._post(
            "/webhooks", cast_to=WebhookEndpoint, body=body, options=options
        )

    def list(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[WebhookEndpoint]:
        """List webhook endpoints. Returned in full, unpaginated."""
        return self._get_api_list(
            "/webhooks",
            model=WebhookEndpoint,
            data_key="endpoints",
            options=options,
        )

    def event_types(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[WebhookEventType]:
        """List every event type endpoints may subscribe to."""
        return self._get_api_list(
            "/webhooks/event-types",
            model=WebhookEventType,
            data_key="event_types",
            options=options,
        )

    def deliveries(
        self,
        *,
        endpoint_id: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        event_type: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[WebhookDelivery]:
        """List delivery attempts across all endpoints (auto-paginating).

        Args:
            endpoint_id: Restrict to one endpoint.
            status: Restrict to one delivery status.
            event_type: Restrict to one event type.
            limit: Page size (1-200; the server defaults to 50).
        """
        return self._get_api_list(
            "/webhooks/deliveries",
            model=WebhookDelivery,
            query={
                "endpoint_id": endpoint_id,
                "status": status,
                "event_type": event_type,
                "limit": limit,
                "cursor": cursor,
            },
            options=options,
        )

    async def redeliver(
        self, delivery_id: str, *, options: RequestOptions | None = None
    ) -> WebhookRedelivery:
        """Queue a recorded delivery for a fresh attempt cycle."""
        return await self._post(
            f"/webhooks/deliveries/{delivery_id}/redeliver",
            cast_to=WebhookRedelivery,
            options=options,
        )

    def throttle_drops(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[WebhookThrottleDrop]:
        """List events the dispatch throttle dropped over the last 30 days."""
        return self._get_api_list(
            "/webhooks/throttle-drops",
            model=WebhookThrottleDrop,
            data_key="drops",
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
        """Update an endpoint's URL, subscriptions, description, or enabled state.

        Changing the URL clears verification: the endpoint must echo a fresh
        challenge before events resume.
        """
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
    ) -> WebhookSecret:
        """Rotate an endpoint's signing secret. The new secret is shown once."""
        return await self._post(
            f"/webhooks/{webhook_id}/rotate-secret",
            cast_to=WebhookSecret,
            options=options,
        )

    async def verify(
        self, webhook_id: str, *, options: RequestOptions | None = None
    ) -> WebhookVerification:
        """Send a signed verification challenge to the endpoint.

        The endpoint becomes verified once it echoes the ``challenge`` value,
        either in its response body or the ``X-Warmbly-Webhook-Challenge``
        header.
        """
        return await self._post(
            f"/webhooks/{webhook_id}/verify",
            cast_to=WebhookVerification,
            options=options,
        )

    def endpoint_deliveries(
        self,
        webhook_id: str,
        *,
        status: NotGivenOr[str] = NOT_GIVEN,
        event_type: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[WebhookDelivery]:
        """List delivery attempts for a single endpoint (auto-paginating)."""
        return self._get_api_list(
            f"/webhooks/{webhook_id}/deliveries",
            model=WebhookDelivery,
            query={
                "status": status,
                "event_type": event_type,
                "limit": limit,
                "cursor": cursor,
            },
            options=options,
        )
