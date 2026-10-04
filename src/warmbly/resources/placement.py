"""The ``placement`` resource: inbox placement tests.

Maps to the ``/v1/placement`` route group. A placement test sends a template
or a campaign step from one of your mailboxes to a panel of seed inboxes and
reports where each copy landed (inbox, Gmail tab, spam, or never seen). A
*batch* runs the same test from many senders, a few at a time.

Reads need the ``read_analytics`` API-key permission, starting or cancelling a
test or batch needs ``send_campaigns``, and listing or changing the seed
inboxes needs ``read_emails`` and ``write_emails`` respectively. Every
response from this group is wrapped in a ``{"data": ...}`` envelope; the
models here unwrap it, so the methods return the payload directly.

Starting a test sends real mail, and past the monthly free allowance it is
paid in credits: pass ``max_credits`` to agree to a price. The SDK attaches an
``Idempotency-Key`` to the creating calls, so a retried request does not start
a second test.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import model_validator

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
    "PlacementBatchGroup",
    "PlacementBatchPreview",
    "PlacementBatchSender",
    "PlacementBatchSenderView",
    "PlacementContentCheck",
    "PlacementCounts",
    "PlacementCoverage",
    "PlacementFamilyCounts",
    "PlacementOverview",
    "PlacementPanelInfo",
    "PlacementResult",
    "PlacementSeed",
    "PlacementTest",
    "PlacementTestDetail",
    "PlacementUsage",
]


class _PlacementModel(BaseModel):
    """Base for placement models: unwraps the ``{"data": ...}`` envelope."""

    @model_validator(mode="before")
    @classmethod
    def _unwrap_data(cls, value: Any) -> Any:
        if isinstance(value, dict) and set(value) == {"data"}:
            return value["data"]
        return value


class _TestsEnvelope(BaseModel):
    """``{"data": [PlacementTest, ...]}`` as returned by test creation."""

    data: list[PlacementTest] = []


class _SeedsEnvelope(BaseModel):
    """``{"data": [PlacementSeed, ...]}`` as returned by the seed listing."""

    data: list[PlacementSeed] = []


# -- models -----------------------------------------------------------------


class PlacementCounts(_PlacementModel):
    """Where a set of probes landed.

    ``delivered`` is every copy that left and got a verdict (inbox,
    promotions, other, spam and missing). The four rates are fractions of
    ``delivered`` between 0 and 1 and are ``None`` until something is
    delivered; ``tabs_rate`` covers Gmail's Promotions and other tabs.
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
    delivered: int | None = None
    inbox_rate: float | None = None
    tabs_rate: float | None = None
    spam_rate: float | None = None
    missing_rate: float | None = None


class PlacementFamilyCounts(_PlacementModel):
    """One recipient host family's share of a test (``family`` is a mailhost
    value such as ``google_workspace`` or ``outlook``)."""

    family: str | None = None
    label: str | None = None
    counts: PlacementCounts | None = None


class PlacementTest(_PlacementModel):
    """One placement test: a copy sent from one sender to a seed panel.

    ``status`` is ``running``, ``completed``, ``cancelled`` or ``failed``;
    ``origin`` is ``manual``, ``monitor``, ``admin``, ``remote`` or ``batch``;
    ``panel`` is ``instance``, ``workspace`` or ``cloud``; ``pace`` is
    ``spaced`` or ``quick``. The copy (``body_html`` / ``body_plain``) is only
    present on a single test, not in lists.
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


class PlacementResult(_PlacementModel):
    """One probe: one copy to one seed, as the dashboard shows it.

    ``seed`` is masked on the shared panels. ``folder`` is ``pending``,
    ``inbox``, ``promotions``, ``other``, ``spam``, ``missing``, ``failed`` or
    ``cancelled``.
    """

    seed: str | None = None
    family: str | None = None
    family_label: str | None = None
    folder: str | None = None
    scheduled_at: str | None = None
    sent_at: str | None = None
    detected_at: str | None = None
    error: str | None = None


class PlacementContentCheck(_PlacementModel):
    """The rules pass over a test's copy: a ``score`` and its ``issues``.

    Each issue carries ``severity`` (``warn`` or ``high``), ``code``,
    ``message``, and optionally ``field``, ``spans`` and ``suggestion``.
    """

    score: int | None = None
    issues: Sequence[dict[str, Any]] = []


class PlacementTestDetail(PlacementTest):
    """One test in full: every probe, the content check and, for a tracking
    comparison, the other half under ``compare``."""

    results: Sequence[PlacementResult] = []
    content: PlacementContentCheck | None = None
    compare: PlacementTest | None = None


class PlacementPanelFamily(_PlacementModel):
    """The seeds one host family contributes to a panel."""

    family: str | None = None
    label: str | None = None
    seeds: int | None = None


class PlacementPanelInfo(_PlacementModel):
    """Whether the workspace can test on a panel (``instance``, ``workspace``
    or ``cloud``). ``reason`` explains an unavailable panel; a ``metered``
    panel counts against the monthly allowance."""

    panel: str | None = None
    available: bool | None = None
    reason: str | None = None
    seeds: int | None = None
    families: Sequence[PlacementPanelFamily] = []
    metered: bool | None = None


class PlacementUsage(_PlacementModel):
    """The workspace's monthly allowance on the metered panels.

    ``limit`` is ``None`` when the instance does not meter tests, and
    ``credit_balance`` is ``None`` when credits are off.
    """

    used: int | None = None
    limit: int | None = None
    credits_per_test: int | None = None
    credit_balance: int | None = None
    period_start: str | None = None
    period_end: str | None = None


class PlacementOverview(_PlacementModel):
    """The panels a workspace can test on and its remaining allowance."""

    panels: Sequence[PlacementPanelInfo] = []
    usage: PlacementUsage | None = None
    workspace_seeds: int | None = None
    seeds_per_test: int | None = None
    spacing_seconds: int | None = None


class PlacementSeed(_PlacementModel):
    """One of the workspace's own mailboxes as a seed candidate.

    ``seed`` says whether it is currently a seed inbox; ``blocker`` is why it
    cannot become one (empty when it can).
    """

    email_account_id: str
    email: str | None = None
    family: str | None = None
    label: str | None = None
    status: str | None = None
    seed: bool | None = None
    blocker: str | None = None


class PlacementSenderScope(_PlacementModel):
    """How a batch's senders were selected on the server."""

    type: str | None = None
    campaign_id: str | None = None
    providers: Sequence[str] = []
    domains: Sequence[str] = []
    tag_ids: Sequence[str] = []
    include_inactive: bool | None = None
    untested_days: int | None = None


class PlacementSample(_PlacementModel):
    """How the resolved senders were sampled (``mode`` is ``all``,
    ``random``, ``percent``, ``per_domain`` or ``per_provider``)."""

    mode: str | None = None
    count: int | None = None
    percent: int | None = None
    stratify: str | None = None


class PlacementBatchSelection(_PlacementModel):
    """How a batch's senders were chosen. ``matched`` is how many senders the
    scope resolved to before sampling."""

    sender_account_ids: int | None = None
    sender_scope: PlacementSenderScope | None = None
    sample: PlacementSample | None = None
    matched: int | None = None


class PlacementBatchProgress(_PlacementModel):
    """A batch's senders counted by status."""

    total: int | None = None
    queued: int | None = None
    deferred: int | None = None
    running: int | None = None
    completed: int | None = None
    skipped: int | None = None
    failed: int | None = None
    cancelled: int | None = None


class PlacementBatch(_PlacementModel):
    """A placement test run from many senders, with its progress and headline
    placement.

    ``status`` is ``queued``, ``running``, ``completed``,
    ``completed_with_warnings``, ``cancelled`` or ``failed``; ``tracking`` is
    ``campaign``, ``on``, ``off`` or ``compare``; ``on_unavailable`` is
    ``skip`` or ``defer``.
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


class PlacementBatchGroup(_PlacementModel):
    """A batch's placement for one sending domain or provider."""

    key: str | None = None
    label: str | None = None
    senders: int | None = None
    tested: int | None = None
    counts: PlacementCounts | None = None


class PlacementBatchMatrixRow(_PlacementModel):
    """One sending domain's placement per recipient provider."""

    domain: str | None = None
    recipients: Sequence[PlacementFamilyCounts] = []


class PlacementBatchDetail(PlacementBatch):
    """One batch in full. ``summary`` is the tracked half of a tracking
    comparison and ``untracked`` the other half."""

    untracked: PlacementCounts | None = None
    domains: Sequence[PlacementBatchGroup] = []
    providers: Sequence[PlacementBatchGroup] = []
    recipients: Sequence[PlacementFamilyCounts] = []
    matrix: Sequence[PlacementBatchMatrixRow] = []
    content: PlacementContentCheck | None = None


class PlacementBatchSender(_PlacementModel):
    """One sender of a batch.

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


class PlacementBatchSenderView(PlacementBatchSender):
    """A batch sender with where its copies landed."""

    sender_family_label: str | None = None
    summary: PlacementCounts | None = None
    test_ids: Sequence[str] = []


class PlacementBatchProviderCount(_PlacementModel):
    """How many selected senders share a provider."""

    key: str | None = None
    label: str | None = None
    senders: int | None = None


class PlacementBatchPreview(_PlacementModel):
    """What a batch would do, before it is started (nothing is sent).

    ``matched`` is the senders the scope resolved to and ``selected`` the
    senders the sample kept. ``variants`` is two for a tracking comparison.
    ``free_tests`` / ``paid_tests`` split ``tests`` against the monthly
    allowance and ``credits`` is the most the paid ones cost.
    """

    matched: int | None = None
    selected: int | None = None
    inactive: int | None = None
    domains: int | None = None
    providers: Sequence[PlacementBatchProviderCount] = []
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


class PlacementCoverage(_PlacementModel):
    """How much of the connected fleet delivered a placement test recently."""

    mailboxes: int | None = None
    tested_7d: int | None = None
    tested_30d: int | None = None
    never_tested: int | None = None


# -- request helpers --------------------------------------------------------


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
        """Show the seed panels the workspace can test on and its allowance.

        Requires the ``read_analytics`` API-key permission.
        """
        return self._get(
            "/placement/overview", cast_to=PlacementOverview, options=options
        )

    def list_tests(
        self,
        *,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[PlacementTest]:
        """List the workspace's placement tests, newest first.

        Requires the ``read_analytics`` API-key permission.

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

    def get_test(
        self, test_id: str, *, options: RequestOptions | None = None
    ) -> PlacementTestDetail:
        """Retrieve one test with every probe and the content check.

        Requires the ``read_analytics`` API-key permission.
        """
        return self._get(
            f"/placement/tests/{test_id}", cast_to=PlacementTestDetail, options=options
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
    ) -> list[PlacementTest]:
        """Start a placement test. This sends real mail.

        Requires the ``send_campaigns`` API-key permission. Returns one test,
        or two for a tracking comparison.

        Args:
            sender_account_id: The mailbox to send from. It must be connected
                and must not itself be a seed.
            campaign_id: Copy the subject and body from this campaign's step.
            sequence_id: The step to copy (with ``campaign_id``).
            contact_id: The contact the copy is rendered against.
            subject: A subject, for an ad-hoc test.
            body_html: An HTML body, for an ad-hoc test.
            body_plain: A plain-text body, for an ad-hoc test.
            tracking: ``campaign`` (default), ``on``, ``off`` or ``compare``.
            panel: ``instance`` (default), ``workspace`` or ``cloud``.
            seed_ids: Narrow a ``workspace`` panel test to these seeds.
            families: Keep only seeds hosted by these providers.
            pace: ``spaced`` (default) or ``quick``.
            max_credits: The most you agree to pay, in credits, for a test
                past the monthly free allowance.
        """
        envelope = self._post(
            "/placement/tests",
            cast_to=_TestsEnvelope,
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
        return envelope.data

    def cancel_test(
        self, test_id: str, *, options: RequestOptions | None = None
    ) -> PlacementTest:
        """Stop the copies of a test that have not been sent yet.

        Requires the ``send_campaigns`` API-key permission.
        """
        return self._post(
            f"/placement/tests/{test_id}/cancel",
            cast_to=PlacementTest,
            options=options,
        )

    def list_batches(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[PlacementBatch]:
        """List the workspace's placement batches, newest first.

        Requires the ``read_analytics`` API-key permission.

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

    def get_batch(
        self, batch_id: str, *, options: RequestOptions | None = None
    ) -> PlacementBatchDetail:
        """Retrieve one batch with its placement overall and grouped by
        sending domain, sending provider and recipient provider.

        Requires the ``read_analytics`` API-key permission.
        """
        return self._get(
            f"/placement/batches/{batch_id}",
            cast_to=PlacementBatchDetail,
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
    ) -> SyncCursorPage[PlacementBatchSenderView]:
        """List a batch's senders with where each one's copies landed.

        Requires the ``read_analytics`` API-key permission. Worst inbox rate
        first unless ``sort`` says otherwise.

        Args:
            batch_id: The batch id.
            status: Only senders in this status.
            q: Filter to senders whose address contains this text.
            sort: The sort order.
            limit: Page size, 1 to 100 (default 25).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            f"/placement/batches/{batch_id}/senders",
            model=PlacementBatchSenderView,
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
        """Report how many senders, tests, sends and credits a batch would
        come to. Starts nothing.

        Requires the ``send_campaigns`` API-key permission. Takes the same
        arguments as :meth:`create_batch`.
        """
        return self._post(
            "/placement/batches/preview",
            cast_to=PlacementBatchPreview,
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
    ) -> PlacementBatch:
        """Queue a placement test from many senders. This sends real mail.

        Requires the ``send_campaigns`` API-key permission. The server
        snapshots the senders and starts them a few at a time.

        Args:
            sender_account_ids: An explicit list of sending mailboxes. Give
                this or ``sender_scope``.
            sender_scope: Select senders on the server instead, e.g.
                ``{"type": "workspace", "providers": ["gmail"]}``. ``type`` is
                ``campaign`` (with ``campaign_id``) or ``workspace``; optional
                filters are ``providers``, ``domains``, ``tag_ids``,
                ``include_inactive`` and ``untested_days``.
            sample: Pick part of the resolved senders, e.g.
                ``{"mode": "percent", "percent": 20}``. ``mode`` is ``all``,
                ``random``, ``percent``, ``per_domain`` or ``per_provider``.
            campaign_id: Copy the subject and body from this campaign's step.
            sequence_id: The step to copy (with ``campaign_id``).
            contact_id: The contact the copy is rendered against.
            subject: A subject, for an ad-hoc test.
            body_html: An HTML body, for an ad-hoc test.
            body_plain: A plain-text body, for an ad-hoc test.
            tracking: ``campaign``, ``on``, ``off`` or ``compare``.
            panel: ``instance``, ``workspace`` or ``cloud``.
            pace: ``spaced`` or ``quick``.
            families: Keep only seeds hosted by these providers.
            seed_ids: Narrow a ``workspace`` panel test to these seeds.
            on_unavailable: What to do with a sender that cannot run when its
                turn comes: ``skip`` or ``defer``.
            max_credits: The most you agree to pay, in credits, across the
                whole batch for tests past the monthly free allowance.
        """
        return self._post(
            "/placement/batches",
            cast_to=PlacementBatch,
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
    ) -> PlacementBatch:
        """Stop a batch. Copies already sent keep being classified.

        Requires the ``send_campaigns`` API-key permission.
        """
        return self._post(
            f"/placement/batches/{batch_id}/cancel",
            cast_to=PlacementBatch,
            options=options,
        )

    def coverage(self, *, options: RequestOptions | None = None) -> PlacementCoverage:
        """Report how much of the connected fleet delivered a placement test
        in the last 7 and 30 days.

        Requires the ``read_analytics`` API-key permission.
        """
        return self._get(
            "/placement/coverage", cast_to=PlacementCoverage, options=options
        )

    def list_seeds(
        self, *, options: RequestOptions | None = None
    ) -> list[PlacementSeed]:
        """List the workspace's mailboxes and which are its seed inboxes.

        Requires the ``read_emails`` API-key permission. A key limited to some
        mailboxes only sees those.
        """
        return self._get(
            "/placement/seeds", cast_to=_SeedsEnvelope, options=options
        ).data

    def set_seed(
        self,
        email_account_id: str,
        *,
        seed: bool,
        options: RequestOptions | None = None,
    ) -> PlacementSeed:
        """Make a workspace mailbox a seed inbox, or stop it being one.

        Requires the ``write_emails`` API-key permission.

        Args:
            email_account_id: The mailbox id.
            seed: ``True`` to make it a seed inbox, ``False`` to remove it.
        """
        return self._put(
            f"/placement/seeds/{email_account_id}",
            cast_to=PlacementSeed,
            body={"seed": seed},
            options=options,
        )


class AsyncPlacement(AsyncAPIResource):
    """Asynchronous ``placement`` resource."""

    async def overview(
        self, *, options: RequestOptions | None = None
    ) -> PlacementOverview:
        """Show the seed panels the workspace can test on and its allowance.

        Requires the ``read_analytics`` API-key permission.
        """
        return await self._get(
            "/placement/overview", cast_to=PlacementOverview, options=options
        )

    def list_tests(
        self,
        *,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[PlacementTest]:
        """List the workspace's placement tests, newest first.

        Requires the ``read_analytics`` API-key permission.

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

    async def get_test(
        self, test_id: str, *, options: RequestOptions | None = None
    ) -> PlacementTestDetail:
        """Retrieve one test with every probe and the content check.

        Requires the ``read_analytics`` API-key permission.
        """
        return await self._get(
            f"/placement/tests/{test_id}", cast_to=PlacementTestDetail, options=options
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
    ) -> list[PlacementTest]:
        """Start a placement test. This sends real mail.

        Requires the ``send_campaigns`` API-key permission. Returns one test,
        or two for a tracking comparison. See the synchronous
        :meth:`Placement.create_test` for the arguments.
        """
        envelope = await self._post(
            "/placement/tests",
            cast_to=_TestsEnvelope,
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
        return envelope.data

    async def cancel_test(
        self, test_id: str, *, options: RequestOptions | None = None
    ) -> PlacementTest:
        """Stop the copies of a test that have not been sent yet.

        Requires the ``send_campaigns`` API-key permission.
        """
        return await self._post(
            f"/placement/tests/{test_id}/cancel",
            cast_to=PlacementTest,
            options=options,
        )

    def list_batches(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[PlacementBatch]:
        """List the workspace's placement batches, newest first.

        Requires the ``read_analytics`` API-key permission.

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

    async def get_batch(
        self, batch_id: str, *, options: RequestOptions | None = None
    ) -> PlacementBatchDetail:
        """Retrieve one batch with its placement overall and grouped by
        sending domain, sending provider and recipient provider.

        Requires the ``read_analytics`` API-key permission.
        """
        return await self._get(
            f"/placement/batches/{batch_id}",
            cast_to=PlacementBatchDetail,
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
    ) -> AsyncPaginator[PlacementBatchSenderView]:
        """List a batch's senders with where each one's copies landed.

        Requires the ``read_analytics`` API-key permission. Worst inbox rate
        first unless ``sort`` says otherwise.

        Args:
            batch_id: The batch id.
            status: Only senders in this status.
            q: Filter to senders whose address contains this text.
            sort: The sort order.
            limit: Page size, 1 to 100 (default 25).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            f"/placement/batches/{batch_id}/senders",
            model=PlacementBatchSenderView,
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
        """Report how many senders, tests, sends and credits a batch would
        come to. Starts nothing.

        Requires the ``send_campaigns`` API-key permission. Takes the same
        arguments as :meth:`create_batch`.
        """
        return await self._post(
            "/placement/batches/preview",
            cast_to=PlacementBatchPreview,
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
    ) -> PlacementBatch:
        """Queue a placement test from many senders. This sends real mail.

        Requires the ``send_campaigns`` API-key permission. See the
        synchronous :meth:`Placement.create_batch` for the arguments.
        """
        return await self._post(
            "/placement/batches",
            cast_to=PlacementBatch,
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
    ) -> PlacementBatch:
        """Stop a batch. Copies already sent keep being classified.

        Requires the ``send_campaigns`` API-key permission.
        """
        return await self._post(
            f"/placement/batches/{batch_id}/cancel",
            cast_to=PlacementBatch,
            options=options,
        )

    async def coverage(
        self, *, options: RequestOptions | None = None
    ) -> PlacementCoverage:
        """Report how much of the connected fleet delivered a placement test
        in the last 7 and 30 days.

        Requires the ``read_analytics`` API-key permission.
        """
        return await self._get(
            "/placement/coverage", cast_to=PlacementCoverage, options=options
        )

    async def list_seeds(
        self, *, options: RequestOptions | None = None
    ) -> list[PlacementSeed]:
        """List the workspace's mailboxes and which are its seed inboxes.

        Requires the ``read_emails`` API-key permission. A key limited to some
        mailboxes only sees those.
        """
        envelope = await self._get(
            "/placement/seeds", cast_to=_SeedsEnvelope, options=options
        )
        return envelope.data

    async def set_seed(
        self,
        email_account_id: str,
        *,
        seed: bool,
        options: RequestOptions | None = None,
    ) -> PlacementSeed:
        """Make a workspace mailbox a seed inbox, or stop it being one.

        Requires the ``write_emails`` API-key permission.

        Args:
            email_account_id: The mailbox id.
            seed: ``True`` to make it a seed inbox, ``False`` to remove it.
        """
        return await self._put(
            f"/placement/seeds/{email_account_id}",
            cast_to=PlacementSeed,
            body={"seed": seed},
            options=options,
        )
