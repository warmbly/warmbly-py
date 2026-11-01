"""The ``placement`` resource: inbox placement tests on seed inboxes.

Maps to the ``/v1/placement`` route group. A placement test sends one copy of
an email (a template, or a campaign step) from one of your mailboxes to a panel
of seed inboxes and reports where each copy landed: the primary inbox, a Gmail
tab, spam, or nowhere. A *batch* runs the same test from many senders at once
and groups the result by sending domain, sending provider and recipient
provider. A campaign can also carry a *monitor* that repeats its first step's
test on a schedule (see :meth:`Campaigns.set_placement_monitor`).

The panel a test sends to is one of ``"instance"`` (the seed inboxes the
operator runs for every workspace), ``"workspace"`` (your own mailboxes marked
as seeds with :meth:`Placement.set_seed`) or ``"cloud"`` (Warmbly Cloud's panel,
for a linked self-hosted instance). The instance and cloud panels count against
a monthly allowance; :meth:`Placement.overview` reports what is left, and
a test past it can be paid for in credits by passing ``max_credits``.

Most calls answer in a ``{"data": ...}`` envelope, which these models keep: the
payload sits on ``.data``. List calls return an auto-paging iterator instead.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGiven, NotGivenOr, RequestOptions
from .._utils import drop_not_given
from ._nullsafe import NullSafeModel

__all__ = [
    "AsyncPlacement",
    "Placement",
    "PlacementBatch",
    "PlacementBatchDetail",
    "PlacementBatchDetailResponse",
    "PlacementBatchPreview",
    "PlacementBatchPreviewResponse",
    "PlacementBatchProgress",
    "PlacementBatchResponse",
    "PlacementBatchSender",
    "PlacementContentCheck",
    "PlacementCounts",
    "PlacementCoverage",
    "PlacementCoverageResponse",
    "PlacementEvidence",
    "PlacementFamilyCounts",
    "PlacementGroup",
    "PlacementGroupCount",
    "PlacementMatrixRow",
    "PlacementMetric",
    "PlacementMonitor",
    "PlacementMonitorDeleted",
    "PlacementMonitorResponse",
    "PlacementOverview",
    "PlacementOverviewResponse",
    "PlacementPanel",
    "PlacementPanelFamily",
    "PlacementResult",
    "PlacementSeed",
    "PlacementSeedResponse",
    "PlacementTest",
    "PlacementTestDetail",
    "PlacementTestDetailResponse",
    "PlacementTestResponse",
    "PlacementTestsResponse",
    "PlacementUsage",
]


# -- models ----------------------------------------------------------------


class PlacementMetric(NullSafeModel):
    """A rate with its denominator and a 95% interval, as the server derives it.

    ``value`` is ``None`` until there is something to divide by.
    ``wilson_95_independence_interval`` is ``{"lower", "upper"}`` when present.
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


class PlacementCounts(NullSafeModel):
    """Where a set of probes landed.

    ``delivered`` is every copy that left and got a verdict (inbox, promotions,
    other, spam, missing). The four ``*_rate`` fields are shares of
    ``delivered`` and stay ``None`` until something is delivered. ``archive``
    is the wire name of the archived count.
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


class PlacementFamilyCounts(NullSafeModel):
    """One recipient host family's share of a test (``google_workspace``, ...)."""

    family: str | None = None
    label: str | None = None
    counts: PlacementCounts | None = None


class PlacementEvidence(NullSafeModel):
    """The authentication evidence read from a received probe's headers."""

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
    dkim_verification: dict[str, Any] | None = None


class PlacementResult(NullSafeModel):
    """One probe: one copy to one seed inbox.

    ``seed`` is the seed's address, masked on the shared panels. ``folder`` is
    one of ``pending``, ``inbox``, ``promotions``, ``other``, ``spam``,
    ``missing``, ``failed``, ``cancelled``, ``unknown``, ``archive`` or
    ``custom``. ``late_observation`` is set when a copy counted as missing
    showed up afterwards.
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


class PlacementContentCheck(NullSafeModel):
    """The rules pass over a test's copy: a ``score`` and its ``issues``.

    Each issue carries ``severity`` (``"warn"`` or ``"high"``), ``code``,
    ``message`` and, when it points at something, ``field``, ``spans`` and
    ``suggestion``.
    """

    score: int | None = None
    issues: Sequence[dict[str, Any]] = []


class PlacementTest(NullSafeModel):
    """One test: a copy sent from one mailbox to a seed panel.

    ``status`` is ``running``, ``completed``, ``cancelled`` or ``failed``.
    ``origin`` says what started it (``manual``, ``monitor``, ``batch``,
    ``admin`` or ``remote``) and ``pace`` is ``spaced`` or ``quick``.
    ``summary`` and ``families`` count where the copies landed overall and per
    recipient family. The copy (``body_html``/``body_plain``) is left out of
    list results. ``compare_group_id`` links the two halves of a tracking
    comparison.
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


class PlacementTestDetail(PlacementTest):
    """A test in full: every probe in ``results``, the ``content`` check and,
    for a tracking comparison, the other half in ``compare``."""

    results: Sequence[PlacementResult] = []
    content: PlacementContentCheck | None = None
    compare: PlacementTest | None = None


class PlacementPanelFamily(NullSafeModel):
    """How many seeds one host family contributes to a panel."""

    family: str | None = None
    label: str | None = None
    seeds: int | None = None


class PlacementPanel(NullSafeModel):
    """Whether the workspace can test on one panel.

    ``reason`` explains an unavailable panel. ``metered`` panels count against
    the monthly allowance.
    """

    panel: str | None = None
    available: bool | None = None
    reason: str | None = None
    seeds: int | None = None
    families: Sequence[PlacementPanelFamily] = []
    metered: bool | None = None


class PlacementUsage(NullSafeModel):
    """The workspace's monthly allowance on the metered panels.

    ``limit`` is ``None`` when the instance does not meter tests.
    ``credits_per_test`` is the price of a test past the allowance (``0`` when
    tests cannot be paid for) and ``credit_balance`` the spendable balance
    (``None`` when credits are off).
    """

    used: int | None = None
    limit: int | None = None
    credits_per_test: int | None = None
    credit_balance: int | None = None
    period_start: str | None = None
    period_end: str | None = None


class PlacementOverview(NullSafeModel):
    """What the workspace can test on and how much of its allowance is left."""

    panels: Sequence[PlacementPanel] = []
    usage: PlacementUsage | None = None
    workspace_seeds: int | None = None
    seeds_per_test: int | None = None
    spacing_seconds: int | None = None


class PlacementSeed(NullSafeModel):
    """One of the workspace's mailboxes as a seed inbox candidate.

    ``seed`` is whether it currently receives tests. ``blocker`` says why a
    mailbox cannot become a seed and is absent when it can.
    """

    email_account_id: str | None = None
    email: str | None = None
    family: str | None = None
    label: str | None = None
    status: str | None = None
    seed: bool | None = None
    blocker: str | None = None


class PlacementMonitor(NullSafeModel):
    """A campaign's scheduled placement test.

    It re-tests the campaign's first email step every ``interval_days`` (1 to
    30) and raises an alert when the inbox rate falls below ``alert_below``
    percent, optionally pausing the campaign (``pause_on_alert``).
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


class PlacementMonitorDeleted(NullSafeModel):
    """The result of removing a placement monitor (``204 No Content``)."""

    campaign_id: str | None = None
    deleted: bool | None = None


class PlacementBatchProgress(NullSafeModel):
    """A batch's senders counted by status."""

    total: int | None = None
    queued: int | None = None
    deferred: int | None = None
    running: int | None = None
    completed: int | None = None
    skipped: int | None = None
    failed: int | None = None
    cancelled: int | None = None


class PlacementBatch(NullSafeModel):
    """One placement test run from many senders.

    ``status`` is ``queued``, ``running``, ``completed``,
    ``completed_with_warnings``, ``cancelled`` or ``failed``. ``selection``
    records how the senders were chosen (``sender_account_ids`` count,
    ``sender_scope``, ``sample``, ``matched``). ``progress`` counts the senders
    by status and ``summary`` is where the headline copy landed.
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
    status: str | None = None
    error: str | None = None
    retry_until: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    progress: PlacementBatchProgress | None = None
    summary: PlacementCounts | None = None


class PlacementGroup(NullSafeModel):
    """A batch's placement for one sending domain or sending provider."""

    key: str | None = None
    label: str | None = None
    senders: int | None = None
    tested: int | None = None
    counts: PlacementCounts | None = None


class PlacementMatrixRow(NullSafeModel):
    """One sending domain's placement per recipient provider."""

    domain: str | None = None
    recipients: Sequence[PlacementFamilyCounts] = []


class PlacementBatchDetail(PlacementBatch):
    """A batch in full, grouped by sending domain, sending provider and
    recipient provider. ``untracked`` is the untracked half of a tracking
    comparison, where ``summary`` is the tracked half."""

    untracked: PlacementCounts | None = None
    domains: Sequence[PlacementGroup] = []
    providers: Sequence[PlacementGroup] = []
    recipients: Sequence[PlacementFamilyCounts] = []
    matrix: Sequence[PlacementMatrixRow] = []
    content: PlacementContentCheck | None = None


class PlacementBatchSender(NullSafeModel):
    """One sender of a batch and where its copies landed.

    ``status`` is ``queued``, ``deferred``, ``running``, ``completed``,
    ``skipped``, ``failed`` or ``cancelled``; ``reason`` and ``detail`` say why
    a sender was skipped or deferred. ``test_ids`` are the tests it ran.
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


class PlacementGroupCount(NullSafeModel):
    """How many selected senders share a provider."""

    key: str | None = None
    label: str | None = None
    senders: int | None = None


class PlacementBatchPreview(NullSafeModel):
    """What a batch would do, before it is started. Nothing is queued.

    ``matched`` is how many senders the scope resolved to and ``selected`` how
    many the sample kept. ``variants`` is 2 for a tracking comparison.
    ``max_sends`` is the most probes the batch sends. On a metered panel,
    ``free_tests`` and ``paid_tests`` split ``tests`` against the allowance and
    ``credits`` is the most the paid ones cost; pass at least that as
    ``max_credits`` to start the batch.
    """

    matched: int | None = None
    selected: int | None = None
    inactive: int | None = None
    domains: int | None = None
    providers: Sequence[PlacementGroupCount] = []
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


class PlacementCoverage(NullSafeModel):
    """How much of the workspace's connected fleet delivered a placement test
    in the last 7 and 30 days."""

    mailboxes: int | None = None
    tested_7d: int | None = None
    tested_30d: int | None = None
    never_tested: int | None = None


class PlacementOverviewResponse(NullSafeModel):
    """``{"data": PlacementOverview}``."""

    data: PlacementOverview | None = None


class PlacementTestsResponse(NullSafeModel):
    """The tests a create call started: one, or two for a tracking comparison."""

    data: Sequence[PlacementTest] = []


class PlacementTestResponse(NullSafeModel):
    """``{"data": PlacementTest}``."""

    data: PlacementTest | None = None


class PlacementTestDetailResponse(NullSafeModel):
    """``{"data": PlacementTestDetail}``."""

    data: PlacementTestDetail | None = None


class PlacementSeedResponse(NullSafeModel):
    """``{"data": PlacementSeed}``."""

    data: PlacementSeed | None = None


class PlacementMonitorResponse(NullSafeModel):
    """``{"data": PlacementMonitor}``; ``data`` is ``None`` when the campaign
    has no monitor."""

    data: PlacementMonitor | None = None


class PlacementBatchResponse(NullSafeModel):
    """``{"data": PlacementBatch}``."""

    data: PlacementBatch | None = None


class PlacementBatchDetailResponse(NullSafeModel):
    """``{"data": PlacementBatchDetail}``."""

    data: PlacementBatchDetail | None = None


class PlacementBatchPreviewResponse(NullSafeModel):
    """``{"data": PlacementBatchPreview}``."""

    data: PlacementBatchPreview | None = None


class PlacementCoverageResponse(NullSafeModel):
    """``{"data": PlacementCoverage}``."""

    data: PlacementCoverage | None = None


def _listed(value: NotGivenOr[Sequence[str]]) -> NotGivenOr[list[str]]:
    """Copy a sequence into a list, leaving an omitted argument omitted."""
    return value if isinstance(value, NotGiven) else list(value)


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
    """Build the single-test body."""
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
            "seed_ids": _listed(seed_ids),
            "families": _listed(families),
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
    """Build the body shared by the batch preview and create calls."""
    return drop_not_given(
        {
            "sender_account_ids": _listed(sender_account_ids),
            "sender_scope": (
                sender_scope
                if isinstance(sender_scope, NotGiven)
                else dict(sender_scope)
            ),
            "sample": sample if isinstance(sample, NotGiven) else dict(sample),
            "campaign_id": campaign_id,
            "sequence_id": sequence_id,
            "contact_id": contact_id,
            "subject": subject,
            "body_html": body_html,
            "body_plain": body_plain,
            "tracking": tracking,
            "panel": panel,
            "pace": pace,
            "families": _listed(families),
            "seed_ids": _listed(seed_ids),
            "on_unavailable": on_unavailable,
            "max_credits": max_credits,
        }
    )


# -- resource --------------------------------------------------------------


class Placement(SyncAPIResource):
    """Synchronous ``placement`` resource."""

    # -- workspace --------------------------------------------------------
    def overview(
        self, *, options: RequestOptions | None = None
    ) -> PlacementOverviewResponse:
        """Report which seed panels the workspace can test on and its allowance.

        Requires the view-analytics permission (API scope ``read_analytics``).
        """
        return self._get(
            "/placement/overview", cast_to=PlacementOverviewResponse, options=options
        )

    def coverage(
        self, *, options: RequestOptions | None = None
    ) -> PlacementCoverageResponse:
        """Report how much of the connected fleet delivered a test recently.

        Counts the mailboxes tested in the last 7 and 30 days and those never
        tested.

        Requires the view-analytics permission (API scope ``read_analytics``).
        """
        return self._get(
            "/placement/coverage", cast_to=PlacementCoverageResponse, options=options
        )

    # -- seeds ------------------------------------------------------------
    def list_seeds(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[PlacementSeed]:
        """List the workspace's mailboxes and which of them are seed inboxes.

        The list is not paged by the server, so iterating yields one page. A
        key limited to some mailboxes only sees those.

        Requires the view-campaigns permission to read mailboxes (API scope
        ``read_emails``).
        """
        return self._get_api_list(
            "/placement/seeds", model=PlacementSeed, options=options
        )

    def set_seed(
        self,
        email_account_id: str,
        *,
        seed: bool,
        options: RequestOptions | None = None,
    ) -> PlacementSeedResponse:
        """Make a workspace mailbox a seed inbox, or stop it being one.

        Seeds receive the workspace panel's tests; a seed cannot send a test.
        The mailbox's ``blocker`` explains why one cannot become a seed.

        Requires the manage-emails permission (API scope ``write_emails``).

        Args:
            email_account_id: The mailbox id.
            seed: ``True`` to make it a seed, ``False`` to take it off.
        """
        return self._put(
            f"/placement/seeds/{email_account_id}",
            cast_to=PlacementSeedResponse,
            body={"seed": seed},
            options=options,
        )

    # -- tests ------------------------------------------------------------
    def list_tests(
        self,
        *,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[PlacementTest]:
        """List the workspace's placement tests, newest first (auto-paginating).

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            campaign_id: Only tests of this campaign.
            limit: Page size (1-100; the server defaults to 25).
        """
        return self._get_api_list(
            "/placement/tests",
            model=PlacementTest,
            query={"campaign_id": campaign_id, "limit": limit, "cursor": cursor},
            options=options,
        )

    def retrieve_test(
        self, test_id: str, *, options: RequestOptions | None = None
    ) -> PlacementTestDetailResponse:
        """Retrieve one test with every probe, the content check and, for a
        tracking comparison, the other half.

        Requires the view-analytics permission (API scope ``read_analytics``).
        """
        return self._get(
            f"/placement/tests/{test_id}",
            cast_to=PlacementTestDetailResponse,
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
        max_credits: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PlacementTestsResponse:
        """Start a placement test: one, or two for a tracking comparison.

        This sends real mail from the mailbox to the seed panel. Name the copy
        either with a campaign step (``campaign_id`` and ``sequence_id``,
        optionally a ``contact_id`` to render it for) or write it inline
        (``subject`` with ``body_html`` and/or ``body_plain``).

        Requires the send-campaigns permission (API scope ``send_campaigns``).
        The call carries an ``Idempotency-Key``, so a retry does not start a
        second test.

        Args:
            sender_account_id: The mailbox to send from. It must be connected
                and running, and not itself a seed.
            campaign_id: A campaign whose step to test.
            sequence_id: The campaign step to test.
            contact_id: A contact to render the copy for.
            subject: The subject, for an inline copy.
            body_html: The HTML body, for an inline copy.
            body_plain: The plain-text body, for an inline copy.
            tracking: ``"campaign"`` (default; copy the campaign's own
                tracking, none for an inline copy), ``"on"``, ``"off"`` or
                ``"compare"`` (send the copy twice, tracked and untracked).
            panel: ``"instance"`` (default), ``"workspace"`` or ``"cloud"``.
            seed_ids: Specific workspace seeds to send to; needs
                ``panel="workspace"``.
            families: Only seeds hosted by these providers (for example
                ``"gmail"``); omit for all.
            pace: ``"spaced"`` (default, about a minute apart) or ``"quick"``
                (a few seconds apart, for a result in minutes).
            max_credits: The most you agree to pay in credits when the test
                goes past the monthly allowance. Without it, a test past the
                allowance is refused with the price in the message.
        """
        return self._post(
            "/placement/tests",
            cast_to=PlacementTestsResponse,
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

    def cancel_test(
        self, test_id: str, *, options: RequestOptions | None = None
    ) -> PlacementTestResponse:
        """Stop the copies of a test that have not been sent yet.

        Requires the send-campaigns permission (API scope ``send_campaigns``).
        """
        return self._post(
            f"/placement/tests/{test_id}/cancel",
            cast_to=PlacementTestResponse,
            options=options,
        )

    # -- batches ----------------------------------------------------------
    def list_batches(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[PlacementBatch]:
        """List the workspace's placement batches, newest first (auto-paginating).

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            limit: Page size (1-100; the server defaults to 25).
        """
        return self._get_api_list(
            "/placement/batches",
            model=PlacementBatch,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def retrieve_batch(
        self, batch_id: str, *, options: RequestOptions | None = None
    ) -> PlacementBatchDetailResponse:
        """Retrieve one batch with its placement overall and grouped by sending
        domain, sending provider and recipient provider.

        Requires the view-analytics permission (API scope ``read_analytics``).
        """
        return self._get(
            f"/placement/batches/{batch_id}",
            cast_to=PlacementBatchDetailResponse,
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

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            batch_id: The batch id.
            status: Only senders in this status (``queued``, ``deferred``,
                ``running``, ``completed``, ``skipped``, ``failed`` or
                ``cancelled``).
            q: Search by sender address.
            sort: ``"worst"`` (lowest inbox rate first, the default),
                ``"best"``, ``"email"`` or ``"status"``.
            limit: Page size (1-100; the server defaults to 25).
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
    ) -> PlacementBatchPreviewResponse:
        """Report how many senders, tests, sends and credits a batch would
        come to. Nothing is started.

        Takes the same arguments as :meth:`create_batch`.

        Requires the send-campaigns permission (API scope ``send_campaigns``).
        """
        return self._post(
            "/placement/batches/preview",
            cast_to=PlacementBatchPreviewResponse,
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
    ) -> PlacementBatchResponse:
        """Run a placement test from many senders.

        The senders are snapshotted and queued; the backend starts a few at a
        time. This sends real mail. Choose the senders with *either*
        ``sender_account_ids`` or ``sender_scope``. Run :meth:`preview_batch`
        first to see the size and cost.

        Requires the send-campaigns permission (API scope ``send_campaigns``).
        The call carries an ``Idempotency-Key``, so a retry does not queue a
        second batch.

        Args:
            sender_account_ids: Explicit sender mailbox ids.
            sender_scope: A server-side selection, so a large fleet needs no id
                list: ``{"type": "campaign" | "workspace", "campaign_id": ...,
                "providers": [...], "domains": [...], "tag_ids": [...],
                "include_inactive": bool, "untested_days": int}``. A
                ``"campaign"`` scope needs ``campaign_id``.
            sample: Pick part of the resolved senders: ``{"mode": "all" |
                "random" | "percent" | "per_domain" | "per_provider",
                "count": int, "percent": int, "stratify": "provider" |
                "domain"}``.
            campaign_id: A campaign whose step to test.
            sequence_id: The campaign step to test.
            contact_id: A contact to render the copy for.
            subject: The subject, for an inline copy.
            body_html: The HTML body, for an inline copy.
            body_plain: The plain-text body, for an inline copy.
            tracking: ``"campaign"`` (default), ``"on"``, ``"off"`` or
                ``"compare"``.
            panel: ``"instance"`` (default), ``"workspace"`` or ``"cloud"``.
            pace: Batches always send spaced; leave unset or ``"spaced"``.
            families: Only seeds hosted by these providers.
            seed_ids: Specific workspace seeds; needs ``panel="workspace"``.
            on_unavailable: What to do with a sender that cannot run when its
                turn comes: ``"defer"`` (default, retry later) or ``"skip"``.
            max_credits: The most you agree to pay in credits across the whole
                batch for tests past the monthly allowance.
        """
        return self._post(
            "/placement/batches",
            cast_to=PlacementBatchResponse,
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

    def cancel_batch(
        self, batch_id: str, *, options: RequestOptions | None = None
    ) -> PlacementBatchResponse:
        """Stop a batch. Copies already sent keep being classified.

        Requires the send-campaigns permission (API scope ``send_campaigns``).
        """
        return self._post(
            f"/placement/batches/{batch_id}/cancel",
            cast_to=PlacementBatchResponse,
            options=options,
        )


class AsyncPlacement(AsyncAPIResource):
    """Asynchronous ``placement`` resource."""

    # -- workspace --------------------------------------------------------
    async def overview(
        self, *, options: RequestOptions | None = None
    ) -> PlacementOverviewResponse:
        """Report which seed panels the workspace can test on and its allowance.

        Requires the view-analytics permission (API scope ``read_analytics``).
        """
        return await self._get(
            "/placement/overview", cast_to=PlacementOverviewResponse, options=options
        )

    async def coverage(
        self, *, options: RequestOptions | None = None
    ) -> PlacementCoverageResponse:
        """Report how much of the connected fleet delivered a test recently.

        Counts the mailboxes tested in the last 7 and 30 days and those never
        tested.

        Requires the view-analytics permission (API scope ``read_analytics``).
        """
        return await self._get(
            "/placement/coverage", cast_to=PlacementCoverageResponse, options=options
        )

    # -- seeds ------------------------------------------------------------
    def list_seeds(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[PlacementSeed]:
        """List the workspace's mailboxes and which of them are seed inboxes.

        The list is not paged by the server, so iterating yields one page. A
        key limited to some mailboxes only sees those.

        Requires the view-campaigns permission to read mailboxes (API scope
        ``read_emails``).
        """
        return self._get_api_list(
            "/placement/seeds", model=PlacementSeed, options=options
        )

    async def set_seed(
        self,
        email_account_id: str,
        *,
        seed: bool,
        options: RequestOptions | None = None,
    ) -> PlacementSeedResponse:
        """Make a workspace mailbox a seed inbox, or stop it being one.

        Seeds receive the workspace panel's tests; a seed cannot send a test.
        The mailbox's ``blocker`` explains why one cannot become a seed.

        Requires the manage-emails permission (API scope ``write_emails``).

        Args:
            email_account_id: The mailbox id.
            seed: ``True`` to make it a seed, ``False`` to take it off.
        """
        return await self._put(
            f"/placement/seeds/{email_account_id}",
            cast_to=PlacementSeedResponse,
            body={"seed": seed},
            options=options,
        )

    # -- tests ------------------------------------------------------------
    def list_tests(
        self,
        *,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[PlacementTest]:
        """List the workspace's placement tests, newest first (auto-paginating).

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            campaign_id: Only tests of this campaign.
            limit: Page size (1-100; the server defaults to 25).
        """
        return self._get_api_list(
            "/placement/tests",
            model=PlacementTest,
            query={"campaign_id": campaign_id, "limit": limit, "cursor": cursor},
            options=options,
        )

    async def retrieve_test(
        self, test_id: str, *, options: RequestOptions | None = None
    ) -> PlacementTestDetailResponse:
        """Retrieve one test with every probe, the content check and, for a
        tracking comparison, the other half.

        Requires the view-analytics permission (API scope ``read_analytics``).
        """
        return await self._get(
            f"/placement/tests/{test_id}",
            cast_to=PlacementTestDetailResponse,
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
        max_credits: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PlacementTestsResponse:
        """Start a placement test: one, or two for a tracking comparison.

        This sends real mail from the mailbox to the seed panel. Name the copy
        either with a campaign step (``campaign_id`` and ``sequence_id``,
        optionally a ``contact_id`` to render it for) or write it inline
        (``subject`` with ``body_html`` and/or ``body_plain``).

        Requires the send-campaigns permission (API scope ``send_campaigns``).
        The call carries an ``Idempotency-Key``, so a retry does not start a
        second test.

        Args:
            sender_account_id: The mailbox to send from. It must be connected
                and running, and not itself a seed.
            campaign_id: A campaign whose step to test.
            sequence_id: The campaign step to test.
            contact_id: A contact to render the copy for.
            subject: The subject, for an inline copy.
            body_html: The HTML body, for an inline copy.
            body_plain: The plain-text body, for an inline copy.
            tracking: ``"campaign"`` (default; copy the campaign's own
                tracking, none for an inline copy), ``"on"``, ``"off"`` or
                ``"compare"`` (send the copy twice, tracked and untracked).
            panel: ``"instance"`` (default), ``"workspace"`` or ``"cloud"``.
            seed_ids: Specific workspace seeds to send to; needs
                ``panel="workspace"``.
            families: Only seeds hosted by these providers (for example
                ``"gmail"``); omit for all.
            pace: ``"spaced"`` (default, about a minute apart) or ``"quick"``
                (a few seconds apart, for a result in minutes).
            max_credits: The most you agree to pay in credits when the test
                goes past the monthly allowance. Without it, a test past the
                allowance is refused with the price in the message.
        """
        return await self._post(
            "/placement/tests",
            cast_to=PlacementTestsResponse,
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

    async def cancel_test(
        self, test_id: str, *, options: RequestOptions | None = None
    ) -> PlacementTestResponse:
        """Stop the copies of a test that have not been sent yet.

        Requires the send-campaigns permission (API scope ``send_campaigns``).
        """
        return await self._post(
            f"/placement/tests/{test_id}/cancel",
            cast_to=PlacementTestResponse,
            options=options,
        )

    # -- batches ----------------------------------------------------------
    def list_batches(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[PlacementBatch]:
        """List the workspace's placement batches, newest first (auto-paginating).

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            limit: Page size (1-100; the server defaults to 25).
        """
        return self._get_api_list(
            "/placement/batches",
            model=PlacementBatch,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def retrieve_batch(
        self, batch_id: str, *, options: RequestOptions | None = None
    ) -> PlacementBatchDetailResponse:
        """Retrieve one batch with its placement overall and grouped by sending
        domain, sending provider and recipient provider.

        Requires the view-analytics permission (API scope ``read_analytics``).
        """
        return await self._get(
            f"/placement/batches/{batch_id}",
            cast_to=PlacementBatchDetailResponse,
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

        Requires the view-analytics permission (API scope ``read_analytics``).

        Args:
            batch_id: The batch id.
            status: Only senders in this status (``queued``, ``deferred``,
                ``running``, ``completed``, ``skipped``, ``failed`` or
                ``cancelled``).
            q: Search by sender address.
            sort: ``"worst"`` (lowest inbox rate first, the default),
                ``"best"``, ``"email"`` or ``"status"``.
            limit: Page size (1-100; the server defaults to 25).
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
    ) -> PlacementBatchPreviewResponse:
        """Report how many senders, tests, sends and credits a batch would
        come to. Nothing is started.

        Takes the same arguments as :meth:`create_batch`.

        Requires the send-campaigns permission (API scope ``send_campaigns``).
        """
        return await self._post(
            "/placement/batches/preview",
            cast_to=PlacementBatchPreviewResponse,
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
    ) -> PlacementBatchResponse:
        """Run a placement test from many senders.

        The senders are snapshotted and queued; the backend starts a few at a
        time. This sends real mail. Choose the senders with *either*
        ``sender_account_ids`` or ``sender_scope``. Run :meth:`preview_batch`
        first to see the size and cost.

        Requires the send-campaigns permission (API scope ``send_campaigns``).
        The call carries an ``Idempotency-Key``, so a retry does not queue a
        second batch.

        Args:
            sender_account_ids: Explicit sender mailbox ids.
            sender_scope: A server-side selection, so a large fleet needs no id
                list: ``{"type": "campaign" | "workspace", "campaign_id": ...,
                "providers": [...], "domains": [...], "tag_ids": [...],
                "include_inactive": bool, "untested_days": int}``. A
                ``"campaign"`` scope needs ``campaign_id``.
            sample: Pick part of the resolved senders: ``{"mode": "all" |
                "random" | "percent" | "per_domain" | "per_provider",
                "count": int, "percent": int, "stratify": "provider" |
                "domain"}``.
            campaign_id: A campaign whose step to test.
            sequence_id: The campaign step to test.
            contact_id: A contact to render the copy for.
            subject: The subject, for an inline copy.
            body_html: The HTML body, for an inline copy.
            body_plain: The plain-text body, for an inline copy.
            tracking: ``"campaign"`` (default), ``"on"``, ``"off"`` or
                ``"compare"``.
            panel: ``"instance"`` (default), ``"workspace"`` or ``"cloud"``.
            pace: Batches always send spaced; leave unset or ``"spaced"``.
            families: Only seeds hosted by these providers.
            seed_ids: Specific workspace seeds; needs ``panel="workspace"``.
            on_unavailable: What to do with a sender that cannot run when its
                turn comes: ``"defer"`` (default, retry later) or ``"skip"``.
            max_credits: The most you agree to pay in credits across the whole
                batch for tests past the monthly allowance.
        """
        return await self._post(
            "/placement/batches",
            cast_to=PlacementBatchResponse,
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

    async def cancel_batch(
        self, batch_id: str, *, options: RequestOptions | None = None
    ) -> PlacementBatchResponse:
        """Stop a batch. Copies already sent keep being classified.

        Requires the send-campaigns permission (API scope ``send_campaigns``).
        """
        return await self._post(
            f"/placement/batches/{batch_id}/cancel",
            cast_to=PlacementBatchResponse,
            options=options,
        )
