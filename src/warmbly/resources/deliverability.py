"""The ``deliverability`` resource: ingest bounce and complaint events.

Maps to ``POST /v1/deliverability/events``. This is the inbound side of the
deliverability pipeline: a downstream processor (an SES bounce handler, a
provider webhook relay) posts what it saw, and Warmbly applies the
organization's suppression and auto-pause rules to it.

Ingestion is fire-and-forget — the endpoint answers ``202 Accepted`` and does
the work behind it. Pass ``idempotency_key`` so a retried delivery from your
own queue is not counted twice.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._models import BaseModel
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncDeliverability",
    "Deliverability",
    "DeliverabilityEventAccepted",
]


class DeliverabilityEventAccepted(BaseModel):
    """The acknowledgement of an ingested event (``202 Accepted``, no body)."""

    accepted: bool | None = None


def _event_body(
    *,
    event_type: str,
    recipient_email: str,
    campaign_id: NotGivenOr[str],
    task_id: NotGivenOr[str],
    contact_id: NotGivenOr[str],
    provider: NotGivenOr[str],
    reason: NotGivenOr[str],
    idempotency_key: NotGivenOr[str],
    metadata: NotGivenOr[Mapping[str, Any]],
) -> dict[str, Any]:
    return drop_not_given(
        {
            "event_type": event_type,
            "recipient_email": recipient_email,
            "campaign_id": campaign_id,
            "task_id": task_id,
            "contact_id": contact_id,
            "provider": provider,
            "reason": reason,
            "idempotency_key": idempotency_key,
            "metadata": metadata,
        }
    )


class Deliverability(SyncAPIResource):
    """Synchronous ``deliverability`` resource."""

    def ingest_event(
        self,
        *,
        event_type: str,
        recipient_email: str,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        task_id: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        provider: NotGivenOr[str] = NOT_GIVEN,
        reason: NotGivenOr[str] = NOT_GIVEN,
        idempotency_key: NotGivenOr[str] = NOT_GIVEN,
        metadata: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> DeliverabilityEventAccepted:
        """Record a bounce, complaint, or unsubscribe.

        Depending on the organization's outreach settings this can suppress
        the recipient and pause the campaign, so treat it as a write.

        Args:
            event_type: The kind of event (bounce, complaint, unsubscribe).
            recipient_email: The address the event is about.
            campaign_id: The campaign the send belonged to.
            task_id: The send task the event is about.
            contact_id: The contact the address maps to.
            provider: Where the signal came from.
            reason: The provider's stated reason.
            idempotency_key: A stable key so a replayed event is deduped
                server-side.
            metadata: Any extra provider fields worth keeping.
        """
        return self._post(
            "/deliverability/events",
            cast_to=DeliverabilityEventAccepted,
            body=_event_body(
                event_type=event_type,
                recipient_email=recipient_email,
                campaign_id=campaign_id,
                task_id=task_id,
                contact_id=contact_id,
                provider=provider,
                reason=reason,
                idempotency_key=idempotency_key,
                metadata=metadata,
            ),
            options=options,
        )


class AsyncDeliverability(AsyncAPIResource):
    """Asynchronous ``deliverability`` resource."""

    async def ingest_event(
        self,
        *,
        event_type: str,
        recipient_email: str,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        task_id: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        provider: NotGivenOr[str] = NOT_GIVEN,
        reason: NotGivenOr[str] = NOT_GIVEN,
        idempotency_key: NotGivenOr[str] = NOT_GIVEN,
        metadata: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> DeliverabilityEventAccepted:
        """Record a bounce, complaint, or unsubscribe.

        Depending on the organization's outreach settings this can suppress
        the recipient and pause the campaign, so treat it as a write.

        Args:
            event_type: The kind of event (bounce, complaint, unsubscribe).
            recipient_email: The address the event is about.
            campaign_id: The campaign the send belonged to.
            task_id: The send task the event is about.
            contact_id: The contact the address maps to.
            provider: Where the signal came from.
            reason: The provider's stated reason.
            idempotency_key: A stable key so a replayed event is deduped
                server-side.
            metadata: Any extra provider fields worth keeping.
        """
        return await self._post(
            "/deliverability/events",
            cast_to=DeliverabilityEventAccepted,
            body=_event_body(
                event_type=event_type,
                recipient_email=recipient_email,
                campaign_id=campaign_id,
                task_id=task_id,
                contact_id=contact_id,
                provider=provider,
                reason=reason,
                idempotency_key=idempotency_key,
                metadata=metadata,
            ),
            options=options,
        )
