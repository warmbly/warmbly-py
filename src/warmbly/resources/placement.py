"""The ``placement`` resource: inbox placement tests and batches.

Maps to the ``/v1/placement`` route group.

A *placement test* sends one real message (a campaign step, a template, or
ad-hoc copy) from one of your mailboxes to a panel of seed inboxes at the major
mailbox providers, then reports where each copy landed: ``inbox``,
``promotions`` or another Gmail tab, ``spam``, ``missing`` and so on. The
result counts everything overall and per recipient provider, adds the
authentication evidence the seed saw, and runs a content check over the copy.
``tracking="compare"`` sends the same copy twice, tracked and untracked, so the
cost of tracking shows up directly; that returns two tests from
:meth:`Placement.create_tests`.

Tests run on a *panel*: ``instance`` (the operator's seed inboxes),
``workspace`` (your own mailboxes marked as seeds with :meth:`Placement.set_seed`)
or ``cloud`` (Warmbly Cloud's panel for a linked self-hosted instance).
:meth:`Placement.overview` says which panels you can use and how much of the
monthly allowance is left. Starting a test sends real mail, so it needs the
``SEND_CAMPAIGNS`` permission; reading results needs ``READ_ANALYTICS``.

A *batch* runs the same test from many mailboxes. Choose the senders with
exactly one of ``sender_account_ids`` (an explicit list) or ``sender_scope``
(a server-side filter such as the whole workspace or one campaign's senders,
narrowed by provider, domain, tag, or "not tested in N days"), optionally keep
only a ``sample`` of them, and the backend starts them a few at a time.
:meth:`Placement.preview_batch` takes the same arguments and reports what the
batch would cost without starting anything. Tests started by a batch are read
through the batch, not :meth:`Placement.list_tests`.
"""

from __future__ import annotations

import contextlib
from collections.abc import Mapping, Sequence
from typing import Any, Generic, TypeVar

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncPlacement",
    "BatchGroupCount",
    "ContentCheck",
    "ContentIssue",
    "ContentSpan",
    "ObservationInterval",
    "ObservationMetric",
    "Placement",
    "PlacementBatch",
    "PlacementBatchDetail",
    "PlacementBatchGroup",
    "PlacementBatchMatrixRow",
    "PlacementBatchPreview",
    "PlacementBatchProgress",
    "PlacementBatchSelection",
    "PlacementBatchSender",
    "PlacementCounts",
    "PlacementCoverage",
    "PlacementDkimVerification",
    "PlacementEvidence",
    "PlacementFamilyCounts",
    "PlacementOverview",
    "PlacementPanelFamily",
    "PlacementPanelInfo",
    "PlacementResult",
    "PlacementSample",
    "PlacementSeed",
    "PlacementSenderScope",
    "PlacementTest",
    "PlacementTestDetail",
    "PlacementUsage",
]

_D = TypeVar("_D", bound=BaseModel)


class _Data(BaseModel, Generic[_D]):
    """The ``{"data": ...}`` envelope the placement routes wrap results in."""

    data: _D


class _DataList(BaseModel, Generic[_D]):
    """The ``{"data": [...]}`` envelope around a list of results."""

    data: list[_D]


def _unwrap(envelope: _Data[_D]) -> _D:
    """Return the enveloped payload, carrying the request id across."""
    inner = envelope.data
    with contextlib.suppress(AttributeError):  # a malformed payload stays raw
        inner._request_id = envelope._request_id
    return inner


def _unwrap_list(envelope: _DataList[_D]) -> list[_D]:
    """Return an enveloped list, carrying the request id onto each item."""
    for item in envelope.data:
        with contextlib.suppress(AttributeError):  # a malformed item stays raw
            item._request_id = envelope._request_id
    return envelope.data


class ObservationInterval(BaseModel):
    """A 95% Wilson interval, assuming independent observations."""

    lower: float | None = None
    upper: float | None = None


class ObservationMetric(BaseModel):
    """A rate with the population, denominator and uncertainty behind it."""

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

    ``delivered`` is every copy that left and got a verdict (``inbox`` +
    ``promotions`` + ``other`` + ``spam`` + ``missing``). The ``*_rate`` fields
    are shares of ``delivered`` and are ``None`` until something is delivered.
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
    """One recipient provider family's share of a test or batch."""

    family: str | None = None
    label: str | None = None
    counts: PlacementCounts | None = None


class PlacementDkimVerification(BaseModel):
    """The DKIM verification a seed ran on a received copy."""

    dkim: str | None = None
    alignment: str | None = None
    signing_domain: str | None = None
    verifier: str | None = None
    observed_at: str | None = None


class PlacementEvidence(BaseModel):
    """The authentication evidence a seed recorded for a received copy."""

    dkim_verification: PlacementDkimVerification | None = None
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


class PlacementResult(BaseModel):
    """One probe: one copy sent to one seed inbox.

    ``seed`` is masked on the shared panels. ``folder`` is ``pending``,
    ``inbox``, ``promotions``, ``other``, ``spam``, ``missing``, ``failed``,
    ``cancelled``, ``unknown``, ``archive`` or ``custom``.
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


class ContentSpan(BaseModel):
    """The exact fragment of the copy that triggered a content issue."""

    field: str | None = None
    text: str | None = None
    line: int | None = None
    excerpt: str | None = None


class ContentIssue(BaseModel):
    """One finding of the content check. ``severity`` is ``warn`` or ``high``."""

    severity: str | None = None
    code: str | None = None
    message: str | None = None
    field: str | None = None
    spans: Sequence[ContentSpan] = []
    suggestion: str | None = None


class ContentCheck(BaseModel):
    """The rules pass over a test's copy."""

    score: int | None = None
    issues: Sequence[ContentIssue] = []


class PlacementTest(BaseModel):
    """One test: a copy sent from one sender to a seed panel.

    ``status`` is ``running``, ``completed``, ``cancelled`` or ``failed``;
    ``origin`` is ``manual``, ``monitor``, ``admin``, ``remote`` or ``batch``;
    ``pace`` is ``spaced`` or ``quick``. ``summary`` and ``families`` count
    where the copies landed. The copy bodies are only set on a single test
    read, not in lists.
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
    """One test in full: every probe, the content check, and the other half of
    a tracking comparison (``compare``) when there is one."""

    results: Sequence[PlacementResult] = []
    content: ContentCheck | None = None
    compare: PlacementTest | None = None


class PlacementPanelFamily(BaseModel):
    """The seeds one provider family contributes to a panel."""

    family: str | None = None
    label: str | None = None
    seeds: int | None = None


class PlacementPanelInfo(BaseModel):
    """Whether the workspace can test on a panel.

    ``panel`` is ``instance``, ``workspace`` or ``cloud``; ``reason`` explains
    an unavailable panel; ``metered`` panels count against the allowance.
    """

    panel: str | None = None
    available: bool | None = None
    reason: str | None = None
    seeds: int | None = None
    families: Sequence[PlacementPanelFamily] = []
    metered: bool | None = None


class PlacementUsage(BaseModel):
    """The workspace's monthly allowance on the metered panels.

    ``limit`` is ``None`` when tests are not metered; ``credit_balance`` is
    ``None`` when credits are off.
    """

    used: int | None = None
    limit: int | None = None
    credits_per_test: int | None = None
    credit_balance: int | None = None
    period_start: str | None = None
    period_end: str | None = None


class PlacementOverview(BaseModel):
    """What the workspace can test on and how much allowance is left."""

    panels: Sequence[PlacementPanelInfo] = []
    usage: PlacementUsage | None = None
    workspace_seeds: int | None = None
    seeds_per_test: int | None = None
    spacing_seconds: int | None = None


class PlacementSeed(BaseModel):
    """One of the workspace's mailboxes as a seed-inbox candidate.

    ``seed`` is whether it is currently a seed; ``blocker`` says why it cannot
    become one.
    """

    email_account_id: str
    email: str | None = None
    family: str | None = None
    label: str | None = None
    status: str | None = None
    seed: bool | None = None
    blocker: str | None = None


class PlacementSenderScope(BaseModel):
    """How a batch's senders were selected on the server."""

    type: str | None = None
    campaign_id: str | None = None
    providers: Sequence[str] = []
    domains: Sequence[str] = []
    tag_ids: Sequence[str] = []
    include_inactive: bool | None = None
    untested_days: int | None = None


class PlacementSample(BaseModel):
    """The part of the resolved senders a batch kept."""

    mode: str | None = None
    count: int | None = None
    percent: int | None = None
    stratify: str | None = None


class PlacementBatchSelection(BaseModel):
    """How a batch's senders were chosen.

    ``sender_account_ids`` is the size of an explicit list, ``matched`` how many
    senders were found before sampling.
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
    ``completed_with_warnings``, ``cancelled`` or ``failed``;
    ``on_unavailable`` is ``skip`` or ``defer``. ``summary`` is the headline
    placement (the tracked half of a tracking comparison).
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
    """One batch in full.

    ``untracked`` is the untracked half of a tracking comparison.
    """

    untracked: PlacementCounts | None = None
    domains: Sequence[PlacementBatchGroup] = []
    providers: Sequence[PlacementBatchGroup] = []
    recipients: Sequence[PlacementFamilyCounts] = []
    matrix: Sequence[PlacementBatchMatrixRow] = []
    content: ContentCheck | None = None


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


class BatchGroupCount(BaseModel):
    """How many selected senders share a provider."""

    key: str | None = None
    label: str | None = None
    senders: int | None = None


class PlacementBatchPreview(BaseModel):
    """What a batch would do, before it is started.

    ``matched`` is the senders the scope resolved to and ``selected`` how many
    the sample kept. ``variants`` is two for a tracking comparison.
    ``max_sends`` is the most copies the batch sends; each sender's daily limit
    can only make it fewer.
    """

    matched: int | None = None
    selected: int | None = None
    inactive: int | None = None
    domains: int | None = None
    providers: Sequence[BatchGroupCount] = []
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


class PlacementCoverage(BaseModel):
    """How much of the connected fleet delivered a placement test recently."""

    mailboxes: int | None = None
    tested_7d: int | None = None
    tested_30d: int | None = None
    never_tested: int | None = None


def _test_body(
    *,
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
    max_credits: NotGivenOr[int],
) -> dict[str, Any]:
    """The copy, panel and pacing keys a test and a batch share."""
    return drop_not_given(
        {
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
            "max_credits": max_credits,
        }
    )


class Placement(SyncAPIResource):
    """Synchronous ``placement`` resource."""

    # -- workspace ------------------------------------------------------------
    def overview(self, *, options: RequestOptions | None = None) -> PlacementOverview:
        """Report the panels the workspace can test on and its allowance.

        Requires the ``READ_ANALYTICS`` permission.
        """
        return _unwrap(
            self._get(
                "/placement/overview",
                cast_to=_Data[PlacementOverview],
                options=options,
            )
        )

    def coverage(self, *, options: RequestOptions | None = None) -> PlacementCoverage:
        """Report how much of the connected fleet delivered a placement test.

        Counts mailboxes tested in the last 7 and 30 days and never tested.
        Requires the ``READ_ANALYTICS`` permission.
        """
        return _unwrap(
            self._get(
                "/placement/coverage",
                cast_to=_Data[PlacementCoverage],
                options=options,
            )
        )

    # -- tests ----------------------------------------------------------------
    def list_tests(
        self,
        *,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[PlacementTest]:
        """List the workspace's tests, newest first (auto-paginating).

        Tests started by a batch are left out; read them through the batch.
        Requires the ``READ_ANALYTICS`` permission.

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
    ) -> PlacementTestDetail:
        """Retrieve one test with every probe and the content check.

        For a tracking comparison ``compare`` holds the other half. Requires
        the ``READ_ANALYTICS`` permission.
        """
        return _unwrap(
            self._get(
                f"/placement/tests/{test_id}",
                cast_to=_Data[PlacementTestDetail],
                options=options,
            )
        )

    def create_tests(
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
        pace: NotGivenOr[str] = NOT_GIVEN,
        families: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        seed_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        max_credits: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> list[PlacementTest]:
        """Start a test from one mailbox.

        Sends real mail, so it needs the ``SEND_CAMPAIGNS`` permission. Returns
        one test, or two for ``tracking="compare"``. Name the copy with a
        campaign step or give ad-hoc ``subject`` and bodies.

        Args:
            sender_account_id: The mailbox to send from.
            campaign_id: A campaign to take the copy from (with ``sequence_id``,
                the step) and, for ``tracking="campaign"``, the tracking.
            sequence_id: The campaign step whose copy is tested.
            contact_id: A contact to render the copy's merge fields for.
            subject: The subject, for ad-hoc copy.
            body_html: The HTML body, for ad-hoc copy.
            body_plain: The plain-text body, for ad-hoc copy.
            tracking: ``"campaign"`` (the campaign's own tracking, none for
                ad-hoc copy), ``"on"``, ``"off"`` or ``"compare"`` (send it
                twice, tracked and untracked).
            panel: ``"instance"``, ``"workspace"`` or ``"cloud"``.
            pace: ``"spaced"`` (about a minute apart) or ``"quick"`` (a few
                seconds apart).
            families: Keep only seeds hosted by these provider families.
            seed_ids: Test only these seed inboxes.
            max_credits: The most credits you agree to pay, for tests past the
                monthly free allowance.
        """
        return _unwrap_list(
            self._post(
                "/placement/tests",
                cast_to=_DataList[PlacementTest],
                body={
                    "sender_account_id": sender_account_id,
                    **_test_body(
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
                        max_credits=max_credits,
                    ),
                },
                options=options,
            )
        )

    def cancel_test(
        self, test_id: str, *, options: RequestOptions | None = None
    ) -> PlacementTest:
        """Stop the copies of a test that have not been sent yet.

        Requires the ``SEND_CAMPAIGNS`` permission. A test that is no longer
        running is refused with a ``409``.
        """
        return _unwrap(
            self._post(
                f"/placement/tests/{test_id}/cancel",
                cast_to=_Data[PlacementTest],
                options=options,
            )
        )

    # -- seed inboxes ---------------------------------------------------------
    def list_seeds(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[PlacementSeed]:
        """List the workspace's mailboxes and which of them are seed inboxes.

        Requires the ``READ_EMAILS`` permission. A key limited to some
        mailboxes only sees those.
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
    ) -> PlacementSeed:
        """Make a mailbox a seed inbox of the workspace panel, or not.

        States an absolute value, so a retry is safe. Requires the
        ``WRITE_EMAILS`` permission.

        Args:
            email_account_id: The mailbox id.
            seed: ``True`` to use it as a seed, ``False`` to stop.
        """
        return _unwrap(
            self._put(
                f"/placement/seeds/{email_account_id}",
                cast_to=_Data[PlacementSeed],
                body={"seed": seed},
                options=options,
            )
        )

    # -- batches --------------------------------------------------------------
    def list_batches(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[PlacementBatch]:
        """List the workspace's batches, newest first (auto-paginating).

        Requires the ``READ_ANALYTICS`` permission.

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
    ) -> PlacementBatchDetail:
        """Retrieve one batch with its placement overall and grouped.

        The groups are by sending domain, sending provider, recipient provider
        and the domain-by-recipient matrix. Requires the ``READ_ANALYTICS``
        permission.
        """
        return _unwrap(
            self._get(
                f"/placement/batches/{batch_id}",
                cast_to=_Data[PlacementBatchDetail],
                options=options,
            )
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
        """List a batch's senders with where each one's copies landed.

        Requires the ``READ_ANALYTICS`` permission.

        Args:
            batch_id: The batch id.
            status: Only senders in this status (``queued``, ``deferred``,
                ``running``, ``completed``, ``skipped``, ``failed`` or
                ``cancelled``).
            q: A substring of the sender address.
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
        on_unavailable: NotGivenOr[str] = NOT_GIVEN,
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
        max_credits: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PlacementBatchPreview:
        """Count what a batch would come to, without starting anything.

        Reports the senders, tests, the most copies sent, free and paid tests
        and credits. Takes the same arguments as :meth:`create_batch`. Requires
        the ``SEND_CAMPAIGNS`` permission.

        Choose the senders with exactly one of ``sender_account_ids`` and
        ``sender_scope``.

        Args:
            sender_account_ids: An explicit list of sending mailbox ids.
            sender_scope: A server-side selection:
                ``{"type": "workspace"}`` or ``{"type": "campaign",
                "campaign_id": ...}``, narrowed with optional ``providers``,
                ``domains``, ``tag_ids``, ``include_inactive`` and
                ``untested_days``.
            sample: Keep only part of the resolved senders:
                ``{"mode": "all" | "random" | "percent" | "per_domain" |
                "per_provider", "count": n, "percent": n, "stratify":
                "provider" | "domain"}``.
            on_unavailable: ``"defer"`` (retry later) or ``"skip"`` a sender
                that cannot run when its turn comes.
            campaign_id: A campaign to take the copy from (with ``sequence_id``,
                the step) and, for ``tracking="campaign"``, the tracking.
            sequence_id: The campaign step whose copy is tested.
            contact_id: A contact to render the copy's merge fields for.
            subject: The subject, for ad-hoc copy.
            body_html: The HTML body, for ad-hoc copy.
            body_plain: The plain-text body, for ad-hoc copy.
            tracking: ``"campaign"`` (the campaign's own tracking, none for
                ad-hoc copy), ``"on"``, ``"off"`` or ``"compare"`` (send it
                twice, tracked and untracked).
            panel: ``"instance"``, ``"workspace"`` or ``"cloud"``.
            pace: ``"spaced"`` (about a minute apart) or ``"quick"`` (a few
                seconds apart).
            families: Keep only seeds hosted by these provider families.
            seed_ids: Test only these seed inboxes.
            max_credits: The most credits you agree to pay, for tests past the
                monthly free allowance.
        """
        return _unwrap(
            self._post(
                "/placement/batches/preview",
                cast_to=_Data[PlacementBatchPreview],
                body={
                    **_test_body(
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
                        max_credits=max_credits,
                    ),
                    **drop_not_given(
                        {
                            "sender_account_ids": sender_account_ids,
                            "sender_scope": sender_scope,
                            "sample": sample,
                            "on_unavailable": on_unavailable,
                        }
                    ),
                },
                options=options,
            )
        )

    def create_batch(
        self,
        *,
        sender_account_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        sender_scope: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        sample: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        on_unavailable: NotGivenOr[str] = NOT_GIVEN,
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
        max_credits: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PlacementBatch:
        """Start a placement test from many mailboxes.

        Sends real mail, so it needs the ``SEND_CAMPAIGNS`` permission. The
        batch is returned ``queued`` as soon as its senders are written down;
        the backend starts them a few at a time. A key limited to some
        mailboxes may only name those in ``sender_account_ids``.

        Choose the senders with exactly one of ``sender_account_ids`` and
        ``sender_scope``.

        Args:
            sender_account_ids: An explicit list of sending mailbox ids.
            sender_scope: A server-side selection:
                ``{"type": "workspace"}`` or ``{"type": "campaign",
                "campaign_id": ...}``, narrowed with optional ``providers``,
                ``domains``, ``tag_ids``, ``include_inactive`` and
                ``untested_days``.
            sample: Keep only part of the resolved senders:
                ``{"mode": "all" | "random" | "percent" | "per_domain" |
                "per_provider", "count": n, "percent": n, "stratify":
                "provider" | "domain"}``.
            on_unavailable: ``"defer"`` (retry later) or ``"skip"`` a sender
                that cannot run when its turn comes.
            campaign_id: A campaign to take the copy from (with ``sequence_id``,
                the step) and, for ``tracking="campaign"``, the tracking.
            sequence_id: The campaign step whose copy is tested.
            contact_id: A contact to render the copy's merge fields for.
            subject: The subject, for ad-hoc copy.
            body_html: The HTML body, for ad-hoc copy.
            body_plain: The plain-text body, for ad-hoc copy.
            tracking: ``"campaign"`` (the campaign's own tracking, none for
                ad-hoc copy), ``"on"``, ``"off"`` or ``"compare"`` (send it
                twice, tracked and untracked).
            panel: ``"instance"``, ``"workspace"`` or ``"cloud"``.
            pace: ``"spaced"`` (about a minute apart) or ``"quick"`` (a few
                seconds apart).
            families: Keep only seeds hosted by these provider families.
            seed_ids: Test only these seed inboxes.
            max_credits: The most credits you agree to pay, for tests past the
                monthly free allowance.
        """
        return _unwrap(
            self._post(
                "/placement/batches",
                cast_to=_Data[PlacementBatch],
                body={
                    **_test_body(
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
                        max_credits=max_credits,
                    ),
                    **drop_not_given(
                        {
                            "sender_account_ids": sender_account_ids,
                            "sender_scope": sender_scope,
                            "sample": sample,
                            "on_unavailable": on_unavailable,
                        }
                    ),
                },
                options=options,
            )
        )

    def cancel_batch(
        self, batch_id: str, *, options: RequestOptions | None = None
    ) -> PlacementBatch:
        """Stop a batch. Copies already sent keep being classified.

        Requires the ``SEND_CAMPAIGNS`` permission. A batch that is no longer
        running is refused with a ``409``.
        """
        return _unwrap(
            self._post(
                f"/placement/batches/{batch_id}/cancel",
                cast_to=_Data[PlacementBatch],
                options=options,
            )
        )


class AsyncPlacement(AsyncAPIResource):
    """Asynchronous ``placement`` resource."""

    # -- workspace ------------------------------------------------------------
    async def overview(
        self, *, options: RequestOptions | None = None
    ) -> PlacementOverview:
        """Report the panels the workspace can test on and its allowance.

        Requires the ``READ_ANALYTICS`` permission.
        """
        return _unwrap(
            await self._get(
                "/placement/overview",
                cast_to=_Data[PlacementOverview],
                options=options,
            )
        )

    async def coverage(
        self, *, options: RequestOptions | None = None
    ) -> PlacementCoverage:
        """Report how much of the connected fleet delivered a placement test.

        Counts mailboxes tested in the last 7 and 30 days and never tested.
        Requires the ``READ_ANALYTICS`` permission.
        """
        return _unwrap(
            await self._get(
                "/placement/coverage",
                cast_to=_Data[PlacementCoverage],
                options=options,
            )
        )

    # -- tests ----------------------------------------------------------------
    def list_tests(
        self,
        *,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[PlacementTest]:
        """List the workspace's tests, newest first (auto-paginating).

        Tests started by a batch are left out; read them through the batch.
        Requires the ``READ_ANALYTICS`` permission.

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
    ) -> PlacementTestDetail:
        """Retrieve one test with every probe and the content check.

        For a tracking comparison ``compare`` holds the other half. Requires
        the ``READ_ANALYTICS`` permission.
        """
        return _unwrap(
            await self._get(
                f"/placement/tests/{test_id}",
                cast_to=_Data[PlacementTestDetail],
                options=options,
            )
        )

    async def create_tests(
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
        pace: NotGivenOr[str] = NOT_GIVEN,
        families: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        seed_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        max_credits: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> list[PlacementTest]:
        """Start a test from one mailbox.

        Sends real mail, so it needs the ``SEND_CAMPAIGNS`` permission. Returns
        one test, or two for ``tracking="compare"``. Name the copy with a
        campaign step or give ad-hoc ``subject`` and bodies.

        Args:
            sender_account_id: The mailbox to send from.
            campaign_id: A campaign to take the copy from (with ``sequence_id``,
                the step) and, for ``tracking="campaign"``, the tracking.
            sequence_id: The campaign step whose copy is tested.
            contact_id: A contact to render the copy's merge fields for.
            subject: The subject, for ad-hoc copy.
            body_html: The HTML body, for ad-hoc copy.
            body_plain: The plain-text body, for ad-hoc copy.
            tracking: ``"campaign"`` (the campaign's own tracking, none for
                ad-hoc copy), ``"on"``, ``"off"`` or ``"compare"`` (send it
                twice, tracked and untracked).
            panel: ``"instance"``, ``"workspace"`` or ``"cloud"``.
            pace: ``"spaced"`` (about a minute apart) or ``"quick"`` (a few
                seconds apart).
            families: Keep only seeds hosted by these provider families.
            seed_ids: Test only these seed inboxes.
            max_credits: The most credits you agree to pay, for tests past the
                monthly free allowance.
        """
        return _unwrap_list(
            await self._post(
                "/placement/tests",
                cast_to=_DataList[PlacementTest],
                body={
                    "sender_account_id": sender_account_id,
                    **_test_body(
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
                        max_credits=max_credits,
                    ),
                },
                options=options,
            )
        )

    async def cancel_test(
        self, test_id: str, *, options: RequestOptions | None = None
    ) -> PlacementTest:
        """Stop the copies of a test that have not been sent yet.

        Requires the ``SEND_CAMPAIGNS`` permission. A test that is no longer
        running is refused with a ``409``.
        """
        return _unwrap(
            await self._post(
                f"/placement/tests/{test_id}/cancel",
                cast_to=_Data[PlacementTest],
                options=options,
            )
        )

    # -- seed inboxes ---------------------------------------------------------
    def list_seeds(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[PlacementSeed]:
        """List the workspace's mailboxes and which of them are seed inboxes.

        Requires the ``READ_EMAILS`` permission. A key limited to some
        mailboxes only sees those.
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
    ) -> PlacementSeed:
        """Make a mailbox a seed inbox of the workspace panel, or not.

        States an absolute value, so a retry is safe. Requires the
        ``WRITE_EMAILS`` permission.

        Args:
            email_account_id: The mailbox id.
            seed: ``True`` to use it as a seed, ``False`` to stop.
        """
        return _unwrap(
            await self._put(
                f"/placement/seeds/{email_account_id}",
                cast_to=_Data[PlacementSeed],
                body={"seed": seed},
                options=options,
            )
        )

    # -- batches --------------------------------------------------------------
    def list_batches(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[PlacementBatch]:
        """List the workspace's batches, newest first (auto-paginating).

        Requires the ``READ_ANALYTICS`` permission.

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
    ) -> PlacementBatchDetail:
        """Retrieve one batch with its placement overall and grouped.

        The groups are by sending domain, sending provider, recipient provider
        and the domain-by-recipient matrix. Requires the ``READ_ANALYTICS``
        permission.
        """
        return _unwrap(
            await self._get(
                f"/placement/batches/{batch_id}",
                cast_to=_Data[PlacementBatchDetail],
                options=options,
            )
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
        """List a batch's senders with where each one's copies landed.

        Requires the ``READ_ANALYTICS`` permission.

        Args:
            batch_id: The batch id.
            status: Only senders in this status (``queued``, ``deferred``,
                ``running``, ``completed``, ``skipped``, ``failed`` or
                ``cancelled``).
            q: A substring of the sender address.
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
        on_unavailable: NotGivenOr[str] = NOT_GIVEN,
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
        max_credits: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PlacementBatchPreview:
        """Count what a batch would come to, without starting anything.

        Reports the senders, tests, the most copies sent, free and paid tests
        and credits. Takes the same arguments as :meth:`create_batch`. Requires
        the ``SEND_CAMPAIGNS`` permission.

        Choose the senders with exactly one of ``sender_account_ids`` and
        ``sender_scope``.

        Args:
            sender_account_ids: An explicit list of sending mailbox ids.
            sender_scope: A server-side selection:
                ``{"type": "workspace"}`` or ``{"type": "campaign",
                "campaign_id": ...}``, narrowed with optional ``providers``,
                ``domains``, ``tag_ids``, ``include_inactive`` and
                ``untested_days``.
            sample: Keep only part of the resolved senders:
                ``{"mode": "all" | "random" | "percent" | "per_domain" |
                "per_provider", "count": n, "percent": n, "stratify":
                "provider" | "domain"}``.
            on_unavailable: ``"defer"`` (retry later) or ``"skip"`` a sender
                that cannot run when its turn comes.
            campaign_id: A campaign to take the copy from (with ``sequence_id``,
                the step) and, for ``tracking="campaign"``, the tracking.
            sequence_id: The campaign step whose copy is tested.
            contact_id: A contact to render the copy's merge fields for.
            subject: The subject, for ad-hoc copy.
            body_html: The HTML body, for ad-hoc copy.
            body_plain: The plain-text body, for ad-hoc copy.
            tracking: ``"campaign"`` (the campaign's own tracking, none for
                ad-hoc copy), ``"on"``, ``"off"`` or ``"compare"`` (send it
                twice, tracked and untracked).
            panel: ``"instance"``, ``"workspace"`` or ``"cloud"``.
            pace: ``"spaced"`` (about a minute apart) or ``"quick"`` (a few
                seconds apart).
            families: Keep only seeds hosted by these provider families.
            seed_ids: Test only these seed inboxes.
            max_credits: The most credits you agree to pay, for tests past the
                monthly free allowance.
        """
        return _unwrap(
            await self._post(
                "/placement/batches/preview",
                cast_to=_Data[PlacementBatchPreview],
                body={
                    **_test_body(
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
                        max_credits=max_credits,
                    ),
                    **drop_not_given(
                        {
                            "sender_account_ids": sender_account_ids,
                            "sender_scope": sender_scope,
                            "sample": sample,
                            "on_unavailable": on_unavailable,
                        }
                    ),
                },
                options=options,
            )
        )

    async def create_batch(
        self,
        *,
        sender_account_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        sender_scope: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        sample: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        on_unavailable: NotGivenOr[str] = NOT_GIVEN,
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
        max_credits: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> PlacementBatch:
        """Start a placement test from many mailboxes.

        Sends real mail, so it needs the ``SEND_CAMPAIGNS`` permission. The
        batch is returned ``queued`` as soon as its senders are written down;
        the backend starts them a few at a time. A key limited to some
        mailboxes may only name those in ``sender_account_ids``.

        Choose the senders with exactly one of ``sender_account_ids`` and
        ``sender_scope``.

        Args:
            sender_account_ids: An explicit list of sending mailbox ids.
            sender_scope: A server-side selection:
                ``{"type": "workspace"}`` or ``{"type": "campaign",
                "campaign_id": ...}``, narrowed with optional ``providers``,
                ``domains``, ``tag_ids``, ``include_inactive`` and
                ``untested_days``.
            sample: Keep only part of the resolved senders:
                ``{"mode": "all" | "random" | "percent" | "per_domain" |
                "per_provider", "count": n, "percent": n, "stratify":
                "provider" | "domain"}``.
            on_unavailable: ``"defer"`` (retry later) or ``"skip"`` a sender
                that cannot run when its turn comes.
            campaign_id: A campaign to take the copy from (with ``sequence_id``,
                the step) and, for ``tracking="campaign"``, the tracking.
            sequence_id: The campaign step whose copy is tested.
            contact_id: A contact to render the copy's merge fields for.
            subject: The subject, for ad-hoc copy.
            body_html: The HTML body, for ad-hoc copy.
            body_plain: The plain-text body, for ad-hoc copy.
            tracking: ``"campaign"`` (the campaign's own tracking, none for
                ad-hoc copy), ``"on"``, ``"off"`` or ``"compare"`` (send it
                twice, tracked and untracked).
            panel: ``"instance"``, ``"workspace"`` or ``"cloud"``.
            pace: ``"spaced"`` (about a minute apart) or ``"quick"`` (a few
                seconds apart).
            families: Keep only seeds hosted by these provider families.
            seed_ids: Test only these seed inboxes.
            max_credits: The most credits you agree to pay, for tests past the
                monthly free allowance.
        """
        return _unwrap(
            await self._post(
                "/placement/batches",
                cast_to=_Data[PlacementBatch],
                body={
                    **_test_body(
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
                        max_credits=max_credits,
                    ),
                    **drop_not_given(
                        {
                            "sender_account_ids": sender_account_ids,
                            "sender_scope": sender_scope,
                            "sample": sample,
                            "on_unavailable": on_unavailable,
                        }
                    ),
                },
                options=options,
            )
        )

    async def cancel_batch(
        self, batch_id: str, *, options: RequestOptions | None = None
    ) -> PlacementBatch:
        """Stop a batch. Copies already sent keep being classified.

        Requires the ``SEND_CAMPAIGNS`` permission. A batch that is no longer
        running is refused with a ``409``.
        """
        return _unwrap(
            await self._post(
                f"/placement/batches/{batch_id}/cancel",
                cast_to=_Data[PlacementBatch],
                options=options,
            )
        )
