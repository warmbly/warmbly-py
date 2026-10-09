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

from pydantic import Field

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given
from .forms import CampaignFormStats

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
    "CampaignEstimate",
    "CampaignForms",
    "CampaignLeadCC",
    "CampaignLeadCCList",
    "CampaignLeadCCSuggestion",
    "CampaignLeadCCSuggestions",
    "CampaignLeadHold",
    "CampaignLeadSupply",
    "CampaignLog",
    "CampaignMailboxPlan",
    "CampaignOrgAllowance",
    "CampaignPreflight",
    "CampaignRampInfo",
    "CampaignRunState",
    "CampaignSegmentLink",
    "CampaignSegments",
    "CampaignSendLimit",
    "CampaignSendPlan",
    "CampaignSendWindow",
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
    "LeadHold",
    "PlacementMonitor",
    "PlacementMonitorDeleted",
    "PlacementMonitorResult",
]


class Campaign(BaseModel):
    """An email campaign.

    ``days`` is a weekday bitmask; ``schedule_windows`` supersedes it when
    present. ``senders`` is loaded on demand, not on the list endpoint.

    ``timezone`` is the zone the schedule is read in and is empty when the
    campaign follows the workspace timezone; ``effective_timezone`` is the zone
    actually in use either way. ``entry_delay_minutes`` holds a contact's first
    email back that long after they entered the campaign (``0`` sends it as soon
    as it is due). A ``continuous`` campaign that runs out of leads stays active
    and waits for more instead of finishing, with ``idle_since`` set while it
    waits.

    ``kind`` is retired: one-time campaigns no longer exist on the server, so
    newer servers omit it. It is kept here only so older servers still parse.
    """

    id: str
    user_id: str | None = None
    organization_id: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None
    kind: str | None = None
    stop_on_reply: bool | None = None
    open_tracking: bool | None = None
    link_tracking: bool | None = None
    text_only: bool | None = None
    daily_limit: int | None = None
    unsubscribe_header: bool | None = None
    risky_emails: bool | None = None
    unsubscribe_mode: str | None = None
    cc: Sequence[str] = []
    bcc: Sequence[str] = []
    start_date: str | None = None
    end_date: str | None = None
    timezone: str | None = None
    effective_timezone: str | None = None
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
    entry_delay_minutes: int | None = None
    continuous: bool | None = None
    idle_since: str | None = None
    guardrail_enabled: bool | None = None
    guardrail_bounce_rate_max: float | None = None
    guardrail_complaint_rate_max: float | None = None
    guardrail_reply_rate_min: float | None = None
    guardrail_min_sample: int | None = None
    guardrail_window_days: int | None = None
    guardrail_tripped_at: str | None = None
    guardrail_reason: str | None = None
    tracking_domain: str | None = None
    tracking_domain_verified: bool | None = None
    tracking_domain_verified_at: str | None = None
    utm_tracking: bool | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    last_status_change_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CampaignDeleted(BaseModel):
    """The result of deleting a campaign (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class CampaignsOverview(BaseModel):
    """Status-bucket counts and per-folder totals for the campaigns browser.

    ``one_time`` is retired along with one-time campaigns; newer servers omit it.
    """

    total: int | None = None
    active: int | None = None
    paused: int | None = None
    draft: int | None = None
    completed: int | None = None
    one_time: int | None = None
    folders: Sequence[dict[str, Any]] = []


class CampaignRunState(BaseModel):
    """The result of starting or stopping a campaign.

    ``waiting_for_leads`` is ``True`` when a continuous campaign started with
    nothing left to send: it is active and idle, waiting for leads, rather than
    sending. Only :meth:`Campaigns.start` reports it.
    """

    status: str | None = None
    waiting_for_leads: bool | None = None


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
    the *next* step fires. ``thread_reply`` sends the step as a reply inside the
    conversation the campaign's first email opened (default ``True``); it only
    matters once the contact has already received an email from the campaign.
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
    thread_reply: bool | None = None
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
    """A single activity-log entry for a campaign.

    ``event_type`` names what happened and ``metadata`` carries the specifics
    of that kind of entry.
    """

    id: str
    campaign_id: str | None = None
    event_type: str | None = None
    message: str | None = None
    metadata: dict[str, Any] | None = None
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
    tokens that had no value, so a composer can flag both inline. ``from_``
    is the ``{"name", "email"}`` sender as recipients see it, present when an
    ``account_id`` was given, and ``attachments`` the files this send would
    carry, present when a ``campaign_id`` was.
    """

    subject: str | None = None
    body_html: str | None = None
    body_plain: str | None = None
    from_: dict[str, Any] | None = Field(default=None, alias="from")
    attachments: Sequence[dict[str, Any]] = []
    errors: Sequence[str] = []
    unresolved: Sequence[str] = []


class CampaignEstimate(BaseModel):
    """A projection of an audience against a sender pool. Nothing is written.

    ``daily_capacity`` is the pool's per-day ceiling under the campaign limit
    and ``remaining_today`` subtracts what those mailboxes already sent today.
    ``sending_days`` and ``estimated_finish_at`` are ``None`` when the pool has
    no capacity at all, or the projection horizon passes first.

    The projection also reports ``steps`` (emails per contact) and
    ``total_sends`` (recipients times steps), ``first_touch_finish_at`` (the day
    the last contact gets a first email), ``steady_capacity`` and
    ``full_capacity_at`` (capacity once every mailbox has graduated from warmup),
    ``ramping`` and ``held`` mailbox counts, the ``warmup`` traffic sharing the
    pool, ``other_campaigns_per_day``, the ``bottleneck`` clamp (empty when the
    mailboxes' own caps are the limit), a day-by-day ``timeline`` and the pool
    ``senders``.
    """

    recipients: int | None = None
    mailboxes: int | None = None
    daily_capacity: int | None = None
    remaining_today: int | None = None
    sending_days: int | None = None
    estimated_finish_at: str | None = None
    steps: int | None = None
    total_sends: int | None = None
    first_touch_finish_at: str | None = None
    steady_capacity: int | None = None
    full_capacity_at: str | None = None
    ramping: int | None = None
    held: int | None = None
    warmup: dict[str, Any] | None = None
    other_campaigns_per_day: int | None = None
    bottleneck: str | None = None
    timeline: Sequence[dict[str, Any]] = []
    senders: Sequence[dict[str, Any]] = []


class CampaignSegmentLink(BaseModel):
    """One segment linked to a campaign, with live counts.

    ``contact_count`` is the segment's size now, ``lead_count`` how many of
    those are already leads of the campaign, and ``held_out_count`` how many
    are deliberately kept out.
    """

    segment_id: str | None = None
    name: str | None = None
    color: str | None = None
    description: str | None = None
    contact_count: int | None = None
    lead_count: int | None = None
    held_out_count: int | None = None
    linked_at: str | None = None


class CampaignSegments(BaseModel):
    """A campaign's linked segments.

    ``added`` is how many new leads the last replace enrolled; it is ``None``
    when simply reading the set. Detaching a segment withdraws the leads it
    brought: ``withdrawn`` is how many were removed and ``contacted`` how many of
    that audience the campaign had already written to, which stay. Both are
    ``None`` when simply reading the set.
    """

    data: Sequence[CampaignSegmentLink] = []
    added: int | None = None
    withdrawn: int | None = None
    contacted: int | None = None


class CampaignForms(BaseModel):
    """How the forms linked from a campaign performed for its recipients."""

    data: Sequence[CampaignFormStats] = []


class PlacementMonitor(BaseModel):
    """A campaign's scheduled inbox-placement test.

    The monitor re-tests the campaign's first email step every
    ``interval_days``. ``panel`` is the seed panel it tests against
    (``instance``, ``workspace`` or ``cloud``); ``alert_below`` is the placement
    percentage that raises an alert and ``pause_on_alert`` pauses the campaign
    when it does.
    """

    id: str
    campaign_id: str | None = None
    created_by: str | None = None
    enabled: bool | None = None
    interval_days: int | None = None
    panel: str | None = None
    alert_below: int | None = None
    pause_on_alert: bool | None = None
    next_run_at: str | None = None
    last_run_at: str | None = None
    last_test_id: str | None = None
    last_alert_at: str | None = None
    last_error: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class PlacementMonitorResult(BaseModel):
    """The ``{"data": ...}`` envelope around a placement monitor.

    ``data`` is ``None`` when the campaign has no monitor.
    """

    data: PlacementMonitor | None = None


class PlacementMonitorDeleted(BaseModel):
    """The result of removing a placement monitor (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class CampaignSendLimit(BaseModel):
    """One clamp in a send plan's waterfall and how many sends it removed.

    ``kind`` is one of ``campaign_daily_limit``, ``campaign_ramp``,
    ``warmup_graduation``, ``workspace_risk``, ``domain_auth``, ``resting``,
    ``warmup_health_hold``, ``other_campaigns``, ``warmup_health_pace``,
    ``mailbox_hours``, ``spacing``, ``sending_window``, ``not_running``,
    ``org_daily_limit``, ``new_lead_cap``, ``leads`` or ``sending_behavior``.
    """

    kind: str | None = None
    emails: int | None = None
    mailboxes: int | None = None


class CampaignSendWindow(BaseModel):
    """A campaign's sending calendar for today."""

    sending_day: bool | None = None
    open_now: bool | None = None
    opens_at: str | None = None
    closes_at: str | None = None
    minutes_left: int | None = None
    starts_at: str | None = None
    ends_at: str | None = None


class CampaignLeadSupply(BaseModel):
    """How many leads are due, so the plan is bounded by leads as well as mailboxes."""

    due_now: int | None = None
    due_later_today: int | None = None
    new_leads_due_today: int | None = None
    waiting_on_step: int | None = None
    waiting_on_condition: int | None = None
    held: int | None = None
    waiting_on_sender: int | None = None
    new_leads_started_today: int | None = None
    max_new_leads_per_day: int | None = None
    next_due_at: str | None = None


class CampaignRampInfo(BaseModel):
    """The warmup graduation ceiling holding a mailbox below its own cap."""

    ceiling: int | None = None
    mailbox_cap: int | None = None
    days_to_full_cap: int | None = None
    held: bool | None = None


class CampaignMailboxPlan(BaseModel):
    """One mailbox's day on a campaign.

    ``state`` is why it is or is not sending right now: ``sending``,
    ``budget_spent``, ``hours_closed``, ``no_working_day``, ``domain_auth``,
    ``resting``, ``health_hold``, ``window_closed`` or ``no_worker``.
    ``limited_by`` names the clamp that set ``cap_today``.
    """

    id: str | None = None
    email: str | None = None
    provider: str | None = None
    configured_cap: int | None = None
    cap_today: int | None = None
    limited_by: str | None = None
    sent_today: int | None = None
    sent_by_other_campaigns: int | None = None
    expected_remaining: int | None = None
    state: str | None = None
    reopens_at: str | None = None
    health: str | None = None
    min_gap_seconds: int | None = None
    graduation: CampaignRampInfo | None = None


class CampaignOrgAllowance(BaseModel):
    """The workspace's plan-level daily campaign allowance."""

    daily_limit: int | None = None
    sent_today: int | None = None
    remaining: int | None = None


class CampaignSendPlan(BaseModel):
    """What one campaign will send today, and why that number is what it is.

    Derived on every read through the scheduler's own gates. The arithmetic
    adds up: ``configured_ceiling`` minus every ``limits`` entry minus
    ``sent_today`` equals ``expected_remaining``. ``projected_today`` is what has
    gone out plus what is still expected to, and ``bottleneck`` names the limit
    that decides it (empty when nothing binds below the ceiling, or
    ``budget_spent`` when the day is simply used). ``day`` is the UTC budget day;
    ``stale`` is ``True`` when the figures come from a snapshot the campaign has
    since outrun and a fresh one is being computed.
    """

    campaign_id: str | None = None
    status: str | None = None
    day: str | None = None
    timezone: str | None = None
    computed_at: str | None = None
    stale: bool | None = None
    configured_ceiling: int | None = None
    projected_today: int | None = None
    sent_today: int | None = None
    expected_remaining: int | None = None
    bottleneck: str | None = None
    limits: Sequence[CampaignSendLimit] = []
    window: CampaignSendWindow | None = None
    leads: CampaignLeadSupply | None = None
    mailboxes: Sequence[CampaignMailboxPlan] = []
    organization: CampaignOrgAllowance | None = None
    next_wake_at: str | None = None


class LeadHold(BaseModel):
    """One contact's flow parked inside one campaign.

    ``source`` is ``manual`` (a member or API call), ``out_of_office`` (an
    auto-reply parked it) or ``inbox_tagging`` (a classified reply did).
    ``until`` is ``None`` for a hold with no end, which only a resume lifts.
    """

    since: str | None = None
    until: str | None = None
    reason: str | None = None
    source: str | None = None


class CampaignLeadHold(BaseModel):
    """The hold state of one lead, as returned by the hold, pause and resume calls.

    ``hold`` is ``None`` when the lead is not held.
    """

    campaign_id: str | None = None
    contact_id: str | None = None
    hold: LeadHold | None = None


class CampaignLeadCC(BaseModel):
    """A contact copied on every email one campaign sends one lead.

    ``status`` says whether the next email copies them: ``active`` is copied,
    ``unsubscribed``, ``bounced`` and ``undeliverable`` are left off.
    """

    contact_id: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    status: str | None = None
    bounced_at: str | None = None


class CampaignLeadCCList(BaseModel):
    """The contacts copied on one lead."""

    campaign_id: str | None = None
    contact_id: str | None = None
    cc: Sequence[CampaignLeadCC] = []


class CampaignLeadCCSuggestion(BaseModel):
    """A contact who looks like a colleague of the lead.

    ``reason`` is ``company`` when the company names match and ``domain`` when
    only the email domain does.
    """

    contact_id: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    reason: str | None = None


class CampaignLeadCCSuggestions(BaseModel):
    """Likely colleagues of a lead, offered first when choosing who to copy."""

    data: Sequence[CampaignLeadCCSuggestion] = []


def _campaign_body(
    *,
    for_create: bool = False,
    name: NotGivenOr[str] = NOT_GIVEN,
    description: NotGivenOr[str] = NOT_GIVEN,
    status: NotGivenOr[str] = NOT_GIVEN,
    kind: NotGivenOr[str] = NOT_GIVEN,
    stop_on_reply: NotGivenOr[bool] = NOT_GIVEN,
    open_tracking: NotGivenOr[bool] = NOT_GIVEN,
    link_tracking: NotGivenOr[bool] = NOT_GIVEN,
    text_only: NotGivenOr[bool] = NOT_GIVEN,
    daily_limit: NotGivenOr[int] = NOT_GIVEN,
    unsubscribe_header: NotGivenOr[bool] = NOT_GIVEN,
    risky_emails: NotGivenOr[bool] = NOT_GIVEN,
    unsubscribe_mode: NotGivenOr[str] = NOT_GIVEN,
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
    entry_delay_minutes: NotGivenOr[int] = NOT_GIVEN,
    continuous: NotGivenOr[bool] = NOT_GIVEN,
    tracking_domain: NotGivenOr[str] = NOT_GIVEN,
    utm_tracking: NotGivenOr[bool] = NOT_GIVEN,
    utm_source: NotGivenOr[str] = NOT_GIVEN,
    utm_medium: NotGivenOr[str] = NOT_GIVEN,
    utm_campaign: NotGivenOr[str] = NOT_GIVEN,
    guardrail_enabled: NotGivenOr[bool] = NOT_GIVEN,
    guardrail_bounce_rate_max: NotGivenOr[float] = NOT_GIVEN,
    guardrail_complaint_rate_max: NotGivenOr[float] = NOT_GIVEN,
    guardrail_reply_rate_min: NotGivenOr[float] = NOT_GIVEN,
    guardrail_min_sample: NotGivenOr[int] = NOT_GIVEN,
    guardrail_window_days: NotGivenOr[int] = NOT_GIVEN,
    steps: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
    variants: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
    senders: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
    advanced_overrides: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
) -> dict[str, Any]:
    """Build the create/update campaign body.

    The two bodies differ in one place: create names the tag and folder lists
    ``email_tag_ids`` / ``folder_ids``, update names them ``email_tags`` /
    ``folders``. *for_create* picks the pair, so a caller never has to.
    """
    return drop_not_given(
        {
            "name": name,
            "description": description,
            "status": status,
            "kind": kind,
            "stop_on_reply": stop_on_reply,
            "open_tracking": open_tracking,
            "link_tracking": link_tracking,
            "text_only": text_only,
            "daily_limit": daily_limit,
            "unsubscribe_header": unsubscribe_header,
            "risky_emails": risky_emails,
            "unsubscribe_mode": unsubscribe_mode,
            "cc": cc,
            "bcc": bcc,
            "start_date": start_date,
            "end_date": end_date,
            "timezone": timezone,
            "days": days,
            "start_time": start_time,
            "end_time": end_time,
            "schedule_windows": schedule_windows,
            "email_tag_ids" if for_create else "email_tags": email_tags,
            "folder_ids" if for_create else "folders": folders,
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
            "entry_delay_minutes": entry_delay_minutes,
            "continuous": continuous,
            "tracking_domain": tracking_domain,
            "utm_tracking": utm_tracking,
            "utm_source": utm_source,
            "utm_medium": utm_medium,
            "utm_campaign": utm_campaign,
            "guardrail_enabled": guardrail_enabled,
            "guardrail_bounce_rate_max": guardrail_bounce_rate_max,
            "guardrail_complaint_rate_max": guardrail_complaint_rate_max,
            "guardrail_reply_rate_min": guardrail_reply_rate_min,
            "guardrail_min_sample": guardrail_min_sample,
            "guardrail_window_days": guardrail_window_days,
            "steps": steps,
            "variants": variants,
            "senders": senders,
            "advanced_overrides": advanced_overrides,
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
    thread_reply: NotGivenOr[bool] = NOT_GIVEN,
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
            "thread_reply": thread_reply,
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
        kind: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        stop_on_reply: NotGivenOr[bool] = NOT_GIVEN,
        open_tracking: NotGivenOr[bool] = NOT_GIVEN,
        link_tracking: NotGivenOr[bool] = NOT_GIVEN,
        text_only: NotGivenOr[bool] = NOT_GIVEN,
        daily_limit: NotGivenOr[int] = NOT_GIVEN,
        unsubscribe_header: NotGivenOr[bool] = NOT_GIVEN,
        risky_emails: NotGivenOr[bool] = NOT_GIVEN,
        unsubscribe_mode: NotGivenOr[str] = NOT_GIVEN,
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
        entry_delay_minutes: NotGivenOr[int] = NOT_GIVEN,
        continuous: NotGivenOr[bool] = NOT_GIVEN,
        tracking_domain: NotGivenOr[str] = NOT_GIVEN,
        utm_tracking: NotGivenOr[bool] = NOT_GIVEN,
        utm_source: NotGivenOr[str] = NOT_GIVEN,
        utm_medium: NotGivenOr[str] = NOT_GIVEN,
        utm_campaign: NotGivenOr[str] = NOT_GIVEN,
        guardrail_enabled: NotGivenOr[bool] = NOT_GIVEN,
        guardrail_bounce_rate_max: NotGivenOr[float] = NOT_GIVEN,
        guardrail_complaint_rate_max: NotGivenOr[float] = NOT_GIVEN,
        guardrail_reply_rate_min: NotGivenOr[float] = NOT_GIVEN,
        guardrail_min_sample: NotGivenOr[int] = NOT_GIVEN,
        guardrail_window_days: NotGivenOr[int] = NOT_GIVEN,
        steps: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        variants: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        senders: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        advanced_overrides: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Campaign:
        """Create a campaign.

        Only *name* is required; every other field falls back to a sane
        default, so a minimal ``create(name=...)`` produces a usable draft.

        Args:
            name: A human-readable name for the campaign.
            kind: Retired. One-time campaigns no longer exist on the server, which
                ignores this field; it is still sent if you pass it.
            description: An optional longer description.
            stop_on_reply: Stop sequencing a contact once they reply.
            open_tracking: Enable open tracking.
            link_tracking: Enable link/click tracking.
            text_only: Send plain text only.
            daily_limit: Max emails per day across the campaign.
            unsubscribe_header: Add a ``List-Unsubscribe`` header.
            risky_emails: Allow sending to addresses flagged as risky.
            unsubscribe_mode: The in-body opt-out appended after the signature:
                ``inherit`` (the workspace default), ``text``, ``link`` or ``off``.
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
            contact_order_by: Which contact ordering leads are drawn in.
            contact_order_dir: ``asc`` or ``desc``.
            contact_order_field: A custom field to order by.
            sender_strategy: ``tags`` (senders resolved from *email_tags*) or
                ``explicit`` (the campaign's own sender pool).
            rotation_mode: How volume spreads across the chosen mailboxes.
            ramp_enabled: Ramp the campaign's daily volume up over time.
            ramp_start: The first day's ramp ceiling.
            ramp_increment: How much the ramp ceiling rises each day.
            ramp_ceiling: Where the ramp stops rising.
            esp_match_mode: ESP matching: ``off``, ``prefer`` or ``strict``.
            max_new_leads_per_day: New-lead throttle; ``0`` is unlimited.
            prioritize_new_leads: Send to new leads before continuing older ones.
            entry_delay_minutes: Hold a contact's first email back this many minutes
                after they entered the campaign; ``0`` sends it as soon as it is due.
            continuous: Keep the campaign active when it runs out of leads: it waits,
                idle, for more instead of finishing.
            tracking_domain: A campaign-scoped tracking domain, honored once verified.
            utm_tracking: Append UTM parameters to every link in the body.
            utm_source: The ``utm_source`` value (default ``"warmbly"``).
            utm_medium: The ``utm_medium`` value (default ``"email"``).
            utm_campaign: The ``utm_campaign`` value (default: the campaign name).
            guardrail_enabled: Auto-pause the campaign the moment a rate band is
                breached.
            guardrail_bounce_rate_max: Pause at or above this bounce rate; ``0``
                disables the rule.
            guardrail_complaint_rate_max: Pause at or above this complaint rate; ``0``
                disables the rule.
            guardrail_reply_rate_min: Pause *below* this reply rate; ``0`` disables the
                rule.
            guardrail_min_sample: The smallest sample a guardrail rule will act on.
            guardrail_window_days: The rolling window the rates are measured over.
            steps: Initial sequence steps, in order; they can also be added later with
                :meth:`create_step`.
            variants: A/B variants for the first step.
            senders: The explicit sender pool, for ``sender_strategy="explicit"``.
            advanced_overrides: Per-campaign overrides of the organization's outreach
                settings.
        """
        return self._post(
            "/campaigns",
            cast_to=Campaign,
            body=_campaign_body(
                for_create=True,
                name=name,
                kind=kind,
                description=description,
                stop_on_reply=stop_on_reply,
                open_tracking=open_tracking,
                link_tracking=link_tracking,
                text_only=text_only,
                daily_limit=daily_limit,
                unsubscribe_header=unsubscribe_header,
                risky_emails=risky_emails,
                unsubscribe_mode=unsubscribe_mode,
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
                entry_delay_minutes=entry_delay_minutes,
                continuous=continuous,
                tracking_domain=tracking_domain,
                utm_tracking=utm_tracking,
                utm_source=utm_source,
                utm_medium=utm_medium,
                utm_campaign=utm_campaign,
                guardrail_enabled=guardrail_enabled,
                guardrail_bounce_rate_max=guardrail_bounce_rate_max,
                guardrail_complaint_rate_max=guardrail_complaint_rate_max,
                guardrail_reply_rate_min=guardrail_reply_rate_min,
                guardrail_min_sample=guardrail_min_sample,
                guardrail_window_days=guardrail_window_days,
                steps=steps,
                variants=variants,
                senders=senders,
                advanced_overrides=advanced_overrides,
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

    def estimate(
        self,
        *,
        segment_ids: Sequence[str],
        email_tag_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        daily_limit: NotGivenOr[int] = NOT_GIVEN,
        days: NotGivenOr[int] = NOT_GIVEN,
        timezone: NotGivenOr[str] = NOT_GIVEN,
        start_date: NotGivenOr[str] = NOT_GIVEN,
        start_time: NotGivenOr[str] = NOT_GIVEN,
        end_time: NotGivenOr[str] = NOT_GIVEN,
        step_waits: NotGivenOr[Sequence[int]] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignEstimate:
        """Project an audience against a sender pool before a campaign exists.

        Answers "how many people is this, and how long will reaching them
        take" without writing anything.

        Args:
            segment_ids: The segments making up the audience.
            email_tag_ids: Mailbox tags the senders would be drawn from.
            daily_limit: The per-campaign daily cap to project under.
            days: Weekday bitmask for the sending window.
            timezone: IANA timezone the schedule is interpreted in.
            start_date: RFC 3339 date sending would start.
            start_time: Daily sending window start (``"HH:MM"``).
            end_time: Daily sending window end (``"HH:MM"``).
            step_waits: Each follow-up's ``wait_after`` in days, in order (at
                most 30). Omit for a single email.
            campaign_id: Project a saved campaign, filling anything not sent from
                it.
        """
        return self._post(
            "/campaigns-estimate",
            cast_to=CampaignEstimate,
            body=drop_not_given(
                {
                    "segment_ids": list(segment_ids),
                    "email_tag_ids": email_tag_ids,
                    "daily_limit": daily_limit,
                    "days": days,
                    "timezone": timezone,
                    "start_date": start_date,
                    "start_time": start_time,
                    "end_time": end_time,
                    "step_waits": step_waits,
                    "campaign_id": campaign_id,
                }
            ),
            options=options,
        )

    def preview_template(
        self,
        *,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        contact: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        account_id: NotGivenOr[str] = NOT_GIVEN,
        step_id: NotGivenOr[str] = NOT_GIVEN,
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
            contact_id: A real contact of the organization to render for,
                instead of the built-in sample. Needs ``read_contacts``.
            campaign_id: The campaign whose opt-out footer, plain-text setting
                and attachments apply.
            account_id: The mailbox whose signature applies, and which is
                reported back as the sender.
            step_id: The step being previewed, so the attachment list is the
                one that step actually sends. Omitted lists the campaign-wide
                files only.
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
                    "contact_id": contact_id,
                    "campaign_id": campaign_id,
                    "account_id": account_id,
                    "step_id": step_id,
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
        status: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        stop_on_reply: NotGivenOr[bool] = NOT_GIVEN,
        open_tracking: NotGivenOr[bool] = NOT_GIVEN,
        link_tracking: NotGivenOr[bool] = NOT_GIVEN,
        text_only: NotGivenOr[bool] = NOT_GIVEN,
        daily_limit: NotGivenOr[int] = NOT_GIVEN,
        unsubscribe_header: NotGivenOr[bool] = NOT_GIVEN,
        risky_emails: NotGivenOr[bool] = NOT_GIVEN,
        unsubscribe_mode: NotGivenOr[str] = NOT_GIVEN,
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
        entry_delay_minutes: NotGivenOr[int] = NOT_GIVEN,
        continuous: NotGivenOr[bool] = NOT_GIVEN,
        tracking_domain: NotGivenOr[str] = NOT_GIVEN,
        utm_tracking: NotGivenOr[bool] = NOT_GIVEN,
        utm_source: NotGivenOr[str] = NOT_GIVEN,
        utm_medium: NotGivenOr[str] = NOT_GIVEN,
        utm_campaign: NotGivenOr[str] = NOT_GIVEN,
        guardrail_enabled: NotGivenOr[bool] = NOT_GIVEN,
        guardrail_bounce_rate_max: NotGivenOr[float] = NOT_GIVEN,
        guardrail_complaint_rate_max: NotGivenOr[float] = NOT_GIVEN,
        guardrail_reply_rate_min: NotGivenOr[float] = NOT_GIVEN,
        guardrail_min_sample: NotGivenOr[int] = NOT_GIVEN,
        guardrail_window_days: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Campaign:
        """Update a campaign.

        The explicit sender *list* is edited with :meth:`set_senders`; only the
        strategy and rotation toggles ride this call.

        Args:
            campaign_id: The campaign id.
            name: A new name for the campaign.
            status: The campaign status to move to.
            description: An optional longer description.
            stop_on_reply: Stop sequencing a contact once they reply.
            open_tracking: Enable open tracking.
            link_tracking: Enable link/click tracking.
            text_only: Send plain text only.
            daily_limit: Max emails per day across the campaign.
            unsubscribe_header: Add a ``List-Unsubscribe`` header.
            risky_emails: Allow sending to addresses flagged as risky.
            unsubscribe_mode: The in-body opt-out appended after the signature:
                ``inherit`` (the workspace default), ``text``, ``link`` or ``off``.
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
            contact_order_by: Which contact ordering leads are drawn in.
            contact_order_dir: ``asc`` or ``desc``.
            contact_order_field: A custom field to order by.
            sender_strategy: ``tags`` (senders resolved from *email_tags*) or
                ``explicit`` (the campaign's own sender pool).
            rotation_mode: How volume spreads across the chosen mailboxes.
            ramp_enabled: Ramp the campaign's daily volume up over time.
            ramp_start: The first day's ramp ceiling.
            ramp_increment: How much the ramp ceiling rises each day.
            ramp_ceiling: Where the ramp stops rising.
            esp_match_mode: ESP matching: ``off``, ``prefer`` or ``strict``.
            max_new_leads_per_day: New-lead throttle; ``0`` is unlimited.
            prioritize_new_leads: Send to new leads before continuing older ones.
            entry_delay_minutes: Hold a contact's first email back this many minutes
                after they entered the campaign; ``0`` sends it as soon as it is due.
            continuous: Keep the campaign active when it runs out of leads: it waits,
                idle, for more instead of finishing.
            tracking_domain: A campaign-scoped tracking domain, honored once verified.
            utm_tracking: Append UTM parameters to every link in the body.
            utm_source: The ``utm_source`` value (default ``"warmbly"``).
            utm_medium: The ``utm_medium`` value (default ``"email"``).
            utm_campaign: The ``utm_campaign`` value (default: the campaign name).
            guardrail_enabled: Auto-pause the campaign the moment a rate band is
                breached.
            guardrail_bounce_rate_max: Pause at or above this bounce rate; ``0``
                disables the rule.
            guardrail_complaint_rate_max: Pause at or above this complaint rate; ``0``
                disables the rule.
            guardrail_reply_rate_min: Pause *below* this reply rate; ``0`` disables the
                rule.
            guardrail_min_sample: The smallest sample a guardrail rule will act on.
            guardrail_window_days: The rolling window the rates are measured over.
        """
        return self._patch(
            f"/campaigns/{campaign_id}",
            cast_to=Campaign,
            body=_campaign_body(
                name=name,
                status=status,
                description=description,
                stop_on_reply=stop_on_reply,
                open_tracking=open_tracking,
                link_tracking=link_tracking,
                text_only=text_only,
                daily_limit=daily_limit,
                unsubscribe_header=unsubscribe_header,
                risky_emails=risky_emails,
                unsubscribe_mode=unsubscribe_mode,
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
                entry_delay_minutes=entry_delay_minutes,
                continuous=continuous,
                tracking_domain=tracking_domain,
                utm_tracking=utm_tracking,
                utm_source=utm_source,
                utm_medium=utm_medium,
                utm_campaign=utm_campaign,
                guardrail_enabled=guardrail_enabled,
                guardrail_bounce_rate_max=guardrail_bounce_rate_max,
                guardrail_complaint_rate_max=guardrail_complaint_rate_max,
                guardrail_reply_rate_min=guardrail_reply_rate_min,
                guardrail_min_sample=guardrail_min_sample,
                guardrail_window_days=guardrail_window_days,
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

    def duplicate(
        self,
        campaign_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Campaign:
        """Create a draft copy of a campaign's configuration.

        The copy carries the settings and the sequence, not the leads or the
        sending history.

        Args:
            campaign_id: The campaign to copy.
            name: A name for the copy. Omitted, the server derives one.
        """
        return self._post(
            f"/campaigns/{campaign_id}/duplicate",
            cast_to=Campaign,
            body=drop_not_given({"name": name}),
            options=options,
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
        self,
        campaign_id: str,
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
        thread_reply: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignStep:
        """Append a step to a campaign's sequence.

        Called with no fields it creates a blank step to fill in later with
        :meth:`update_step`. Any field you pass (the same ones
        :meth:`update_step` takes) is applied to the new step in the same call;
        if the server refuses them, no blank step is left behind.
        """
        body = _step_body(
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
            thread_reply=thread_reply,
        )
        return self._post(
            f"/campaigns/{campaign_id}/steps",
            cast_to=CampaignStep,
            body=body or None,
            options=options,
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
        thread_reply: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignStep:
        """Update a sequence step.

        Args:
            thread_reply: Send this step as a reply in the conversation the first
                email opened instead of starting a new one.
            wait_after: Days to wait before the next step fires.
            kind: The step kind; non-email kinds carry their behaviour in
                *action*.
            action: The action configuration for a non-email step.
            conditions: Branch conditions gating the step. A condition's ``field``
                can be ``reply_intent`` (operator ``is``, the intent in ``label``),
                which matches the intent automatic inbox tagging stored for the
                contact's human reply; like ``ai_label`` it is decided at schedule
                time with no model call.
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
                thread_reply=thread_reply,
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

    # -- linked segments + forms --------------------------------------------
    def list_segments(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignSegments:
        """List the segments linked to a campaign, with live counts."""
        return self._get(
            f"/campaigns/{campaign_id}/segments",
            cast_to=CampaignSegments,
            options=options,
        )

    def set_segments(
        self,
        campaign_id: str,
        *,
        segment_ids: Sequence[str],
        options: RequestOptions | None = None,
    ) -> CampaignSegments:
        """Replace a campaign's linked segments.

        A linked segment is a live audience source: its members are enrolled as
        leads immediately and kept current as the segment changes. This is the
        desired final set, so a retry is safe; pass ``[]`` to detach every
        segment. Detaching a segment withdraws the leads it brought, except those
        the campaign has already written to or that someone added by hand; the
        result reports ``withdrawn`` and ``contacted``.

        Args:
            campaign_id: The campaign id.
            segment_ids: The segments to link, at most 20.
        """
        return self._put(
            f"/campaigns/{campaign_id}/segments",
            cast_to=CampaignSegments,
            body={"segment_ids": list(segment_ids)},
            options=options,
        )

    def list_forms(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignForms:
        """Report how the forms linked from a campaign performed for it."""
        return self._get(
            f"/campaigns/{campaign_id}/forms",
            cast_to=CampaignForms,
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

    # -- scheduled placement test --------------------------------------------
    def placement_monitor(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> PlacementMonitorResult:
        """Read a campaign's scheduled placement test.

        ``data`` is ``None`` when the campaign has no monitor. Requires the
        ``read_campaigns`` scope.
        """
        return self._get(
            f"/campaigns/{campaign_id}/placement-monitor",
            cast_to=PlacementMonitorResult,
            options=options,
        )

    def set_placement_monitor(
        self,
        campaign_id: str,
        *,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        interval_days: NotGivenOr[int] = NOT_GIVEN,
        panel: NotGivenOr[str] = NOT_GIVEN,
        alert_below: NotGivenOr[int] = NOT_GIVEN,
        pause_on_alert: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PlacementMonitorResult:
        """Create or update a campaign's scheduled placement test.

        Fields you leave out keep their stored value, or the default on a new
        monitor. A new or re-enabled monitor runs its first test within minutes.
        Repeating the same call lands on the same state, so no idempotency key is
        needed. Requires the ``send_campaigns`` scope.

        Args:
            enabled: Whether the schedule runs.
            interval_days: Days between tests (the server enforces a range).
            panel: The seed panel: ``instance``, ``workspace`` or ``cloud``.
            alert_below: Raise an alert when placement falls below this percentage
                (0 to 100).
            pause_on_alert: Pause the campaign when the alert fires.
        """
        return self._put(
            f"/campaigns/{campaign_id}/placement-monitor",
            cast_to=PlacementMonitorResult,
            body=drop_not_given(
                {
                    "enabled": enabled,
                    "interval_days": interval_days,
                    "panel": panel,
                    "alert_below": alert_below,
                    "pause_on_alert": pause_on_alert,
                }
            ),
            options=options,
        )

    def delete_placement_monitor(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> PlacementMonitorDeleted:
        """Remove a campaign's scheduled placement test.

        Answers ``404`` when the campaign has no monitor. Requires the
        ``send_campaigns`` scope.
        """
        return self._delete(
            f"/campaigns/{campaign_id}/placement-monitor",
            cast_to=PlacementMonitorDeleted,
            options=options,
        )

    # -- send plan -----------------------------------------------------------
    def send_plan(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignSendPlan:
        """Read today's sending plan: what will go out and every limit behind it.

        Derived on each read through the scheduler's own gates and never stored.
        Requires the ``read_campaigns`` scope.
        """
        return self._get(
            f"/campaigns/{campaign_id}/send-plan",
            cast_to=CampaignSendPlan,
            options=options,
        )

    # -- per-lead hold and CC ------------------------------------------------
    def lead_hold(
        self,
        campaign_id: str,
        contact_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> CampaignLeadHold:
        """Read whether one lead's flow is currently held.

        Requires the ``read_campaigns`` scope.
        """
        return self._get(
            f"/campaigns/{campaign_id}/leads/{contact_id}/hold",
            cast_to=CampaignLeadHold,
            options=options,
        )

    def pause_lead(
        self,
        campaign_id: str,
        contact_id: str,
        *,
        until: NotGivenOr[str | None] = NOT_GIVEN,
        reason: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignLeadHold:
        """Park one contact's flow inside one campaign.

        The contact stays subscribed and stays a lead of the campaign: this is
        not an unsubscribe and not a suppression. Pausing a held lead replaces
        the hold and keeps its start, so a retry is safe. Requires the
        ``write_campaigns`` scope.

        Args:
            until: RFC 3339 time the hold lifts. Omit or pass ``None`` to hold
                with no end, which only :meth:`resume_lead` lifts.
            reason: A note shown beside the hold.
        """
        return self._post(
            f"/campaigns/{campaign_id}/leads/{contact_id}/pause",
            cast_to=CampaignLeadHold,
            body=drop_not_given({"until": until, "reason": reason}),
            options=options,
        )

    def resume_lead(
        self,
        campaign_id: str,
        contact_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> CampaignLeadHold:
        """Lift a lead's hold now.

        Resuming a lead that is not held succeeds; a contact that is not a lead
        of the campaign is a ``404``. Requires the ``write_campaigns`` scope.
        """
        return self._post(
            f"/campaigns/{campaign_id}/leads/{contact_id}/resume",
            cast_to=CampaignLeadHold,
            options=options,
        )

    def lead_cc(
        self,
        campaign_id: str,
        contact_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> CampaignLeadCCList:
        """List the contacts copied on every email to one lead.

        Requires the ``read_campaigns`` and ``read_contacts`` scopes.
        """
        return self._get(
            f"/campaigns/{campaign_id}/leads/{contact_id}/cc",
            cast_to=CampaignLeadCCList,
            options=options,
        )

    def set_lead_cc(
        self,
        campaign_id: str,
        contact_id: str,
        *,
        contact_ids: Sequence[str],
        options: RequestOptions | None = None,
    ) -> CampaignLeadCCList:
        """Replace the contacts copied on one lead.

        The list is the whole new state, so an empty list removes every copy and
        a retry lands on the same state. Requires the ``write_campaigns`` and
        ``read_contacts`` scopes.

        Args:
            contact_ids: The ids of the contacts to copy.
        """
        return self._put(
            f"/campaigns/{campaign_id}/leads/{contact_id}/cc",
            cast_to=CampaignLeadCCList,
            body={"contact_ids": list(contact_ids)},
            options=options,
        )

    def suggest_lead_cc(
        self,
        campaign_id: str,
        contact_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> CampaignLeadCCSuggestions:
        """Suggest likely colleagues of a lead to copy.

        Requires the ``read_campaigns`` and ``read_contacts`` scopes.
        """
        return self._get(
            f"/campaigns/{campaign_id}/leads/{contact_id}/cc/suggestions",
            cast_to=CampaignLeadCCSuggestions,
            options=options,
        )


class AsyncCampaigns(AsyncAPIResource):
    """Asynchronous ``campaigns`` resource."""

    # -- campaign records ----------------------------------------------------
    async def create(
        self,
        *,
        name: str,
        kind: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        stop_on_reply: NotGivenOr[bool] = NOT_GIVEN,
        open_tracking: NotGivenOr[bool] = NOT_GIVEN,
        link_tracking: NotGivenOr[bool] = NOT_GIVEN,
        text_only: NotGivenOr[bool] = NOT_GIVEN,
        daily_limit: NotGivenOr[int] = NOT_GIVEN,
        unsubscribe_header: NotGivenOr[bool] = NOT_GIVEN,
        risky_emails: NotGivenOr[bool] = NOT_GIVEN,
        unsubscribe_mode: NotGivenOr[str] = NOT_GIVEN,
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
        entry_delay_minutes: NotGivenOr[int] = NOT_GIVEN,
        continuous: NotGivenOr[bool] = NOT_GIVEN,
        tracking_domain: NotGivenOr[str] = NOT_GIVEN,
        utm_tracking: NotGivenOr[bool] = NOT_GIVEN,
        utm_source: NotGivenOr[str] = NOT_GIVEN,
        utm_medium: NotGivenOr[str] = NOT_GIVEN,
        utm_campaign: NotGivenOr[str] = NOT_GIVEN,
        guardrail_enabled: NotGivenOr[bool] = NOT_GIVEN,
        guardrail_bounce_rate_max: NotGivenOr[float] = NOT_GIVEN,
        guardrail_complaint_rate_max: NotGivenOr[float] = NOT_GIVEN,
        guardrail_reply_rate_min: NotGivenOr[float] = NOT_GIVEN,
        guardrail_min_sample: NotGivenOr[int] = NOT_GIVEN,
        guardrail_window_days: NotGivenOr[int] = NOT_GIVEN,
        steps: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        variants: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        senders: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        advanced_overrides: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Campaign:
        """Create a campaign.

        Only *name* is required; every other field falls back to a sane
        default, so a minimal ``create(name=...)`` produces a usable draft.

        Args:
            name: A human-readable name for the campaign.
            kind: Retired. One-time campaigns no longer exist on the server, which
                ignores this field; it is still sent if you pass it.
            description: An optional longer description.
            stop_on_reply: Stop sequencing a contact once they reply.
            open_tracking: Enable open tracking.
            link_tracking: Enable link/click tracking.
            text_only: Send plain text only.
            daily_limit: Max emails per day across the campaign.
            unsubscribe_header: Add a ``List-Unsubscribe`` header.
            risky_emails: Allow sending to addresses flagged as risky.
            unsubscribe_mode: The in-body opt-out appended after the signature:
                ``inherit`` (the workspace default), ``text``, ``link`` or ``off``.
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
            contact_order_by: Which contact ordering leads are drawn in.
            contact_order_dir: ``asc`` or ``desc``.
            contact_order_field: A custom field to order by.
            sender_strategy: ``tags`` (senders resolved from *email_tags*) or
                ``explicit`` (the campaign's own sender pool).
            rotation_mode: How volume spreads across the chosen mailboxes.
            ramp_enabled: Ramp the campaign's daily volume up over time.
            ramp_start: The first day's ramp ceiling.
            ramp_increment: How much the ramp ceiling rises each day.
            ramp_ceiling: Where the ramp stops rising.
            esp_match_mode: ESP matching: ``off``, ``prefer`` or ``strict``.
            max_new_leads_per_day: New-lead throttle; ``0`` is unlimited.
            prioritize_new_leads: Send to new leads before continuing older ones.
            entry_delay_minutes: Hold a contact's first email back this many minutes
                after they entered the campaign; ``0`` sends it as soon as it is due.
            continuous: Keep the campaign active when it runs out of leads: it waits,
                idle, for more instead of finishing.
            tracking_domain: A campaign-scoped tracking domain, honored once verified.
            utm_tracking: Append UTM parameters to every link in the body.
            utm_source: The ``utm_source`` value (default ``"warmbly"``).
            utm_medium: The ``utm_medium`` value (default ``"email"``).
            utm_campaign: The ``utm_campaign`` value (default: the campaign name).
            guardrail_enabled: Auto-pause the campaign the moment a rate band is
                breached.
            guardrail_bounce_rate_max: Pause at or above this bounce rate; ``0``
                disables the rule.
            guardrail_complaint_rate_max: Pause at or above this complaint rate; ``0``
                disables the rule.
            guardrail_reply_rate_min: Pause *below* this reply rate; ``0`` disables the
                rule.
            guardrail_min_sample: The smallest sample a guardrail rule will act on.
            guardrail_window_days: The rolling window the rates are measured over.
            steps: Initial sequence steps, in order; they can also be added later with
                :meth:`create_step`.
            variants: A/B variants for the first step.
            senders: The explicit sender pool, for ``sender_strategy="explicit"``.
            advanced_overrides: Per-campaign overrides of the organization's outreach
                settings.
        """
        return await self._post(
            "/campaigns",
            cast_to=Campaign,
            body=_campaign_body(
                for_create=True,
                name=name,
                kind=kind,
                description=description,
                stop_on_reply=stop_on_reply,
                open_tracking=open_tracking,
                link_tracking=link_tracking,
                text_only=text_only,
                daily_limit=daily_limit,
                unsubscribe_header=unsubscribe_header,
                risky_emails=risky_emails,
                unsubscribe_mode=unsubscribe_mode,
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
                entry_delay_minutes=entry_delay_minutes,
                continuous=continuous,
                tracking_domain=tracking_domain,
                utm_tracking=utm_tracking,
                utm_source=utm_source,
                utm_medium=utm_medium,
                utm_campaign=utm_campaign,
                guardrail_enabled=guardrail_enabled,
                guardrail_bounce_rate_max=guardrail_bounce_rate_max,
                guardrail_complaint_rate_max=guardrail_complaint_rate_max,
                guardrail_reply_rate_min=guardrail_reply_rate_min,
                guardrail_min_sample=guardrail_min_sample,
                guardrail_window_days=guardrail_window_days,
                steps=steps,
                variants=variants,
                senders=senders,
                advanced_overrides=advanced_overrides,
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

    async def estimate(
        self,
        *,
        segment_ids: Sequence[str],
        email_tag_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        daily_limit: NotGivenOr[int] = NOT_GIVEN,
        days: NotGivenOr[int] = NOT_GIVEN,
        timezone: NotGivenOr[str] = NOT_GIVEN,
        start_date: NotGivenOr[str] = NOT_GIVEN,
        start_time: NotGivenOr[str] = NOT_GIVEN,
        end_time: NotGivenOr[str] = NOT_GIVEN,
        step_waits: NotGivenOr[Sequence[int]] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignEstimate:
        """Project an audience against a sender pool before a campaign exists.

        Answers "how many people is this, and how long will reaching them
        take" without writing anything.

        Args:
            segment_ids: The segments making up the audience.
            email_tag_ids: Mailbox tags the senders would be drawn from.
            daily_limit: The per-campaign daily cap to project under.
            days: Weekday bitmask for the sending window.
            timezone: IANA timezone the schedule is interpreted in.
            start_date: RFC 3339 date sending would start.
            start_time: Daily sending window start (``"HH:MM"``).
            end_time: Daily sending window end (``"HH:MM"``).
            step_waits: Each follow-up's ``wait_after`` in days, in order (at
                most 30). Omit for a single email.
            campaign_id: Project a saved campaign, filling anything not sent from
                it.
        """
        return await self._post(
            "/campaigns-estimate",
            cast_to=CampaignEstimate,
            body=drop_not_given(
                {
                    "segment_ids": list(segment_ids),
                    "email_tag_ids": email_tag_ids,
                    "daily_limit": daily_limit,
                    "days": days,
                    "timezone": timezone,
                    "start_date": start_date,
                    "start_time": start_time,
                    "end_time": end_time,
                    "step_waits": step_waits,
                    "campaign_id": campaign_id,
                }
            ),
            options=options,
        )

    async def preview_template(
        self,
        *,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        contact: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        account_id: NotGivenOr[str] = NOT_GIVEN,
        step_id: NotGivenOr[str] = NOT_GIVEN,
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
            contact_id: A real contact of the organization to render for,
                instead of the built-in sample. Needs ``read_contacts``.
            campaign_id: The campaign whose opt-out footer, plain-text setting
                and attachments apply.
            account_id: The mailbox whose signature applies, and which is
                reported back as the sender.
            step_id: The step being previewed, so the attachment list is the
                one that step actually sends. Omitted lists the campaign-wide
                files only.
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
                    "contact_id": contact_id,
                    "campaign_id": campaign_id,
                    "account_id": account_id,
                    "step_id": step_id,
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
        status: NotGivenOr[str] = NOT_GIVEN,
        description: NotGivenOr[str] = NOT_GIVEN,
        stop_on_reply: NotGivenOr[bool] = NOT_GIVEN,
        open_tracking: NotGivenOr[bool] = NOT_GIVEN,
        link_tracking: NotGivenOr[bool] = NOT_GIVEN,
        text_only: NotGivenOr[bool] = NOT_GIVEN,
        daily_limit: NotGivenOr[int] = NOT_GIVEN,
        unsubscribe_header: NotGivenOr[bool] = NOT_GIVEN,
        risky_emails: NotGivenOr[bool] = NOT_GIVEN,
        unsubscribe_mode: NotGivenOr[str] = NOT_GIVEN,
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
        entry_delay_minutes: NotGivenOr[int] = NOT_GIVEN,
        continuous: NotGivenOr[bool] = NOT_GIVEN,
        tracking_domain: NotGivenOr[str] = NOT_GIVEN,
        utm_tracking: NotGivenOr[bool] = NOT_GIVEN,
        utm_source: NotGivenOr[str] = NOT_GIVEN,
        utm_medium: NotGivenOr[str] = NOT_GIVEN,
        utm_campaign: NotGivenOr[str] = NOT_GIVEN,
        guardrail_enabled: NotGivenOr[bool] = NOT_GIVEN,
        guardrail_bounce_rate_max: NotGivenOr[float] = NOT_GIVEN,
        guardrail_complaint_rate_max: NotGivenOr[float] = NOT_GIVEN,
        guardrail_reply_rate_min: NotGivenOr[float] = NOT_GIVEN,
        guardrail_min_sample: NotGivenOr[int] = NOT_GIVEN,
        guardrail_window_days: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Campaign:
        """Update a campaign.

        The explicit sender *list* is edited with :meth:`set_senders`; only the
        strategy and rotation toggles ride this call.

        Args:
            campaign_id: The campaign id.
            name: A new name for the campaign.
            status: The campaign status to move to.
            description: An optional longer description.
            stop_on_reply: Stop sequencing a contact once they reply.
            open_tracking: Enable open tracking.
            link_tracking: Enable link/click tracking.
            text_only: Send plain text only.
            daily_limit: Max emails per day across the campaign.
            unsubscribe_header: Add a ``List-Unsubscribe`` header.
            risky_emails: Allow sending to addresses flagged as risky.
            unsubscribe_mode: The in-body opt-out appended after the signature:
                ``inherit`` (the workspace default), ``text``, ``link`` or ``off``.
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
            contact_order_by: Which contact ordering leads are drawn in.
            contact_order_dir: ``asc`` or ``desc``.
            contact_order_field: A custom field to order by.
            sender_strategy: ``tags`` (senders resolved from *email_tags*) or
                ``explicit`` (the campaign's own sender pool).
            rotation_mode: How volume spreads across the chosen mailboxes.
            ramp_enabled: Ramp the campaign's daily volume up over time.
            ramp_start: The first day's ramp ceiling.
            ramp_increment: How much the ramp ceiling rises each day.
            ramp_ceiling: Where the ramp stops rising.
            esp_match_mode: ESP matching: ``off``, ``prefer`` or ``strict``.
            max_new_leads_per_day: New-lead throttle; ``0`` is unlimited.
            prioritize_new_leads: Send to new leads before continuing older ones.
            entry_delay_minutes: Hold a contact's first email back this many minutes
                after they entered the campaign; ``0`` sends it as soon as it is due.
            continuous: Keep the campaign active when it runs out of leads: it waits,
                idle, for more instead of finishing.
            tracking_domain: A campaign-scoped tracking domain, honored once verified.
            utm_tracking: Append UTM parameters to every link in the body.
            utm_source: The ``utm_source`` value (default ``"warmbly"``).
            utm_medium: The ``utm_medium`` value (default ``"email"``).
            utm_campaign: The ``utm_campaign`` value (default: the campaign name).
            guardrail_enabled: Auto-pause the campaign the moment a rate band is
                breached.
            guardrail_bounce_rate_max: Pause at or above this bounce rate; ``0``
                disables the rule.
            guardrail_complaint_rate_max: Pause at or above this complaint rate; ``0``
                disables the rule.
            guardrail_reply_rate_min: Pause *below* this reply rate; ``0`` disables the
                rule.
            guardrail_min_sample: The smallest sample a guardrail rule will act on.
            guardrail_window_days: The rolling window the rates are measured over.
        """
        return await self._patch(
            f"/campaigns/{campaign_id}",
            cast_to=Campaign,
            body=_campaign_body(
                name=name,
                status=status,
                description=description,
                stop_on_reply=stop_on_reply,
                open_tracking=open_tracking,
                link_tracking=link_tracking,
                text_only=text_only,
                daily_limit=daily_limit,
                unsubscribe_header=unsubscribe_header,
                risky_emails=risky_emails,
                unsubscribe_mode=unsubscribe_mode,
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
                entry_delay_minutes=entry_delay_minutes,
                continuous=continuous,
                tracking_domain=tracking_domain,
                utm_tracking=utm_tracking,
                utm_source=utm_source,
                utm_medium=utm_medium,
                utm_campaign=utm_campaign,
                guardrail_enabled=guardrail_enabled,
                guardrail_bounce_rate_max=guardrail_bounce_rate_max,
                guardrail_complaint_rate_max=guardrail_complaint_rate_max,
                guardrail_reply_rate_min=guardrail_reply_rate_min,
                guardrail_min_sample=guardrail_min_sample,
                guardrail_window_days=guardrail_window_days,
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

    async def duplicate(
        self,
        campaign_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Campaign:
        """Create a draft copy of a campaign's configuration.

        The copy carries the settings and the sequence, not the leads or the
        sending history.

        Args:
            campaign_id: The campaign to copy.
            name: A name for the copy. Omitted, the server derives one.
        """
        return await self._post(
            f"/campaigns/{campaign_id}/duplicate",
            cast_to=Campaign,
            body=drop_not_given({"name": name}),
            options=options,
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
        self,
        campaign_id: str,
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
        thread_reply: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignStep:
        """Append a step to a campaign's sequence.

        Called with no fields it creates a blank step to fill in later with
        :meth:`update_step`. Any field you pass (the same ones
        :meth:`update_step` takes) is applied to the new step in the same call;
        if the server refuses them, no blank step is left behind.
        """
        body = _step_body(
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
            thread_reply=thread_reply,
        )
        return await self._post(
            f"/campaigns/{campaign_id}/steps",
            cast_to=CampaignStep,
            body=body or None,
            options=options,
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
        thread_reply: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignStep:
        """Update a sequence step.

        Args:
            thread_reply: Send this step as a reply in the conversation the first
                email opened instead of starting a new one.
            wait_after: Days to wait before the next step fires.
            kind: The step kind; non-email kinds carry their behaviour in
                *action*.
            action: The action configuration for a non-email step.
            conditions: Branch conditions gating the step. A condition's ``field``
                can be ``reply_intent`` (operator ``is``, the intent in ``label``),
                which matches the intent automatic inbox tagging stored for the
                contact's human reply; like ``ai_label`` it is decided at schedule
                time with no model call.
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
                thread_reply=thread_reply,
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

    # -- linked segments + forms --------------------------------------------
    async def list_segments(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignSegments:
        """List the segments linked to a campaign, with live counts."""
        return await self._get(
            f"/campaigns/{campaign_id}/segments",
            cast_to=CampaignSegments,
            options=options,
        )

    async def set_segments(
        self,
        campaign_id: str,
        *,
        segment_ids: Sequence[str],
        options: RequestOptions | None = None,
    ) -> CampaignSegments:
        """Replace a campaign's linked segments.

        A linked segment is a live audience source: its members are enrolled as
        leads immediately and kept current as the segment changes. This is the
        desired final set, so a retry is safe; pass ``[]`` to detach every
        segment. Detaching a segment withdraws the leads it brought, except those
        the campaign has already written to or that someone added by hand; the
        result reports ``withdrawn`` and ``contacted``.

        Args:
            campaign_id: The campaign id.
            segment_ids: The segments to link, at most 20.
        """
        return await self._put(
            f"/campaigns/{campaign_id}/segments",
            cast_to=CampaignSegments,
            body={"segment_ids": list(segment_ids)},
            options=options,
        )

    async def list_forms(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignForms:
        """Report how the forms linked from a campaign performed for it."""
        return await self._get(
            f"/campaigns/{campaign_id}/forms",
            cast_to=CampaignForms,
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

    # -- scheduled placement test --------------------------------------------
    async def placement_monitor(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> PlacementMonitorResult:
        """Read a campaign's scheduled placement test.

        ``data`` is ``None`` when the campaign has no monitor. Requires the
        ``read_campaigns`` scope.
        """
        return await self._get(
            f"/campaigns/{campaign_id}/placement-monitor",
            cast_to=PlacementMonitorResult,
            options=options,
        )

    async def set_placement_monitor(
        self,
        campaign_id: str,
        *,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        interval_days: NotGivenOr[int] = NOT_GIVEN,
        panel: NotGivenOr[str] = NOT_GIVEN,
        alert_below: NotGivenOr[int] = NOT_GIVEN,
        pause_on_alert: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PlacementMonitorResult:
        """Create or update a campaign's scheduled placement test.

        Fields you leave out keep their stored value, or the default on a new
        monitor. A new or re-enabled monitor runs its first test within minutes.
        Repeating the same call lands on the same state, so no idempotency key is
        needed. Requires the ``send_campaigns`` scope.

        Args:
            enabled: Whether the schedule runs.
            interval_days: Days between tests (the server enforces a range).
            panel: The seed panel: ``instance``, ``workspace`` or ``cloud``.
            alert_below: Raise an alert when placement falls below this percentage
                (0 to 100).
            pause_on_alert: Pause the campaign when the alert fires.
        """
        return await self._put(
            f"/campaigns/{campaign_id}/placement-monitor",
            cast_to=PlacementMonitorResult,
            body=drop_not_given(
                {
                    "enabled": enabled,
                    "interval_days": interval_days,
                    "panel": panel,
                    "alert_below": alert_below,
                    "pause_on_alert": pause_on_alert,
                }
            ),
            options=options,
        )

    async def delete_placement_monitor(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> PlacementMonitorDeleted:
        """Remove a campaign's scheduled placement test.

        Answers ``404`` when the campaign has no monitor. Requires the
        ``send_campaigns`` scope.
        """
        return await self._delete(
            f"/campaigns/{campaign_id}/placement-monitor",
            cast_to=PlacementMonitorDeleted,
            options=options,
        )

    # -- send plan -----------------------------------------------------------
    async def send_plan(
        self, campaign_id: str, *, options: RequestOptions | None = None
    ) -> CampaignSendPlan:
        """Read today's sending plan: what will go out and every limit behind it.

        Derived on each read through the scheduler's own gates and never stored.
        Requires the ``read_campaigns`` scope.
        """
        return await self._get(
            f"/campaigns/{campaign_id}/send-plan",
            cast_to=CampaignSendPlan,
            options=options,
        )

    # -- per-lead hold and CC ------------------------------------------------
    async def lead_hold(
        self,
        campaign_id: str,
        contact_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> CampaignLeadHold:
        """Read whether one lead's flow is currently held.

        Requires the ``read_campaigns`` scope.
        """
        return await self._get(
            f"/campaigns/{campaign_id}/leads/{contact_id}/hold",
            cast_to=CampaignLeadHold,
            options=options,
        )

    async def pause_lead(
        self,
        campaign_id: str,
        contact_id: str,
        *,
        until: NotGivenOr[str | None] = NOT_GIVEN,
        reason: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> CampaignLeadHold:
        """Park one contact's flow inside one campaign.

        The contact stays subscribed and stays a lead of the campaign: this is
        not an unsubscribe and not a suppression. Pausing a held lead replaces
        the hold and keeps its start, so a retry is safe. Requires the
        ``write_campaigns`` scope.

        Args:
            until: RFC 3339 time the hold lifts. Omit or pass ``None`` to hold
                with no end, which only :meth:`resume_lead` lifts.
            reason: A note shown beside the hold.
        """
        return await self._post(
            f"/campaigns/{campaign_id}/leads/{contact_id}/pause",
            cast_to=CampaignLeadHold,
            body=drop_not_given({"until": until, "reason": reason}),
            options=options,
        )

    async def resume_lead(
        self,
        campaign_id: str,
        contact_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> CampaignLeadHold:
        """Lift a lead's hold now.

        Resuming a lead that is not held succeeds; a contact that is not a lead
        of the campaign is a ``404``. Requires the ``write_campaigns`` scope.
        """
        return await self._post(
            f"/campaigns/{campaign_id}/leads/{contact_id}/resume",
            cast_to=CampaignLeadHold,
            options=options,
        )

    async def lead_cc(
        self,
        campaign_id: str,
        contact_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> CampaignLeadCCList:
        """List the contacts copied on every email to one lead.

        Requires the ``read_campaigns`` and ``read_contacts`` scopes.
        """
        return await self._get(
            f"/campaigns/{campaign_id}/leads/{contact_id}/cc",
            cast_to=CampaignLeadCCList,
            options=options,
        )

    async def set_lead_cc(
        self,
        campaign_id: str,
        contact_id: str,
        *,
        contact_ids: Sequence[str],
        options: RequestOptions | None = None,
    ) -> CampaignLeadCCList:
        """Replace the contacts copied on one lead.

        The list is the whole new state, so an empty list removes every copy and
        a retry lands on the same state. Requires the ``write_campaigns`` and
        ``read_contacts`` scopes.

        Args:
            contact_ids: The ids of the contacts to copy.
        """
        return await self._put(
            f"/campaigns/{campaign_id}/leads/{contact_id}/cc",
            cast_to=CampaignLeadCCList,
            body={"contact_ids": list(contact_ids)},
            options=options,
        )

    async def suggest_lead_cc(
        self,
        campaign_id: str,
        contact_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> CampaignLeadCCSuggestions:
        """Suggest likely colleagues of a lead to copy.

        Requires the ``read_campaigns`` and ``read_contacts`` scopes.
        """
        return await self._get(
            f"/campaigns/{campaign_id}/leads/{contact_id}/cc/suggestions",
            cast_to=CampaignLeadCCSuggestions,
            options=options,
        )
