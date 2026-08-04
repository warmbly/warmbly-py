"""The ``campaigns`` resource: create, configure, and run outreach campaigns.

Maps to the ``/v1/campaigns`` route group, plus the two sibling routes
``/v1/campaigns-overview`` and ``/v1/campaign-template-preview``. Covers the
campaign record itself, its sequence steps, A/B variants and analysis,
attachments, sender pool, advanced deliverability settings, tracking-domain
verification, and the run lifecycle (preflight, test-email, start, stop, logs).

A campaign's schedule can be expressed either as the coarse
``days``/``start_time``/``end_time`` triple or as authoritative per-day
``schedule_windows``; when both are sent, ``schedule_windows`` wins.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncCampaigns",
    "Campaign",
    "CampaignABAnalysis",
    "CampaignABVariant",
    "CampaignABVariantDeleted",
    "CampaignAdvanced",
    "CampaignAttachment",
    "CampaignAttachmentDeleted",
    "CampaignDeleted",
    "CampaignLog",
    "CampaignPreflight",
    "CampaignRunState",
    "CampaignSender",
    "CampaignSenders",
    "CampaignStep",
    "CampaignStepDeleted",
    "CampaignTemplatePreview",
    "CampaignTestEmail",
    "CampaignTrackingDomainStatus",
    "Campaigns",
    "CampaignsOverview",
    "LayoutSaved",
]


class Campaign(BaseModel):
    """An email campaign.

    ``days`` is a weekday bitmask; ``schedule_windows`` supersedes it when
    present. ``senders`` is loaded on demand, not on the list endpoint.
    """

    id: str
    user_id: str | None = None
    organization_id: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None
    stop_on_reply: bool | None = None
    open_tracking: bool | None = None
    link_tracking: bool | None = None
    text_only: bool | None = None
    daily_limit: int | None = None
    unsubscribe_header: bool | None = None
    risky_emails: bool | None = None
    cc: Sequence[str] = []
    bcc: Sequence[str] = []
    start_date: str | None = None
    end_date: str | None = None
    timezone: str | None = None
    days: int | None = None
    start_time: str | None = None
    end_time: str | None = None
    schedule_windows: dict[str, Any] | None = None
    email_tags: Sequence[str] = []
    folders: Sequence[str] = []
    contact_order_by: str | None = None
    contact_order_dir: str | None = None
    contact_order_field: str | None = None
    sender_strategy: str | None = None
    rotation_mode: str | None = None
    senders: Sequence[dict[str, Any]] = []
    ramp_enabled: bool | None = None
    ramp_start: int | None = None
    ramp_increment: int | None = None
    ramp_ceiling: int | None = None
    ramp_level: int | None = None
    ramp_level_date: str | None = None
    esp_match_mode: str | None = None
    max_new_leads_per_day: int | None = None
    prioritize_new_leads: bool | None = None
    tracking_domain: str | None = None
    tracking_domain_verified: bool | None = None
    tracking_domain_verified_at: str | None = None
    last_status_change_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CampaignDeleted(BaseModel):
    """The result of deleting a campaign (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class CampaignsOverview(BaseModel):
    """Status-bucket counts and per-folder totals for the campaigns browser."""

    total: int | None = None
    active: int | None = None
    paused: int | None = None
    draft: int | None = None
    completed: int | None = None
    folders: Sequence[dict[str, Any]] = []


class CampaignRunState(BaseModel):
    """The result of starting or stopping a campaign."""

    status: str | None = None


class CampaignAdvanced(BaseModel):
    """A campaign's per-campaign overrides of the org's outreach settings.

    ``overrides`` mirrors the organization-level settings tree exposed by
    ``client.outreach.settings()``; anything absent falls back to the org
    default.
    """

    campaign_id: str | None = None
    overrides: dict[str, Any] | None = None
    updated_at: str | None = None


class CampaignStep(BaseModel):
    """A single step in a campaign's sending sequence.

    ``kind`` distinguishes an email step from a non-email action step, whose
    behaviour lives in ``action``. ``wait_after`` is the delay, in days, before
    the *next* step fires.
    """

    id: str
    name: str | None = None
    subject: str | None = None
    body_plain: str | None = None
    body_html: str | None = None
    body_sync: bool | None = None
    body_code: bool | None = None
    wait_after: int | None = None
    position: int | None = None
    x: float | None = None
    y: float | None = None
    kind: str | None = None
    action: dict[str, Any] | None = None
    conditions: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CampaignStepDeleted(BaseModel):
    """The result of deleting a sequence step."""

    id: str | None = None
    deleted: bool | None = None


class LayoutSaved(BaseModel):
    """The acknowledgement of a cosmetic node-position save."""

    ok: bool | None = None


class CampaignABVariant(BaseModel):
    """An A/B test variant attached to a campaign step."""

    id: str
    campaign_id: str | None = None
    step_id: str | None = None
    name: str | None = None
    weight: int | None = None
    subject: str | None = None
    body_html: str | None = None
    body_plain: str | None = None
    is_control: bool | None = None
    is_active: bool | None = None
    metadata: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CampaignABVariantDeleted(BaseModel):
    """The result of deleting an A/B variant (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class CampaignABAnalysis(BaseModel):
    """Aggregated performance across a campaign's A/B variants (permissive)."""

    campaign_id: str | None = None
    variants: Sequence[dict[str, Any]] = []
    winner: str | None = None
    confidence: float | None = None


class CampaignAttachment(BaseModel):
    """A file attached to a campaign, or to one of its steps.

    ``url`` is a presigned download link and expires; re-list to refresh it.
    """

    id: str
    campaign_id: str | None = None
    step_id: str | None = None
    filename: str | None = None
    mime_type: str | None = None
    size: int | None = None
    url: str | None = None
    created_at: str | None = None


class CampaignAttachmentDeleted(BaseModel):
    """The result of deleting an attachment (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class CampaignPreflight(BaseModel):
    """The readiness report produced before launching (permissive)."""

    campaign_id: str | None = None
    ready: bool | None = None
    checks: Sequence[dict[str, Any]] = []
    warnings: Sequence[dict[str, Any]] = []
    errors: Sequence[dict[str, Any]] = []


class CampaignTestEmail(BaseModel):
    """The result of sending a test email for a campaign step."""

    message: str | None = None
    recipient: str | None = None
    subject: str | None = None
    account_id: str | None = None


class CampaignLog(BaseModel):
    """A single activity-log entry for a campaign (permissive)."""

    id: str
    campaign_id: str | None = None
    level: str | None = None
    event: str | None = None
    message: str | None = None
    data: dict[str, Any] | None = None
    created_at: str | None = None


class CampaignSender(BaseModel):
    """One mailbox in a campaign's sender pool."""

    email_account_id: str | None = None
    weight: int | None = None
    enabled: bool | None = None
    last_sent_at: str | None = None


class CampaignSenders(BaseModel):
    """A campaign's full sender pool."""

    data: Sequence[CampaignSender] = []


class CampaignTrackingDomainStatus(BaseModel):
    """The tracking-domain configuration and verification state."""

    tracking_domain: str | None = None
    tracking_domain_verified: bool | None = None
    tracking_domain_verified_at: str | None = None


class CampaignTemplatePreview(BaseModel):
    """A template rendered exactly as the send path would render it.

    ``errors`` carries template parse failures and ``unresolved`` the merge
    tokens that had no value, so a composer can flag both inline.
    """

    subject: str | None = None
    body_html: str | None = None
    body_plain: str | None = None
    errors: Sequence[str] = []
    unresolved: Sequence[str] = []


def _campaign_body(
    *,
    name: NotGivenOr[str] = NOT_GIVEN,
    description: NotGivenOr[str] = NOT_GIVEN,
    status: NotGivenOr[str] = NOT_GIVEN,
    stop_on_reply: NotGivenOr[bool] = NOT_GIVEN,
    open_tracking: NotGivenOr[bool] = NOT_GIVEN,
    link_tracking: NotGivenOr[bool] = NOT_GIVEN,
    text_only: NotGivenOr[bool] = NOT_GIVEN,
    daily_limit: NotGivenOr[int] = NOT_GIVEN,
    unsubscribe_header: NotGivenOr[bool] = NOT_GIVEN,
    risky_emails: NotGivenOr[bool] = NOT_GIVEN,
    cc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
    bcc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
    start_date: NotGivenOr[str] = NOT_GIVEN,
    end_date: NotGivenOr[str] = NOT_GIVEN,
    timezone: NotGivenOr[str] = NOT_GIVEN,
    days: NotGivenOr[int] = NOT_GIVEN,
    start_time: NotGivenOr[str] = NOT_GIVEN,
    end_time: NotGivenOr[str] = NOT_GIVEN,
    schedule_windows: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
    email_tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
    folders: NotGivenOr[Sequence[str]] = NOT_GIVEN,
    contact_order_by: NotGivenOr[str] = NOT_GIVEN,
    contact_order_dir: NotGivenOr[str] = NOT_GIVEN,
    contact_order_field: NotGivenOr[str] = NOT_GIVEN,
    sender_strategy: NotGivenOr[str] = NOT_GIVEN,
    rotation_mode: NotGivenOr[str] = NOT_GIVEN,
    ramp_enabled: NotGivenOr[bool] = NOT_GIVEN,
    ramp_start: NotGivenOr[int] = NOT_GIVEN,
    ramp_increment: NotGivenOr[int] = NOT_GIVEN,
    ramp_ceiling: NotGivenOr[int] = NOT_GIVEN,
    esp_match_mode: NotGivenOr[str] = NOT_GIVEN,
    max_new_leads_per_day: NotGivenOr[int] = NOT_GIVEN,
    prioritize_new_leads: NotGivenOr[bool] = NOT_GIVEN,
    tracking_domain: NotGivenOr[str] = NOT_GIVEN,
) -> dict[str, Any]:
    """Build the create/update campaign body (they share one field set)."""
    return drop_not_given(
        {
            "name": name,
            "description": description,
            "status": status,
            "stop_on_reply": stop_on_reply,
            "open_tracking": open_tracking,
            "link_tracking": link_tracking,
            "text_only": text_only,
            "daily_limit": daily_limit,
            "unsubscribe_header": unsubscribe_header,
            "risky_emails": risky_emails,
            "cc": cc,
            "bcc": bcc,
            "start_date": start_date,
            "end_date": end_date,
            "timezone": timezone,
            "days": days,
            "start_time": start_time,
            "end_time": end_time,
            "schedule_windows": schedule_windows,
            "email_tags": email_tags,
            "folders": folders,
            "contact_order_by": contact_order_by,
            "contact_order_dir": contact_order_dir,
            "contact_order_field": contact_order_field,
            "sender_strategy": sender_strategy,
            "rotation_mode": rotation_mode,
            "ramp_enabled": ramp_enabled,
            "ramp_start": ramp_start,
            "ramp_increment": ramp_increment,
            "ramp_ceiling": ramp_ceiling,
            "esp_match_mode": esp_match_mode,
            "max_new_leads_per_day": max_new_leads_per_day,
            "prioritize_new_leads": prioritize_new_leads,
            "tracking_domain": tracking_domain,
        }
    )


def _step_body(
    *,
    name: NotGivenOr[str],
    subject: NotGivenOr[str],
    body_html: NotGivenOr[str],
    body_plain: NotGivenOr[str],
    body_sync: NotGivenOr[bool],
    body_code: NotGivenOr[bool],
    wait_after: NotGivenOr[int],
    kind: NotGivenOr[str],
    action: NotGivenOr[Mapping[str, Any]],
    conditions: NotGivenOr[Mapping[str, Any]],
) -> dict[str, Any]:
    return drop_not_given(
        {
            "name": name,
            "subject": subject,
            "body_html": body_html,
            "body_plain": body_plain,
            "body_sync": body_sync,
            "body_code": body_code,
            "wait_after": wait_after,
            "kind": kind,
            "action": action,
            "conditions": conditions,
        }
    )


def _variant_body(
    *,
    name: NotGivenOr[str],
    step_id: NotGivenOr[str],
    weight: NotGivenOr[int],
    subject: NotGivenOr[str],
    body_html: NotGivenOr[str],
    body_plain: NotGivenOr[str],
    is_control: NotGivenOr[bool],
    is_active: NotGivenOr[bool],
) -> dict[str, Any]:
    return drop_not_given(
        {
            "name": name,
            "step_id": step_id,
            "weight": weight,
            "subject": subject,
            "body_html": body_html,
            "body_plain": body_plain,
            "is_control": is_control,
            "is_active": is_active,
        }
    )


class Campaigns(SyncAPIResource):
    """Synchronous ``campaigns`` resource."""

    # -- campaign records ----------------------------------------------------
    def create(
        self,
        *,
        name: str,
        description: NotGivenOr[str] = NOT_GIVEN,
        stop_on_reply: NotGivenOr[bool] = NOT_GIVEN,
        open_tracking: NotGivenOr[bool] = NOT_GIVEN,
        link_tracking: NotGivenOr[bool] = NOT_GIVEN,
        text_only: NotGivenOr[bool] = NOT_GIVEN,
        daily_limit: NotGivenOr[int] = NOT_GIVEN,
        unsubscribe_header: NotGivenOr[bool] = NOT_GIVEN,
        risky_emails: NotGivenOr[bool] = NOT_GIVEN,
        cc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        bcc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        start_date: NotGivenOr[str] = NOT_GIVEN,
        end_date: NotGivenOr[str] = NOT_GIVEN,
        timezone: NotGivenOr[str] = NOT_GIVEN,
        days: NotGivenOr[int] = NOT_GIVEN,
        start_time: NotGivenOr[str] = NOT_GIVEN,
        end_time: NotGivenOr[str] = NOT_GIVEN,
        schedule_windows: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        email_tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        folders: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Campaign:
        """Create a campaign.

        Only *name* is required; every other field falls back to a sane
        default, so a minimal ``create(name=...)`` produces a usable draft.

        Args:
            name: A human-readable name for the campaign.
            description: An optional longer description.
            stop_on_reply: Stop sequencing a contact once they reply.
            open_tracking: Enable open tracking.
            link_tracking: Enable link/click tracking.
            text_only: Send plain text only.
            daily_limit: Max emails per day across the campaign.
            unsubscribe_header: Add a ``List-Unsubscribe`` header.
            risky_emails: Allow sending to addresses flagged as risky.
            cc: Addresses to CC on every send.
            bcc: Addresses to BCC on every send.
            start_date: RFC 3339 date the campaign may start sending.
            end_date: RFC 3339 date the campaign stops sending.
            timezone: IANA timezone the schedule is interpreted in.
            days: Weekday bitmask for the sending window.
            start_time: Daily window start (``"HH:MM"``).
            end_time: Daily window end (``"HH:MM"``).
            schedule_windows: Per-day windows; supersedes
                *days*/*start_time*/*end_time*.
            email_tags: Mailbox tags to draw senders from.
            folders: Folder ids to file the campaign under.
        """
        return self._post(
            "/campaigns",
            cast_to=Campaign,
            body=_campaign_body(
                name=name,
                description=description,
                stop_on_reply=stop_on_reply,
                open_tracking=open_tracking,
                link_tracking=link_tracking,
                text_only=text_only,
                daily_limit=daily_limit,
                unsubscribe_header=unsubscribe_header,
                risky_emails=risky_emails,
                cc=cc,
                bcc=bcc,
                start_date=start_date,
                end_date=end_date,
                timezone=timezone,
                days=days,
                start_time=start_time,
                end_time=end_time,
                schedule_windows=schedule_windows,
                email_tags=email_tags,
                folders=folders,
            ),
            options=options,
        )

    def list(
        self,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        folder: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[Campaign]:
        """List campaigns (auto-paginating).

        Args:
            q: Search string matched against the campaign name.
            status: Restrict to one status.
            folder: Restrict to one folder id.
        """
        return self._get_api_list(
            "/campaigns",
            model=Campaign,
            query={
                "q": q,
                "status": status,
                "folder": folder,
                "limit": limit,
                "cursor": cursor,
            },
            options=options,
        )

    def overview(self, *, options: RequestOptions | None = None) -> CampaignsOverview:
        """Return status-bucket counts and per-folder totals."""
        return self._get(
            "/campaigns-overview", cast_to=CampaignsOverview, options=options
        )

    def preview_template(
        self,
        *,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        contact: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignTemplatePreview:
        """Render subject/body exactly as the send path would. No side effects.

        Args:
            subject: The subject template.
            body_html: The HTML body template.
            body_plain: The plain-text body template.
            contact: Overrides for the sample contact the preview renders
                against (``first_name``, ``last_name``, ``email``, ``company``,
                ``phone``, ``custom_fields``).
        """
        return self._post(
            "/campaign-template-preview",
            cast_to=CampaignTemplatePreview,
            body=drop_not_given(
                {
                    "subject": subject,
                    "body_html": body_html,
                    "body_plain": body_plain,
                    "contact": contact,
                }
            ),
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
        text_only: NotGivenOr[bool] = NOT_GIVEN,
        daily_limit: NotGivenOr[int] = NOT_GIVEN,
        unsubscribe_header: NotGivenOr[bool] = NOT_GIVEN,
        risky_emails: NotGivenOr[bool] = NOT_GIVEN,
        cc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        bcc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        start_date: NotGivenOr[str] = NOT_GIVEN,
        end_date: NotGivenOr[str] = NOT_GIVEN,
        timezone: NotGivenOr[str] = NOT_GIVEN,
        days: NotGivenOr[int] = NOT_GIVEN,
        start_time: NotGivenOr[str] = NOT_GIVEN,
        end_time: NotGivenOr[str] = NOT_GIVEN,
        schedule_windows: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        email_tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        folders: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        contact_order_by: NotGivenOr[str] = NOT_GIVEN,
        contact_order_dir: NotGivenOr[str] = NOT_GIVEN,
        contact_order_field: NotGivenOr[str] = NOT_GIVEN,
        sender_strategy: NotGivenOr[str] = NOT_GIVEN,
        rotation_mode: NotGivenOr[str] = NOT_GIVEN,
        ramp_enabled: NotGivenOr[bool] = NOT_GIVEN,
        ramp_start: NotGivenOr[int] = NOT_GIVEN,
        ramp_increment: NotGivenOr[int] = NOT_GIVEN,
        ramp_ceiling: NotGivenOr[int] = NOT_GIVEN,
        esp_match_mode: NotGivenOr[str] = NOT_GIVEN,
        max_new_leads_per_day: NotGivenOr[int] = NOT_GIVEN,
        prioritize_new_leads: NotGivenOr[bool] = NOT_GIVEN,
        tracking_domain: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Campaign:
        """Update a campaign.

        The explicit sender *list* is edited with :meth:`set_senders`; only the
        strategy and rotation toggles ride this call.
        """
        return self._patch(
            f"/campaigns/{campaign_id}",
            cast_to=Campaign,
            body=_campaign_body(
                name=name,
                description=description,
                status=status,
                stop_on_reply=stop_on_reply,
                open_tracking=open_tracking,
                link_tracking=link_tracking,
                text_only=text_only,
                daily_limit=daily_limit,
                unsubscribe_header=unsubscribe_header,
                risky_emails=risky_emails,
                cc=cc,
                bcc=bcc,
                start_date=start_date,
                end_date=end_date,
                timezone=timezone,
                days=days,
                start_time=start_time,
                end_time=end_time,
                schedule_windows=schedule_windows,
                email_tags=email_tags,
                folders=folders,
                contact_order_by=contact_order_by,
                contact_order_dir=contact_order_dir,
                contact_order_field=contact_order_field,
                sender_strategy=sender_strategy,
                rotation_mode=rotation_mode,
                ramp_enabled=ramp_enabled,
                ramp_start=ramp_start,
                ramp_increment=ramp_increment,
                ramp_ceiling=ramp_ceiling,
                esp_match_mode=esp_match_mode,
                max_new_leads_per_day=max_new_leads_per_day,
                prioritize_new_leads=prioritize_new_leads,
                tracking_domain=tracking_domain,
            ),
            options=options,
        )

    def delete(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignDeleted:
        """Delete a campaign."""
        return self._delete(
            f"/campaigns/{campaign_id}", cast_to=CampaignDeleted, options=options
        )

    # -- advanced settings ---------------------------------------------------
    def retrieve_advanced(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignAdvanced:
        """Retrieve a campaign's overrides of the org's outreach settings."""
        return self._get(
            f"/campaigns/{campaign_id}/advanced",
            cast_to=CampaignAdvanced,
            options=options,
        )

    def update_advanced(
        self,
        campaign_id: str,
        *,
        settings: Mapping[str, Any],
        options: RequestOptions | None = None,
    ) -> None:
        """Replace a campaign's outreach-settings overrides.

        Args:
            campaign_id: The campaign to configure.
            settings: The overrides tree, shaped like the organization
                settings returned by ``client.outreach.settings()``.
        """
        return self._patch(
            f"/campaigns/{campaign_id}/advanced",
            cast_to=type(None),
            body={"settings": dict(settings)},
            options=options,
        )

    # -- sequence steps ------------------------------------------------------
    def list_steps(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[CampaignStep]:
        """List a campaign's sequence steps, in order."""
        return self._get_api_list(
            f"/campaigns/{campaign_id}/steps", model=CampaignStep, options=options
        )

    def create_step(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignStep:
        """Append a blank step to a campaign's sequence.

        Takes no body: the step is created empty and then filled in with
        :meth:`update_step`.
        """
        return self._post(
            f"/campaigns/{campaign_id}/steps", cast_to=CampaignStep, options=options
        )

    def update_step(
        self,
        campaign_id: str,
        step_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        body_sync: NotGivenOr[bool] = NOT_GIVEN,
        body_code: NotGivenOr[bool] = NOT_GIVEN,
        wait_after: NotGivenOr[int] = NOT_GIVEN,
        kind: NotGivenOr[str] = NOT_GIVEN,
        action: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        conditions: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignStep:
        """Update a sequence step.

        Args:
            wait_after: Days to wait before the next step fires.
            kind: The step kind; non-email kinds carry their behaviour in
                *action*.
            action: The action configuration for a non-email step.
            conditions: Branch conditions gating the step.
        """
        return self._patch(
            f"/campaigns/{campaign_id}/steps/{step_id}",
            cast_to=CampaignStep,
            body=_step_body(
                name=name,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                body_sync=body_sync,
                body_code=body_code,
                wait_after=wait_after,
                kind=kind,
                action=action,
                conditions=conditions,
            ),
            options=options,
        )

    def delete_step(
        self,
        campaign_id: str,
        step_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> CampaignStepDeleted:
        """Delete a sequence step."""
        return self._delete(
            f"/campaigns/{campaign_id}/steps/{step_id}",
            cast_to=CampaignStepDeleted,
            options=options,
        )

    def set_step_layout(
        self,
        campaign_id: str,
        *,
        positions: Sequence[Mapping[str, Any]],
        options: RequestOptions | None = None,
    ) -> LayoutSaved:
        """Persist the sequence builder's node positions.

        Cosmetic and unaudited.

        Args:
            positions: One ``{"id", "x", "y"}`` entry per step.
        """
        return self._patch(
            f"/campaigns/{campaign_id}/step-layout",
            cast_to=LayoutSaved,
            body={"positions": [dict(p) for p in positions]},
            options=options,
        )

    # -- A/B variants --------------------------------------------------------
    def list_ab_variants(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[CampaignABVariant]:
        """List a campaign's A/B variants."""
        return self._get_api_list(
            f"/campaigns/{campaign_id}/ab-variants",
            model=CampaignABVariant,
            options=options,
        )

    def create_ab_variant(
        self,
        campaign_id: str,
        *,
        name: str,
        step_id: NotGivenOr[str] = NOT_GIVEN,
        weight: NotGivenOr[int] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        is_control: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignABVariant:
        """Create an A/B variant.

        Args:
            name: A label for the variant.
            step_id: Scope the variant to one sequence step.
            weight: The variant's share of the split.
            is_control: Mark this variant as the control.
        """
        return self._post(
            f"/campaigns/{campaign_id}/ab-variants",
            cast_to=CampaignABVariant,
            body=_variant_body(
                name=name,
                step_id=step_id,
                weight=weight,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                is_control=is_control,
                is_active=NOT_GIVEN,
            ),
            options=options,
        )

    def update_ab_variant(
        self,
        campaign_id: str,
        variant_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        weight: NotGivenOr[int] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        is_control: NotGivenOr[bool] = NOT_GIVEN,
        is_active: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignABVariant:
        """Update an A/B variant."""
        return self._patch(
            f"/campaigns/{campaign_id}/ab-variants/{variant_id}",
            cast_to=CampaignABVariant,
            body=_variant_body(
                name=name,
                step_id=NOT_GIVEN,
                weight=weight,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                is_control=is_control,
                is_active=is_active,
            ),
            options=options,
        )

    def delete_ab_variant(
        self,
        campaign_id: str,
        variant_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> CampaignABVariantDeleted:
        """Delete an A/B variant."""
        return self._delete(
            f"/campaigns/{campaign_id}/ab-variants/{variant_id}",
            cast_to=CampaignABVariantDeleted,
            options=options,
        )

    def ab_analysis(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignABAnalysis:
        """Retrieve the A/B performance analysis for a campaign."""
        return self._get(
            f"/campaigns/{campaign_id}/ab-analysis",
            cast_to=CampaignABAnalysis,
            options=options,
        )

    # -- attachments ---------------------------------------------------------
    def list_attachments(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[CampaignAttachment]:
        """List a campaign's attachments, with fresh presigned URLs."""
        return self._get_api_list(
            f"/campaigns/{campaign_id}/attachments",
            model=CampaignAttachment,
            options=options,
        )

    def upload_attachment(
        self,
        campaign_id: str,
        *,
        file: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        step_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignAttachment:
        """Upload a file attachment (multipart, max 15 MB).

        Args:
            campaign_id: The campaign to attach to.
            file: The raw file bytes.
            filename: The filename recipients see.
            content_type: The file's MIME type.
            step_id: Scope the attachment to one sequence step instead of the
                whole campaign.
        """
        form = drop_not_given({"step_id": step_id})
        return self._client.request(
            cast_to=CampaignAttachment,
            method="POST",
            path=f"/campaigns/{campaign_id}/attachments",
            form=form or None,
            files={"file": (filename, file, content_type)},
            options=options,
        )

    def delete_attachment(
        self,
        campaign_id: str,
        attachment_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> CampaignAttachmentDeleted:
        """Delete an attachment."""
        return self._delete(
            f"/campaigns/{campaign_id}/attachments/{attachment_id}",
            cast_to=CampaignAttachmentDeleted,
            options=options,
        )

    # -- senders + tracking domain ------------------------------------------
    def senders(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignSenders:
        """Retrieve a campaign's explicit sender pool."""
        return self._get(
            f"/campaigns/{campaign_id}/senders",
            cast_to=CampaignSenders,
            options=options,
        )

    def set_senders(
        self,
        campaign_id: str,
        *,
        senders: Sequence[Mapping[str, Any]],
        options: RequestOptions | None = None,
    ) -> CampaignSenders:
        """Replace a campaign's sender pool wholesale.

        Args:
            senders: One ``{"email_account_id", "weight", "enabled"}`` entry
                per mailbox. This is the desired final set, so a ``PUT`` retry
                is safe.
        """
        return self._put(
            f"/campaigns/{campaign_id}/senders",
            cast_to=CampaignSenders,
            body={"senders": [dict(s) for s in senders]},
            options=options,
        )

    def verify_tracking_domain(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignTrackingDomainStatus:
        """Re-check the DNS for a campaign's custom tracking domain."""
        return self._post(
            f"/campaigns/{campaign_id}/tracking-domain/verify",
            cast_to=CampaignTrackingDomainStatus,
            options=options,
        )

    # -- run lifecycle -------------------------------------------------------
    def preflight(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignPreflight:
        """Run the pre-launch readiness checks without sending anything."""
        return self._post(
            f"/campaigns/{campaign_id}/preflight",
            cast_to=CampaignPreflight,
            options=options,
        )

    def send_test_email(
        self,
        campaign_id: str,
        *,
        account_id: str,
        recipient: str,
        step_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignTestEmail:
        """Send one real preview email for a campaign step.

        Args:
            campaign_id: The campaign to preview.
            account_id: The mailbox to send from.
            recipient: Where to send the preview.
            step_id: Which step to render; defaults to the first.
        """
        return self._post(
            f"/campaigns/{campaign_id}/test-email",
            cast_to=CampaignTestEmail,
            body=drop_not_given(
                {
                    "account_id": account_id,
                    "recipient": recipient,
                    "step_id": step_id,
                }
            ),
            options=options,
        )

    def start(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignRunState:
        """Start sending. This dispatches real mail."""
        return self._post(
            f"/campaigns/{campaign_id}/start",
            cast_to=CampaignRunState,
            options=options,
        )

    def stop(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignRunState:
        """Stop sending."""
        return self._post(
            f"/campaigns/{campaign_id}/stop",
            cast_to=CampaignRunState,
            options=options,
        )

    def logs(
        self,
        campaign_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[CampaignLog]:
        """List a campaign's activity log (auto-paginating).

        Args:
            limit: Page size (1-100; the server defaults to 50).
        """
        return self._get_api_list(
            f"/campaigns/{campaign_id}/logs",
            model=CampaignLog,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )


class AsyncCampaigns(AsyncAPIResource):
    """Asynchronous ``campaigns`` resource."""

    # -- campaign records ----------------------------------------------------
    async def create(
        self,
        *,
        name: str,
        description: NotGivenOr[str] = NOT_GIVEN,
        stop_on_reply: NotGivenOr[bool] = NOT_GIVEN,
        open_tracking: NotGivenOr[bool] = NOT_GIVEN,
        link_tracking: NotGivenOr[bool] = NOT_GIVEN,
        text_only: NotGivenOr[bool] = NOT_GIVEN,
        daily_limit: NotGivenOr[int] = NOT_GIVEN,
        unsubscribe_header: NotGivenOr[bool] = NOT_GIVEN,
        risky_emails: NotGivenOr[bool] = NOT_GIVEN,
        cc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        bcc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        start_date: NotGivenOr[str] = NOT_GIVEN,
        end_date: NotGivenOr[str] = NOT_GIVEN,
        timezone: NotGivenOr[str] = NOT_GIVEN,
        days: NotGivenOr[int] = NOT_GIVEN,
        start_time: NotGivenOr[str] = NOT_GIVEN,
        end_time: NotGivenOr[str] = NOT_GIVEN,
        schedule_windows: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        email_tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        folders: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Campaign:
        """Create a campaign.

        Only *name* is required; every other field falls back to a sane
        default, so a minimal ``create(name=...)`` produces a usable draft.

        Args:
            name: A human-readable name for the campaign.
            description: An optional longer description.
            stop_on_reply: Stop sequencing a contact once they reply.
            open_tracking: Enable open tracking.
            link_tracking: Enable link/click tracking.
            text_only: Send plain text only.
            daily_limit: Max emails per day across the campaign.
            unsubscribe_header: Add a ``List-Unsubscribe`` header.
            risky_emails: Allow sending to addresses flagged as risky.
            cc: Addresses to CC on every send.
            bcc: Addresses to BCC on every send.
            start_date: RFC 3339 date the campaign may start sending.
            end_date: RFC 3339 date the campaign stops sending.
            timezone: IANA timezone the schedule is interpreted in.
            days: Weekday bitmask for the sending window.
            start_time: Daily window start (``"HH:MM"``).
            end_time: Daily window end (``"HH:MM"``).
            schedule_windows: Per-day windows; supersedes
                *days*/*start_time*/*end_time*.
            email_tags: Mailbox tags to draw senders from.
            folders: Folder ids to file the campaign under.
        """
        return await self._post(
            "/campaigns",
            cast_to=Campaign,
            body=_campaign_body(
                name=name,
                description=description,
                stop_on_reply=stop_on_reply,
                open_tracking=open_tracking,
                link_tracking=link_tracking,
                text_only=text_only,
                daily_limit=daily_limit,
                unsubscribe_header=unsubscribe_header,
                risky_emails=risky_emails,
                cc=cc,
                bcc=bcc,
                start_date=start_date,
                end_date=end_date,
                timezone=timezone,
                days=days,
                start_time=start_time,
                end_time=end_time,
                schedule_windows=schedule_windows,
                email_tags=email_tags,
                folders=folders,
            ),
            options=options,
        )

    def list(
        self,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        folder: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[Campaign]:
        """List campaigns (auto-paginating).

        Args:
            q: Search string matched against the campaign name.
            status: Restrict to one status.
            folder: Restrict to one folder id.
        """
        return self._get_api_list(
            "/campaigns",
            model=Campaign,
            query={
                "q": q,
                "status": status,
                "folder": folder,
                "limit": limit,
                "cursor": cursor,
            },
            options=options,
        )

    async def overview(
        self, *, options: RequestOptions | None = None
    ) -> CampaignsOverview:
        """Return status-bucket counts and per-folder totals."""
        return await self._get(
            "/campaigns-overview", cast_to=CampaignsOverview, options=options
        )

    async def preview_template(
        self,
        *,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        contact: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignTemplatePreview:
        """Render subject/body exactly as the send path would. No side effects.

        Args:
            subject: The subject template.
            body_html: The HTML body template.
            body_plain: The plain-text body template.
            contact: Overrides for the sample contact the preview renders
                against (``first_name``, ``last_name``, ``email``, ``company``,
                ``phone``, ``custom_fields``).
        """
        return await self._post(
            "/campaign-template-preview",
            cast_to=CampaignTemplatePreview,
            body=drop_not_given(
                {
                    "subject": subject,
                    "body_html": body_html,
                    "body_plain": body_plain,
                    "contact": contact,
                }
            ),
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
        text_only: NotGivenOr[bool] = NOT_GIVEN,
        daily_limit: NotGivenOr[int] = NOT_GIVEN,
        unsubscribe_header: NotGivenOr[bool] = NOT_GIVEN,
        risky_emails: NotGivenOr[bool] = NOT_GIVEN,
        cc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        bcc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        start_date: NotGivenOr[str] = NOT_GIVEN,
        end_date: NotGivenOr[str] = NOT_GIVEN,
        timezone: NotGivenOr[str] = NOT_GIVEN,
        days: NotGivenOr[int] = NOT_GIVEN,
        start_time: NotGivenOr[str] = NOT_GIVEN,
        end_time: NotGivenOr[str] = NOT_GIVEN,
        schedule_windows: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        email_tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        folders: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        contact_order_by: NotGivenOr[str] = NOT_GIVEN,
        contact_order_dir: NotGivenOr[str] = NOT_GIVEN,
        contact_order_field: NotGivenOr[str] = NOT_GIVEN,
        sender_strategy: NotGivenOr[str] = NOT_GIVEN,
        rotation_mode: NotGivenOr[str] = NOT_GIVEN,
        ramp_enabled: NotGivenOr[bool] = NOT_GIVEN,
        ramp_start: NotGivenOr[int] = NOT_GIVEN,
        ramp_increment: NotGivenOr[int] = NOT_GIVEN,
        ramp_ceiling: NotGivenOr[int] = NOT_GIVEN,
        esp_match_mode: NotGivenOr[str] = NOT_GIVEN,
        max_new_leads_per_day: NotGivenOr[int] = NOT_GIVEN,
        prioritize_new_leads: NotGivenOr[bool] = NOT_GIVEN,
        tracking_domain: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Campaign:
        """Update a campaign.

        The explicit sender *list* is edited with :meth:`set_senders`; only the
        strategy and rotation toggles ride this call.
        """
        return await self._patch(
            f"/campaigns/{campaign_id}",
            cast_to=Campaign,
            body=_campaign_body(
                name=name,
                description=description,
                status=status,
                stop_on_reply=stop_on_reply,
                open_tracking=open_tracking,
                link_tracking=link_tracking,
                text_only=text_only,
                daily_limit=daily_limit,
                unsubscribe_header=unsubscribe_header,
                risky_emails=risky_emails,
                cc=cc,
                bcc=bcc,
                start_date=start_date,
                end_date=end_date,
                timezone=timezone,
                days=days,
                start_time=start_time,
                end_time=end_time,
                schedule_windows=schedule_windows,
                email_tags=email_tags,
                folders=folders,
                contact_order_by=contact_order_by,
                contact_order_dir=contact_order_dir,
                contact_order_field=contact_order_field,
                sender_strategy=sender_strategy,
                rotation_mode=rotation_mode,
                ramp_enabled=ramp_enabled,
                ramp_start=ramp_start,
                ramp_increment=ramp_increment,
                ramp_ceiling=ramp_ceiling,
                esp_match_mode=esp_match_mode,
                max_new_leads_per_day=max_new_leads_per_day,
                prioritize_new_leads=prioritize_new_leads,
                tracking_domain=tracking_domain,
            ),
            options=options,
        )

    async def delete(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignDeleted:
        """Delete a campaign."""
        return await self._delete(
            f"/campaigns/{campaign_id}", cast_to=CampaignDeleted, options=options
        )

    # -- advanced settings ---------------------------------------------------
    async def retrieve_advanced(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignAdvanced:
        """Retrieve a campaign's overrides of the org's outreach settings."""
        return await self._get(
            f"/campaigns/{campaign_id}/advanced",
            cast_to=CampaignAdvanced,
            options=options,
        )

    async def update_advanced(
        self,
        campaign_id: str,
        *,
        settings: Mapping[str, Any],
        options: RequestOptions | None = None,
    ) -> None:
        """Replace a campaign's outreach-settings overrides.

        Args:
            campaign_id: The campaign to configure.
            settings: The overrides tree, shaped like the organization
                settings returned by ``client.outreach.settings()``.
        """
        return await self._patch(
            f"/campaigns/{campaign_id}/advanced",
            cast_to=type(None),
            body={"settings": dict(settings)},
            options=options,
        )

    # -- sequence steps ------------------------------------------------------
    def list_steps(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[CampaignStep]:
        """List a campaign's sequence steps, in order."""
        return self._get_api_list(
            f"/campaigns/{campaign_id}/steps", model=CampaignStep, options=options
        )

    async def create_step(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignStep:
        """Append a blank step to a campaign's sequence.

        Takes no body: the step is created empty and then filled in with
        :meth:`update_step`.
        """
        return await self._post(
            f"/campaigns/{campaign_id}/steps", cast_to=CampaignStep, options=options
        )

    async def update_step(
        self,
        campaign_id: str,
        step_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        body_sync: NotGivenOr[bool] = NOT_GIVEN,
        body_code: NotGivenOr[bool] = NOT_GIVEN,
        wait_after: NotGivenOr[int] = NOT_GIVEN,
        kind: NotGivenOr[str] = NOT_GIVEN,
        action: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        conditions: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignStep:
        """Update a sequence step.

        Args:
            wait_after: Days to wait before the next step fires.
            kind: The step kind; non-email kinds carry their behaviour in
                *action*.
            action: The action configuration for a non-email step.
            conditions: Branch conditions gating the step.
        """
        return await self._patch(
            f"/campaigns/{campaign_id}/steps/{step_id}",
            cast_to=CampaignStep,
            body=_step_body(
                name=name,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                body_sync=body_sync,
                body_code=body_code,
                wait_after=wait_after,
                kind=kind,
                action=action,
                conditions=conditions,
            ),
            options=options,
        )

    async def delete_step(
        self,
        campaign_id: str,
        step_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> CampaignStepDeleted:
        """Delete a sequence step."""
        return await self._delete(
            f"/campaigns/{campaign_id}/steps/{step_id}",
            cast_to=CampaignStepDeleted,
            options=options,
        )

    async def set_step_layout(
        self,
        campaign_id: str,
        *,
        positions: Sequence[Mapping[str, Any]],
        options: RequestOptions | None = None,
    ) -> LayoutSaved:
        """Persist the sequence builder's node positions.

        Cosmetic and unaudited.

        Args:
            positions: One ``{"id", "x", "y"}`` entry per step.
        """
        return await self._patch(
            f"/campaigns/{campaign_id}/step-layout",
            cast_to=LayoutSaved,
            body={"positions": [dict(p) for p in positions]},
            options=options,
        )

    # -- A/B variants --------------------------------------------------------
    def list_ab_variants(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[CampaignABVariant]:
        """List a campaign's A/B variants."""
        return self._get_api_list(
            f"/campaigns/{campaign_id}/ab-variants",
            model=CampaignABVariant,
            options=options,
        )

    async def create_ab_variant(
        self,
        campaign_id: str,
        *,
        name: str,
        step_id: NotGivenOr[str] = NOT_GIVEN,
        weight: NotGivenOr[int] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        is_control: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignABVariant:
        """Create an A/B variant.

        Args:
            name: A label for the variant.
            step_id: Scope the variant to one sequence step.
            weight: The variant's share of the split.
            is_control: Mark this variant as the control.
        """
        return await self._post(
            f"/campaigns/{campaign_id}/ab-variants",
            cast_to=CampaignABVariant,
            body=_variant_body(
                name=name,
                step_id=step_id,
                weight=weight,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                is_control=is_control,
                is_active=NOT_GIVEN,
            ),
            options=options,
        )

    async def update_ab_variant(
        self,
        campaign_id: str,
        variant_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        weight: NotGivenOr[int] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        is_control: NotGivenOr[bool] = NOT_GIVEN,
        is_active: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignABVariant:
        """Update an A/B variant."""
        return await self._patch(
            f"/campaigns/{campaign_id}/ab-variants/{variant_id}",
            cast_to=CampaignABVariant,
            body=_variant_body(
                name=name,
                step_id=NOT_GIVEN,
                weight=weight,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                is_control=is_control,
                is_active=is_active,
            ),
            options=options,
        )

    async def delete_ab_variant(
        self,
        campaign_id: str,
        variant_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> CampaignABVariantDeleted:
        """Delete an A/B variant."""
        return await self._delete(
            f"/campaigns/{campaign_id}/ab-variants/{variant_id}",
            cast_to=CampaignABVariantDeleted,
            options=options,
        )

    async def ab_analysis(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignABAnalysis:
        """Retrieve the A/B performance analysis for a campaign."""
        return await self._get(
            f"/campaigns/{campaign_id}/ab-analysis",
            cast_to=CampaignABAnalysis,
            options=options,
        )

    # -- attachments ---------------------------------------------------------
    def list_attachments(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[CampaignAttachment]:
        """List a campaign's attachments, with fresh presigned URLs."""
        return self._get_api_list(
            f"/campaigns/{campaign_id}/attachments",
            model=CampaignAttachment,
            options=options,
        )

    async def upload_attachment(
        self,
        campaign_id: str,
        *,
        file: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        step_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignAttachment:
        """Upload a file attachment (multipart, max 15 MB).

        Args:
            campaign_id: The campaign to attach to.
            file: The raw file bytes.
            filename: The filename recipients see.
            content_type: The file's MIME type.
            step_id: Scope the attachment to one sequence step instead of the
                whole campaign.
        """
        form = drop_not_given({"step_id": step_id})
        return await self._client.request(
            cast_to=CampaignAttachment,
            method="POST",
            path=f"/campaigns/{campaign_id}/attachments",
            form=form or None,
            files={"file": (filename, file, content_type)},
            options=options,
        )

    async def delete_attachment(
        self,
        campaign_id: str,
        attachment_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> CampaignAttachmentDeleted:
        """Delete an attachment."""
        return await self._delete(
            f"/campaigns/{campaign_id}/attachments/{attachment_id}",
            cast_to=CampaignAttachmentDeleted,
            options=options,
        )

    # -- senders + tracking domain ------------------------------------------
    async def senders(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignSenders:
        """Retrieve a campaign's explicit sender pool."""
        return await self._get(
            f"/campaigns/{campaign_id}/senders",
            cast_to=CampaignSenders,
            options=options,
        )

    async def set_senders(
        self,
        campaign_id: str,
        *,
        senders: Sequence[Mapping[str, Any]],
        options: RequestOptions | None = None,
    ) -> CampaignSenders:
        """Replace a campaign's sender pool wholesale.

        Args:
            senders: One ``{"email_account_id", "weight", "enabled"}`` entry
                per mailbox. This is the desired final set, so a ``PUT`` retry
                is safe.
        """
        return await self._put(
            f"/campaigns/{campaign_id}/senders",
            cast_to=CampaignSenders,
            body={"senders": [dict(s) for s in senders]},
            options=options,
        )

    async def verify_tracking_domain(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignTrackingDomainStatus:
        """Re-check the DNS for a campaign's custom tracking domain."""
        return await self._post(
            f"/campaigns/{campaign_id}/tracking-domain/verify",
            cast_to=CampaignTrackingDomainStatus,
            options=options,
        )

    # -- run lifecycle -------------------------------------------------------
    async def preflight(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignPreflight:
        """Run the pre-launch readiness checks without sending anything."""
        return await self._post(
            f"/campaigns/{campaign_id}/preflight",
            cast_to=CampaignPreflight,
            options=options,
        )

    async def send_test_email(
        self,
        campaign_id: str,
        *,
        account_id: str,
        recipient: str,
        step_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignTestEmail:
        """Send one real preview email for a campaign step.

        Args:
            campaign_id: The campaign to preview.
            account_id: The mailbox to send from.
            recipient: Where to send the preview.
            step_id: Which step to render; defaults to the first.
        """
        return await self._post(
            f"/campaigns/{campaign_id}/test-email",
            cast_to=CampaignTestEmail,
            body=drop_not_given(
                {
                    "account_id": account_id,
                    "recipient": recipient,
                    "step_id": step_id,
                }
            ),
            options=options,
        )

    async def start(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignRunState:
        """Start sending. This dispatches real mail."""
        return await self._post(
            f"/campaigns/{campaign_id}/start",
            cast_to=CampaignRunState,
            options=options,
        )

    async def stop(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignRunState:
        """Stop sending."""
        return await self._post(
            f"/campaigns/{campaign_id}/stop",
            cast_to=CampaignRunState,
            options=options,
        )

    def logs(
        self,
        campaign_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[CampaignLog]:
        """List a campaign's activity log (auto-paginating).

        Args:
            limit: Page size (1-100; the server defaults to 50).
        """
        return self._get_api_list(
            f"/campaigns/{campaign_id}/logs",
            model=CampaignLog,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )
