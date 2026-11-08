"""The ``placement`` resource: inbox placement tests and batches.

Maps to the ``/v1/placement`` route group. A placement test sends a template
or a campaign step from one of the workspace's mailboxes to a panel of seed
inboxes and reports where each copy landed: the primary inbox, a Gmail tab,
spam, or nowhere. A batch runs the same test from many senders at once.

Reads need the ``read_analytics`` scope; starting or cancelling a test or batch
needs ``send_campaigns``; listing seeds needs ``read_emails`` and marking a
mailbox as a seed needs ``write_emails``. Every route is scoped to the
selected organization.

Tests and batches cost money past the workspace's monthly free allowance, so
the create routes take ``max_usd``: the most the caller agrees to pay. A
refused request sends and charges nothing. Creating a test or batch carries an
``Idempotency-Key`` automatically, so a retry is never charged twice.

Single objects arrive wrapped as ``{"data": ...}``; each wrapper is a small
envelope model exposing that object on ``.data``.
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
    "AsyncPlacement",
    "Placement",
    "PlacementBatch",
    "PlacementBatchDetail",
    "PlacementBatchDetailEnvelope",
    "PlacementBatchEnvelope",
    "PlacementBatchGroup",
    "PlacementBatchMatrixRow",
    "PlacementBatchPreview",
    "PlacementBatchPreviewEnvelope",
    "PlacementBatchProgress",
    "PlacementBatchSender",
    "PlacementContentCheck",
    "PlacementContentIssue",
    "PlacementCounts",
    "PlacementCoverage",
    "PlacementCoverageEnvelope",
    "PlacementFamilyCounts",
    "PlacementMetric",
    "PlacementMonitor",
    "PlacementMonitorDeleted",
    "PlacementMonitorEnvelope",
    "PlacementOverview",
    "PlacementOverviewEnvelope",
    "PlacementPanel",
    "PlacementPanelFamily",
    "PlacementProviderCount",
    "PlacementResult",
    "PlacementSeed",
    "PlacementSeedEnvelope",
    "PlacementTest",
    "PlacementTestDetail",
    "PlacementTestDetailEnvelope",
    "PlacementTestEnvelope",
    "PlacementTestsCreated",
    "PlacementUsage",
]


class PlacementMetric(BaseModel):
    """A rate with the counts behind it and an interval around it.

    ``value`` is ``numerator / denominator``, ``None`` while the denominator is
    zero. ``wilson_95_independence_interval`` is ``{"lower", "upper"}``.
    """

    version: str | None = None
    population: str | None = None
    denominator_kind: str | None = None
    unit: str | None = None
    source: str | None = None
    classification_policy: str | None = None
    numerator: int | None = None
    denominator: int | None = None
    unresolved: int | None = None
    window_days: int | None = None
    window_basis: str | None = None
    missingness_basis: str | None = None
    value: float | None = None
    wilson_95_independence_interval: dict[str, float] | None = None


class PlacementCounts(BaseModel):
    """Where a set of probes landed.

    ``delivered`` is every copy that left and got a verdict (inbox, promotions,
    other, spam and missing). The four rates are shares of ``delivered`` and
    are ``None`` until something is delivered. ``archive`` counts copies found
    in an archive folder.
    """

    total: int | None = None
    pending: int | None = None
    inbox: int | None = None
    promotions: int | None = None
    other: int | None = None
    spam: int | None = None
    missing: int | None = None
    failed: int | None = None
    cancelled: int | None = None
    unknown: int | None = None
    archive: int | None = None
    custom: int | None = None
    observed_receipts: int | None = None
    classified_receipts: int | None = None
    unresolved: int | None = None
    primary_metric: PlacementMetric | None = None
    non_spam_metric: PlacementMetric | None = None
    delivered: int | None = None
    inbox_rate: float | None = None
    tabs_rate: float | None = None
    spam_rate: float | None = None
    missing_rate: float | None = None


class PlacementFamilyCounts(BaseModel):
    """One recipient provider family's share of a test or batch."""

    family: str | None = None
    label: str | None = None
    counts: PlacementCounts | None = None


class PlacementTest(BaseModel):
    """One test: a template sent from one sender to a seed panel.

    ``status`` is ``running``, ``completed``, ``cancelled`` or ``failed``;
    ``origin`` is ``manual``, ``monitor``, ``admin``, ``remote`` or ``batch``;
    ``panel`` is ``instance``, ``workspace`` or ``cloud``; ``pace`` is
    ``spaced`` or ``quick``. ``body_html`` and ``body_plain`` are left out of
    lists. ``compare_group_id`` links the two halves of a tracking comparison.
    """

    id: str
    sender_account_id: str | None = None
    sender_email: str | None = None
    created_by: str | None = None
    campaign_id: str | None = None
    sequence_id: str | None = None
    contact_id: str | None = None
    monitor_id: str | None = None
    batch_id: str | None = None
    subject: str | None = None
    body_html: str | None = None
    body_plain: str | None = None
    open_tracking: bool | None = None
    link_tracking: bool | None = None
    compare_group_id: str | None = None
    origin: str | None = None
    panel: str | None = None
    status: str | None = None
    error: str | None = None
    pace: str | None = None
    credits_charged: int | None = None
    credits_refunded: int | None = None
    credits_settled_at: str | None = None
    charged_usd: float | None = None
    refunded_usd: float | None = None
    created_at: str | None = None
    finished_at: str | None = None
    summary: PlacementCounts | None = None
    families: Sequence[PlacementFamilyCounts] = []


class PlacementResult(BaseModel):
    """One probe: where one copy to one seed landed.

    ``seed`` is the seed's address, masked on the shared panels. ``folder`` is
    ``pending``, ``inbox``, ``promotions``, ``other``, ``spam``, ``missing``,
    ``failed``, ``cancelled``, ``unknown``, ``archive`` or ``custom``.
    ``evidence`` carries the authentication results the seed saw.
    """

    seed: str | None = None
    family: str | None = None
    family_label: str | None = None
    folder: str | None = None
    scheduled_at: str | None = None
    sent_at: str | None = None
    detected_at: str | None = None
    error: str | None = None
    first_folder: str | None = None
    observed_at: str | None = None
    late_observation: bool | None = None
    evidence: dict[str, Any] | None = None


class PlacementContentIssue(BaseModel):
    """One finding of the content check; ``severity`` is ``warn`` or ``high``."""

    severity: str | None = None
    code: str | None = None
    message: str | None = None
    field: str | None = None
    spans: Sequence[dict[str, Any]] = []
    suggestion: str | None = None


class PlacementContentCheck(BaseModel):
    """The rules pass over a test's subject and body."""

    score: int | None = None
    issues: Sequence[PlacementContentIssue] = []


class PlacementTestDetail(PlacementTest):
    """One test in full: every copy, the content check and, for a tracking
    comparison, the other half in ``compare``."""

    results: Sequence[PlacementResult] = []
    content: PlacementContentCheck | None = None
    compare: PlacementTest | None = None


class PlacementPanelFamily(BaseModel):
    """The seeds one provider family contributes to a panel."""

    family: str | None = None
    label: str | None = None
    seeds: int | None = None


class PlacementPanel(BaseModel):
    """Whether the workspace can test on a seed panel.

    ``panel`` is ``instance``, ``workspace`` or ``cloud``. ``reason`` explains
    an unavailable panel in one sentence. ``metered`` panels count against the
    monthly allowance.
    """

    panel: str | None = None
    available: bool | None = None
    reason: str | None = None
    seeds: int | None = None
    families: Sequence[PlacementPanelFamily] = []
    metered: bool | None = None


class PlacementUsage(BaseModel):
    """The workspace's monthly allowance on the metered panels.

    ``limit`` is ``None`` when the instance does not meter tests.
    ``balance_usd`` and ``credit_balance`` are ``None`` when the balance is
    off. The credit fields are the legacy form of the dollar figures.
    """

    used: int | None = None
    limit: int | None = None
    price_per_test_usd: float | None = None
    balance_usd: float | None = None
    credits_per_test: int | None = None
    credit_balance: int | None = None
    period_start: str | None = None
    period_end: str | None = None


class PlacementOverview(BaseModel):
    """What a workspace can test on and how much allowance is left."""

    panels: Sequence[PlacementPanel] = []
    usage: PlacementUsage | None = None
    workspace_seeds: int | None = None
    seeds_per_test: int | None = None
    spacing_seconds: int | None = None


class PlacementSeed(BaseModel):
    """One of the workspace's mailboxes as a seed candidate.

    ``seed`` says whether it is a seed inbox now; ``blocker`` is why it cannot
    become one, empty when it can.
    """

    email_account_id: str
    email: str | None = None
    family: str | None = None
    label: str | None = None
    status: str | None = None
    seed: bool | None = None
    blocker: str | None = None


class PlacementBatchProgress(BaseModel):
    """A batch's senders counted by status."""

    total: int | None = None
    queued: int | None = None
    deferred: int | None = None
    running: int | None = None
    completed: int | None = None
    skipped: int | None = None
    failed: int | None = None
    cancelled: int | None = None


class PlacementBatch(BaseModel):
    """One placement test run from many senders.

    ``status`` is ``queued``, ``running``, ``completed``,
    ``completed_with_warnings``, ``cancelled`` or ``failed``. ``selection``
    records how the senders were chosen (``sender_account_ids`` count,
    ``sender_scope``, ``sample`` and ``matched``). ``summary`` is the headline
    copy's placement (the tracked half of a comparison).
    """

    id: str
    created_by: str | None = None
    campaign_id: str | None = None
    sequence_id: str | None = None
    contact_id: str | None = None
    subject: str | None = None
    body_html: str | None = None
    body_plain: str | None = None
    tracking: str | None = None
    panel: str | None = None
    pace: str | None = None
    families: Sequence[str] = []
    seed_ids: Sequence[str] = []
    on_unavailable: str | None = None
    selection: dict[str, Any] | None = None
    sender_count: int | None = None
    max_credits: int | None = None
    credits_spent: int | None = None
    max_usd: float | None = None
    spent_usd: float | None = None
    status: str | None = None
    error: str | None = None
    retry_until: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    progress: PlacementBatchProgress | None = None
    summary: PlacementCounts | None = None


class PlacementBatchGroup(BaseModel):
    """A batch's placement for one sending domain or sending provider."""

    key: str | None = None
    label: str | None = None
    senders: int | None = None
    tested: int | None = None
    counts: PlacementCounts | None = None


class PlacementBatchMatrixRow(BaseModel):
    """One sending domain's placement per recipient provider."""

    domain: str | None = None
    recipients: Sequence[PlacementFamilyCounts] = []


class PlacementBatchDetail(PlacementBatch):
    """One batch in full, grouped by sending domain, sending provider and
    recipient provider.

    ``untracked`` is the untracked half of a tracking comparison.
    """

    untracked: PlacementCounts | None = None
    domains: Sequence[PlacementBatchGroup] = []
    providers: Sequence[PlacementBatchGroup] = []
    recipients: Sequence[PlacementFamilyCounts] = []
    matrix: Sequence[PlacementBatchMatrixRow] = []
    content: PlacementContentCheck | None = None


class PlacementBatchSender(BaseModel):
    """One sender of a batch with where its copies landed.

    ``status`` is ``queued``, ``deferred``, ``running``, ``completed``,
    ``skipped``, ``failed`` or ``cancelled``.
    """

    id: str
    batch_id: str | None = None
    email_account_id: str | None = None
    sender_email: str | None = None
    sender_domain: str | None = None
    sender_family: str | None = None
    status: str | None = None
    reason: str | None = None
    detail: str | None = None
    attempts: int | None = None
    next_attempt_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    sender_family_label: str | None = None
    summary: PlacementCounts | None = None
    test_ids: Sequence[str] = []


class PlacementProviderCount(BaseModel):
    """How many selected senders share a provider."""

    key: str | None = None
    label: str | None = None
    senders: int | None = None


class PlacementBatchPreview(BaseModel):
    """What a batch would do, before it is started. Nothing is sent."""

    matched: int | None = None
    selected: int | None = None
    inactive: int | None = None
    domains: int | None = None
    providers: Sequence[PlacementProviderCount] = []
    variants: int | None = None
    tests: int | None = None
    seeds_per_test: int | None = None
    max_sends: int | None = None
    metered: bool | None = None
    free_tests: int | None = None
    paid_tests: int | None = None
    cost_usd: float | None = None
    credits: int | None = None
    usage: PlacementUsage | None = None
    senders_max: int | None = None
    concurrency: int | None = None


class PlacementCoverage(BaseModel):
    """How much of the connected fleet delivered a placement test recently."""

    mailboxes: int | None = None
    tested_7d: int | None = None
    tested_30d: int | None = None
    never_tested: int | None = None


class PlacementMonitor(BaseModel):
    """A campaign's scheduled placement test.

    ``panel`` is ``instance``, ``workspace`` or ``cloud``; ``alert_below`` is
    an inbox rate in percent.
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


class PlacementMonitorDeleted(BaseModel):
    """The result of removing a monitor (``204 No Content``)."""

    deleted: bool | None = None


class PlacementOverviewEnvelope(BaseModel):
    """``{"data": overview}``."""

    data: PlacementOverview | None = None


class PlacementTestsCreated(BaseModel):
    """``{"data": [tests]}``: one test, or two for a tracking comparison."""

    data: Sequence[PlacementTest] = []


class PlacementTestEnvelope(BaseModel):
    """``{"data": test}``."""

    data: PlacementTest | None = None


class PlacementTestDetailEnvelope(BaseModel):
    """``{"data": test detail}``."""

    data: PlacementTestDetail | None = None


class PlacementSeedEnvelope(BaseModel):
    """``{"data": seed}``."""

    data: PlacementSeed | None = None


class PlacementBatchEnvelope(BaseModel):
    """``{"data": batch}``."""

    data: PlacementBatch | None = None


class PlacementBatchDetailEnvelope(BaseModel):
    """``{"data": batch detail}``."""

    data: PlacementBatchDetail | None = None


class PlacementBatchPreviewEnvelope(BaseModel):
    """``{"data": preview}``."""

    data: PlacementBatchPreview | None = None


class PlacementCoverageEnvelope(BaseModel):
    """``{"data": coverage}``."""

    data: PlacementCoverage | None = None


class PlacementMonitorEnvelope(BaseModel):
    """``{"data": monitor}``; ``data`` is ``None`` when the campaign has none."""

    data: PlacementMonitor | None = None


def _test_body(
    *,
    sender_account_id: str,
    campaign_id: NotGivenOr[str],
    sequence_id: NotGivenOr[str],
    contact_id: NotGivenOr[str],
    subject: NotGivenOr[str],
    body_html: NotGivenOr[str],
    body_plain: NotGivenOr[str],
    tracking: NotGivenOr[str],
    panel: NotGivenOr[str],
    seed_ids: NotGivenOr[Sequence[str]],
    families: NotGivenOr[Sequence[str]],
    pace: NotGivenOr[str],
    max_usd: NotGivenOr[float],
    max_credits: NotGivenOr[int],
) -> dict[str, Any]:
    return drop_not_given(
        {
            "sender_account_id": sender_account_id,
            "campaign_id": campaign_id,
            "sequence_id": sequence_id,
            "contact_id": contact_id,
            "subject": subject,
            "body_html": body_html,
            "body_plain": body_plain,
            "tracking": tracking,
            "panel": panel,
            "seed_ids": seed_ids,
            "families": families,
            "pace": pace,
            "max_usd": max_usd,
            "max_credits": max_credits,
        }
    )


def _batch_body(
    *,
    sender_account_ids: NotGivenOr[Sequence[str]],
    sender_scope: NotGivenOr[Mapping[str, Any]],
    sample: NotGivenOr[Mapping[str, Any]],
    campaign_id: NotGivenOr[str],
    sequence_id: NotGivenOr[str],
    contact_id: NotGivenOr[str],
    subject: NotGivenOr[str],
    body_html: NotGivenOr[str],
    body_plain: NotGivenOr[str],
    tracking: NotGivenOr[str],
    panel: NotGivenOr[str],
    pace: NotGivenOr[str],
    families: NotGivenOr[Sequence[str]],
    seed_ids: NotGivenOr[Sequence[str]],
    on_unavailable: NotGivenOr[str],
    max_usd: NotGivenOr[float],
    max_credits: NotGivenOr[int],
) -> dict[str, Any]:
    return drop_not_given(
        {
            "sender_account_ids": sender_account_ids,
            "sender_scope": sender_scope,
            "sample": sample,
            "campaign_id": campaign_id,
            "sequence_id": sequence_id,
            "contact_id": contact_id,
            "subject": subject,
            "body_html": body_html,
            "body_plain": body_plain,
            "tracking": tracking,
            "panel": panel,
            "pace": pace,
            "families": families,
            "seed_ids": seed_ids,
            "on_unavailable": on_unavailable,
            "max_usd": max_usd,
            "max_credits": max_credits,
        }
    )


def _monitor_body(
    *,
    enabled: NotGivenOr[bool],
    interval_days: NotGivenOr[int],
    panel: NotGivenOr[str],
    alert_below: NotGivenOr[int],
    pause_on_alert: NotGivenOr[bool],
) -> dict[str, Any]:
    return drop_not_given(
        {
            "enabled": enabled,
            "interval_days": interval_days,
            "panel": panel,
            "alert_below": alert_below,
            "pause_on_alert": pause_on_alert,
        }
    )


class Placement(SyncAPIResource):
    """Synchronous ``placement`` resource."""

    def overview(
        self,
        *,
        options: RequestOptions | None = None,
    ) -> PlacementOverviewEnvelope:
        """Get the seed panels the workspace can test on and its monthly allowance.

        Requires the ``read_analytics`` scope.
        """
        return self._get(
            "/placement/overview",
            cast_to=PlacementOverviewEnvelope,
            options=options,
        )

    def coverage(
        self,
        *,
        options: RequestOptions | None = None,
    ) -> PlacementCoverageEnvelope:
        """Report how much of the connected fleet delivered a test in the last 7 and 30 days.

        Requires the ``read_analytics`` scope.
        """
        return self._get(
            "/placement/coverage",
            cast_to=PlacementCoverageEnvelope,
            options=options,
        )

    def list_tests(
        self,
        *,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[PlacementTest]:
        """List the workspace's tests, newest first (auto-paginating).

        Requires the ``read_analytics`` scope.

        Args:
            campaign_id: Only tests started for this campaign.
            limit: Page size, 1 to 100 (default 25).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/placement/tests",
            model=PlacementTest,
            query=drop_not_given(
                {"campaign_id": campaign_id, "limit": limit, "cursor": cursor}
            ),
            options=options,
        )

    def create_test(
        self,
        *,
        sender_account_id: str,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        sequence_id: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        tracking: NotGivenOr[str] = NOT_GIVEN,
        panel: NotGivenOr[str] = NOT_GIVEN,
        seed_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        families: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        pace: NotGivenOr[str] = NOT_GIVEN,
        max_usd: NotGivenOr[float] = NOT_GIVEN,
        max_credits: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PlacementTestsCreated:
        """Start a test, or two linked tests for a tracking comparison.

        Every check runs before anything is scheduled, so a refused request
        sends and charges nothing. Requires the ``send_campaigns`` scope.

        Args:
            sender_account_id: The mailbox that sends every copy. It must be
                connected and active and cannot be a seed inbox.
            campaign_id: Test with this campaign's opt-out line, tracking and
                attachments.
            sequence_id: A step of ``campaign_id``; its subject and body are
                used when the request carries neither.
            contact_id: The contact merge fields are rendered for.
            subject: The subject; required when there is no step to take it
                from.
            body_html: HTML body. A test needs this or ``body_plain``.
            body_plain: Plain-text body.
            tracking: ``campaign`` (default), ``on``, ``off`` or ``compare``
                (one untracked and one tracked test to the same seeds).
            panel: ``instance`` (default), ``workspace`` or ``cloud``.
            seed_ids: Only with ``panel="workspace"``: send to exactly these
                seed inboxes.
            families: Only seeds at these provider families.
            pace: ``spaced`` (default, about 60 seconds between copies) or
                ``quick`` (about 8 seconds).
            max_usd: The most to pay when the month's free tests are used up.
            max_credits: The legacy form of ``max_usd``, read only when
                ``max_usd`` is absent.
        """
        return self._post(
            "/placement/tests",
            cast_to=PlacementTestsCreated,
            body=_test_body(
                sender_account_id=sender_account_id,
                campaign_id=campaign_id,
                sequence_id=sequence_id,
                contact_id=contact_id,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                tracking=tracking,
                panel=panel,
                seed_ids=seed_ids,
                families=families,
                pace=pace,
                max_usd=max_usd,
                max_credits=max_credits,
            ),
            options=options,
        )

    def retrieve_test(
        self, test_id: str, *, options: RequestOptions | None = None
    ) -> PlacementTestDetailEnvelope:
        """Get one test with every copy, the content check and its comparison half.

        Requires the ``read_analytics`` scope.
        """
        return self._get(
            f"/placement/tests/{test_id}",
            cast_to=PlacementTestDetailEnvelope,
            options=options,
        )

    def cancel_test(
        self, test_id: str, *, options: RequestOptions | None = None
    ) -> PlacementTestEnvelope:
        """Stop the copies of a test that have not been sent yet.

        Requires the ``send_campaigns`` scope.
        """
        return self._post(
            f"/placement/tests/{test_id}/cancel",
            cast_to=PlacementTestEnvelope,
            options=options,
        )

    def list_seeds(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[PlacementSeed]:
        """List the workspace's mailboxes and which of them are seed inboxes.

        Requires the ``read_emails`` scope. The list is not paginated; it is
        returned as a single page. A key limited to some mailboxes sees only
        those.
        """
        return self._get_api_list(
            "/placement/seeds",
            model=PlacementSeed,
            options=options,
        )

    def set_seed(
        self,
        email_account_id: str,
        *,
        seed: bool,
        options: RequestOptions | None = None,
    ) -> PlacementSeedEnvelope:
        """Make a workspace mailbox a seed inbox, or take it off the panel.

        Requires the ``write_emails`` scope.

        Args:
            email_account_id: The mailbox.
            seed: ``True`` to make it a seed inbox, ``False`` to remove it.
        """
        return self._put(
            f"/placement/seeds/{email_account_id}",
            cast_to=PlacementSeedEnvelope,
            body={"seed": seed},
            options=options,
        )

    def list_batches(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[PlacementBatch]:
        """List the workspace's batches, newest first (auto-paginating).

        Requires the ``read_analytics`` scope.

        Args:
            limit: Page size, 1 to 100 (default 25).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/placement/batches",
            model=PlacementBatch,
            query=drop_not_given({"limit": limit, "cursor": cursor}),
            options=options,
        )

    def preview_batch(
        self,
        *,
        sender_account_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        sender_scope: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        sample: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        sequence_id: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        tracking: NotGivenOr[str] = NOT_GIVEN,
        panel: NotGivenOr[str] = NOT_GIVEN,
        pace: NotGivenOr[str] = NOT_GIVEN,
        families: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        seed_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        on_unavailable: NotGivenOr[str] = NOT_GIVEN,
        max_usd: NotGivenOr[float] = NOT_GIVEN,
        max_credits: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PlacementBatchPreviewEnvelope:
        """Report how many senders, tests, sends and dollars a batch would come to.

        Starts nothing and charges nothing. Takes the same arguments as
        :meth:`create_batch`. Requires the ``send_campaigns`` scope.

        Args:
            sender_account_ids: The mailboxes to send from. Give this or
                ``sender_scope``.
            sender_scope: Selects senders on the server, as ``{"type":
                "campaign" | "workspace", "campaign_id", "providers",
                "domains", "tag_ids", "include_inactive", "untested_days"}``.
            sample: Picks part of the resolved senders, as ``{"mode": "all" |
                "random" | "percent" | "per_domain" | "per_provider",
                "count", "percent", "stratify"}``.
            campaign_id: Test with this campaign's settings.
            sequence_id: A step of ``campaign_id``.
            contact_id: The contact merge fields are rendered for.
            subject: The subject.
            body_html: HTML body. A batch needs this or ``body_plain``.
            body_plain: Plain-text body.
            tracking: ``campaign`` (default), ``on``, ``off`` or ``compare``.
            panel: ``instance`` (default), ``workspace`` or ``cloud``.
            pace: ``spaced`` (default) or ``quick``.
            families: Only seeds at these provider families.
            seed_ids: Only with ``panel="workspace"``: these seed inboxes.
            on_unavailable: What to do with a sender that cannot run when its
                turn comes: ``defer`` (default) or ``skip``.
            max_usd: The most to pay across the whole batch.
            max_credits: The legacy form of ``max_usd``.
        """
        return self._post(
            "/placement/batches/preview",
            cast_to=PlacementBatchPreviewEnvelope,
            body=_batch_body(
                sender_account_ids=sender_account_ids,
                sender_scope=sender_scope,
                sample=sample,
                campaign_id=campaign_id,
                sequence_id=sequence_id,
                contact_id=contact_id,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                tracking=tracking,
                panel=panel,
                pace=pace,
                families=families,
                seed_ids=seed_ids,
                on_unavailable=on_unavailable,
                max_usd=max_usd,
                max_credits=max_credits,
            ),
            options=options,
        )

    def create_batch(
        self,
        *,
        sender_account_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        sender_scope: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        sample: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        sequence_id: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        tracking: NotGivenOr[str] = NOT_GIVEN,
        panel: NotGivenOr[str] = NOT_GIVEN,
        pace: NotGivenOr[str] = NOT_GIVEN,
        families: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        seed_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        on_unavailable: NotGivenOr[str] = NOT_GIVEN,
        max_usd: NotGivenOr[float] = NOT_GIVEN,
        max_credits: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PlacementBatchEnvelope:
        """Queue a placement test from many senders.

        The server snapshots the senders and starts them a few at a time.
        Requires the ``send_campaigns`` scope.

        Args:
            sender_account_ids: The mailboxes to send from. Give this or
                ``sender_scope``.
            sender_scope: Selects senders on the server, as ``{"type":
                "campaign" | "workspace", "campaign_id", "providers",
                "domains", "tag_ids", "include_inactive", "untested_days"}``.
            sample: Picks part of the resolved senders, as ``{"mode": "all" |
                "random" | "percent" | "per_domain" | "per_provider",
                "count", "percent", "stratify"}``.
            campaign_id: Test with this campaign's settings.
            sequence_id: A step of ``campaign_id``.
            contact_id: The contact merge fields are rendered for.
            subject: The subject.
            body_html: HTML body. A batch needs this or ``body_plain``.
            body_plain: Plain-text body.
            tracking: ``campaign`` (default), ``on``, ``off`` or ``compare``.
            panel: ``instance`` (default), ``workspace`` or ``cloud``.
            pace: ``spaced`` (default) or ``quick``.
            families: Only seeds at these provider families.
            seed_ids: Only with ``panel="workspace"``: these seed inboxes.
            on_unavailable: What to do with a sender that cannot run when its
                turn comes: ``defer`` (default) or ``skip``.
            max_usd: The most to pay across the whole batch.
            max_credits: The legacy form of ``max_usd``.
        """
        return self._post(
            "/placement/batches",
            cast_to=PlacementBatchEnvelope,
            body=_batch_body(
                sender_account_ids=sender_account_ids,
                sender_scope=sender_scope,
                sample=sample,
                campaign_id=campaign_id,
                sequence_id=sequence_id,
                contact_id=contact_id,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                tracking=tracking,
                panel=panel,
                pace=pace,
                families=families,
                seed_ids=seed_ids,
                on_unavailable=on_unavailable,
                max_usd=max_usd,
                max_credits=max_credits,
            ),
            options=options,
        )

    def retrieve_batch(
        self, batch_id: str, *, options: RequestOptions | None = None
    ) -> PlacementBatchDetailEnvelope:
        """Get one batch with its placement overall and grouped by sending
        domain, sending provider and recipient provider.

        Requires the ``read_analytics`` scope.
        """
        return self._get(
            f"/placement/batches/{batch_id}",
            cast_to=PlacementBatchDetailEnvelope,
            options=options,
        )

    def cancel_batch(
        self, batch_id: str, *, options: RequestOptions | None = None
    ) -> PlacementBatchEnvelope:
        """Stop a batch. Copies already sent keep being classified.

        Requires the ``send_campaigns`` scope.
        """
        return self._post(
            f"/placement/batches/{batch_id}/cancel",
            cast_to=PlacementBatchEnvelope,
            options=options,
        )

    def list_batch_senders(
        self,
        batch_id: str,
        *,
        status: NotGivenOr[str] = NOT_GIVEN,
        q: NotGivenOr[str] = NOT_GIVEN,
        sort: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[PlacementBatchSender]:
        """List a batch's senders with where each one's copies landed
        (auto-paginating).

        Requires the ``read_analytics`` scope.

        Args:
            batch_id: The batch.
            status: Only senders in this status.
            q: Filter to senders whose address contains this text.
            sort: ``worst`` (default, lowest inbox rate first), ``best``,
                ``email`` or ``status``.
            limit: Page size, 1 to 100 (default 25).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            f"/placement/batches/{batch_id}/senders",
            model=PlacementBatchSender,
            query=drop_not_given(
                {
                    "status": status,
                    "q": q,
                    "sort": sort,
                    "limit": limit,
                    "cursor": cursor,
                }
            ),
            options=options,
        )


class AsyncPlacement(AsyncAPIResource):
    """Asynchronous ``placement`` resource."""

    async def overview(
        self,
        *,
        options: RequestOptions | None = None,
    ) -> PlacementOverviewEnvelope:
        """Get the seed panels the workspace can test on and its monthly allowance.

        Requires the ``read_analytics`` scope.
        """
        return await self._get(
            "/placement/overview",
            cast_to=PlacementOverviewEnvelope,
            options=options,
        )

    async def coverage(
        self,
        *,
        options: RequestOptions | None = None,
    ) -> PlacementCoverageEnvelope:
        """Report how much of the connected fleet delivered a test in the last 7 and 30 days.

        Requires the ``read_analytics`` scope.
        """
        return await self._get(
            "/placement/coverage",
            cast_to=PlacementCoverageEnvelope,
            options=options,
        )

    def list_tests(
        self,
        *,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[PlacementTest]:
        """List the workspace's tests, newest first (auto-paginating).

        Requires the ``read_analytics`` scope.

        Args:
            campaign_id: Only tests started for this campaign.
            limit: Page size, 1 to 100 (default 25).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/placement/tests",
            model=PlacementTest,
            query=drop_not_given(
                {"campaign_id": campaign_id, "limit": limit, "cursor": cursor}
            ),
            options=options,
        )

    async def create_test(
        self,
        *,
        sender_account_id: str,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        sequence_id: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        tracking: NotGivenOr[str] = NOT_GIVEN,
        panel: NotGivenOr[str] = NOT_GIVEN,
        seed_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        families: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        pace: NotGivenOr[str] = NOT_GIVEN,
        max_usd: NotGivenOr[float] = NOT_GIVEN,
        max_credits: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PlacementTestsCreated:
        """Start a test, or two linked tests for a tracking comparison.

        Every check runs before anything is scheduled, so a refused request
        sends and charges nothing. Requires the ``send_campaigns`` scope.

        Args:
            sender_account_id: The mailbox that sends every copy. It must be
                connected and active and cannot be a seed inbox.
            campaign_id: Test with this campaign's opt-out line, tracking and
                attachments.
            sequence_id: A step of ``campaign_id``; its subject and body are
                used when the request carries neither.
            contact_id: The contact merge fields are rendered for.
            subject: The subject; required when there is no step to take it
                from.
            body_html: HTML body. A test needs this or ``body_plain``.
            body_plain: Plain-text body.
            tracking: ``campaign`` (default), ``on``, ``off`` or ``compare``
                (one untracked and one tracked test to the same seeds).
            panel: ``instance`` (default), ``workspace`` or ``cloud``.
            seed_ids: Only with ``panel="workspace"``: send to exactly these
                seed inboxes.
            families: Only seeds at these provider families.
            pace: ``spaced`` (default, about 60 seconds between copies) or
                ``quick`` (about 8 seconds).
            max_usd: The most to pay when the month's free tests are used up.
            max_credits: The legacy form of ``max_usd``, read only when
                ``max_usd`` is absent.
        """
        return await self._post(
            "/placement/tests",
            cast_to=PlacementTestsCreated,
            body=_test_body(
                sender_account_id=sender_account_id,
                campaign_id=campaign_id,
                sequence_id=sequence_id,
                contact_id=contact_id,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                tracking=tracking,
                panel=panel,
                seed_ids=seed_ids,
                families=families,
                pace=pace,
                max_usd=max_usd,
                max_credits=max_credits,
            ),
            options=options,
        )

    async def retrieve_test(
        self, test_id: str, *, options: RequestOptions | None = None
    ) -> PlacementTestDetailEnvelope:
        """Get one test with every copy, the content check and its comparison half.

        Requires the ``read_analytics`` scope.
        """
        return await self._get(
            f"/placement/tests/{test_id}",
            cast_to=PlacementTestDetailEnvelope,
            options=options,
        )

    async def cancel_test(
        self, test_id: str, *, options: RequestOptions | None = None
    ) -> PlacementTestEnvelope:
        """Stop the copies of a test that have not been sent yet.

        Requires the ``send_campaigns`` scope.
        """
        return await self._post(
            f"/placement/tests/{test_id}/cancel",
            cast_to=PlacementTestEnvelope,
            options=options,
        )

    def list_seeds(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[PlacementSeed]:
        """List the workspace's mailboxes and which of them are seed inboxes.

        Requires the ``read_emails`` scope. The list is not paginated; it is
        returned as a single page. A key limited to some mailboxes sees only
        those.
        """
        return self._get_api_list(
            "/placement/seeds",
            model=PlacementSeed,
            options=options,
        )

    async def set_seed(
        self,
        email_account_id: str,
        *,
        seed: bool,
        options: RequestOptions | None = None,
    ) -> PlacementSeedEnvelope:
        """Make a workspace mailbox a seed inbox, or take it off the panel.

        Requires the ``write_emails`` scope.

        Args:
            email_account_id: The mailbox.
            seed: ``True`` to make it a seed inbox, ``False`` to remove it.
        """
        return await self._put(
            f"/placement/seeds/{email_account_id}",
            cast_to=PlacementSeedEnvelope,
            body={"seed": seed},
            options=options,
        )

    def list_batches(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[PlacementBatch]:
        """List the workspace's batches, newest first (auto-paginating).

        Requires the ``read_analytics`` scope.

        Args:
            limit: Page size, 1 to 100 (default 25).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/placement/batches",
            model=PlacementBatch,
            query=drop_not_given({"limit": limit, "cursor": cursor}),
            options=options,
        )

    async def preview_batch(
        self,
        *,
        sender_account_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        sender_scope: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        sample: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        sequence_id: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        tracking: NotGivenOr[str] = NOT_GIVEN,
        panel: NotGivenOr[str] = NOT_GIVEN,
        pace: NotGivenOr[str] = NOT_GIVEN,
        families: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        seed_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        on_unavailable: NotGivenOr[str] = NOT_GIVEN,
        max_usd: NotGivenOr[float] = NOT_GIVEN,
        max_credits: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PlacementBatchPreviewEnvelope:
        """Report how many senders, tests, sends and dollars a batch would come to.

        Starts nothing and charges nothing. Takes the same arguments as
        :meth:`create_batch`. Requires the ``send_campaigns`` scope.

        Args:
            sender_account_ids: The mailboxes to send from. Give this or
                ``sender_scope``.
            sender_scope: Selects senders on the server, as ``{"type":
                "campaign" | "workspace", "campaign_id", "providers",
                "domains", "tag_ids", "include_inactive", "untested_days"}``.
            sample: Picks part of the resolved senders, as ``{"mode": "all" |
                "random" | "percent" | "per_domain" | "per_provider",
                "count", "percent", "stratify"}``.
            campaign_id: Test with this campaign's settings.
            sequence_id: A step of ``campaign_id``.
            contact_id: The contact merge fields are rendered for.
            subject: The subject.
            body_html: HTML body. A batch needs this or ``body_plain``.
            body_plain: Plain-text body.
            tracking: ``campaign`` (default), ``on``, ``off`` or ``compare``.
            panel: ``instance`` (default), ``workspace`` or ``cloud``.
            pace: ``spaced`` (default) or ``quick``.
            families: Only seeds at these provider families.
            seed_ids: Only with ``panel="workspace"``: these seed inboxes.
            on_unavailable: What to do with a sender that cannot run when its
                turn comes: ``defer`` (default) or ``skip``.
            max_usd: The most to pay across the whole batch.
            max_credits: The legacy form of ``max_usd``.
        """
        return await self._post(
            "/placement/batches/preview",
            cast_to=PlacementBatchPreviewEnvelope,
            body=_batch_body(
                sender_account_ids=sender_account_ids,
                sender_scope=sender_scope,
                sample=sample,
                campaign_id=campaign_id,
                sequence_id=sequence_id,
                contact_id=contact_id,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                tracking=tracking,
                panel=panel,
                pace=pace,
                families=families,
                seed_ids=seed_ids,
                on_unavailable=on_unavailable,
                max_usd=max_usd,
                max_credits=max_credits,
            ),
            options=options,
        )

    async def create_batch(
        self,
        *,
        sender_account_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        sender_scope: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        sample: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        sequence_id: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        tracking: NotGivenOr[str] = NOT_GIVEN,
        panel: NotGivenOr[str] = NOT_GIVEN,
        pace: NotGivenOr[str] = NOT_GIVEN,
        families: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        seed_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        on_unavailable: NotGivenOr[str] = NOT_GIVEN,
        max_usd: NotGivenOr[float] = NOT_GIVEN,
        max_credits: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PlacementBatchEnvelope:
        """Queue a placement test from many senders.

        The server snapshots the senders and starts them a few at a time.
        Requires the ``send_campaigns`` scope.

        Args:
            sender_account_ids: The mailboxes to send from. Give this or
                ``sender_scope``.
            sender_scope: Selects senders on the server, as ``{"type":
                "campaign" | "workspace", "campaign_id", "providers",
                "domains", "tag_ids", "include_inactive", "untested_days"}``.
            sample: Picks part of the resolved senders, as ``{"mode": "all" |
                "random" | "percent" | "per_domain" | "per_provider",
                "count", "percent", "stratify"}``.
            campaign_id: Test with this campaign's settings.
            sequence_id: A step of ``campaign_id``.
            contact_id: The contact merge fields are rendered for.
            subject: The subject.
            body_html: HTML body. A batch needs this or ``body_plain``.
            body_plain: Plain-text body.
            tracking: ``campaign`` (default), ``on``, ``off`` or ``compare``.
            panel: ``instance`` (default), ``workspace`` or ``cloud``.
            pace: ``spaced`` (default) or ``quick``.
            families: Only seeds at these provider families.
            seed_ids: Only with ``panel="workspace"``: these seed inboxes.
            on_unavailable: What to do with a sender that cannot run when its
                turn comes: ``defer`` (default) or ``skip``.
            max_usd: The most to pay across the whole batch.
            max_credits: The legacy form of ``max_usd``.
        """
        return await self._post(
            "/placement/batches",
            cast_to=PlacementBatchEnvelope,
            body=_batch_body(
                sender_account_ids=sender_account_ids,
                sender_scope=sender_scope,
                sample=sample,
                campaign_id=campaign_id,
                sequence_id=sequence_id,
                contact_id=contact_id,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                tracking=tracking,
                panel=panel,
                pace=pace,
                families=families,
                seed_ids=seed_ids,
                on_unavailable=on_unavailable,
                max_usd=max_usd,
                max_credits=max_credits,
            ),
            options=options,
        )

    async def retrieve_batch(
        self, batch_id: str, *, options: RequestOptions | None = None
    ) -> PlacementBatchDetailEnvelope:
        """Get one batch with its placement overall and grouped by sending
        domain, sending provider and recipient provider.

        Requires the ``read_analytics`` scope.
        """
        return await self._get(
            f"/placement/batches/{batch_id}",
            cast_to=PlacementBatchDetailEnvelope,
            options=options,
        )

    async def cancel_batch(
        self, batch_id: str, *, options: RequestOptions | None = None
    ) -> PlacementBatchEnvelope:
        """Stop a batch. Copies already sent keep being classified.

        Requires the ``send_campaigns`` scope.
        """
        return await self._post(
            f"/placement/batches/{batch_id}/cancel",
            cast_to=PlacementBatchEnvelope,
            options=options,
        )

    def list_batch_senders(
        self,
        batch_id: str,
        *,
        status: NotGivenOr[str] = NOT_GIVEN,
        q: NotGivenOr[str] = NOT_GIVEN,
        sort: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[PlacementBatchSender]:
        """List a batch's senders with where each one's copies landed
        (auto-paginating).

        Requires the ``read_analytics`` scope.

        Args:
            batch_id: The batch.
            status: Only senders in this status.
            q: Filter to senders whose address contains this text.
            sort: ``worst`` (default, lowest inbox rate first), ``best``,
                ``email`` or ``status``.
            limit: Page size, 1 to 100 (default 25).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            f"/placement/batches/{batch_id}/senders",
            model=PlacementBatchSender,
            query=drop_not_given(
                {
                    "status": status,
                    "q": q,
                    "sort": sort,
                    "limit": limit,
                    "cursor": cursor,
                }
            ),
            options=options,
        )
