"""The ``placement`` resource: inbox placement tests against a seed panel.

Maps to the ``/v1/placement`` route group. A placement test sends one copy of a
message from one of your mailboxes to a panel of seed inboxes and reports where
each copy landed (inbox, a Gmail tab, spam, or never seen). A *batch* runs the
same test from many senders at once, chosen by id or by a scope the server
resolves, and rolls the results up per sending domain, sending provider and
recipient provider. ``coverage`` shows how much of the fleet has been tested.

Reads need the ``read_analytics`` permission (seed listing needs
``read_emails``); starting or cancelling a test or batch needs
``send_campaigns``; changing which mailboxes are seeds needs ``write_emails``.

The server wraps single objects and lists in ``{"data": ...}``; the methods
here unwrap that and return the models directly.
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
    "ObservationInterval",
    "ObservationMetric",
    "Placement",
    "PlacementBatch",
    "PlacementBatchDetail",
    "PlacementBatchGroup",
    "PlacementBatchGroupCount",
    "PlacementBatchMatrixRow",
    "PlacementBatchPreview",
    "PlacementBatchProgress",
    "PlacementBatchSelection",
    "PlacementBatchSender",
    "PlacementContentCheck",
    "PlacementContentIssue",
    "PlacementContentSpan",
    "PlacementCounts",
    "PlacementCoverage",
    "PlacementDkimVerification",
    "PlacementEvidence",
    "PlacementFamilyCounts",
    "PlacementOverview",
    "PlacementPanel",
    "PlacementPanelFamily",
    "PlacementResult",
    "PlacementSample",
    "PlacementSenderScope",
    "PlacementTest",
    "PlacementTestDetail",
    "PlacementUsage",
    "PlacementWorkspaceSeed",
]


class ObservationInterval(BaseModel):
    """The 95% Wilson interval around an observed rate."""

    lower: float | None = None
    upper: float | None = None


class ObservationMetric(BaseModel):
    """An instrument reading, not a real-recipient inbox probability.

    ``value`` is ``None`` until there is a denominator. ``unit`` is
    ``fraction`` or ``percent``, and ``population`` says what was measured
    (``seed_panel``, ``warmup_pool`` or ``warmup_pool_major_providers``).
    ``wilson_95_independence_interval`` brackets ``value`` on the assumption
    that the observations are independent.
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
    wilson_95_independence_interval: ObservationInterval | None = None


class PlacementCounts(BaseModel):
    """Where a set of probes landed.

    ``delivered`` is every copy that left and got a verdict (inbox, promotions,
    other tabs, spam and missing). The rates are shares of ``delivered`` and are
    ``None`` until something was delivered: ``inbox_rate`` is the primary inbox,
    ``tabs_rate`` the Gmail tabs, ``spam_rate`` spam and ``missing_rate`` copies
    that were never seen. ``archive`` is the count of copies filed to archive.
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
    primary_metric: ObservationMetric | None = None
    non_spam_metric: ObservationMetric | None = None
    delivered: int | None = None
    inbox_rate: float | None = None
    tabs_rate: float | None = None
    spam_rate: float | None = None
    missing_rate: float | None = None


class PlacementFamilyCounts(BaseModel):
    """One host family's share of a test (``family`` is a mail host id)."""

    family: str | None = None
    label: str | None = None
    counts: PlacementCounts | None = None


class PlacementTest(BaseModel):
    """One test: a message sent from one sender to a seed panel.

    ``status`` is ``running``, ``completed``, ``cancelled`` or ``failed``.
    ``origin`` is ``manual``, ``monitor``, ``admin``, ``remote`` or ``batch``.
    ``panel`` is ``instance``, ``workspace`` or ``cloud``. ``summary`` and
    ``families`` say where the copies landed, overall and per host family; the
    message body is left out of lists.
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
    created_at: str | None = None
    finished_at: str | None = None
    summary: PlacementCounts | None = None
    families: Sequence[PlacementFamilyCounts] = []


class PlacementDkimVerification(BaseModel):
    """The platform's own DKIM check of a received probe."""

    dkim: str | None = None
    alignment: str | None = None
    signing_domain: str | None = None
    verifier: str | None = None
    observed_at: str | None = None


class PlacementEvidence(BaseModel):
    """What the receiving side recorded about a probe's authentication.

    Header claims are kept apart from verified verdicts: ``trust`` is
    ``unknown`` or ``unverified_headers``, and the ``*_claim`` fields are what
    the headers said, not a verified result.
    """

    version: str | None = None
    source: str | None = None
    trust: str | None = None
    observed_at: str | None = None
    spf: str | None = None
    dkim: str | None = None
    dmarc: str | None = None
    alignment: str | None = None
    tls: str | None = None
    from_domain: str | None = None
    envelope_domain_claim: str | None = None
    signing_domain_claim: str | None = None
    selector_claim: str | None = None
    authentication_results_present: bool | None = None
    one_click_headers_present: bool | None = None
    one_click_signing_claim: bool | None = None
    one_click_compliance: str | None = None
    dkim_verification: PlacementDkimVerification | None = None


class PlacementResult(BaseModel):
    """One probe: one copy to one seed.

    ``seed`` is the seed address, masked on the shared panels. ``folder`` is
    ``pending``, ``inbox``, ``promotions``, ``other``, ``spam``, ``missing``,
    ``failed``, ``cancelled``, ``unknown``, ``archive`` or ``custom``.
    ``late_observation`` marks a copy counted as missing that showed up later.
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
    evidence: PlacementEvidence | None = None


class PlacementContentSpan(BaseModel):
    """The exact fragment that triggered a content issue."""

    field: str | None = None
    text: str | None = None
    line: int | None = None
    excerpt: str | None = None


class PlacementContentIssue(BaseModel):
    """One advisory content problem (``severity`` is ``warn`` or ``high``)."""

    severity: str | None = None
    code: str | None = None
    message: str | None = None
    field: str | None = None
    spans: Sequence[PlacementContentSpan] = []
    suggestion: str | None = None


class PlacementContentCheck(BaseModel):
    """The advisory content-safety pass over a test's copy (0 to 100, higher is safer)."""

    score: int | None = None
    issues: Sequence[PlacementContentIssue] = []


class PlacementTestDetail(PlacementTest):
    """A test in full: every probe, the content check and, for a tracking
    comparison, the other half as ``compare``."""

    results: Sequence[PlacementResult] = []
    content: PlacementContentCheck | None = None
    compare: PlacementTest | None = None


class PlacementPanelFamily(BaseModel):
    """The seeds one host family contributes to a panel."""

    family: str | None = None
    label: str | None = None
    seeds: int | None = None


class PlacementPanel(BaseModel):
    """Whether this workspace can test on a seed panel.

    ``panel`` is ``instance``, ``workspace`` or ``cloud``. ``reason`` explains
    an unavailable panel. Metered panels count against the monthly allowance.
    """

    panel: str | None = None
    available: bool | None = None
    reason: str | None = None
    seeds: int | None = None
    families: Sequence[PlacementPanelFamily] = []
    metered: bool | None = None


class PlacementUsage(BaseModel):
    """A workspace's monthly allowance on the metered panels.

    ``limit`` is ``None`` when tests are not metered, and ``credit_balance`` is
    ``None`` when credits are off.
    """

    used: int | None = None
    limit: int | None = None
    credits_per_test: int | None = None
    credit_balance: int | None = None
    period_start: str | None = None
    period_end: str | None = None


class PlacementOverview(BaseModel):
    """What the workspace can test on, and how much allowance is left."""

    panels: Sequence[PlacementPanel] = []
    usage: PlacementUsage | None = None
    workspace_seeds: int | None = None
    seeds_per_test: int | None = None
    spacing_seconds: int | None = None


class PlacementWorkspaceSeed(BaseModel):
    """One of the workspace's mailboxes as a seed candidate.

    ``blocker`` is why a mailbox cannot become a seed, absent when it can.
    """

    email_account_id: str | None = None
    email: str | None = None
    family: str | None = None
    label: str | None = None
    status: str | None = None
    seed: bool | None = None
    blocker: str | None = None


class PlacementCoverage(BaseModel):
    """How much of the connected fleet delivered a placement test recently."""

    mailboxes: int | None = None
    tested_7d: int | None = None
    tested_30d: int | None = None
    never_tested: int | None = None


class PlacementSenderScope(BaseModel):
    """How a batch's senders were selected on the server.

    ``type`` is ``campaign`` or ``workspace``; the other fields narrow it.
    """

    type: str | None = None
    campaign_id: str | None = None
    providers: Sequence[str] = []
    domains: Sequence[str] = []
    tag_ids: Sequence[str] = []
    include_inactive: bool | None = None
    untested_days: int | None = None


class PlacementSample(BaseModel):
    """Which part of the resolved senders a batch tests.

    ``mode`` is ``all``, ``random``, ``percent``, ``per_domain`` or
    ``per_provider``.
    """

    mode: str | None = None
    count: int | None = None
    percent: int | None = None
    stratify: str | None = None


class PlacementBatchSelection(BaseModel):
    """How a batch's senders were chosen.

    ``sender_account_ids`` is the *count* of ids given, not the ids; ``matched``
    is how many senders the scope resolved to before sampling.
    """

    sender_account_ids: int | None = None
    sender_scope: PlacementSenderScope | None = None
    sample: PlacementSample | None = None
    matched: int | None = None


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
    ``completed_with_warnings``, ``cancelled`` or ``failed``. ``tracking`` is
    ``campaign``, ``on``, ``off`` or ``compare``, ``pace`` is ``spaced`` and
    ``on_unavailable`` is ``skip`` or ``defer``. ``progress`` counts the senders
    by status and ``summary`` is the headline placement.
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
    selection: PlacementBatchSelection | None = None
    sender_count: int | None = None
    max_credits: int | None = None
    credits_spent: int | None = None
    status: str | None = None
    error: str | None = None
    retry_until: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    progress: PlacementBatchProgress | None = None
    summary: PlacementCounts | None = None


class PlacementBatchGroup(BaseModel):
    """A batch's placement for one sending domain or provider."""

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
    """A batch in full.

    ``summary`` is the tracked half of a tracking comparison, the copy a
    campaign really sends, and ``untracked`` the other half.
    """

    untracked: PlacementCounts | None = None
    domains: Sequence[PlacementBatchGroup] = []
    providers: Sequence[PlacementBatchGroup] = []
    recipients: Sequence[PlacementFamilyCounts] = []
    matrix: Sequence[PlacementBatchMatrixRow] = []
    content: PlacementContentCheck | None = None


class PlacementBatchSender(BaseModel):
    """One sender of a batch, with where its copies landed.

    ``status`` is ``queued``, ``deferred``, ``running``, ``completed``,
    ``skipped``, ``failed`` or ``cancelled``.
    """

    id: str
    batch_id: str | None = None
    email_account_id: str | None = None
    sender_email: str | None = None
    sender_domain: str | None = None
    sender_family: str | None = None
    sender_family_label: str | None = None
    status: str | None = None
    reason: str | None = None
    detail: str | None = None
    attempts: int | None = None
    next_attempt_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    summary: PlacementCounts | None = None
    test_ids: Sequence[str] = []


class PlacementBatchGroupCount(BaseModel):
    """How many selected senders share a provider."""

    key: str | None = None
    label: str | None = None
    senders: int | None = None


class PlacementBatchPreview(BaseModel):
    """What a batch would do, before it starts.

    ``matched`` senders resolved, ``selected`` kept by the sample. ``variants``
    is two for a tracking comparison, which doubles every count. ``max_sends``
    is the most probes the batch sends. ``free_tests``/``paid_tests`` split
    ``tests`` against the monthly allowance and ``credits`` is the most the paid
    ones cost.
    """

    matched: int | None = None
    selected: int | None = None
    inactive: int | None = None
    domains: int | None = None
    providers: Sequence[PlacementBatchGroupCount] = []
    variants: int | None = None
    tests: int | None = None
    seeds_per_test: int | None = None
    max_sends: int | None = None
    metered: bool | None = None
    free_tests: int | None = None
    paid_tests: int | None = None
    credits: int | None = None
    usage: PlacementUsage | None = None
    senders_max: int | None = None
    concurrency: int | None = None


class _Overview(BaseModel):
    data: PlacementOverview


class _Tests(BaseModel):
    data: Sequence[PlacementTest] = []


class _Test(BaseModel):
    data: PlacementTest


class _TestDetail(BaseModel):
    data: PlacementTestDetail


class _Batch(BaseModel):
    data: PlacementBatch


class _BatchDetail(BaseModel):
    data: PlacementBatchDetail


class _BatchPreview(BaseModel):
    data: PlacementBatchPreview


class _Coverage(BaseModel):
    data: PlacementCoverage


class _Seed(BaseModel):
    data: PlacementWorkspaceSeed


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
            "max_credits": max_credits,
        }
    )


class Placement(SyncAPIResource):
    """Synchronous ``placement`` resource."""

    def overview(self, *, options: RequestOptions | None = None) -> PlacementOverview:
        """Read the seed panels this workspace can test on and its allowance.

        Requires the ``read_analytics`` permission.
        """
        return (
            self._get("/placement/overview", cast_to=_Overview, options=options)
        ).data

    def list_tests(
        self,
        *,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[PlacementTest]:
        """List the workspace's placement tests, newest first (auto-paginating).

        Tests a batch started are listed under the batch instead. Requires the
        ``read_analytics`` permission.

        Args:
            campaign_id: Only tests for this campaign.
            limit: Tests per page (1 to 100, default 25).
            cursor: Opaque pagination cursor from a previous page.
            options: Per-request overrides.
        """
        return self._get_api_list(
            "/placement/tests",
            model=PlacementTest,
            query={"campaign_id": campaign_id, "limit": limit, "cursor": cursor},
            options=options,
        )

    def retrieve_test(
        self, test_id: str, *, options: RequestOptions | None = None
    ) -> PlacementTestDetail:
        """Retrieve one test with every probe and the content check.

        Requires the ``read_analytics`` permission.
        """
        return (
            self._get(
                f"/placement/tests/{test_id}", cast_to=_TestDetail, options=options
            )
        ).data

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
        max_credits: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> list[PlacementTest]:
        """Start a placement test: one test, or two for a tracking comparison.

        Sends a copy from *sender_account_id* to the seed panel, so it is a
        side-effectful call (an idempotency key is sent automatically). Requires
        the ``send_campaigns`` permission.

        Args:
            sender_account_id: The mailbox to send the test from.
            campaign_id: Test a campaign step's copy (with *sequence_id* and
                optionally *contact_id* to fill its variables).
            sequence_id: The campaign step to test.
            contact_id: A contact to fill the copy's variables from.
            subject: The subject, when not testing a campaign step.
            body_html: The HTML body, when not testing a campaign step.
            body_plain: The plain-text body.
            tracking: ``"campaign"`` (the campaign's own tracking, the default),
                ``"on"``, ``"off"``, or ``"compare"`` to run the same copy
                tracked and untracked.
            panel: ``"instance"`` (the default), ``"workspace"`` or ``"cloud"``.
            seed_ids: Narrow a ``"workspace"`` panel test to these seed inboxes.
            families: Keep only seeds hosted by these providers.
            pace: ``"spaced"`` (the default) or ``"quick"``.
            max_credits: The most you agree to pay for a test past the free
                allowance; a higher price is refused, never charged.
            options: Per-request overrides.
        """
        return list(
            (
                self._post(
                    "/placement/tests",
                    cast_to=_Tests,
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
                        max_credits=max_credits,
                    ),
                    options=options,
                )
            ).data
        )

    def cancel_test(
        self, test_id: str, *, options: RequestOptions | None = None
    ) -> PlacementTest:
        """Stop the copies of a test that have not been sent yet.

        Requires the ``send_campaigns`` permission.
        """
        return (
            self._post(
                f"/placement/tests/{test_id}/cancel",
                cast_to=_Test,
                options=options,
            )
        ).data

    def list_batches(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[PlacementBatch]:
        """List the workspace's placement batches, newest first (auto-paginating).

        Requires the ``read_analytics`` permission.

        Args:
            limit: Batches per page (1 to 100, default 25).
            cursor: Opaque pagination cursor from a previous page.
            options: Per-request overrides.
        """
        return self._get_api_list(
            "/placement/batches",
            model=PlacementBatch,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def retrieve_batch(
        self, batch_id: str, *, options: RequestOptions | None = None
    ) -> PlacementBatchDetail:
        """Retrieve a batch with its placement overall and by sending domain,
        sending provider and recipient provider.

        Requires the ``read_analytics`` permission.
        """
        return (
            self._get(
                f"/placement/batches/{batch_id}",
                cast_to=_BatchDetail,
                options=options,
            )
        ).data

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
        """List a batch's senders with where each one's copies landed.

        Auto-paginating. Requires the ``read_analytics`` permission.

        Args:
            batch_id: The batch id.
            status: Only senders in this status (``queued``, ``deferred``,
                ``running``, ``completed``, ``skipped``, ``failed`` or
                ``cancelled``).
            q: Search the sender address.
            sort: ``"worst"`` (lowest inbox rate first, the default),
                ``"best"``, ``"email"`` or ``"status"``.
            limit: Senders per page (1 to 100, default 25).
            cursor: Opaque pagination cursor from a previous page.
            options: Per-request overrides.
        """
        return self._get_api_list(
            f"/placement/batches/{batch_id}/senders",
            model=PlacementBatchSender,
            query={
                "status": status,
                "q": q,
                "sort": sort,
                "limit": limit,
                "cursor": cursor,
            },
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
        max_credits: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PlacementBatchPreview:
        """Report how many senders, tests, sends and credits a batch would come to.

        Starts nothing. Takes the same arguments as :meth:`create_batch`.
        Requires the ``send_campaigns`` permission.

        Args:
            sender_account_ids: The senders to test from, by id.
            sender_scope: Select senders on the server instead: ``{"type":
                "campaign" | "workspace"}`` plus optional ``campaign_id``,
                ``providers``, ``domains``, ``tag_ids``, ``include_inactive``
                and ``untested_days`` filters.
            sample: Test part of the resolved senders: ``{"mode": "all" |
                "random" | "percent" | "per_domain" | "per_provider"}`` with
                ``count``, ``percent`` or ``stratify`` as the mode needs.
            campaign_id: Test a campaign step's copy.
            sequence_id: The campaign step to test.
            contact_id: A contact to fill the copy's variables from.
            subject: The subject, when not testing a campaign step.
            body_html: The HTML body, when not testing a campaign step.
            body_plain: The plain-text body.
            tracking: ``"campaign"`` (the default), ``"on"``, ``"off"`` or
                ``"compare"``.
            panel: ``"instance"`` (the default), ``"workspace"`` or ``"cloud"``.
            pace: A batch always sends ``"spaced"``.
            families: Keep only seeds hosted by these providers.
            seed_ids: Narrow a ``"workspace"`` panel batch to these seeds.
            on_unavailable: What to do with a sender that cannot run when its
                turn comes: ``"skip"`` or ``"defer"``.
            max_credits: The most you agree to pay across the whole batch for
                tests past the free allowance.
            options: Per-request overrides.
        """
        return (
            self._post(
                "/placement/batches/preview",
                cast_to=_BatchPreview,
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
                    max_credits=max_credits,
                ),
                options=options,
            )
        ).data

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
        max_credits: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PlacementBatch:
        """Queue a placement test from many senders.

        The server snapshots the senders and starts them a few at a time, so
        this is a side-effectful call (an idempotency key is sent
        automatically). Requires the ``send_campaigns`` permission.

        Args:
            sender_account_ids: The senders to test from, by id.
            sender_scope: Select senders on the server instead: ``{"type":
                "campaign" | "workspace"}`` plus optional ``campaign_id``,
                ``providers``, ``domains``, ``tag_ids``, ``include_inactive``
                and ``untested_days`` filters.
            sample: Test part of the resolved senders: ``{"mode": "all" |
                "random" | "percent" | "per_domain" | "per_provider"}`` with
                ``count``, ``percent`` or ``stratify`` as the mode needs.
            campaign_id: Test a campaign step's copy.
            sequence_id: The campaign step to test.
            contact_id: A contact to fill the copy's variables from.
            subject: The subject, when not testing a campaign step.
            body_html: The HTML body, when not testing a campaign step.
            body_plain: The plain-text body.
            tracking: ``"campaign"`` (the default), ``"on"``, ``"off"`` or
                ``"compare"``.
            panel: ``"instance"`` (the default), ``"workspace"`` or ``"cloud"``.
            pace: A batch always sends ``"spaced"``.
            families: Keep only seeds hosted by these providers.
            seed_ids: Narrow a ``"workspace"`` panel batch to these seeds.
            on_unavailable: What to do with a sender that cannot run when its
                turn comes: ``"skip"`` or ``"defer"``.
            max_credits: The most you agree to pay across the whole batch for
                tests past the free allowance.
            options: Per-request overrides.
        """
        return (
            self._post(
                "/placement/batches",
                cast_to=_Batch,
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
                    max_credits=max_credits,
                ),
                options=options,
            )
        ).data

    def cancel_batch(
        self, batch_id: str, *, options: RequestOptions | None = None
    ) -> PlacementBatch:
        """Stop a batch. Copies already sent keep being classified.

        Requires the ``send_campaigns`` permission.
        """
        return (
            self._post(
                f"/placement/batches/{batch_id}/cancel",
                cast_to=_Batch,
                options=options,
            )
        ).data

    def coverage(self, *, options: RequestOptions | None = None) -> PlacementCoverage:
        """Report how much of the connected fleet delivered a test recently.

        Counts over the last 7 and 30 days. Requires the ``read_analytics``
        permission.
        """
        return (
            self._get("/placement/coverage", cast_to=_Coverage, options=options)
        ).data

    def seeds(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[PlacementWorkspaceSeed]:
        """List the workspace's mailboxes and which of them are seed inboxes.

        Requires the ``read_emails`` permission.
        """
        return self._get_api_list(
            "/placement/seeds", model=PlacementWorkspaceSeed, options=options
        )

    def set_seed(
        self,
        email_id: str,
        *,
        seed: bool,
        options: RequestOptions | None = None,
    ) -> PlacementWorkspaceSeed:
        """Make a workspace mailbox a seed inbox, or stop it being one.

        Setting the same value again lands on the same state. Requires the
        ``write_emails`` permission.

        Args:
            email_id: The mailbox id.
            seed: ``True`` to use it as a seed inbox, ``False`` to stop.
            options: Per-request overrides.
        """
        return (
            self._put(
                f"/placement/seeds/{email_id}",
                cast_to=_Seed,
                body={"seed": seed},
                options=options,
            )
        ).data


class AsyncPlacement(AsyncAPIResource):
    """Asynchronous ``placement`` resource."""

    async def overview(
        self, *, options: RequestOptions | None = None
    ) -> PlacementOverview:
        """Read the seed panels this workspace can test on and its allowance.

        Requires the ``read_analytics`` permission.
        """
        return (
            await self._get("/placement/overview", cast_to=_Overview, options=options)
        ).data

    def list_tests(
        self,
        *,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[PlacementTest]:
        """List the workspace's placement tests, newest first (auto-paginating).

        Tests a batch started are listed under the batch instead. Requires the
        ``read_analytics`` permission.

        Args:
            campaign_id: Only tests for this campaign.
            limit: Tests per page (1 to 100, default 25).
            cursor: Opaque pagination cursor from a previous page.
            options: Per-request overrides.
        """
        return self._get_api_list(
            "/placement/tests",
            model=PlacementTest,
            query={"campaign_id": campaign_id, "limit": limit, "cursor": cursor},
            options=options,
        )

    async def retrieve_test(
        self, test_id: str, *, options: RequestOptions | None = None
    ) -> PlacementTestDetail:
        """Retrieve one test with every probe and the content check.

        Requires the ``read_analytics`` permission.
        """
        return (
            await self._get(
                f"/placement/tests/{test_id}", cast_to=_TestDetail, options=options
            )
        ).data

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
        max_credits: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> list[PlacementTest]:
        """Start a placement test: one test, or two for a tracking comparison.

        Sends a copy from *sender_account_id* to the seed panel, so it is a
        side-effectful call (an idempotency key is sent automatically). Requires
        the ``send_campaigns`` permission.

        Args:
            sender_account_id: The mailbox to send the test from.
            campaign_id: Test a campaign step's copy (with *sequence_id* and
                optionally *contact_id* to fill its variables).
            sequence_id: The campaign step to test.
            contact_id: A contact to fill the copy's variables from.
            subject: The subject, when not testing a campaign step.
            body_html: The HTML body, when not testing a campaign step.
            body_plain: The plain-text body.
            tracking: ``"campaign"`` (the campaign's own tracking, the default),
                ``"on"``, ``"off"``, or ``"compare"`` to run the same copy
                tracked and untracked.
            panel: ``"instance"`` (the default), ``"workspace"`` or ``"cloud"``.
            seed_ids: Narrow a ``"workspace"`` panel test to these seed inboxes.
            families: Keep only seeds hosted by these providers.
            pace: ``"spaced"`` (the default) or ``"quick"``.
            max_credits: The most you agree to pay for a test past the free
                allowance; a higher price is refused, never charged.
            options: Per-request overrides.
        """
        return list(
            (
                await self._post(
                    "/placement/tests",
                    cast_to=_Tests,
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
                        max_credits=max_credits,
                    ),
                    options=options,
                )
            ).data
        )

    async def cancel_test(
        self, test_id: str, *, options: RequestOptions | None = None
    ) -> PlacementTest:
        """Stop the copies of a test that have not been sent yet.

        Requires the ``send_campaigns`` permission.
        """
        return (
            await self._post(
                f"/placement/tests/{test_id}/cancel",
                cast_to=_Test,
                options=options,
            )
        ).data

    def list_batches(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[PlacementBatch]:
        """List the workspace's placement batches, newest first (auto-paginating).

        Requires the ``read_analytics`` permission.

        Args:
            limit: Batches per page (1 to 100, default 25).
            cursor: Opaque pagination cursor from a previous page.
            options: Per-request overrides.
        """
        return self._get_api_list(
            "/placement/batches",
            model=PlacementBatch,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def retrieve_batch(
        self, batch_id: str, *, options: RequestOptions | None = None
    ) -> PlacementBatchDetail:
        """Retrieve a batch with its placement overall and by sending domain,
        sending provider and recipient provider.

        Requires the ``read_analytics`` permission.
        """
        return (
            await self._get(
                f"/placement/batches/{batch_id}",
                cast_to=_BatchDetail,
                options=options,
            )
        ).data

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
        """List a batch's senders with where each one's copies landed.

        Auto-paginating. Requires the ``read_analytics`` permission.

        Args:
            batch_id: The batch id.
            status: Only senders in this status (``queued``, ``deferred``,
                ``running``, ``completed``, ``skipped``, ``failed`` or
                ``cancelled``).
            q: Search the sender address.
            sort: ``"worst"`` (lowest inbox rate first, the default),
                ``"best"``, ``"email"`` or ``"status"``.
            limit: Senders per page (1 to 100, default 25).
            cursor: Opaque pagination cursor from a previous page.
            options: Per-request overrides.
        """
        return self._get_api_list(
            f"/placement/batches/{batch_id}/senders",
            model=PlacementBatchSender,
            query={
                "status": status,
                "q": q,
                "sort": sort,
                "limit": limit,
                "cursor": cursor,
            },
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
        max_credits: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PlacementBatchPreview:
        """Report how many senders, tests, sends and credits a batch would come to.

        Starts nothing. Takes the same arguments as :meth:`create_batch`.
        Requires the ``send_campaigns`` permission.

        Args:
            sender_account_ids: The senders to test from, by id.
            sender_scope: Select senders on the server instead: ``{"type":
                "campaign" | "workspace"}`` plus optional ``campaign_id``,
                ``providers``, ``domains``, ``tag_ids``, ``include_inactive``
                and ``untested_days`` filters.
            sample: Test part of the resolved senders: ``{"mode": "all" |
                "random" | "percent" | "per_domain" | "per_provider"}`` with
                ``count``, ``percent`` or ``stratify`` as the mode needs.
            campaign_id: Test a campaign step's copy.
            sequence_id: The campaign step to test.
            contact_id: A contact to fill the copy's variables from.
            subject: The subject, when not testing a campaign step.
            body_html: The HTML body, when not testing a campaign step.
            body_plain: The plain-text body.
            tracking: ``"campaign"`` (the default), ``"on"``, ``"off"`` or
                ``"compare"``.
            panel: ``"instance"`` (the default), ``"workspace"`` or ``"cloud"``.
            pace: A batch always sends ``"spaced"``.
            families: Keep only seeds hosted by these providers.
            seed_ids: Narrow a ``"workspace"`` panel batch to these seeds.
            on_unavailable: What to do with a sender that cannot run when its
                turn comes: ``"skip"`` or ``"defer"``.
            max_credits: The most you agree to pay across the whole batch for
                tests past the free allowance.
            options: Per-request overrides.
        """
        return (
            await self._post(
                "/placement/batches/preview",
                cast_to=_BatchPreview,
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
                    max_credits=max_credits,
                ),
                options=options,
            )
        ).data

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
        max_credits: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PlacementBatch:
        """Queue a placement test from many senders.

        The server snapshots the senders and starts them a few at a time, so
        this is a side-effectful call (an idempotency key is sent
        automatically). Requires the ``send_campaigns`` permission.

        Args:
            sender_account_ids: The senders to test from, by id.
            sender_scope: Select senders on the server instead: ``{"type":
                "campaign" | "workspace"}`` plus optional ``campaign_id``,
                ``providers``, ``domains``, ``tag_ids``, ``include_inactive``
                and ``untested_days`` filters.
            sample: Test part of the resolved senders: ``{"mode": "all" |
                "random" | "percent" | "per_domain" | "per_provider"}`` with
                ``count``, ``percent`` or ``stratify`` as the mode needs.
            campaign_id: Test a campaign step's copy.
            sequence_id: The campaign step to test.
            contact_id: A contact to fill the copy's variables from.
            subject: The subject, when not testing a campaign step.
            body_html: The HTML body, when not testing a campaign step.
            body_plain: The plain-text body.
            tracking: ``"campaign"`` (the default), ``"on"``, ``"off"`` or
                ``"compare"``.
            panel: ``"instance"`` (the default), ``"workspace"`` or ``"cloud"``.
            pace: A batch always sends ``"spaced"``.
            families: Keep only seeds hosted by these providers.
            seed_ids: Narrow a ``"workspace"`` panel batch to these seeds.
            on_unavailable: What to do with a sender that cannot run when its
                turn comes: ``"skip"`` or ``"defer"``.
            max_credits: The most you agree to pay across the whole batch for
                tests past the free allowance.
            options: Per-request overrides.
        """
        return (
            await self._post(
                "/placement/batches",
                cast_to=_Batch,
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
                    max_credits=max_credits,
                ),
                options=options,
            )
        ).data

    async def cancel_batch(
        self, batch_id: str, *, options: RequestOptions | None = None
    ) -> PlacementBatch:
        """Stop a batch. Copies already sent keep being classified.

        Requires the ``send_campaigns`` permission.
        """
        return (
            await self._post(
                f"/placement/batches/{batch_id}/cancel",
                cast_to=_Batch,
                options=options,
            )
        ).data

    async def coverage(
        self, *, options: RequestOptions | None = None
    ) -> PlacementCoverage:
        """Report how much of the connected fleet delivered a test recently.

        Counts over the last 7 and 30 days. Requires the ``read_analytics``
        permission.
        """
        return (
            await self._get("/placement/coverage", cast_to=_Coverage, options=options)
        ).data

    def seeds(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[PlacementWorkspaceSeed]:
        """List the workspace's mailboxes and which of them are seed inboxes.

        Requires the ``read_emails`` permission.
        """
        return self._get_api_list(
            "/placement/seeds", model=PlacementWorkspaceSeed, options=options
        )

    async def set_seed(
        self,
        email_id: str,
        *,
        seed: bool,
        options: RequestOptions | None = None,
    ) -> PlacementWorkspaceSeed:
        """Make a workspace mailbox a seed inbox, or stop it being one.

        Setting the same value again lands on the same state. Requires the
        ``write_emails`` permission.

        Args:
            email_id: The mailbox id.
            seed: ``True`` to use it as a seed inbox, ``False`` to stop.
            options: Per-request overrides.
        """
        return (
            await self._put(
                f"/placement/seeds/{email_id}",
                cast_to=_Seed,
                body={"seed": seed},
                options=options,
            )
        ).data
