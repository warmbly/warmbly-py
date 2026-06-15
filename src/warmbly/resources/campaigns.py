"""The ``campaigns`` resource — create, configure, and run email campaigns.

Maps to the ``/v1/campaigns`` route group. Covers campaign CRUD, advanced
settings, A/B variants and analysis, attachments, sequence steps, senders,
the tracking-domain verification flow, and the run lifecycle (preflight,
test-email, start, stop, logs).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .._models import BaseModel
from .._pagination import AsyncCursorPage, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncCampaigns",
    "Campaign",
    "CampaignABAnalysis",
    "CampaignABVariant",
    "CampaignAdvanced",
    "CampaignAttachment",
    "CampaignDeleted",
    "CampaignLog",
    "CampaignPreflight",
    "CampaignSenders",
    "CampaignStep",
    "CampaignTestEmail",
    "CampaignTrackingDomainVerification",
    "Campaigns",
]


class Campaign(BaseModel):
    """An email campaign."""

    id: str
    user_id: str | None = None
    organization_id: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None
    stop_on_reply: bool | None = None
    open_tracking: bool | None = None
    link_tracking: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CampaignDeleted(BaseModel):
    """The result of deleting a campaign."""

    id: str | None = None
    status: str | None = None


class CampaignAdvanced(BaseModel):
    """Advanced configuration for a campaign.

    The backend exposes a flexible bag of tuning knobs; unknown fields are
    tolerated, with the commonly used ones surfaced as typed attributes.
    """

    campaign_id: str | None = None
    daily_limit: int | None = None
    sending_window: dict[str, Any] | None = None
    timezone: str | None = None
    tracking_domain: str | None = None
    settings: dict[str, Any] | None = None


class CampaignStep(BaseModel):
    """A single step in a campaign's sending sequence."""

    id: str
    campaign_id: str | None = None
    order: int | None = None
    type: str | None = None
    subject: str | None = None
    body: str | None = None
    wait_days: int | None = None
    variants: Sequence[dict[str, Any]] = []
    created_at: str | None = None
    updated_at: str | None = None


class CampaignABVariant(BaseModel):
    """An A/B test variant attached to a campaign."""

    id: str
    campaign_id: str | None = None
    name: str | None = None
    subject: str | None = None
    body: str | None = None
    weight: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CampaignABAnalysis(BaseModel):
    """Aggregated performance analysis across a campaign's A/B variants."""

    campaign_id: str | None = None
    variants: Sequence[dict[str, Any]] = []
    winner: str | None = None
    confidence: float | None = None


class CampaignAttachment(BaseModel):
    """A file attached to a campaign."""

    id: str
    campaign_id: str | None = None
    filename: str | None = None
    content_type: str | None = None
    size: int | None = None
    url: str | None = None
    created_at: str | None = None


class CampaignPreflight(BaseModel):
    """The result of a preflight readiness check before launching."""

    campaign_id: str | None = None
    ready: bool | None = None
    checks: Sequence[dict[str, Any]] = []
    warnings: Sequence[dict[str, Any]] = []
    errors: Sequence[dict[str, Any]] = []


class CampaignTestEmail(BaseModel):
    """The result of sending a test email for a campaign."""

    campaign_id: str | None = None
    status: str | None = None
    sent_to: Sequence[str] = []
    message: str | None = None


class CampaignLog(BaseModel):
    """A single activity-log entry for a campaign."""

    id: str
    campaign_id: str | None = None
    level: str | None = None
    event: str | None = None
    message: str | None = None
    data: dict[str, Any] | None = None
    created_at: str | None = None


class CampaignSenders(BaseModel):
    """The set of email accounts (senders) assigned to a campaign."""

    campaign_id: str | None = None
    senders: Sequence[dict[str, Any]] = []


class CampaignTrackingDomainVerification(BaseModel):
    """The result of verifying a campaign's tracking domain."""

    campaign_id: str | None = None
    tracking_domain: str | None = None
    verified: bool | None = None
    records: Sequence[dict[str, Any]] = []
    message: str | None = None


class Campaigns(SyncAPIResource):
    """Synchronous ``campaigns`` resource."""

    def create(
        self,
        *,
        name: str,
        description: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        stop_on_reply: NotGivenOr[bool] = NOT_GIVEN,
        open_tracking: NotGivenOr[bool] = NOT_GIVEN,
        link_tracking: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Campaign:
        """Create a campaign.

        Args:
            name: A human-readable name for the campaign.
            description: An optional longer description.
            status: Optional initial status.
            stop_on_reply: Whether to stop sequencing a contact once they reply.
            open_tracking: Whether to enable open tracking.
            link_tracking: Whether to enable link/click tracking.
            options: Per-request overrides.
        """
        body = drop_not_given(
            {
                "name": name,
                "description": description,
                "status": status,
                "stop_on_reply": stop_on_reply,
                "open_tracking": open_tracking,
                "link_tracking": link_tracking,
            }
        )
        return self._post("/campaigns", cast_to=Campaign, body=body, options=options)

    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[Campaign]:
        """List campaigns (auto-paginating)."""
        return self._get_api_list(
            "/campaigns",
            model=Campaign,
            query={"limit": limit, "cursor": cursor, "status": status},
            options=options,
        )

    def retrieve(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> Campaign:
        """Retrieve a single campaign by id."""
        return self._get(f"/campaigns/{campaign_id}", cast_to=Campaign, options=options)

    def update(
        self,
        campaign_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        stop_on_reply: NotGivenOr[bool] = NOT_GIVEN,
        open_tracking: NotGivenOr[bool] = NOT_GIVEN,
        link_tracking: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Campaign:
        """Update a campaign's metadata or tracking settings."""
        body = drop_not_given(
            {
                "name": name,
                "description": description,
                "status": status,
                "stop_on_reply": stop_on_reply,
                "open_tracking": open_tracking,
                "link_tracking": link_tracking,
            }
        )
        return self._patch(
            f"/campaigns/{campaign_id}", cast_to=Campaign, body=body, options=options
        )

    def delete(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignDeleted:
        """Delete a campaign."""
        return self._delete(
            f"/campaigns/{campaign_id}", cast_to=CampaignDeleted, options=options
        )

    def retrieve_advanced(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignAdvanced:
        """Retrieve a campaign's advanced configuration."""
        return self._get(
            f"/campaigns/{campaign_id}/advanced",
            cast_to=CampaignAdvanced,
            options=options,
        )

    def update_advanced(
        self,
        campaign_id: str,
        *,
        daily_limit: NotGivenOr[int] = NOT_GIVEN,
        sending_window: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
        timezone: NotGivenOr[str] = NOT_GIVEN,
        tracking_domain: NotGivenOr[str] = NOT_GIVEN,
        settings: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignAdvanced:
        """Update a campaign's advanced configuration."""
        body = drop_not_given(
            {
                "daily_limit": daily_limit,
                "sending_window": sending_window,
                "timezone": timezone,
                "tracking_domain": tracking_domain,
                "settings": settings,
            }
        )
        return self._patch(
            f"/campaigns/{campaign_id}/advanced",
            cast_to=CampaignAdvanced,
            body=body,
            options=options,
        )

    def list_ab_variants(
        self,
        campaign_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[CampaignABVariant]:
        """List a campaign's A/B variants (auto-paginating)."""
        return self._get_api_list(
            f"/campaigns/{campaign_id}/ab-variants",
            model=CampaignABVariant,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def create_ab_variant(
        self,
        campaign_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body: NotGivenOr[str] = NOT_GIVEN,
        weight: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignABVariant:
        """Create an A/B variant on a campaign."""
        json_body = drop_not_given(
            {
                "name": name,
                "subject": subject,
                "body": body,
                "weight": weight,
            }
        )
        return self._post(
            f"/campaigns/{campaign_id}/ab-variants",
            cast_to=CampaignABVariant,
            body=json_body,
            options=options,
        )

    def update_ab_variant(
        self,
        campaign_id: str,
        variant_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body: NotGivenOr[str] = NOT_GIVEN,
        weight: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignABVariant:
        """Update an A/B variant."""
        json_body = drop_not_given(
            {
                "name": name,
                "subject": subject,
                "body": body,
                "weight": weight,
            }
        )
        return self._patch(
            f"/campaigns/{campaign_id}/ab-variants/{variant_id}",
            cast_to=CampaignABVariant,
            body=json_body,
            options=options,
        )

    def delete_ab_variant(
        self,
        campaign_id: str,
        variant_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> CampaignDeleted:
        """Delete an A/B variant."""
        return self._delete(
            f"/campaigns/{campaign_id}/ab-variants/{variant_id}",
            cast_to=CampaignDeleted,
            options=options,
        )

    def ab_analysis(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignABAnalysis:
        """Retrieve aggregated A/B test analysis for a campaign."""
        return self._get(
            f"/campaigns/{campaign_id}/ab-analysis",
            cast_to=CampaignABAnalysis,
            options=options,
        )

    def list_attachments(
        self,
        campaign_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[CampaignAttachment]:
        """List a campaign's attachments (auto-paginating)."""
        return self._get_api_list(
            f"/campaigns/{campaign_id}/attachments",
            model=CampaignAttachment,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def create_attachment(
        self,
        campaign_id: str,
        *,
        filename: NotGivenOr[str] = NOT_GIVEN,
        content_type: NotGivenOr[str] = NOT_GIVEN,
        url: NotGivenOr[str] = NOT_GIVEN,
        content: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignAttachment:
        """Attach a file to a campaign.

        Args:
            campaign_id: The campaign to attach to.
            filename: The attachment's filename.
            content_type: The attachment's MIME type.
            url: An optional URL to fetch the attachment from.
            content: Optional base64-encoded inline content.
            options: Per-request overrides.
        """
        body = drop_not_given(
            {
                "filename": filename,
                "content_type": content_type,
                "url": url,
                "content": content,
            }
        )
        return self._post(
            f"/campaigns/{campaign_id}/attachments",
            cast_to=CampaignAttachment,
            body=body,
            options=options,
        )

    def delete_attachment(
        self,
        campaign_id: str,
        attachment_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> CampaignDeleted:
        """Remove an attachment from a campaign."""
        return self._delete(
            f"/campaigns/{campaign_id}/attachments/{attachment_id}",
            cast_to=CampaignDeleted,
            options=options,
        )

    def preflight(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignPreflight:
        """Run a preflight readiness check before launching a campaign."""
        return self._post(
            f"/campaigns/{campaign_id}/preflight",
            cast_to=CampaignPreflight,
            options=options,
        )

    def test_email(
        self,
        campaign_id: str,
        *,
        to: NotGivenOr[str | Sequence[str]] = NOT_GIVEN,
        step_id: NotGivenOr[str] = NOT_GIVEN,
        variant_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignTestEmail:
        """Send a test email for a campaign.

        Args:
            campaign_id: The campaign to test.
            to: A recipient address or list of addresses.
            step_id: Optional sequence step to render.
            variant_id: Optional A/B variant to render.
            options: Per-request overrides.
        """
        body = drop_not_given(
            {
                "to": to,
                "step_id": step_id,
                "variant_id": variant_id,
            }
        )
        return self._post(
            f"/campaigns/{campaign_id}/test-email",
            cast_to=CampaignTestEmail,
            body=body,
            options=options,
        )

    def start(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> Campaign:
        """Start (launch) a campaign."""
        return self._post(
            f"/campaigns/{campaign_id}/start", cast_to=Campaign, options=options
        )

    def stop(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> Campaign:
        """Stop (pause) a campaign."""
        return self._post(
            f"/campaigns/{campaign_id}/stop", cast_to=Campaign, options=options
        )

    def logs(
        self,
        campaign_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[CampaignLog]:
        """List a campaign's activity logs (auto-paginating)."""
        return self._get_api_list(
            f"/campaigns/{campaign_id}/logs",
            model=CampaignLog,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def retrieve_senders(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignSenders:
        """Retrieve the senders (email accounts) assigned to a campaign."""
        return self._get(
            f"/campaigns/{campaign_id}/senders",
            cast_to=CampaignSenders,
            options=options,
        )

    def set_senders(
        self,
        campaign_id: str,
        *,
        sender_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        senders: NotGivenOr[Sequence[dict[str, Any]]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignSenders:
        """Replace the set of senders assigned to a campaign.

        Args:
            campaign_id: The campaign to update.
            sender_ids: A list of email-account ids to assign.
            senders: An optional list of richer sender objects.
            options: Per-request overrides.
        """
        body = drop_not_given(
            {
                "sender_ids": sender_ids,
                "senders": senders,
            }
        )
        return self._put(
            f"/campaigns/{campaign_id}/senders",
            cast_to=CampaignSenders,
            body=body,
            options=options,
        )

    def verify_tracking_domain(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignTrackingDomainVerification:
        """Verify a campaign's tracking domain DNS configuration."""
        return self._post(
            f"/campaigns/{campaign_id}/tracking-domain/verify",
            cast_to=CampaignTrackingDomainVerification,
            options=options,
        )

    def list_steps(
        self,
        campaign_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[CampaignStep]:
        """List a campaign's sequence steps (auto-paginating)."""
        return self._get_api_list(
            f"/campaigns/{campaign_id}/steps",
            model=CampaignStep,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def create_step(
        self,
        campaign_id: str,
        *,
        type: NotGivenOr[str] = NOT_GIVEN,
        order: NotGivenOr[int] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body: NotGivenOr[str] = NOT_GIVEN,
        wait_days: NotGivenOr[int] = NOT_GIVEN,
        variants: NotGivenOr[Sequence[dict[str, Any]]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignStep:
        """Add a step to a campaign's sending sequence."""
        json_body = drop_not_given(
            {
                "type": type,
                "order": order,
                "subject": subject,
                "body": body,
                "wait_days": wait_days,
                "variants": variants,
            }
        )
        return self._post(
            f"/campaigns/{campaign_id}/steps",
            cast_to=CampaignStep,
            body=json_body,
            options=options,
        )

    def update_step(
        self,
        campaign_id: str,
        step_id: str,
        *,
        type: NotGivenOr[str] = NOT_GIVEN,
        order: NotGivenOr[int] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body: NotGivenOr[str] = NOT_GIVEN,
        wait_days: NotGivenOr[int] = NOT_GIVEN,
        variants: NotGivenOr[Sequence[dict[str, Any]]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignStep:
        """Update a sequence step."""
        json_body = drop_not_given(
            {
                "type": type,
                "order": order,
                "subject": subject,
                "body": body,
                "wait_days": wait_days,
                "variants": variants,
            }
        )
        return self._patch(
            f"/campaigns/{campaign_id}/steps/{step_id}",
            cast_to=CampaignStep,
            body=json_body,
            options=options,
        )

    def delete_step(
        self,
        campaign_id: str,
        step_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> CampaignDeleted:
        """Delete a sequence step."""
        return self._delete(
            f"/campaigns/{campaign_id}/steps/{step_id}",
            cast_to=CampaignDeleted,
            options=options,
        )


class AsyncCampaigns(AsyncAPIResource):
    """Asynchronous ``campaigns`` resource."""

    async def create(
        self,
        *,
        name: str,
        description: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        stop_on_reply: NotGivenOr[bool] = NOT_GIVEN,
        open_tracking: NotGivenOr[bool] = NOT_GIVEN,
        link_tracking: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Campaign:
        """Create a campaign.

        Args:
            name: A human-readable name for the campaign.
            description: An optional longer description.
            status: Optional initial status.
            stop_on_reply: Whether to stop sequencing a contact once they reply.
            open_tracking: Whether to enable open tracking.
            link_tracking: Whether to enable link/click tracking.
            options: Per-request overrides.
        """
        body = drop_not_given(
            {
                "name": name,
                "description": description,
                "status": status,
                "stop_on_reply": stop_on_reply,
                "open_tracking": open_tracking,
                "link_tracking": link_tracking,
            }
        )
        return await self._post(
            "/campaigns", cast_to=Campaign, body=body, options=options
        )

    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncCursorPage[Campaign]:
        """List campaigns (auto-paginating)."""
        return self._get_api_list(
            "/campaigns",
            model=Campaign,
            query={"limit": limit, "cursor": cursor, "status": status},
            options=options,
        )

    async def retrieve(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> Campaign:
        """Retrieve a single campaign by id."""
        return await self._get(
            f"/campaigns/{campaign_id}", cast_to=Campaign, options=options
        )

    async def update(
        self,
        campaign_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        stop_on_reply: NotGivenOr[bool] = NOT_GIVEN,
        open_tracking: NotGivenOr[bool] = NOT_GIVEN,
        link_tracking: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Campaign:
        """Update a campaign's metadata or tracking settings."""
        body = drop_not_given(
            {
                "name": name,
                "description": description,
                "status": status,
                "stop_on_reply": stop_on_reply,
                "open_tracking": open_tracking,
                "link_tracking": link_tracking,
            }
        )
        return await self._patch(
            f"/campaigns/{campaign_id}", cast_to=Campaign, body=body, options=options
        )

    async def delete(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignDeleted:
        """Delete a campaign."""
        return await self._delete(
            f"/campaigns/{campaign_id}", cast_to=CampaignDeleted, options=options
        )

    async def retrieve_advanced(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignAdvanced:
        """Retrieve a campaign's advanced configuration."""
        return await self._get(
            f"/campaigns/{campaign_id}/advanced",
            cast_to=CampaignAdvanced,
            options=options,
        )

    async def update_advanced(
        self,
        campaign_id: str,
        *,
        daily_limit: NotGivenOr[int] = NOT_GIVEN,
        sending_window: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
        timezone: NotGivenOr[str] = NOT_GIVEN,
        tracking_domain: NotGivenOr[str] = NOT_GIVEN,
        settings: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignAdvanced:
        """Update a campaign's advanced configuration."""
        body = drop_not_given(
            {
                "daily_limit": daily_limit,
                "sending_window": sending_window,
                "timezone": timezone,
                "tracking_domain": tracking_domain,
                "settings": settings,
            }
        )
        return await self._patch(
            f"/campaigns/{campaign_id}/advanced",
            cast_to=CampaignAdvanced,
            body=body,
            options=options,
        )

    def list_ab_variants(
        self,
        campaign_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncCursorPage[CampaignABVariant]:
        """List a campaign's A/B variants (auto-paginating)."""
        return self._get_api_list(
            f"/campaigns/{campaign_id}/ab-variants",
            model=CampaignABVariant,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def create_ab_variant(
        self,
        campaign_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body: NotGivenOr[str] = NOT_GIVEN,
        weight: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignABVariant:
        """Create an A/B variant on a campaign."""
        json_body = drop_not_given(
            {
                "name": name,
                "subject": subject,
                "body": body,
                "weight": weight,
            }
        )
        return await self._post(
            f"/campaigns/{campaign_id}/ab-variants",
            cast_to=CampaignABVariant,
            body=json_body,
            options=options,
        )

    async def update_ab_variant(
        self,
        campaign_id: str,
        variant_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body: NotGivenOr[str] = NOT_GIVEN,
        weight: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignABVariant:
        """Update an A/B variant."""
        json_body = drop_not_given(
            {
                "name": name,
                "subject": subject,
                "body": body,
                "weight": weight,
            }
        )
        return await self._patch(
            f"/campaigns/{campaign_id}/ab-variants/{variant_id}",
            cast_to=CampaignABVariant,
            body=json_body,
            options=options,
        )

    async def delete_ab_variant(
        self,
        campaign_id: str,
        variant_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> CampaignDeleted:
        """Delete an A/B variant."""
        return await self._delete(
            f"/campaigns/{campaign_id}/ab-variants/{variant_id}",
            cast_to=CampaignDeleted,
            options=options,
        )

    async def ab_analysis(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignABAnalysis:
        """Retrieve aggregated A/B test analysis for a campaign."""
        return await self._get(
            f"/campaigns/{campaign_id}/ab-analysis",
            cast_to=CampaignABAnalysis,
            options=options,
        )

    def list_attachments(
        self,
        campaign_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncCursorPage[CampaignAttachment]:
        """List a campaign's attachments (auto-paginating)."""
        return self._get_api_list(
            f"/campaigns/{campaign_id}/attachments",
            model=CampaignAttachment,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def create_attachment(
        self,
        campaign_id: str,
        *,
        filename: NotGivenOr[str] = NOT_GIVEN,
        content_type: NotGivenOr[str] = NOT_GIVEN,
        url: NotGivenOr[str] = NOT_GIVEN,
        content: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignAttachment:
        """Attach a file to a campaign.

        Args:
            campaign_id: The campaign to attach to.
            filename: The attachment's filename.
            content_type: The attachment's MIME type.
            url: An optional URL to fetch the attachment from.
            content: Optional base64-encoded inline content.
            options: Per-request overrides.
        """
        body = drop_not_given(
            {
                "filename": filename,
                "content_type": content_type,
                "url": url,
                "content": content,
            }
        )
        return await self._post(
            f"/campaigns/{campaign_id}/attachments",
            cast_to=CampaignAttachment,
            body=body,
            options=options,
        )

    async def delete_attachment(
        self,
        campaign_id: str,
        attachment_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> CampaignDeleted:
        """Remove an attachment from a campaign."""
        return await self._delete(
            f"/campaigns/{campaign_id}/attachments/{attachment_id}",
            cast_to=CampaignDeleted,
            options=options,
        )

    async def preflight(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignPreflight:
        """Run a preflight readiness check before launching a campaign."""
        return await self._post(
            f"/campaigns/{campaign_id}/preflight",
            cast_to=CampaignPreflight,
            options=options,
        )

    async def test_email(
        self,
        campaign_id: str,
        *,
        to: NotGivenOr[str | Sequence[str]] = NOT_GIVEN,
        step_id: NotGivenOr[str] = NOT_GIVEN,
        variant_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignTestEmail:
        """Send a test email for a campaign.

        Args:
            campaign_id: The campaign to test.
            to: A recipient address or list of addresses.
            step_id: Optional sequence step to render.
            variant_id: Optional A/B variant to render.
            options: Per-request overrides.
        """
        body = drop_not_given(
            {
                "to": to,
                "step_id": step_id,
                "variant_id": variant_id,
            }
        )
        return await self._post(
            f"/campaigns/{campaign_id}/test-email",
            cast_to=CampaignTestEmail,
            body=body,
            options=options,
        )

    async def start(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> Campaign:
        """Start (launch) a campaign."""
        return await self._post(
            f"/campaigns/{campaign_id}/start", cast_to=Campaign, options=options
        )

    async def stop(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> Campaign:
        """Stop (pause) a campaign."""
        return await self._post(
            f"/campaigns/{campaign_id}/stop", cast_to=Campaign, options=options
        )

    def logs(
        self,
        campaign_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncCursorPage[CampaignLog]:
        """List a campaign's activity logs (auto-paginating)."""
        return self._get_api_list(
            f"/campaigns/{campaign_id}/logs",
            model=CampaignLog,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def retrieve_senders(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignSenders:
        """Retrieve the senders (email accounts) assigned to a campaign."""
        return await self._get(
            f"/campaigns/{campaign_id}/senders",
            cast_to=CampaignSenders,
            options=options,
        )

    async def set_senders(
        self,
        campaign_id: str,
        *,
        sender_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        senders: NotGivenOr[Sequence[dict[str, Any]]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignSenders:
        """Replace the set of senders assigned to a campaign.

        Args:
            campaign_id: The campaign to update.
            sender_ids: A list of email-account ids to assign.
            senders: An optional list of richer sender objects.
            options: Per-request overrides.
        """
        body = drop_not_given(
            {
                "sender_ids": sender_ids,
                "senders": senders,
            }
        )
        return await self._put(
            f"/campaigns/{campaign_id}/senders",
            cast_to=CampaignSenders,
            body=body,
            options=options,
        )

    async def verify_tracking_domain(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignTrackingDomainVerification:
        """Verify a campaign's tracking domain DNS configuration."""
        return await self._post(
            f"/campaigns/{campaign_id}/tracking-domain/verify",
            cast_to=CampaignTrackingDomainVerification,
            options=options,
        )

    def list_steps(
        self,
        campaign_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncCursorPage[CampaignStep]:
        """List a campaign's sequence steps (auto-paginating)."""
        return self._get_api_list(
            f"/campaigns/{campaign_id}/steps",
            model=CampaignStep,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def create_step(
        self,
        campaign_id: str,
        *,
        type: NotGivenOr[str] = NOT_GIVEN,
        order: NotGivenOr[int] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body: NotGivenOr[str] = NOT_GIVEN,
        wait_days: NotGivenOr[int] = NOT_GIVEN,
        variants: NotGivenOr[Sequence[dict[str, Any]]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignStep:
        """Add a step to a campaign's sending sequence."""
        json_body = drop_not_given(
            {
                "type": type,
                "order": order,
                "subject": subject,
                "body": body,
                "wait_days": wait_days,
                "variants": variants,
            }
        )
        return await self._post(
            f"/campaigns/{campaign_id}/steps",
            cast_to=CampaignStep,
            body=json_body,
            options=options,
        )

    async def update_step(
        self,
        campaign_id: str,
        step_id: str,
        *,
        type: NotGivenOr[str] = NOT_GIVEN,
        order: NotGivenOr[int] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body: NotGivenOr[str] = NOT_GIVEN,
        wait_days: NotGivenOr[int] = NOT_GIVEN,
        variants: NotGivenOr[Sequence[dict[str, Any]]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignStep:
        """Update a sequence step."""
        json_body = drop_not_given(
            {
                "type": type,
                "order": order,
                "subject": subject,
                "body": body,
                "wait_days": wait_days,
                "variants": variants,
            }
        )
        return await self._patch(
            f"/campaigns/{campaign_id}/steps/{step_id}",
            cast_to=CampaignStep,
            body=json_body,
            options=options,
        )

    async def delete_step(
        self,
        campaign_id: str,
        step_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> CampaignDeleted:
        """Delete a sequence step."""
        return await self._delete(
            f"/campaigns/{campaign_id}/steps/{step_id}",
            cast_to=CampaignDeleted,
            options=options,
        )
