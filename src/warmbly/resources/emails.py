"""The ``emails`` resource: manage email accounts (mailboxes).

Maps to the ``/v1/emails`` route group. An :class:`EmailAccount` is a connected
mailbox (Gmail, Outlook, or SMTP/IMAP) that campaigns send from and that the
warmup engine drives. This resource covers account settings, tracking-domain
configuration, warmup control (start/pause/resume/stop, ban status, appeals),
deliverability auth checks, address verification, bulk tagging, and sending a
one-off email from an account.

Connecting a *new* mailbox is a session-only onboarding flow
(``/v1/emails/onboarding/*``) that writes user-encrypted secrets, so it is not
reachable with an API key or OAuth token and is deliberately absent here.
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
    "AsyncEmails",
    "BulkTagResult",
    "EmailAccount",
    "EmailAccountDeleted",
    "EmailAuthCheck",
    "EmailSendResult",
    "EmailVerification",
    "Emails",
    "MailboxAllowance",
    "MailboxSync",
    "MailboxSyncPolicy",
    "MailboxSyncState",
    "SendLifecycleState",
    "SendingBehavior",
    "SendingBehaviorPlan",
    "TrackingDomainStatus",
    "WarmupAppeal",
    "WarmupBanStatus",
]


class EmailAccount(BaseModel):
    """A connected email account (mailbox).

    ``warmup`` is the timestamp warmup was started at, or ``None`` when warmup
    is off — not a boolean.
    """

    id: str
    user_id: str | None = None
    organization_id: str | None = None
    worker_id: str | None = None
    email: str | None = None
    name: str | None = None
    provider: str | None = None
    status: str | None = None
    signature_plain: str | None = None
    signature_html: str | None = None
    signature_sync: bool | None = None
    signature_code: bool | None = None
    campaign_limit: int | None = None
    min_wait_time: int | None = None
    reply_to: str | None = None
    tracking_domain: str | None = None
    tracking_domain_verified: bool | None = None
    tracking_domain_verified_at: str | None = None
    auth_state: str | None = None
    auth_spf: bool | None = None
    auth_dkim: bool | None = None
    auth_dmarc: bool | None = None
    auth_dmarc_policy: str | None = None
    auth_reason: str | None = None
    auth_checked_at: str | None = None
    auth_failing_since: str | None = None
    save_to_sent: bool | None = None
    warmup: str | None = None
    warmup_paused_at: str | None = None
    warmup_base: int | None = None
    warmup_max: int | None = None
    warmup_increase: int | None = None
    warmup_reply_rate: int | None = None
    warmup_tag: str | None = None
    warmup_pool_type: str | None = None
    warmup_start_time: str | None = None
    warmup_end_time: str | None = None
    warmup_days: int | None = None
    timezone: str | None = None
    tags: Sequence[str] = []
    last_synced_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class EmailAccountDeleted(BaseModel):
    """The result of deleting an email account (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class TrackingDomainStatus(BaseModel):
    """The tracking-domain configuration and verification state.

    ``cname_target`` is the host this install expects the CNAME to point at.
    ``status`` is stable and machine-readable — ``verified``, ``unset``,
    ``no_target``, ``not_found``, ``wrong_target``, ``lookup_error``, or
    ``pending`` when the value is stored state rather than a fresh lookup —
    and ``observed`` is what DNS actually returned, so a customer can spot
    their own typo. ``tracking_host_unresolvable`` means the record is right
    but this install's own tracking host does not resolve, which is an
    operator problem rather than a customer one.
    """

    tracking_domain: str | None = None
    tracking_domain_verified: bool | None = None
    tracking_domain_verified_at: str | None = None
    cname_target: str | None = None
    status: str | None = None
    message: str | None = None
    observed: str | None = None
    tracking_host_unresolvable: bool | None = None


class EmailAuthCheck(BaseModel):
    """The result of a deliverability authentication check for an account."""

    auth_state: str | None = None
    spf: bool | None = None
    dkim: bool | None = None
    dmarc: bool | None = None
    dmarc_policy: str | None = None
    reason: str | None = None
    checked_at: str | None = None


class EmailVerification(BaseModel):
    """The result of verifying an email address (syntax, MX, SMTP probe)."""

    email: str | None = None
    valid: bool | None = None
    deliverable: bool | None = None
    catch_all: bool | None = None
    reason: str | None = None
    status: str | None = None


class WarmupBanStatus(BaseModel):
    """Whether the warmup pool has blocked an account, and why.

    ``blocked_until`` is when the block lapses on its own, and
    ``pending_appeal`` is ``True`` while an appeal is awaiting review — in
    which case a second :meth:`Emails.warmup_appeal` is refused.
    """

    email_account_id: str | None = None
    blocked: bool | None = None
    health_state: str | None = None
    reason: str | None = None
    blocked_at: str | None = None
    blocked_until: str | None = None
    can_appeal: bool | None = None
    pending_appeal: bool | None = None


class WarmupAppeal(BaseModel):
    """The result of submitting a warmup ban appeal."""

    appeal_id: str | None = None


class BulkTagResult(BaseModel):
    """The result of a bulk tag add/remove."""

    updated: int | None = None


class EmailSendResult(BaseModel):
    """The result of queueing a one-off send from an account.

    Sends are queued as tasks, so ``task_id`` identifies the queued work and
    ``scheduled_at`` is when it fires.
    """

    task_id: str | None = None
    scheduled_at: str | None = None
    send_mode: str | None = None


class MailboxAllowance(BaseModel):
    """How many mailboxes the workspace may hold, and why.

    ``allowance`` and ``remaining`` are ``None`` when the workspace is
    unlimited. ``basis`` explains the number: ``unlimited``, ``free`` (an
    unsubscribed workspace), ``override`` (an operator-approved increase),
    ``plan`` (the plan carries an explicit mailbox column), or ``fair_use``
    (the plan's daily sends divided by ``sends_per_mailbox``).
    """

    used: int | None = None
    allowance: int | None = None
    remaining: int | None = None
    basis: str | None = None
    sends_per_mailbox: int | None = None
    plan_daily_sends: int | None = None
    plan_name: str | None = None
    paid: bool | None = None
    pending_request: dict[str, Any] | None = None


class SendLifecycleState(BaseModel):
    """Whether a mailbox is offered to cold sending.

    ``state`` is ``active`` (in rotation), ``resting`` (pulled out to recover
    on warmup traffic alone, and returning on its own once it has), or
    ``reserve`` (held back by its owner, and never entered or left
    automatically).
    """

    state: str | None = None
    since: str | None = None
    reason: str | None = None


class MailboxSyncState(BaseModel):
    """The worker's most recent report of a mailbox's sync.

    ``throttle_reason`` names which budget is exhausted while
    ``throttled_until`` is set: ``burst``, ``hourly``, ``daily``,
    ``org_daily`` or ``priority_daily``.
    """

    backfill_status: str | None = None
    backfill_synced: int | None = None
    backfill_since: str | None = None
    backfill_started_at: str | None = None
    backfill_completed_at: str | None = None
    throttled_until: str | None = None
    throttle_reason: str | None = None
    deferred: int | None = None
    last_synced_at: str | None = None


class MailboxSyncPolicy(BaseModel):
    """The fair-use budget a mailbox syncs under.

    Resolved from the instance settings when the mailbox was loaded onto a
    worker, so a policy change reaches a mailbox on its next load.
    """

    backfill_days: int | None = None
    backfill_messages: int | None = None
    daily_messages: int | None = None
    org_daily_messages: int | None = None


class MailboxSync(BaseModel):
    """Where a mailbox's import stands, and the budget it runs under.

    ``state`` is ``None`` until the worker has reported once.
    """

    state: MailboxSyncState | None = None
    policy: MailboxSyncPolicy | None = None


class SendingBehavior(BaseModel):
    """A mailbox's human sending-behaviour profile.

    These are the *ranges* a mailbox rolls its workday from, not the rolled
    values: see :class:`SendingBehaviorPlan` for the day it actually rolled.
    Every minute-of-day value is minutes since local midnight in the mailbox's
    own timezone, and ``weekdays`` is a Monday-indexed bitmask (bit 0 is
    Monday, so ``31`` is Mon-Fri).
    """

    email_account_id: str | None = None
    enabled: bool | None = None
    daily_limit_min: int | None = None
    daily_limit_max: int | None = None
    hourly_limit_min: int | None = None
    hourly_limit_max: int | None = None
    gap_min_seconds: int | None = None
    gap_max_seconds: int | None = None
    work_start_min: int | None = None
    work_start_max: int | None = None
    work_end_min: int | None = None
    work_end_max: int | None = None
    lunch_enabled: bool | None = None
    lunch_earliest: int | None = None
    lunch_latest: int | None = None
    lunch_min_minutes: int | None = None
    lunch_max_minutes: int | None = None
    weekdays: int | None = None
    timezone: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SendingBehaviorPlan(BaseModel):
    """The workday a mailbox actually rolled for the current local date.

    Rolled once per local day and never updated, so every scheduling pass
    through the day reads the same numbers. This is the read that answers "why
    is nothing sending right now": ``remaining_today`` is what the plan still
    allows, and ``lunch_start_minute`` / ``lunch_end_minute`` are ``None`` on a
    day with no break.
    """

    email_account_id: str | None = None
    plan_date: str | None = None
    timezone: str | None = None
    is_working_day: bool | None = None
    daily_limit: int | None = None
    hourly_limit: int | None = None
    work_start_minute: int | None = None
    work_end_minute: int | None = None
    lunch_start_minute: int | None = None
    lunch_end_minute: int | None = None
    gap_min_seconds: int | None = None
    gap_max_seconds: int | None = None
    sent_today: int | None = None
    remaining_today: int | None = None
    behavior: SendingBehavior | None = None
    created_at: str | None = None


def _behavior_body(
    *,
    enabled: NotGivenOr[bool],
    daily_limit_min: NotGivenOr[int],
    daily_limit_max: NotGivenOr[int],
    hourly_limit_min: NotGivenOr[int],
    hourly_limit_max: NotGivenOr[int],
    gap_min_seconds: NotGivenOr[int],
    gap_max_seconds: NotGivenOr[int],
    work_start_min: NotGivenOr[int],
    work_start_max: NotGivenOr[int],
    work_end_min: NotGivenOr[int],
    work_end_max: NotGivenOr[int],
    lunch_enabled: NotGivenOr[bool],
    lunch_earliest: NotGivenOr[int],
    lunch_latest: NotGivenOr[int],
    lunch_min_minutes: NotGivenOr[int],
    lunch_max_minutes: NotGivenOr[int],
    weekdays: NotGivenOr[int],
) -> dict[str, Any]:
    """Build the behaviour-profile patch; omitted fields keep their value."""
    return drop_not_given(
        {
            "enabled": enabled,
            "daily_limit_min": daily_limit_min,
            "daily_limit_max": daily_limit_max,
            "hourly_limit_min": hourly_limit_min,
            "hourly_limit_max": hourly_limit_max,
            "gap_min_seconds": gap_min_seconds,
            "gap_max_seconds": gap_max_seconds,
            "work_start_min": work_start_min,
            "work_start_max": work_start_max,
            "work_end_min": work_end_min,
            "work_end_max": work_end_max,
            "lunch_enabled": lunch_enabled,
            "lunch_earliest": lunch_earliest,
            "lunch_latest": lunch_latest,
            "lunch_min_minutes": lunch_min_minutes,
            "lunch_max_minutes": lunch_max_minutes,
            "weekdays": weekdays,
        }
    )


def _update_body(
    *,
    name: NotGivenOr[str],
    status: NotGivenOr[str],
    reply_to: NotGivenOr[str],
    timezone: NotGivenOr[str],
    tags: NotGivenOr[Sequence[str]],
    campaign_limit: NotGivenOr[int],
    min_wait_time: NotGivenOr[int],
    signature_plain: NotGivenOr[str],
    signature_html: NotGivenOr[str],
    signature_sync: NotGivenOr[bool],
    signature_code: NotGivenOr[bool],
    save_to_sent: NotGivenOr[bool],
    warmup: NotGivenOr[bool],
    warmup_base: NotGivenOr[int],
    warmup_max: NotGivenOr[int],
    warmup_increase: NotGivenOr[int],
    warmup_reply_rate: NotGivenOr[int],
    warmup_tag: NotGivenOr[str],
    warmup_start_time: NotGivenOr[str],
    warmup_end_time: NotGivenOr[str],
    warmup_days: NotGivenOr[int],
) -> dict[str, Any]:
    return drop_not_given(
        {
            "name": name,
            "status": status,
            "reply_to": reply_to,
            "timezone": timezone,
            "tags": tags,
            "campaign_limit": campaign_limit,
            "min_wait_time": min_wait_time,
            "signature_plain": signature_plain,
            "signature_html": signature_html,
            "signature_sync": signature_sync,
            "signature_code": signature_code,
            "save_to_sent": save_to_sent,
            "warmup": warmup,
            "warmup_base": warmup_base,
            "warmup_max": warmup_max,
            "warmup_increase": warmup_increase,
            "warmup_reply_rate": warmup_reply_rate,
            "warmup_tag": warmup_tag,
            "warmup_start_time": warmup_start_time,
            "warmup_end_time": warmup_end_time,
            "warmup_days": warmup_days,
        }
    )


def _send_body(
    *,
    to: Sequence[str],
    subject: str,
    body_html: NotGivenOr[str],
    body_plain: NotGivenOr[str],
    cc: NotGivenOr[Sequence[str]],
    bcc: NotGivenOr[Sequence[str]],
    in_reply_to: NotGivenOr[Sequence[str]],
    thread_id: NotGivenOr[str],
    send_mode: NotGivenOr[str],
    scheduled_at: NotGivenOr[str],
) -> dict[str, Any]:
    return drop_not_given(
        {
            "to": list(to),
            "cc": cc,
            "bcc": bcc,
            "subject": subject,
            "body_html": body_html,
            "body_plain": body_plain,
            "in_reply_to": in_reply_to,
            "thread_id": thread_id,
            "send_mode": send_mode,
            "scheduled_at": scheduled_at,
        }
    )


class Emails(SyncAPIResource):
    """Synchronous ``emails`` resource."""

    def list(
        self,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        tag: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[EmailAccount]:
        """List connected email accounts (auto-paginating).

        Args:
            q: Search string matched against the address and display name.
            tag: Restrict to accounts carrying this tag.
            limit: Maximum number of accounts per page.
            cursor: Opaque pagination cursor from a previous page.
            options: Per-request overrides.
        """
        return self._get_api_list(
            "/emails",
            model=EmailAccount,
            query={"q": q, "tag": tag, "limit": limit, "cursor": cursor},
            options=options,
        )

    def retrieve(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccount:
        """Retrieve a single email account by id."""
        return self._get(f"/emails/{email_id}", cast_to=EmailAccount, options=options)

    def update(
        self,
        email_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        reply_to: NotGivenOr[str] = NOT_GIVEN,
        timezone: NotGivenOr[str] = NOT_GIVEN,
        tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        campaign_limit: NotGivenOr[int] = NOT_GIVEN,
        min_wait_time: NotGivenOr[int] = NOT_GIVEN,
        signature_plain: NotGivenOr[str] = NOT_GIVEN,
        signature_html: NotGivenOr[str] = NOT_GIVEN,
        signature_sync: NotGivenOr[bool] = NOT_GIVEN,
        signature_code: NotGivenOr[bool] = NOT_GIVEN,
        save_to_sent: NotGivenOr[bool] = NOT_GIVEN,
        warmup: NotGivenOr[bool] = NOT_GIVEN,
        warmup_base: NotGivenOr[int] = NOT_GIVEN,
        warmup_max: NotGivenOr[int] = NOT_GIVEN,
        warmup_increase: NotGivenOr[int] = NOT_GIVEN,
        warmup_reply_rate: NotGivenOr[int] = NOT_GIVEN,
        warmup_tag: NotGivenOr[str] = NOT_GIVEN,
        warmup_start_time: NotGivenOr[str] = NOT_GIVEN,
        warmup_end_time: NotGivenOr[str] = NOT_GIVEN,
        warmup_days: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> EmailAccount:
        """Update an account's settings.

        Args:
            email_id: The account id.
            name: A new display name.
            status: ``"active"``, ``"inactive"``, or ``"revoked"``.
            reply_to: A ``Reply-To`` address for sends from this mailbox.
            timezone: An IANA timezone (e.g. ``"America/New_York"``).
            tags: Replacement list of tags.
            campaign_limit: Max campaign emails per day from this mailbox.
            min_wait_time: Minimum minutes between sends.
            signature_plain: Plain-text signature.
            signature_html: HTML signature.
            signature_sync: Keep the signature in sync with the provider.
            signature_code: Treat the HTML signature as raw code.
            save_to_sent: Copy sends from this mailbox into its Sent folder.
            warmup: Enable or disable warmup.
            warmup_base: Warmup emails per day at the start of the ramp.
            warmup_max: Warmup emails per day at the top of the ramp.
            warmup_increase: Daily ramp increment.
            warmup_reply_rate: Target warmup reply rate, as a percentage.
            warmup_tag: The warmup pool tag.
            warmup_start_time: Daily warmup window start (``"HH:MM"``).
            warmup_end_time: Daily warmup window end (``"HH:MM"``).
            warmup_days: Number of days in the warmup week.
            options: Per-request overrides.
        """
        return self._patch(
            f"/emails/{email_id}",
            cast_to=EmailAccount,
            body=_update_body(
                name=name,
                status=status,
                reply_to=reply_to,
                timezone=timezone,
                tags=tags,
                campaign_limit=campaign_limit,
                min_wait_time=min_wait_time,
                signature_plain=signature_plain,
                signature_html=signature_html,
                signature_sync=signature_sync,
                signature_code=signature_code,
                save_to_sent=save_to_sent,
                warmup=warmup,
                warmup_base=warmup_base,
                warmup_max=warmup_max,
                warmup_increase=warmup_increase,
                warmup_reply_rate=warmup_reply_rate,
                warmup_tag=warmup_tag,
                warmup_start_time=warmup_start_time,
                warmup_end_time=warmup_end_time,
                warmup_days=warmup_days,
            ),
            options=options,
        )

    def delete(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccountDeleted:
        """Disconnect and delete an email account."""
        return self._delete(
            f"/emails/{email_id}", cast_to=EmailAccountDeleted, options=options
        )

    def bulk_tag(
        self,
        *,
        email_ids: Sequence[str],
        add_tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        remove_tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> BulkTagResult:
        """Add and/or remove tags across many mailboxes at once.

        Set semantics, so the call is naturally idempotent.

        Args:
            email_ids: The mailboxes to update (max 1000).
            add_tags: Tags to add (max 100).
            remove_tags: Tags to remove (max 100).
        """
        return self._patch(
            "/emails/tags",
            cast_to=BulkTagResult,
            body=drop_not_given(
                {
                    "email_ids": list(email_ids),
                    "add_tags": add_tags,
                    "remove_tags": remove_tags,
                }
            ),
            options=options,
        )

    def track(
        self,
        email_id: str,
        *,
        domain: str,
        options: RequestOptions | None = None,
    ) -> TrackingDomainStatus:
        """Set the custom open/click tracking domain for an account.

        Args:
            email_id: The account id.
            domain: The custom tracking domain. Pass an empty string to clear
                it and fall back to the shared domain.
        """
        return self._patch(
            f"/emails/{email_id}/track",
            cast_to=TrackingDomainStatus,
            query={"domain": domain},
            options=options,
        )

    def warmup_start(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccount:
        """Start warmup for an account."""
        return self._post(
            f"/emails/{email_id}/warmup/start", cast_to=EmailAccount, options=options
        )

    def warmup_pause(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccount:
        """Pause warmup for an account."""
        return self._post(
            f"/emails/{email_id}/warmup/pause", cast_to=EmailAccount, options=options
        )

    def warmup_resume(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccount:
        """Resume a paused warmup for an account."""
        return self._post(
            f"/emails/{email_id}/warmup/resume", cast_to=EmailAccount, options=options
        )

    def warmup_stop(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccount:
        """Stop warmup for an account."""
        return self._post(
            f"/emails/{email_id}/warmup/stop", cast_to=EmailAccount, options=options
        )

    def warmup_ban_status(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> WarmupBanStatus:
        """Get the warmup ban / blocklist status for an account."""
        return self._get(
            f"/emails/{email_id}/warmup/ban-status",
            cast_to=WarmupBanStatus,
            options=options,
        )

    def warmup_appeal(
        self,
        email_id: str,
        *,
        reason: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> WarmupAppeal:
        """Appeal a warmup ban.

        Args:
            email_id: The account id.
            reason: An explanation supporting the appeal.
        """
        return self._post(
            f"/emails/{email_id}/warmup/appeal",
            cast_to=WarmupAppeal,
            body=drop_not_given({"reason": reason}),
            options=options,
        )

    def auth_check(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAuthCheck:
        """Run a deliverability authentication check (SPF/DKIM/DMARC)."""
        return self._get(
            f"/emails/{email_id}/auth-check",
            cast_to=EmailAuthCheck,
            options=options,
        )

    def refresh_auth_check(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAuthCheck:
        """Re-run the authentication check and record the verdict.

        Recording it is what lifts the cold-send and warmup gate, so this needs
        a write scope where :meth:`auth_check` only needs a read.
        """
        return self._post(
            f"/emails/{email_id}/auth-check",
            cast_to=EmailAuthCheck,
            options=options,
        )

    def tracking_domain(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> TrackingDomainStatus:
        """Read the mailbox's tracking-domain state and the CNAME target.

        Does no DNS work; :meth:`verify_tracking_domain` is the live check.
        """
        return self._get(
            f"/emails/{email_id}/track",
            cast_to=TrackingDomainStatus,
            options=options,
        )

    def verify_tracking_domain(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> TrackingDomainStatus:
        """Re-resolve the stored tracking domain and persist the verdict."""
        return self._post(
            f"/emails/{email_id}/track/verify",
            cast_to=TrackingDomainStatus,
            options=options,
        )

    def hold(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> SendLifecycleState:
        """Take the mailbox out of campaign sending until it is released.

        Warmup is untouched, so the mailbox keeps its reputation while it sits
        out. Bodyless and idempotent.
        """
        return self._post(
            f"/emails/{email_id}/hold", cast_to=SendLifecycleState, options=options
        )

    def release(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> SendLifecycleState:
        """Put a held or resting mailbox back into campaign rotation.

        Where it lands is up to its warmup health: an unhealthy mailbox comes
        back as ``resting`` rather than ``active``.
        """
        return self._post(
            f"/emails/{email_id}/release", cast_to=SendLifecycleState, options=options
        )

    def sync(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> MailboxSync:
        """Report where the mailbox's import stands and what is holding it."""
        return self._get(
            f"/emails/{email_id}/sync", cast_to=MailboxSync, options=options
        )

    def allowance(self, *, options: RequestOptions | None = None) -> MailboxAllowance:
        """Report how many mailboxes the workspace holds and may hold."""
        return self._get("/emails/allowance", cast_to=MailboxAllowance, options=options)

    def behavior(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> SendingBehavior:
        """Read a mailbox's sending-behaviour profile.

        A mailbox that has never been configured reads back the defaults, so
        the object is always complete.
        """
        return self._get(
            f"/emails/{email_id}/behavior", cast_to=SendingBehavior, options=options
        )

    def update_behavior(
        self,
        email_id: str,
        *,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        daily_limit_min: NotGivenOr[int] = NOT_GIVEN,
        daily_limit_max: NotGivenOr[int] = NOT_GIVEN,
        hourly_limit_min: NotGivenOr[int] = NOT_GIVEN,
        hourly_limit_max: NotGivenOr[int] = NOT_GIVEN,
        gap_min_seconds: NotGivenOr[int] = NOT_GIVEN,
        gap_max_seconds: NotGivenOr[int] = NOT_GIVEN,
        work_start_min: NotGivenOr[int] = NOT_GIVEN,
        work_start_max: NotGivenOr[int] = NOT_GIVEN,
        work_end_min: NotGivenOr[int] = NOT_GIVEN,
        work_end_max: NotGivenOr[int] = NOT_GIVEN,
        lunch_enabled: NotGivenOr[bool] = NOT_GIVEN,
        lunch_earliest: NotGivenOr[int] = NOT_GIVEN,
        lunch_latest: NotGivenOr[int] = NOT_GIVEN,
        lunch_min_minutes: NotGivenOr[int] = NOT_GIVEN,
        lunch_max_minutes: NotGivenOr[int] = NOT_GIVEN,
        weekdays: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SendingBehavior:
        """Update a mailbox's behaviour profile.

        Omitted fields keep their stored value, so switching the profile on
        does not mean resending every range. A range that cannot produce a
        sane workday is a 400 naming the field.

        Args:
            email_id: The mailbox id.
            enabled: Whether the profile shapes this mailbox's sending.
            daily_limit_min: Fewest cold sends a rolled day may target (1-500).
            daily_limit_max: Most cold sends a rolled day may target (1-500).
            hourly_limit_min: Low end of the hourly ceiling band (1-200).
            hourly_limit_max: High end of the hourly ceiling band (1-200).
            gap_min_seconds: Shortest gap between two sends (30-86400).
            gap_max_seconds: Longest gap between two sends (30-86400).
            work_start_min: Earliest the workday may start, in minutes since
                local midnight.
            work_start_max: Latest the workday may start. Must still precede
                *work_end_min*.
            work_end_min: Earliest the workday may end.
            work_end_max: Latest the workday may end.
            lunch_enabled: Whether the day carries a break.
            lunch_earliest: Earliest the break may start.
            lunch_latest: Latest the break may start.
            lunch_min_minutes: Shortest break (0-240).
            lunch_max_minutes: Longest break (0-240). The break must fit inside
                the shortest possible workday.
            weekdays: Monday-indexed sending-day bitmask (bit 0 is Monday).
        """
        return self._put(
            f"/emails/{email_id}/behavior",
            cast_to=SendingBehavior,
            body=_behavior_body(
                enabled=enabled,
                daily_limit_min=daily_limit_min,
                daily_limit_max=daily_limit_max,
                hourly_limit_min=hourly_limit_min,
                hourly_limit_max=hourly_limit_max,
                gap_min_seconds=gap_min_seconds,
                gap_max_seconds=gap_max_seconds,
                work_start_min=work_start_min,
                work_start_max=work_start_max,
                work_end_min=work_end_min,
                work_end_max=work_end_max,
                lunch_enabled=lunch_enabled,
                lunch_earliest=lunch_earliest,
                lunch_latest=lunch_latest,
                lunch_min_minutes=lunch_min_minutes,
                lunch_max_minutes=lunch_max_minutes,
                weekdays=weekdays,
            ),
            options=options,
        )

    def behavior_plan(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> SendingBehaviorPlan:
        """Read the workday this mailbox rolled for the current local date."""
        return self._get(
            f"/emails/{email_id}/behavior/plan",
            cast_to=SendingBehaviorPlan,
            options=options,
        )

    def verify(
        self, *, email: str, options: RequestOptions | None = None
    ) -> EmailVerification:
        """Verify an address before sending to it.

        Runs syntax, MX, SMTP RCPT probe, and catch-all detection from a
        non-sending IP, so it never risks a sending mailbox's reputation.
        """
        return self._post(
            "/emails/verify",
            cast_to=EmailVerification,
            body={"email": email},
            options=options,
        )

    def send(
        self,
        email_id: str,
        *,
        to: Sequence[str],
        subject: str,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        cc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        bcc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        in_reply_to: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        thread_id: NotGivenOr[str] = NOT_GIVEN,
        send_mode: NotGivenOr[str] = NOT_GIVEN,
        scheduled_at: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> EmailSendResult:
        """Send a one-off email from this mailbox.

        Args:
            email_id: The id of the mailbox to send from.
            to: Recipient addresses (at least one).
            subject: The email subject.
            body_html: The HTML body.
            body_plain: The plain-text body.
            in_reply_to: ``Message-ID`` values to thread under.
            thread_id: The thread to attach the message to.
            send_mode: ``"instant"`` (the default), ``"smart"`` to slot into
                the mailbox's next scheduler gap, or ``"scheduled"`` to send at
                *scheduled_at*.
            scheduled_at: RFC 3339 send time, at most 29 days out.
        """
        return self._post(
            f"/emails/{email_id}/send",
            cast_to=EmailSendResult,
            body=_send_body(
                to=to,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                cc=cc,
                bcc=bcc,
                in_reply_to=in_reply_to,
                thread_id=thread_id,
                send_mode=send_mode,
                scheduled_at=scheduled_at,
            ),
            options=options,
        )


class AsyncEmails(AsyncAPIResource):
    """Asynchronous ``emails`` resource."""

    def list(
        self,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        tag: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[EmailAccount]:
        """List connected email accounts (auto-paginating).

        Args:
            q: Search string matched against the address and display name.
            tag: Restrict to accounts carrying this tag.
            limit: Maximum number of accounts per page.
            cursor: Opaque pagination cursor from a previous page.
            options: Per-request overrides.
        """
        return self._get_api_list(
            "/emails",
            model=EmailAccount,
            query={"q": q, "tag": tag, "limit": limit, "cursor": cursor},
            options=options,
        )

    async def retrieve(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccount:
        """Retrieve a single email account by id."""
        return await self._get(
            f"/emails/{email_id}", cast_to=EmailAccount, options=options
        )

    async def update(
        self,
        email_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        reply_to: NotGivenOr[str] = NOT_GIVEN,
        timezone: NotGivenOr[str] = NOT_GIVEN,
        tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        campaign_limit: NotGivenOr[int] = NOT_GIVEN,
        min_wait_time: NotGivenOr[int] = NOT_GIVEN,
        signature_plain: NotGivenOr[str] = NOT_GIVEN,
        signature_html: NotGivenOr[str] = NOT_GIVEN,
        signature_sync: NotGivenOr[bool] = NOT_GIVEN,
        signature_code: NotGivenOr[bool] = NOT_GIVEN,
        save_to_sent: NotGivenOr[bool] = NOT_GIVEN,
        warmup: NotGivenOr[bool] = NOT_GIVEN,
        warmup_base: NotGivenOr[int] = NOT_GIVEN,
        warmup_max: NotGivenOr[int] = NOT_GIVEN,
        warmup_increase: NotGivenOr[int] = NOT_GIVEN,
        warmup_reply_rate: NotGivenOr[int] = NOT_GIVEN,
        warmup_tag: NotGivenOr[str] = NOT_GIVEN,
        warmup_start_time: NotGivenOr[str] = NOT_GIVEN,
        warmup_end_time: NotGivenOr[str] = NOT_GIVEN,
        warmup_days: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> EmailAccount:
        """Update an account's settings.

        Args:
            email_id: The account id.
            name: A new display name.
            status: ``"active"``, ``"inactive"``, or ``"revoked"``.
            reply_to: A ``Reply-To`` address for sends from this mailbox.
            timezone: An IANA timezone (e.g. ``"America/New_York"``).
            tags: Replacement list of tags.
            campaign_limit: Max campaign emails per day from this mailbox.
            min_wait_time: Minimum minutes between sends.
            signature_plain: Plain-text signature.
            signature_html: HTML signature.
            signature_sync: Keep the signature in sync with the provider.
            signature_code: Treat the HTML signature as raw code.
            save_to_sent: Copy sends from this mailbox into its Sent folder.
            warmup: Enable or disable warmup.
            warmup_base: Warmup emails per day at the start of the ramp.
            warmup_max: Warmup emails per day at the top of the ramp.
            warmup_increase: Daily ramp increment.
            warmup_reply_rate: Target warmup reply rate, as a percentage.
            warmup_tag: The warmup pool tag.
            warmup_start_time: Daily warmup window start (``"HH:MM"``).
            warmup_end_time: Daily warmup window end (``"HH:MM"``).
            warmup_days: Number of days in the warmup week.
            options: Per-request overrides.
        """
        return await self._patch(
            f"/emails/{email_id}",
            cast_to=EmailAccount,
            body=_update_body(
                name=name,
                status=status,
                reply_to=reply_to,
                timezone=timezone,
                tags=tags,
                campaign_limit=campaign_limit,
                min_wait_time=min_wait_time,
                signature_plain=signature_plain,
                signature_html=signature_html,
                signature_sync=signature_sync,
                signature_code=signature_code,
                save_to_sent=save_to_sent,
                warmup=warmup,
                warmup_base=warmup_base,
                warmup_max=warmup_max,
                warmup_increase=warmup_increase,
                warmup_reply_rate=warmup_reply_rate,
                warmup_tag=warmup_tag,
                warmup_start_time=warmup_start_time,
                warmup_end_time=warmup_end_time,
                warmup_days=warmup_days,
            ),
            options=options,
        )

    async def delete(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccountDeleted:
        """Disconnect and delete an email account."""
        return await self._delete(
            f"/emails/{email_id}", cast_to=EmailAccountDeleted, options=options
        )

    async def bulk_tag(
        self,
        *,
        email_ids: Sequence[str],
        add_tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        remove_tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> BulkTagResult:
        """Add and/or remove tags across many mailboxes at once.

        Set semantics, so the call is naturally idempotent.

        Args:
            email_ids: The mailboxes to update (max 1000).
            add_tags: Tags to add (max 100).
            remove_tags: Tags to remove (max 100).
        """
        return await self._patch(
            "/emails/tags",
            cast_to=BulkTagResult,
            body=drop_not_given(
                {
                    "email_ids": list(email_ids),
                    "add_tags": add_tags,
                    "remove_tags": remove_tags,
                }
            ),
            options=options,
        )

    async def track(
        self,
        email_id: str,
        *,
        domain: str,
        options: RequestOptions | None = None,
    ) -> TrackingDomainStatus:
        """Set the custom open/click tracking domain for an account.

        Args:
            email_id: The account id.
            domain: The custom tracking domain. Pass an empty string to clear
                it and fall back to the shared domain.
        """
        return await self._patch(
            f"/emails/{email_id}/track",
            cast_to=TrackingDomainStatus,
            query={"domain": domain},
            options=options,
        )

    async def warmup_start(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccount:
        """Start warmup for an account."""
        return await self._post(
            f"/emails/{email_id}/warmup/start", cast_to=EmailAccount, options=options
        )

    async def warmup_pause(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccount:
        """Pause warmup for an account."""
        return await self._post(
            f"/emails/{email_id}/warmup/pause", cast_to=EmailAccount, options=options
        )

    async def warmup_resume(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccount:
        """Resume a paused warmup for an account."""
        return await self._post(
            f"/emails/{email_id}/warmup/resume", cast_to=EmailAccount, options=options
        )

    async def warmup_stop(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccount:
        """Stop warmup for an account."""
        return await self._post(
            f"/emails/{email_id}/warmup/stop", cast_to=EmailAccount, options=options
        )

    async def warmup_ban_status(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> WarmupBanStatus:
        """Get the warmup ban / blocklist status for an account."""
        return await self._get(
            f"/emails/{email_id}/warmup/ban-status",
            cast_to=WarmupBanStatus,
            options=options,
        )

    async def warmup_appeal(
        self,
        email_id: str,
        *,
        reason: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> WarmupAppeal:
        """Appeal a warmup ban.

        Args:
            email_id: The account id.
            reason: An explanation supporting the appeal.
        """
        return await self._post(
            f"/emails/{email_id}/warmup/appeal",
            cast_to=WarmupAppeal,
            body=drop_not_given({"reason": reason}),
            options=options,
        )

    async def auth_check(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAuthCheck:
        """Run a deliverability authentication check (SPF/DKIM/DMARC)."""
        return await self._get(
            f"/emails/{email_id}/auth-check",
            cast_to=EmailAuthCheck,
            options=options,
        )

    async def refresh_auth_check(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAuthCheck:
        """Re-run the authentication check and record the verdict.

        Recording it is what lifts the cold-send and warmup gate, so this needs
        a write scope where :meth:`auth_check` only needs a read.
        """
        return await self._post(
            f"/emails/{email_id}/auth-check",
            cast_to=EmailAuthCheck,
            options=options,
        )

    async def tracking_domain(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> TrackingDomainStatus:
        """Read the mailbox's tracking-domain state and the CNAME target.

        Does no DNS work; :meth:`verify_tracking_domain` is the live check.
        """
        return await self._get(
            f"/emails/{email_id}/track",
            cast_to=TrackingDomainStatus,
            options=options,
        )

    async def verify_tracking_domain(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> TrackingDomainStatus:
        """Re-resolve the stored tracking domain and persist the verdict."""
        return await self._post(
            f"/emails/{email_id}/track/verify",
            cast_to=TrackingDomainStatus,
            options=options,
        )

    async def hold(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> SendLifecycleState:
        """Take the mailbox out of campaign sending until it is released.

        Warmup is untouched, so the mailbox keeps its reputation while it sits
        out. Bodyless and idempotent.
        """
        return await self._post(
            f"/emails/{email_id}/hold", cast_to=SendLifecycleState, options=options
        )

    async def release(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> SendLifecycleState:
        """Put a held or resting mailbox back into campaign rotation.

        Where it lands is up to its warmup health: an unhealthy mailbox comes
        back as ``resting`` rather than ``active``.
        """
        return await self._post(
            f"/emails/{email_id}/release", cast_to=SendLifecycleState, options=options
        )

    async def sync(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> MailboxSync:
        """Report where the mailbox's import stands and what is holding it."""
        return await self._get(
            f"/emails/{email_id}/sync", cast_to=MailboxSync, options=options
        )

    async def allowance(
        self, *, options: RequestOptions | None = None
    ) -> MailboxAllowance:
        """Report how many mailboxes the workspace holds and may hold."""
        return await self._get(
            "/emails/allowance", cast_to=MailboxAllowance, options=options
        )

    async def behavior(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> SendingBehavior:
        """Read a mailbox's sending-behaviour profile.

        A mailbox that has never been configured reads back the defaults, so
        the object is always complete.
        """
        return await self._get(
            f"/emails/{email_id}/behavior", cast_to=SendingBehavior, options=options
        )

    async def update_behavior(
        self,
        email_id: str,
        *,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        daily_limit_min: NotGivenOr[int] = NOT_GIVEN,
        daily_limit_max: NotGivenOr[int] = NOT_GIVEN,
        hourly_limit_min: NotGivenOr[int] = NOT_GIVEN,
        hourly_limit_max: NotGivenOr[int] = NOT_GIVEN,
        gap_min_seconds: NotGivenOr[int] = NOT_GIVEN,
        gap_max_seconds: NotGivenOr[int] = NOT_GIVEN,
        work_start_min: NotGivenOr[int] = NOT_GIVEN,
        work_start_max: NotGivenOr[int] = NOT_GIVEN,
        work_end_min: NotGivenOr[int] = NOT_GIVEN,
        work_end_max: NotGivenOr[int] = NOT_GIVEN,
        lunch_enabled: NotGivenOr[bool] = NOT_GIVEN,
        lunch_earliest: NotGivenOr[int] = NOT_GIVEN,
        lunch_latest: NotGivenOr[int] = NOT_GIVEN,
        lunch_min_minutes: NotGivenOr[int] = NOT_GIVEN,
        lunch_max_minutes: NotGivenOr[int] = NOT_GIVEN,
        weekdays: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SendingBehavior:
        """Update a mailbox's behaviour profile.

        Omitted fields keep their stored value, so switching the profile on
        does not mean resending every range. A range that cannot produce a
        sane workday is a 400 naming the field.

        Args:
            email_id: The mailbox id.
            enabled: Whether the profile shapes this mailbox's sending.
            daily_limit_min: Fewest cold sends a rolled day may target (1-500).
            daily_limit_max: Most cold sends a rolled day may target (1-500).
            hourly_limit_min: Low end of the hourly ceiling band (1-200).
            hourly_limit_max: High end of the hourly ceiling band (1-200).
            gap_min_seconds: Shortest gap between two sends (30-86400).
            gap_max_seconds: Longest gap between two sends (30-86400).
            work_start_min: Earliest the workday may start, in minutes since
                local midnight.
            work_start_max: Latest the workday may start. Must still precede
                *work_end_min*.
            work_end_min: Earliest the workday may end.
            work_end_max: Latest the workday may end.
            lunch_enabled: Whether the day carries a break.
            lunch_earliest: Earliest the break may start.
            lunch_latest: Latest the break may start.
            lunch_min_minutes: Shortest break (0-240).
            lunch_max_minutes: Longest break (0-240). The break must fit inside
                the shortest possible workday.
            weekdays: Monday-indexed sending-day bitmask (bit 0 is Monday).
        """
        return await self._put(
            f"/emails/{email_id}/behavior",
            cast_to=SendingBehavior,
            body=_behavior_body(
                enabled=enabled,
                daily_limit_min=daily_limit_min,
                daily_limit_max=daily_limit_max,
                hourly_limit_min=hourly_limit_min,
                hourly_limit_max=hourly_limit_max,
                gap_min_seconds=gap_min_seconds,
                gap_max_seconds=gap_max_seconds,
                work_start_min=work_start_min,
                work_start_max=work_start_max,
                work_end_min=work_end_min,
                work_end_max=work_end_max,
                lunch_enabled=lunch_enabled,
                lunch_earliest=lunch_earliest,
                lunch_latest=lunch_latest,
                lunch_min_minutes=lunch_min_minutes,
                lunch_max_minutes=lunch_max_minutes,
                weekdays=weekdays,
            ),
            options=options,
        )

    async def behavior_plan(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> SendingBehaviorPlan:
        """Read the workday this mailbox rolled for the current local date."""
        return await self._get(
            f"/emails/{email_id}/behavior/plan",
            cast_to=SendingBehaviorPlan,
            options=options,
        )

    async def verify(
        self, *, email: str, options: RequestOptions | None = None
    ) -> EmailVerification:
        """Verify an address before sending to it.

        Runs syntax, MX, SMTP RCPT probe, and catch-all detection from a
        non-sending IP, so it never risks a sending mailbox's reputation.
        """
        return await self._post(
            "/emails/verify",
            cast_to=EmailVerification,
            body={"email": email},
            options=options,
        )

    async def send(
        self,
        email_id: str,
        *,
        to: Sequence[str],
        subject: str,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        cc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        bcc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        in_reply_to: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        thread_id: NotGivenOr[str] = NOT_GIVEN,
        send_mode: NotGivenOr[str] = NOT_GIVEN,
        scheduled_at: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> EmailSendResult:
        """Send a one-off email from this mailbox.

        Args:
            email_id: The id of the mailbox to send from.
            to: Recipient addresses (at least one).
            subject: The email subject.
            body_html: The HTML body.
            body_plain: The plain-text body.
            in_reply_to: ``Message-ID`` values to thread under.
            thread_id: The thread to attach the message to.
            send_mode: ``"instant"`` (the default), ``"smart"`` to slot into
                the mailbox's next scheduler gap, or ``"scheduled"`` to send at
                *scheduled_at*.
            scheduled_at: RFC 3339 send time, at most 29 days out.
        """
        return await self._post(
            f"/emails/{email_id}/send",
            cast_to=EmailSendResult,
            body=_send_body(
                to=to,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                cc=cc,
                bcc=bcc,
                in_reply_to=in_reply_to,
                thread_id=thread_id,
                send_mode=send_mode,
                scheduled_at=scheduled_at,
            ),
            options=options,
        )
