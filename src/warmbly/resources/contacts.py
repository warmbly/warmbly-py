"""The ``contacts`` resource: leads, their notes, activity, and research.

Maps to the ``/v1/contacts`` route group. Contacts are org-scoped and keyed by
email, which is what makes imports and CRM pushes converge rather than
duplicate.

There is no plain ``GET /contacts``: listing goes through
:meth:`Contacts.search`, whose faceted filter body travels in the request
because it is far richer than a query string. Bulk create, update, and delete
all take arrays, and the AI research endpoints charge credits.
"""

from __future__ import annotations

import json as _json
from collections.abc import Mapping, Sequence
from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions, is_given
from .._utils import drop_not_given

__all__ = [
    "AsyncContacts",
    "Contact",
    "ContactActivity",
    "ContactCampaignState",
    "ContactDeleted",
    "ContactDetail",
    "ContactImport",
    "ContactImportAnalysis",
    "ContactImportPreview",
    "ContactImportResult",
    "ContactLookup",
    "ContactNote",
    "ContactNoteDeleted",
    "ContactResearchRun",
    "ContactSalesforcePanel",
    "ContactSearchPage",
    "ContactSegment",
    "ContactSentEmail",
    "ContactTimelineEntry",
    "ContactVerificationOverview",
    "ContactVerificationRequested",
    "Contacts",
    "ContactsAdded",
    "CustomFieldKeys",
    "ResearchBatchQueued",
]


class Contact(BaseModel):
    """A contact (lead).

    ``verification_status`` is the last address verdict (``valid``, ``risky``,
    ``invalid`` or ``unknown``) and the campaign send path drops ``invalid``
    addresses before a worker touches them. ``verification_source`` says who
    produced the verdict (``probe``, ``provider``, ``imported``, ``manual``),
    ``verification_provider`` names the backend or vocabulary behind it, and
    ``verification_confidence`` is how sure the platform is, 0 to 100, scored
    from the check plus what real mail to the address actually did.
    ``verification_requested_at`` is set while a member-requested re-check
    waits to run; the verdict stands until it lands. ``mail_host`` is who
    hosts the contact's inbox (read from the domain's MX by a background
    sweep, empty until it has run) and ``esp_provider`` is that host's family
    (``gmail``, ``outlook`` or ``other``). ``outreach`` is the contact's
    engagement across every campaign (``sent``, ``opened``, ``clicked``,
    ``replied``, ``bounced`` and a ``last_*_at`` stamp for each); the search
    endpoint fills it on every row and it is ``None`` elsewhere.
    """

    id: str
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    company: str | None = None
    phone: str | None = None
    custom_fields: dict[str, str] = {}
    subscribed: bool | None = None
    campaigns: Sequence[dict[str, Any]] = []
    categories: Sequence[dict[str, Any]] = []
    verification_status: str | None = None
    verification_reason: str | None = None
    verification_checked_at: str | None = None
    verification_source: str | None = None
    verification_provider: str | None = None
    verification_sub_status: str | None = None
    verification_confidence: int | None = None
    is_catch_all: bool | None = None
    verification_requested_at: str | None = None
    mail_host: str | None = None
    esp_provider: str | None = None
    esp_resolved_at: str | None = None
    campaign_lead: dict[str, Any] | None = None
    outreach: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ContactDetail(Contact):
    """A contact plus its engagement roll-up and first-touch attribution.

    ``suppression`` is non-``None`` when the address is suppressed, in which
    case campaigns skip it. ``verification`` explains the verdict: the reasons
    behind it and the observations it was scored from. ``source`` is where the
    contact first came from (``manual``, ``campaign``, ``import``,
    ``sheet_sync``, ``api``, ``ai_assistant``, ``form``, ``automation``,
    ``crm_sync``, ``apollo``, ``clay``, or ``unknown`` for a row created
    before attribution existed) and never
    changes; ``source_detail`` is the free-form specifics, such as the file
    name or the automation's name.
    """

    engagement: dict[str, Any] | None = None
    suppression: dict[str, Any] | None = None
    verification: dict[str, Any] | None = None
    source: str | None = None
    source_detail: str | None = None
    first_seen_at: str | None = None


class ContactDeleted(BaseModel):
    """The result of deleting a contact (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class ContactsAdded(BaseModel):
    """The result of a bulk contact create or edit (permissive).

    An address that already exists is updated rather than duplicated.
    """

    created: int | None = None
    updated: int | None = None
    skipped: int | None = None
    failed: int | None = None
    contacts: Sequence[Contact] = []


class ContactSearchPage(BaseModel):
    """One page of contact-search results, plus org-wide counts.

    ``counts`` and ``lead_counts`` are computed over the whole matching set,
    not the page.
    """

    data: Sequence[Contact] = []
    pagination: dict[str, Any] = {}
    counts: dict[str, Any] | None = None
    lead_counts: dict[str, Any] | None = None


class ContactLookup(BaseModel):
    """The result of looking a contact up by sender address or thread.

    ``match`` says how the sender resolved: ``"email"`` when the address is
    the contact's own, ``"thread"`` when the unibox thread answers a campaign
    send to the contact and the reply came from another address. It is empty
    when nothing matched.
    """

    contact: Contact | None = None
    match: str | None = None


class CustomFieldKeys(BaseModel):
    """Every custom-field key in use across the organization's contacts."""

    data: Sequence[str] = []


class ContactNote(BaseModel):
    """A note attached to a contact.

    ``external`` is set when the note lives in a connected CRM.
    """

    id: str
    contact_id: str | None = None
    organization_id: str | None = None
    user_id: str | None = None
    content: str | None = None
    user: dict[str, Any] | None = None
    external: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ContactNoteDeleted(BaseModel):
    """The result of deleting a note (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class ContactActivity(BaseModel):
    """A recorded activity on a contact."""

    id: str
    contact_id: str | None = None
    organization_id: str | None = None
    user_id: str | None = None
    activity_type: str | None = None
    metadata: dict[str, Any] = {}
    user: dict[str, Any] | None = None
    created_at: str | None = None


class ContactSentEmail(BaseModel):
    """An email sent to a contact, with its engagement timestamps."""

    task_id: str | None = None
    status: str | None = None
    message_id: str | None = None
    subject: str | None = None
    sent_at: str | None = None
    email_account_id: str | None = None
    email_account_email: str | None = None
    email_account_name: str | None = None
    campaign_id: str | None = None
    campaign_name: str | None = None
    step_id: str | None = None
    step_name: str | None = None
    opened_at: str | None = None
    machine_opened_at: str | None = None
    clicked_at: str | None = None
    replied_at: str | None = None
    bounced_at: str | None = None


class ContactTimelineEntry(BaseModel):
    """One entry in a contact's merged timeline.

    ``type`` is the event kind (``email_sent``, ``email_opened``,
    ``email_clicked``, ``email_replied``, ``email_bounced``,
    ``reply_received``, ``deliverability``, ``suppressed``, ``note``,
    ``meeting_booked`` / ``_rescheduled`` / ``_canceled``, ``contact_created``,
    ``campaign_added`` / ``_removed``, ``category_added`` / ``_removed``,
    ``form_submitted`` or ``page_hit``) and ``at`` is when it happened; the
    rest of the fields are whichever ones that kind carries.

    On an open or a click, ``machine`` is ``True`` when the hit came from an
    automated fetcher (a mail privacy proxy, a security gateway walking the
    links) rather than a person, with ``machine_reason`` naming the rule that
    caught it, and ``origin`` describing the client and location it came from.
    ``link`` is the exact link behind a click, and ``page_hit`` the page view
    behind a ``page_hit`` event.
    """

    type: str | None = None
    at: str | None = None
    email_account_id: str | None = None
    email_account_email: str | None = None
    email_account_name: str | None = None
    campaign_id: str | None = None
    campaign_name: str | None = None
    step_id: str | None = None
    step_name: str | None = None
    task_id: str | None = None
    subject: str | None = None
    reason: str | None = None
    source: str | None = None
    source_detail: str | None = None
    provider: str | None = None
    intent: str | None = None
    content: str | None = None
    scheduled_for: str | None = None
    join_url: str | None = None
    meeting_state: str | None = None
    category_id: str | None = None
    category_title: str | None = None
    form_id: str | None = None
    form_name: str | None = None
    page_hit: dict[str, Any] | None = None
    machine: bool | None = None
    machine_reason: str | None = None
    origin: dict[str, Any] | None = None
    link: dict[str, Any] | None = None


class ContactResearchRun(BaseModel):
    """One AI research run against a contact.

    ``result`` carries the findings (company, person, signals, hooks, custom
    field updates, notes) and is empty while the run is still queued;
    ``error`` explains a failed one.
    """

    id: str | None = None
    org_id: str | None = None
    contact_id: str | None = None
    requested_by: str | None = None
    status: str | None = None
    objective: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    credits_charged: int | None = None
    model_used: str | None = None
    tokens_used: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ResearchBatchQueued(BaseModel):
    """The number of research runs a batch request actually queued."""

    queued: int | None = None


class ContactImportPreview(BaseModel):
    """A parsed preview of an upload, before any rows are written.

    ``suggested_mapping`` is the server's guess at which column fills which
    contact field; correct it and pass the result as the ``mapping`` of
    :meth:`Contacts.import_commit`. ``inferred_columns`` lists the column
    indexes whose suggestion came from a judgment rather than the header or
    the values, which are worth a second look. ``column_stats`` describes every
    column over the whole file (``filled``, ``distinct``, ``samples``) and is
    set by the background import only. ``mapping_source`` is ``"saved"`` when
    the workspace confirmed a mapping for these exact headers before, and
    ``"suggested"`` otherwise.
    """

    filename: str | None = None
    format: str | None = None
    columns: Sequence[str] = []
    has_header: bool | None = None
    sample_rows: Sequence[Sequence[str]] = []
    total_rows: int | None = None
    suggested_mapping: Sequence[dict[str, Any]] = []
    inferred_columns: Sequence[int] = []
    column_stats: Sequence[dict[str, Any]] = []
    mapping_source: str | None = None


class ContactImportResult(BaseModel):
    """Per-row results from a committed import.

    ``segments_pinned`` is ``None`` when the import named no segments. With
    segments it is ``True`` when every membership write landed and ``False``
    when one did not, with the reason among the ``errors`` notes.
    """

    total: int | None = None
    imported: int | None = None
    updated: int | None = None
    skipped: int | None = None
    failed: int | None = None
    errors: Sequence[dict[str, Any]] = []
    errors_truncated: bool | None = None
    segments_pinned: bool | None = None
    quality: dict[str, Any] | None = None
    started_at: str | None = None
    ended_at: str | None = None


class ContactImport(BaseModel):
    """One staged (background) import of a contact file.

    ``status`` is ``draft`` (uploaded, waiting for a mapping and a start),
    ``queued``, ``running``, ``completed``, ``failed`` or ``cancelled``.
    ``total`` is the number of data rows and ``processed`` how many have
    settled. ``options`` is the saved mapping and settings, ``preview`` is what
    the column mapper shows (a draft only), and ``failures`` are the first
    failed rows once the import has finished; the full set is the
    :meth:`Contacts.download_import_failures` download.
    """

    id: str
    organization_id: str | None = None
    created_by: str | None = None
    filename: str | None = None
    format: str | None = None
    status: str | None = None
    has_header: bool | None = None
    columns: Sequence[str] = []
    total: int | None = None
    processed: int | None = None
    imported: int | None = None
    updated: int | None = None
    skipped: int | None = None
    failed: int | None = None
    options: dict[str, Any] | None = None
    quality: dict[str, Any] | None = None
    segments_pinned: bool | None = None
    notes: Sequence[str] = []
    error: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    preview: ContactImportPreview | None = None
    failures: Sequence[dict[str, Any]] = []


class ContactImportAnalysis(BaseModel):
    """What a staged import would do under a mapping, before anything is written.

    Every data row lands in exactly one of ``new``, ``existing``,
    ``duplicates_in_file``, ``invalid`` or ``conflicts``. ``problem`` is why
    starting the import would be refused as a whole (the plan's contact limit,
    too many new categories) and is empty when it would run.
    """

    rows: int | None = None
    new: int | None = None
    existing: int | None = None
    duplicates_in_file: int | None = None
    invalid: int | None = None
    conflicts: int | None = None
    invalid_samples: Sequence[dict[str, Any]] = []
    quality: dict[str, Any] | None = None
    problem: str | None = None


class ContactSalesforcePanel(BaseModel):
    """A contact's Salesforce panel.

    ``connections`` are the connected Salesforce orgs and ``records`` the
    Lead or Contact the person is in each of them (with its owner, account,
    opportunities, recent tasks and the sync outbox picture). ``can_sync`` is
    whether a manual sync is possible right now.
    """

    connections: Sequence[dict[str, Any]] = []
    records: Sequence[dict[str, Any]] = []
    can_sync: bool | None = None


class ContactCampaignState(BaseModel):
    """One campaign a contact is a lead of, with its progress through it.

    ``lead_status`` is one of ``pending``, ``active``, ``completed``,
    ``replied``, ``bounced``, ``failed``, ``unsubscribed``, ``paused`` or
    ``undeliverable``. ``sender_id`` / ``sender_email`` are the mailbox the
    lead's whole sequence sends from, fixed when its first email went out.
    ``hold`` is the per-lead pause (``since``, ``until``, ``reason``,
    ``source``), present only while it is live, and ``cc`` the contacts copied
    on every email to this lead in this campaign.

    ``steps`` is the flow with this contact's per-step stamps; ``next`` is the
    action the scheduler would take next, derived on read, and is ``None`` once
    the flow has ended for the contact, in which case ``ended_reason`` says
    why.
    """

    campaign_id: str | None = None
    campaign_name: str | None = None
    campaign_status: str | None = None
    lead_status: str | None = None
    failure_reason: str | None = None
    steps: Sequence[dict[str, Any]] = []
    completed_steps: int | None = None
    total_steps: int | None = None
    current_step: dict[str, Any] | None = None
    last_action: str | None = None
    last_action_at: str | None = None
    sender_id: str | None = None
    sender_email: str | None = None
    hold: dict[str, Any] | None = None
    cc: Sequence[dict[str, Any]] = []
    next: dict[str, Any] | None = None
    ended_reason: str | None = None


class ContactSegment(BaseModel):
    """One segment of the organization, and this contact's place in it.

    ``member`` is whether the contact is in the segment right now; ``mode`` is
    ``"include"`` or ``"exclude"`` when a manual override decides that, and
    empty when the conditions alone do.
    """

    id: str | None = None
    name: str | None = None
    color: str | None = None
    mode: str | None = None
    member: bool | None = None


class ContactVerificationOverview(BaseModel):
    """Who checks this workspace's addresses, and the contacts by verdict.

    ``provider`` is ``"builtin"`` or the connected paid provider.
    ``provider_error`` is set when a paid provider is connected but unusable
    (bad key, no credits), in which case the built-in check is in use.
    ``builtin_ready`` says whether the in-house probe can reach mail servers
    from this instance; without it the check still covers syntax, MX and
    disposable domains.
    """

    provider: str | None = None
    connection_id: str | None = None
    credits: int | None = None
    provider_error: str | None = None
    builtin_ready: bool | None = None
    counts: dict[str, int] | None = None


class ContactVerificationRequested(BaseModel):
    """How many contacts a verification action touched.

    ``queued`` is ``True`` for the ``verify`` action: the check runs in the
    background and each contact updates as its verdict lands. ``verifier`` and
    ``verifier_label`` name who runs a queued check (``"builtin"`` or the
    connected provider); ``verifier_error`` says why a connected provider
    cannot be used right now, in which case the built-in check runs instead.
    """

    affected: int | None = None
    action: str | None = None
    queued: bool | None = None
    verifier: str | None = None
    verifier_label: str | None = None
    verifier_error: str | None = None


def _selection_body(
    *,
    contacts: NotGivenOr[Sequence[str]],
    select_all: NotGivenOr[bool],
    filters: NotGivenOr[Mapping[str, Any]],
    exclude: NotGivenOr[Sequence[str]],
) -> dict[str, Any]:
    """Build the contact-selection part of a bulk request body.

    A selection names its contacts either by explicit ``contacts`` ids or, with
    ``all`` set, by the search ``filters`` minus the ``exclude`` ids (the
    dashboard's "select all matching").
    """
    return drop_not_given(
        {
            "contacts": list(contacts) if is_given(contacts) else contacts,
            "all": select_all,
            "filters": filters,
            "exclude": list(exclude) if is_given(exclude) else exclude,
        }
    )


def _search_body(
    *,
    query: NotGivenOr[str],
    custom_field_filters: NotGivenOr[Sequence[Mapping[str, Any]]],
    campaign_ids: NotGivenOr[Sequence[str]],
    lead_status: NotGivenOr[str],
    engagement: NotGivenOr[str],
    category_ids: NotGivenOr[Sequence[str]],
    segment_ids: NotGivenOr[Sequence[str]],
    verification_status: NotGivenOr[str],
    mail_hosts: NotGivenOr[Sequence[str]],
    min_campaigns: NotGivenOr[int],
    max_campaigns: NotGivenOr[int],
    subscribed: NotGivenOr[bool],
    created_after: NotGivenOr[str],
    created_before: NotGivenOr[str],
    updated_after: NotGivenOr[str],
    updated_before: NotGivenOr[str],
    sort_by: NotGivenOr[str],
    reverse: NotGivenOr[bool],
) -> dict[str, Any]:
    """Build the faceted contact filter body (shared by search and export)."""
    return drop_not_given(
        {
            "query": query,
            "custom_field_filters": custom_field_filters,
            "campaign_ids": campaign_ids,
            "lead_status": lead_status,
            "engagement": engagement,
            "category_ids": category_ids,
            "segment_ids": segment_ids,
            "verification_status": verification_status,
            "mail_hosts": mail_hosts,
            "min_campaigns": min_campaigns,
            "max_campaigns": max_campaigns,
            "subscribed": subscribed,
            "created_after": created_after,
            "created_before": created_before,
            "updated_after": updated_after,
            "updated_before": updated_before,
            "sort_by": sort_by,
            "reverse": reverse,
        }
    )


def _update_body(
    *,
    first_name: NotGivenOr[str],
    last_name: NotGivenOr[str],
    email: NotGivenOr[str],
    company: NotGivenOr[str],
    phone: NotGivenOr[str],
    custom_fields: NotGivenOr[Mapping[str, str]],
    subscribed: NotGivenOr[bool],
    campaigns: NotGivenOr[Sequence[str]],
    categories: NotGivenOr[Sequence[str]],
    add_categories: NotGivenOr[Sequence[str]],
    remove_categories: NotGivenOr[Sequence[str]],
) -> dict[str, Any]:
    return drop_not_given(
        {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "company": company,
            "phone": phone,
            "custom_fields": custom_fields,
            "subscribed": subscribed,
            "campaigns": campaigns,
            "categories": categories,
            "add_categories": add_categories,
            "remove_categories": remove_categories,
        }
    )


class Contacts(SyncAPIResource):
    """Synchronous ``contacts`` resource."""

    # -- create / read / update / delete -------------------------------------
    def create(
        self,
        contacts: Sequence[Mapping[str, Any]],
        *,
        options: RequestOptions | None = None,
    ) -> ContactsAdded:
        """Create contacts in bulk.

        The endpoint takes an array, so a single contact is a one-element
        list. An address that already exists is updated rather than
        duplicated.

        Args:
            contacts: One mapping per contact (``first_name``, ``last_name``,
                ``email``, ``company``, ``phone``, ``campaigns``,
                ``categories``, ``segments``, ``custom_fields``,
                ``subscribed``, ``verification_status``,
                ``verification_provider``).

        Note:
            ``segments`` joins the contact to those segments as an *include*
            override, so it belongs whatever the conditions say.
            ``verification_status`` is a verdict you already hold, in Warmbly's
            vocabulary or any provider's the platform knows;
            ``verification_provider`` names that vocabulary. It is stored as an
            imported verdict, which the background check leaves alone until it
            ages out. Contacts created through an API key are always stamped
            with the ``api`` source.
        """
        return self._post(
            "/contacts",
            cast_to=ContactsAdded,
            body=[dict(c) for c in contacts],
            options=options,
        )

    def search(
        self,
        *,
        query: NotGivenOr[str] = NOT_GIVEN,
        custom_field_filters: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        lead_status: NotGivenOr[str] = NOT_GIVEN,
        engagement: NotGivenOr[str] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        segment_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        verification_status: NotGivenOr[str] = NOT_GIVEN,
        mail_hosts: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        min_campaigns: NotGivenOr[int] = NOT_GIVEN,
        max_campaigns: NotGivenOr[int] = NOT_GIVEN,
        subscribed: NotGivenOr[bool] = NOT_GIVEN,
        created_after: NotGivenOr[str] = NOT_GIVEN,
        created_before: NotGivenOr[str] = NOT_GIVEN,
        updated_after: NotGivenOr[str] = NOT_GIVEN,
        updated_before: NotGivenOr[str] = NOT_GIVEN,
        sort_by: NotGivenOr[str] = NOT_GIVEN,
        reverse: NotGivenOr[bool] = NOT_GIVEN,
        category: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactSearchPage:
        """Search contacts. This is the list endpoint.

        Every facet is optional; an empty filter matches every contact. Paging
        is explicit (pass ``cursor`` from ``pagination.next_cursor``) because
        the filter travels in the request body.

        Args:
            query: Text search across the core fields.
            custom_field_filters: One ``{"type", "key", "value"}`` entry per
                custom-field predicate.
            campaign_ids: Contacts must be in *all* these campaigns.
            lead_status: Derived lead status; requires exactly one campaign id.
            engagement: Lead engagement (``opened``, ``not_opened``, ...),
                ANDed with *lead_status*; also requires exactly one campaign id.
            category_ids: Contacts must carry *all* these categories.
            segment_ids: Contacts must be members of *all* these segments.
            verification_status: Address verdict: ``valid``, ``risky``,
                ``invalid`` or ``unknown``.
            mail_hosts: Contacts whose inbox host is any of these; an empty
                string matches contacts not detected yet.
            subscribed: Filter by subscription state.
            sort_by: A column name (``created_at``, ``first_name``,
                ``company``, ...) or ``"custom:<key>"`` for a custom field.
            reverse: Sort ascending when true; the default is descending.
            category: A single category id, as a query filter.
            limit: Page size.
            cursor: An opaque cursor from a previous page.
        """
        return self._post(
            "/contacts/search",
            cast_to=ContactSearchPage,
            body=_search_body(
                query=query,
                custom_field_filters=custom_field_filters,
                campaign_ids=campaign_ids,
                lead_status=lead_status,
                engagement=engagement,
                category_ids=category_ids,
                segment_ids=segment_ids,
                verification_status=verification_status,
                mail_hosts=mail_hosts,
                min_campaigns=min_campaigns,
                max_campaigns=max_campaigns,
                subscribed=subscribed,
                created_after=created_after,
                created_before=created_before,
                updated_after=updated_after,
                updated_before=updated_before,
                sort_by=sort_by,
                reverse=reverse,
            ),
            query={"category": category, "limit": limit, "cursor": cursor},
            options=options,
        )

    def lookup(
        self,
        *,
        email: NotGivenOr[str] = NOT_GIVEN,
        thread_id: NotGivenOr[str] = NOT_GIVEN,
        account_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactLookup:
        """Look a contact up by sender address or by unibox thread.

        Pass ``email``, ``thread_id``, or both. Needs the ``read_contacts``
        permission; a ``thread_id`` reads the unibox, so it also needs
        ``read_unibox``.

        Args:
            email: The sender's address (a ``Name <addr>`` form is accepted).
            thread_id: A unibox thread; resolves a reply from an alias address
                to the lead the thread answers.
            account_id: The mailbox the thread lives in. An API key limited to
                certain mailboxes must name one it may use.
        """
        return self._get(
            "/contacts/lookup",
            cast_to=ContactLookup,
            query={"email": email, "thread_id": thread_id, "account_id": account_id},
            options=options,
        )

    def list_campaigns(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[ContactCampaignState]:
        """List the campaigns a contact is a lead of, with its progress."""
        return self._get_api_list(
            f"/contacts/{contact_id}/campaigns",
            model=ContactCampaignState,
            options=options,
        )

    def list_segments(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[ContactSegment]:
        """List every segment of the organization and this contact's place in it."""
        return self._get_api_list(
            f"/contacts/{contact_id}/segments",
            model=ContactSegment,
            options=options,
        )

    # -- address verification ------------------------------------------------
    def verification(
        self, *, options: RequestOptions | None = None
    ) -> ContactVerificationOverview:
        """Report who verifies this workspace's addresses, and the verdicts."""
        return self._get(
            "/contacts/verification",
            cast_to=ContactVerificationOverview,
            options=options,
        )

    def request_verification(
        self,
        *,
        action: str,
        contacts: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactVerificationRequested:
        """Re-check contacts, or record a manual verdict on them.

        Args:
            action: ``"verify"`` to queue a background re-check,
                ``"mark_deliverable"`` or ``"mark_undeliverable"`` to record a
                verdict outright.
            contacts: The contact ids to act on, at most 10000 per request.
            select_all: Act on every contact matching *filters* instead of
                listing ids (at most 250000).
            filters: The contact search body that *select_all* resolves.
            exclude: Contact ids to drop from a *select_all* selection.
            campaign_id: Instead of listing ids, select every lead of this
                campaign that verification refused.
        """
        return self._post(
            "/contacts/verification",
            cast_to=ContactVerificationRequested,
            body=drop_not_given(
                {
                    "action": action,
                    **_selection_body(
                        contacts=contacts,
                        select_all=select_all,
                        filters=filters,
                        exclude=exclude,
                    ),
                    "campaign_id": campaign_id,
                }
            ),
            options=options,
        )

    def custom_fields(
        self, *, options: RequestOptions | None = None
    ) -> CustomFieldKeys:
        """List every custom-field key in use across the organization."""
        return self._get(
            "/contacts/custom-fields", cast_to=CustomFieldKeys, options=options
        )

    def retrieve(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> ContactDetail:
        """Retrieve a contact with its engagement and suppression state."""
        return self._get(
            f"/contacts/{contact_id}", cast_to=ContactDetail, options=options
        )

    def update(
        self,
        contact_id: str,
        *,
        first_name: NotGivenOr[str] = NOT_GIVEN,
        last_name: NotGivenOr[str] = NOT_GIVEN,
        email: NotGivenOr[str] = NOT_GIVEN,
        company: NotGivenOr[str] = NOT_GIVEN,
        phone: NotGivenOr[str] = NOT_GIVEN,
        custom_fields: NotGivenOr[Mapping[str, str]] = NOT_GIVEN,
        subscribed: NotGivenOr[bool] = NOT_GIVEN,
        campaigns: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        categories: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        add_categories: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        remove_categories: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Contact:
        """Update a contact.

        Args:
            email: Replace the contact's address. The address is the contact's
                identity, so changing it drops the verification verdict and
                the delivery evidence that belonged to the old mailbox.
            campaigns: Replacement campaign membership. Omit to leave as-is.
            categories: Replacement category set. Omit to leave as-is.
            add_categories: Diff-style add; ignored when *categories* is set.
            remove_categories: Diff-style remove; ignored when *categories* is
                set.
        """
        return self._patch(
            f"/contacts/{contact_id}",
            cast_to=Contact,
            body=_update_body(
                first_name=first_name,
                last_name=last_name,
                email=email,
                company=company,
                phone=phone,
                custom_fields=custom_fields,
                subscribed=subscribed,
                campaigns=campaigns,
                categories=categories,
                add_categories=add_categories,
                remove_categories=remove_categories,
            ),
            options=options,
        )

    def delete(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> ContactDeleted:
        """Delete a contact."""
        return self._delete(
            f"/contacts/{contact_id}", cast_to=ContactDeleted, options=options
        )

    def bulk_update(
        self,
        *,
        contacts: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        add_campaigns: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        remove_campaigns: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        add_categories: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        remove_categories: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        fields: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        subscribe: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactsAdded:
        """Apply the same edit to many contacts at once.

        Args:
            contacts: The contact ids to edit, at most 10000 per request.
            select_all: Edit every contact matching *filters* instead of
                listing ids (at most 250000). The response then carries the
                counts rather than every updated row.
            filters: The contact search body that *select_all* resolves.
            exclude: Contact ids to drop from a *select_all* selection.
            fields: One ``{"type", "key", "value"}`` entry per field edit.
            subscribe: Set the subscription state on every listed contact.
        """
        return self._patch(
            "/contacts",
            cast_to=ContactsAdded,
            body=drop_not_given(
                {
                    **_selection_body(
                        contacts=contacts,
                        select_all=select_all,
                        filters=filters,
                        exclude=exclude,
                    ),
                    "add_campaigns": add_campaigns,
                    "remove_campaigns": remove_campaigns,
                    "add_categories": add_categories,
                    "remove_categories": remove_categories,
                    "fields": fields,
                    "subscribe": subscribe,
                }
            ),
            options=options,
        )

    def bulk_delete(
        self,
        contact_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        *,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactDeleted:
        """Delete many contacts at once.

        Args:
            contact_ids: The contact ids to delete, at most 10000 per request.
                Sent as a plain array unless a selection keyword is used.
            select_all: Delete every contact matching *filters* instead of
                listing ids (at most 250000).
            filters: The contact search body that *select_all* resolves.
            exclude: Contact ids to drop from a *select_all* selection.
        """
        body: Any = (
            _selection_body(
                contacts=contact_ids,
                select_all=select_all,
                filters=filters,
                exclude=exclude,
            )
            if is_given(select_all) or is_given(filters) or is_given(exclude)
            else list(contact_ids if is_given(contact_ids) else [])
        )
        return self._delete(
            "/contacts",
            cast_to=ContactDeleted,
            body=body,
            options=options,
        )

    # -- notes ---------------------------------------------------------------
    def list_notes(
        self,
        contact_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[ContactNote]:
        """List a contact's notes (auto-paginating). ``limit`` caps at 100."""
        return self._get_api_list(
            f"/contacts/{contact_id}/notes",
            model=ContactNote,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def create_note(
        self, contact_id: str, *, content: str, options: RequestOptions | None = None
    ) -> ContactNote:
        """Add a note to a contact. ``content`` caps at 10,000 characters."""
        return self._post(
            f"/contacts/{contact_id}/notes",
            cast_to=ContactNote,
            body={"content": content},
            options=options,
        )

    def update_note(
        self,
        contact_id: str,
        note_id: str,
        *,
        content: str,
        options: RequestOptions | None = None,
    ) -> ContactNote:
        """Edit a note's content."""
        return self._patch(
            f"/contacts/{contact_id}/notes/{note_id}",
            cast_to=ContactNote,
            body={"content": content},
            options=options,
        )

    def delete_note(
        self,
        contact_id: str,
        note_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> ContactNoteDeleted:
        """Delete a note."""
        return self._delete(
            f"/contacts/{contact_id}/notes/{note_id}",
            cast_to=ContactNoteDeleted,
            options=options,
        )

    # -- activity, emails, deals, timeline -----------------------------------
    def list_activities(
        self,
        contact_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[ContactActivity]:
        """List a contact's activity feed (auto-paginating). ``limit`` caps at 100."""
        return self._get_api_list(
            f"/contacts/{contact_id}/activities",
            model=ContactActivity,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def list_emails(
        self,
        contact_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        before_at: NotGivenOr[str] = NOT_GIVEN,
        before_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[ContactSentEmail]:
        """List emails sent to a contact, newest first.

        Paged with a ``(before_at, before_id)`` keyset rather than an opaque
        cursor; ``limit`` caps at 200.
        """
        return self._get_api_list(
            f"/contacts/{contact_id}/emails",
            model=ContactSentEmail,
            query={"limit": limit, "before_at": before_at, "before_id": before_id},
            options=options,
        )

    def list_deals(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[dict[str, Any]]:
        """List the CRM deals attached to a contact. Returned in full."""
        return self._get_api_list(
            f"/contacts/{contact_id}/deals", model=dict, options=options
        )

    def timeline(
        self,
        contact_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        before: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[ContactTimelineEntry]:
        """List a contact's merged timeline, newest first.

        Iterating the page follows ``pagination.next_cursor`` on its own;
        ``limit`` caps at 200.

        Args:
            contact_id: The contact id.
            limit: Page size, 1 to 200 (default 50).
            cursor: An opaque cursor from a previous page.
            before: Deprecated. Returns the events strictly older than this
                RFC 3339 timestamp, which can skip events sharing an instant
                with the page boundary. Ignored when *cursor* is set.
        """
        return self._get_api_list(
            f"/contacts/{contact_id}/timeline",
            model=ContactTimelineEntry,
            query={"limit": limit, "cursor": cursor, "before": before},
            options=options,
        )

    # -- AI research ---------------------------------------------------------
    def list_research(
        self,
        contact_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[ContactResearchRun]:
        """List past research runs for a contact. ``limit`` caps at 100."""
        return self._get_api_list(
            f"/contacts/{contact_id}/research",
            model=ContactResearchRun,
            query={"limit": limit},
            options=options,
        )

    def research(
        self,
        contact_id: str,
        *,
        objective: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactResearchRun:
        """Run AI research against a contact. Charges AI credits.

        Args:
            objective: What to research. Defaults to a general profile.
        """
        return self._post(
            f"/contacts/{contact_id}/research",
            cast_to=ContactResearchRun,
            body=drop_not_given({"objective": objective}),
            options=options,
        )

    def research_batch(
        self,
        *,
        contact_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        objective: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ResearchBatchQueued:
        """Queue AI research for many contacts. Charges credits per run.

        Runs asynchronously: watch the ``AI_RESEARCH_PROGRESS`` gateway event,
        or poll :meth:`list_research`. Needs the ``ai_research`` permission.

        Args:
            contact_ids: The contacts to research.
            select_all: Research every contact matching *filters* instead of
                listing ids (at most 250000).
            filters: The contact search body that *select_all* resolves.
            exclude: Contact ids to drop from a *select_all* selection.
            objective: What the research should find out.
        """
        return self._post(
            "/contacts/research/batch",
            cast_to=ResearchBatchQueued,
            body=drop_not_given(
                {
                    "contact_ids": list(contact_ids)
                    if is_given(contact_ids)
                    else contact_ids,
                    **_selection_body(
                        contacts=NOT_GIVEN,
                        select_all=select_all,
                        filters=filters,
                        exclude=exclude,
                    ),
                    "objective": objective,
                }
            ),
            options=options,
        )

    # -- import / export -----------------------------------------------------
    def import_preview(
        self,
        *,
        file: bytes,
        filename: str,
        content_type: str = "text/csv",
        options: RequestOptions | None = None,
    ) -> ContactImportPreview:
        """Parse an upload and return its headers, sample rows, and a mapping.

        Writes nothing. Uploads are capped at 50 MB.

        Args:
            file: The raw CSV/XLSX bytes.
            filename: The filename (its extension selects the parser).
            content_type: The file's MIME type.
        """
        return self._client.request(
            cast_to=ContactImportPreview,
            method="POST",
            path="/contacts/import/preview",
            files={"file": (filename, file, content_type)},
            options=options,
        )

    def import_commit(
        self,
        *,
        file: bytes,
        filename: str,
        import_options: Mapping[str, Any],
        content_type: str = "text/csv",
        options: RequestOptions | None = None,
    ) -> ContactImportResult:
        """Apply a column mapping to an upload and write the rows.

        Args:
            file: The raw CSV/XLSX bytes (the same file you previewed).
            filename: The filename.
            import_options: Column mapping, dedup strategy, target campaign,
                categories, and ``segment_ids`` the imported contacts join.
                Serialized into the ``options`` form field.
            content_type: The file's MIME type.
            options: Per-request transport overrides.
        """
        return self._client.request(
            cast_to=ContactImportResult,
            method="POST",
            path="/contacts/import/commit",
            form={"options": _json.dumps(dict(import_options))},
            files={"file": (filename, file, content_type)},
            options=options,
        )

    def export(
        self,
        *,
        format: str = "csv",
        scope: NotGivenOr[str] = NOT_GIVEN,
        contact_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        fields: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        filename: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> bytes:
        """Export contacts and return the encoded file bytes.

        Args:
            format: ``"csv"``, ``"xlsx"``, or ``"json"``.
            scope: Which contacts to export (all, selected, or filtered).
            contact_ids: Explicit ids, for a selection export.
            filters: A search filter body, for a filtered export.
            fields: The columns to include; defaults to every core field.
            filename: A suggested download filename.

        Returns:
            The raw encoded file. Write it to disk as-is; ``xlsx`` is binary.
        """
        return self._post(
            "/contacts/export",
            cast_to=bytes,
            body=drop_not_given(
                {
                    "format": format,
                    "scope": scope,
                    "contact_ids": contact_ids,
                    "filters": filters,
                    "fields": fields,
                    "filename": filename,
                }
            ),
            options=options,
        )

    # -- staged (background) imports -----------------------------------------
    def create_import(
        self,
        *,
        file: bytes,
        filename: str,
        content_type: str = "text/csv",
        options: RequestOptions | None = None,
    ) -> ContactImport:
        """Upload a file once and get back a draft import with its preview.

        Unlike :meth:`import_commit`, a staged import runs in the background:
        save a mapping with :meth:`save_import_draft`, check it with
        :meth:`analyze_import`, then :meth:`start_import` and follow it with
        :meth:`retrieve_import`. Needs the ``write_contacts`` permission.
        Uploads are capped at 50 MB.

        Args:
            file: The raw CSV/XLSX bytes.
            filename: The filename (its extension selects the parser).
            content_type: The file's MIME type.
        """
        return self._client.request(
            cast_to=ContactImport,
            method="POST",
            path="/contacts/imports",
            files={"file": (filename, file, content_type)},
            options=options,
        )

    def list_imports(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[ContactImport]:
        """List staged imports, newest first (auto-paginating).

        Needs the ``read_contacts`` permission.

        Args:
            limit: Page size, 1 to 100 (default 50).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/contacts/imports",
            model=ContactImport,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def retrieve_import(
        self, import_id: str, *, options: RequestOptions | None = None
    ) -> ContactImport:
        """Retrieve a staged import and its progress (``read_contacts``)."""
        return self._get(
            f"/contacts/imports/{import_id}", cast_to=ContactImport, options=options
        )

    def save_import_draft(
        self,
        import_id: str,
        *,
        import_options: Mapping[str, Any],
        options: RequestOptions | None = None,
    ) -> ContactImport:
        """Autosave a draft import's mapping and settings (``write_contacts``).

        Args:
            import_options: The column mapping, dedup strategy, target
                campaign, categories, ``segment_ids`` and the other import
                settings, as :meth:`import_commit` takes them.
        """
        return self._patch(
            f"/contacts/imports/{import_id}",
            cast_to=ContactImport,
            body=dict(import_options),
            options=options,
        )

    def analyze_import(
        self,
        import_id: str,
        *,
        mapping: Sequence[Mapping[str, Any]],
        has_header: bool = True,
        options: RequestOptions | None = None,
    ) -> ContactImportAnalysis:
        """Report what a draft would do under a mapping, writing nothing.

        Needs the ``write_contacts`` permission.

        Args:
            mapping: One ``{"index", "target"}`` entry per mapped column.
            has_header: Whether the first row is a header row.
        """
        return self._post(
            f"/contacts/imports/{import_id}/analyze",
            cast_to=ContactImportAnalysis,
            body={"mapping": [dict(m) for m in mapping], "has_header": has_header},
            options=options,
        )

    def start_import(
        self,
        import_id: str,
        *,
        import_options: Mapping[str, Any],
        options: RequestOptions | None = None,
    ) -> ContactImport:
        """Start a draft import. Needs the ``bulk_contacts`` permission.

        Starting an import that already started returns it unchanged, so a
        retry is safe.

        Args:
            import_options: The column mapping and settings to run with.
        """
        return self._post(
            f"/contacts/imports/{import_id}/start",
            cast_to=ContactImport,
            body=dict(import_options),
            options=options,
        )

    def cancel_import(
        self, import_id: str, *, options: RequestOptions | None = None
    ) -> ContactImport:
        """Cancel an import. Rows already written stay (``bulk_contacts``)."""
        return self._post(
            f"/contacts/imports/{import_id}/cancel",
            cast_to=ContactImport,
            options=options,
        )

    def download_import_failures(
        self, import_id: str, *, options: RequestOptions | None = None
    ) -> bytes:
        """Download every failed row of an import as CSV (``read_contacts``).

        Returns:
            The raw CSV bytes; write them to disk as-is.
        """
        return self._get(
            f"/contacts/imports/{import_id}/failed.csv",
            cast_to=bytes,
            options=options,
        )

    # -- salesforce panel ----------------------------------------------------
    def get_salesforce(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> ContactSalesforcePanel:
        """Retrieve a contact's linked Salesforce record, deals included.

        Needs the ``read_crm`` permission.
        """
        return self._get(
            f"/contacts/{contact_id}/salesforce",
            cast_to=ContactSalesforcePanel,
            options=options,
        )

    def sync_salesforce(
        self,
        contact_id: str,
        *,
        connection_id: NotGivenOr[str] = NOT_GIVEN,
        create_as: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactSalesforcePanel:
        """Match (or create) the contact in Salesforce and push its fields.

        Matching runs first, so a retry finds the record the first attempt
        created. Needs the ``integrations`` permission.

        Args:
            connection_id: Which Salesforce connection to sync to.
            create_as: ``"lead"`` or ``"contact"``, for a contact that has no
                record yet.
        """
        return self._post(
            f"/contacts/{contact_id}/salesforce/sync",
            cast_to=ContactSalesforcePanel,
            body=drop_not_given(
                {"connection_id": connection_id, "create_as": create_as}
            ),
            options=options,
        )

    def unlink_salesforce(
        self, contact_id: str, link_id: str, *, options: RequestOptions | None = None
    ) -> ContactDeleted:
        """Drop a contact's link to a Salesforce record (``integrations``)."""
        return self._delete(
            f"/contacts/{contact_id}/salesforce/links/{link_id}",
            cast_to=ContactDeleted,
            options=options,
        )


class AsyncContacts(AsyncAPIResource):
    """Asynchronous ``contacts`` resource."""

    # -- create / read / update / delete -------------------------------------
    async def create(
        self,
        contacts: Sequence[Mapping[str, Any]],
        *,
        options: RequestOptions | None = None,
    ) -> ContactsAdded:
        """Create contacts in bulk.

        The endpoint takes an array, so a single contact is a one-element
        list. An address that already exists is updated rather than
        duplicated.

        Args:
            contacts: One mapping per contact (``first_name``, ``last_name``,
                ``email``, ``company``, ``phone``, ``campaigns``,
                ``categories``, ``segments``, ``custom_fields``,
                ``subscribed``, ``verification_status``,
                ``verification_provider``).

        Note:
            ``segments`` joins the contact to those segments as an *include*
            override, so it belongs whatever the conditions say.
            ``verification_status`` is a verdict you already hold, in Warmbly's
            vocabulary or any provider's the platform knows;
            ``verification_provider`` names that vocabulary. It is stored as an
            imported verdict, which the background check leaves alone until it
            ages out. Contacts created through an API key are always stamped
            with the ``api`` source.
        """
        return await self._post(
            "/contacts",
            cast_to=ContactsAdded,
            body=[dict(c) for c in contacts],
            options=options,
        )

    async def search(
        self,
        *,
        query: NotGivenOr[str] = NOT_GIVEN,
        custom_field_filters: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        lead_status: NotGivenOr[str] = NOT_GIVEN,
        engagement: NotGivenOr[str] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        segment_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        verification_status: NotGivenOr[str] = NOT_GIVEN,
        mail_hosts: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        min_campaigns: NotGivenOr[int] = NOT_GIVEN,
        max_campaigns: NotGivenOr[int] = NOT_GIVEN,
        subscribed: NotGivenOr[bool] = NOT_GIVEN,
        created_after: NotGivenOr[str] = NOT_GIVEN,
        created_before: NotGivenOr[str] = NOT_GIVEN,
        updated_after: NotGivenOr[str] = NOT_GIVEN,
        updated_before: NotGivenOr[str] = NOT_GIVEN,
        sort_by: NotGivenOr[str] = NOT_GIVEN,
        reverse: NotGivenOr[bool] = NOT_GIVEN,
        category: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactSearchPage:
        """Search contacts. This is the list endpoint.

        Every facet is optional; an empty filter matches every contact. Paging
        is explicit (pass ``cursor`` from ``pagination.next_cursor``) because
        the filter travels in the request body.

        Args:
            query: Text search across the core fields.
            custom_field_filters: One ``{"type", "key", "value"}`` entry per
                custom-field predicate.
            campaign_ids: Contacts must be in *all* these campaigns.
            lead_status: Derived lead status; requires exactly one campaign id.
            engagement: Lead engagement (``opened``, ``not_opened``, ...),
                ANDed with *lead_status*; also requires exactly one campaign id.
            category_ids: Contacts must carry *all* these categories.
            segment_ids: Contacts must be members of *all* these segments.
            verification_status: Address verdict: ``valid``, ``risky``,
                ``invalid`` or ``unknown``.
            mail_hosts: Contacts whose inbox host is any of these; an empty
                string matches contacts not detected yet.
            subscribed: Filter by subscription state.
            sort_by: A column name (``created_at``, ``first_name``,
                ``company``, ...) or ``"custom:<key>"`` for a custom field.
            reverse: Sort ascending when true; the default is descending.
            category: A single category id, as a query filter.
            limit: Page size.
            cursor: An opaque cursor from a previous page.
        """
        return await self._post(
            "/contacts/search",
            cast_to=ContactSearchPage,
            body=_search_body(
                query=query,
                custom_field_filters=custom_field_filters,
                campaign_ids=campaign_ids,
                lead_status=lead_status,
                engagement=engagement,
                category_ids=category_ids,
                segment_ids=segment_ids,
                verification_status=verification_status,
                mail_hosts=mail_hosts,
                min_campaigns=min_campaigns,
                max_campaigns=max_campaigns,
                subscribed=subscribed,
                created_after=created_after,
                created_before=created_before,
                updated_after=updated_after,
                updated_before=updated_before,
                sort_by=sort_by,
                reverse=reverse,
            ),
            query={"category": category, "limit": limit, "cursor": cursor},
            options=options,
        )

    async def lookup(
        self,
        *,
        email: NotGivenOr[str] = NOT_GIVEN,
        thread_id: NotGivenOr[str] = NOT_GIVEN,
        account_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactLookup:
        """Look a contact up by sender address or by unibox thread.

        Pass ``email``, ``thread_id``, or both. Needs the ``read_contacts``
        permission; a ``thread_id`` reads the unibox, so it also needs
        ``read_unibox``.

        Args:
            email: The sender's address (a ``Name <addr>`` form is accepted).
            thread_id: A unibox thread; resolves a reply from an alias address
                to the lead the thread answers.
            account_id: The mailbox the thread lives in. An API key limited to
                certain mailboxes must name one it may use.
        """
        return await self._get(
            "/contacts/lookup",
            cast_to=ContactLookup,
            query={"email": email, "thread_id": thread_id, "account_id": account_id},
            options=options,
        )

    def list_campaigns(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[ContactCampaignState]:
        """List the campaigns a contact is a lead of, with its progress."""
        return self._get_api_list(
            f"/contacts/{contact_id}/campaigns",
            model=ContactCampaignState,
            options=options,
        )

    def list_segments(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[ContactSegment]:
        """List every segment of the organization and this contact's place in it."""
        return self._get_api_list(
            f"/contacts/{contact_id}/segments",
            model=ContactSegment,
            options=options,
        )

    # -- address verification ------------------------------------------------
    async def verification(
        self, *, options: RequestOptions | None = None
    ) -> ContactVerificationOverview:
        """Report who verifies this workspace's addresses, and the verdicts."""
        return await self._get(
            "/contacts/verification",
            cast_to=ContactVerificationOverview,
            options=options,
        )

    async def request_verification(
        self,
        *,
        action: str,
        contacts: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactVerificationRequested:
        """Re-check contacts, or record a manual verdict on them.

        Args:
            action: ``"verify"`` to queue a background re-check,
                ``"mark_deliverable"`` or ``"mark_undeliverable"`` to record a
                verdict outright.
            contacts: The contact ids to act on, at most 10000 per request.
            select_all: Act on every contact matching *filters* instead of
                listing ids (at most 250000).
            filters: The contact search body that *select_all* resolves.
            exclude: Contact ids to drop from a *select_all* selection.
            campaign_id: Instead of listing ids, select every lead of this
                campaign that verification refused.
        """
        return await self._post(
            "/contacts/verification",
            cast_to=ContactVerificationRequested,
            body=drop_not_given(
                {
                    "action": action,
                    **_selection_body(
                        contacts=contacts,
                        select_all=select_all,
                        filters=filters,
                        exclude=exclude,
                    ),
                    "campaign_id": campaign_id,
                }
            ),
            options=options,
        )

    async def custom_fields(
        self, *, options: RequestOptions | None = None
    ) -> CustomFieldKeys:
        """List every custom-field key in use across the organization."""
        return await self._get(
            "/contacts/custom-fields", cast_to=CustomFieldKeys, options=options
        )

    async def retrieve(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> ContactDetail:
        """Retrieve a contact with its engagement and suppression state."""
        return await self._get(
            f"/contacts/{contact_id}", cast_to=ContactDetail, options=options
        )

    async def update(
        self,
        contact_id: str,
        *,
        first_name: NotGivenOr[str] = NOT_GIVEN,
        last_name: NotGivenOr[str] = NOT_GIVEN,
        email: NotGivenOr[str] = NOT_GIVEN,
        company: NotGivenOr[str] = NOT_GIVEN,
        phone: NotGivenOr[str] = NOT_GIVEN,
        custom_fields: NotGivenOr[Mapping[str, str]] = NOT_GIVEN,
        subscribed: NotGivenOr[bool] = NOT_GIVEN,
        campaigns: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        categories: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        add_categories: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        remove_categories: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Contact:
        """Update a contact.

        Args:
            email: Replace the contact's address. The address is the contact's
                identity, so changing it drops the verification verdict and
                the delivery evidence that belonged to the old mailbox.
            campaigns: Replacement campaign membership. Omit to leave as-is.
            categories: Replacement category set. Omit to leave as-is.
            add_categories: Diff-style add; ignored when *categories* is set.
            remove_categories: Diff-style remove; ignored when *categories* is
                set.
        """
        return await self._patch(
            f"/contacts/{contact_id}",
            cast_to=Contact,
            body=_update_body(
                first_name=first_name,
                last_name=last_name,
                email=email,
                company=company,
                phone=phone,
                custom_fields=custom_fields,
                subscribed=subscribed,
                campaigns=campaigns,
                categories=categories,
                add_categories=add_categories,
                remove_categories=remove_categories,
            ),
            options=options,
        )

    async def delete(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> ContactDeleted:
        """Delete a contact."""
        return await self._delete(
            f"/contacts/{contact_id}", cast_to=ContactDeleted, options=options
        )

    async def bulk_update(
        self,
        *,
        contacts: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        add_campaigns: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        remove_campaigns: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        add_categories: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        remove_categories: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        fields: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        subscribe: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactsAdded:
        """Apply the same edit to many contacts at once.

        Args:
            contacts: The contact ids to edit, at most 10000 per request.
            select_all: Edit every contact matching *filters* instead of
                listing ids (at most 250000). The response then carries the
                counts rather than every updated row.
            filters: The contact search body that *select_all* resolves.
            exclude: Contact ids to drop from a *select_all* selection.
            fields: One ``{"type", "key", "value"}`` entry per field edit.
            subscribe: Set the subscription state on every listed contact.
        """
        return await self._patch(
            "/contacts",
            cast_to=ContactsAdded,
            body=drop_not_given(
                {
                    **_selection_body(
                        contacts=contacts,
                        select_all=select_all,
                        filters=filters,
                        exclude=exclude,
                    ),
                    "add_campaigns": add_campaigns,
                    "remove_campaigns": remove_campaigns,
                    "add_categories": add_categories,
                    "remove_categories": remove_categories,
                    "fields": fields,
                    "subscribe": subscribe,
                }
            ),
            options=options,
        )

    async def bulk_delete(
        self,
        contact_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        *,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactDeleted:
        """Delete many contacts at once.

        Args:
            contact_ids: The contact ids to delete, at most 10000 per request.
                Sent as a plain array unless a selection keyword is used.
            select_all: Delete every contact matching *filters* instead of
                listing ids (at most 250000).
            filters: The contact search body that *select_all* resolves.
            exclude: Contact ids to drop from a *select_all* selection.
        """
        body: Any = (
            _selection_body(
                contacts=contact_ids,
                select_all=select_all,
                filters=filters,
                exclude=exclude,
            )
            if is_given(select_all) or is_given(filters) or is_given(exclude)
            else list(contact_ids if is_given(contact_ids) else [])
        )
        return await self._delete(
            "/contacts",
            cast_to=ContactDeleted,
            body=body,
            options=options,
        )

    # -- notes ---------------------------------------------------------------
    def list_notes(
        self,
        contact_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[ContactNote]:
        """List a contact's notes (auto-paginating). ``limit`` caps at 100."""
        return self._get_api_list(
            f"/contacts/{contact_id}/notes",
            model=ContactNote,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def create_note(
        self, contact_id: str, *, content: str, options: RequestOptions | None = None
    ) -> ContactNote:
        """Add a note to a contact. ``content`` caps at 10,000 characters."""
        return await self._post(
            f"/contacts/{contact_id}/notes",
            cast_to=ContactNote,
            body={"content": content},
            options=options,
        )

    async def update_note(
        self,
        contact_id: str,
        note_id: str,
        *,
        content: str,
        options: RequestOptions | None = None,
    ) -> ContactNote:
        """Edit a note's content."""
        return await self._patch(
            f"/contacts/{contact_id}/notes/{note_id}",
            cast_to=ContactNote,
            body={"content": content},
            options=options,
        )

    async def delete_note(
        self,
        contact_id: str,
        note_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> ContactNoteDeleted:
        """Delete a note."""
        return await self._delete(
            f"/contacts/{contact_id}/notes/{note_id}",
            cast_to=ContactNoteDeleted,
            options=options,
        )

    # -- activity, emails, deals, timeline -----------------------------------
    def list_activities(
        self,
        contact_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[ContactActivity]:
        """List a contact's activity feed (auto-paginating). ``limit`` caps at 100."""
        return self._get_api_list(
            f"/contacts/{contact_id}/activities",
            model=ContactActivity,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def list_emails(
        self,
        contact_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        before_at: NotGivenOr[str] = NOT_GIVEN,
        before_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[ContactSentEmail]:
        """List emails sent to a contact, newest first.

        Paged with a ``(before_at, before_id)`` keyset rather than an opaque
        cursor; ``limit`` caps at 200.
        """
        return self._get_api_list(
            f"/contacts/{contact_id}/emails",
            model=ContactSentEmail,
            query={"limit": limit, "before_at": before_at, "before_id": before_id},
            options=options,
        )

    def list_deals(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[dict[str, Any]]:
        """List the CRM deals attached to a contact. Returned in full."""
        return self._get_api_list(
            f"/contacts/{contact_id}/deals", model=dict, options=options
        )

    def timeline(
        self,
        contact_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        before: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[ContactTimelineEntry]:
        """List a contact's merged timeline, newest first.

        Iterating the page follows ``pagination.next_cursor`` on its own;
        ``limit`` caps at 200.

        Args:
            contact_id: The contact id.
            limit: Page size, 1 to 200 (default 50).
            cursor: An opaque cursor from a previous page.
            before: Deprecated. Returns the events strictly older than this
                RFC 3339 timestamp, which can skip events sharing an instant
                with the page boundary. Ignored when *cursor* is set.
        """
        return self._get_api_list(
            f"/contacts/{contact_id}/timeline",
            model=ContactTimelineEntry,
            query={"limit": limit, "cursor": cursor, "before": before},
            options=options,
        )

    # -- AI research ---------------------------------------------------------
    def list_research(
        self,
        contact_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[ContactResearchRun]:
        """List past research runs for a contact. ``limit`` caps at 100."""
        return self._get_api_list(
            f"/contacts/{contact_id}/research",
            model=ContactResearchRun,
            query={"limit": limit},
            options=options,
        )

    async def research(
        self,
        contact_id: str,
        *,
        objective: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactResearchRun:
        """Run AI research against a contact. Charges AI credits.

        Args:
            objective: What to research. Defaults to a general profile.
        """
        return await self._post(
            f"/contacts/{contact_id}/research",
            cast_to=ContactResearchRun,
            body=drop_not_given({"objective": objective}),
            options=options,
        )

    async def research_batch(
        self,
        *,
        contact_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        objective: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ResearchBatchQueued:
        """Queue AI research for many contacts. Charges credits per run.

        Runs asynchronously: watch the ``AI_RESEARCH_PROGRESS`` gateway event,
        or poll :meth:`list_research`. Needs the ``ai_research`` permission.

        Args:
            contact_ids: The contacts to research.
            select_all: Research every contact matching *filters* instead of
                listing ids (at most 250000).
            filters: The contact search body that *select_all* resolves.
            exclude: Contact ids to drop from a *select_all* selection.
            objective: What the research should find out.
        """
        return await self._post(
            "/contacts/research/batch",
            cast_to=ResearchBatchQueued,
            body=drop_not_given(
                {
                    "contact_ids": list(contact_ids)
                    if is_given(contact_ids)
                    else contact_ids,
                    **_selection_body(
                        contacts=NOT_GIVEN,
                        select_all=select_all,
                        filters=filters,
                        exclude=exclude,
                    ),
                    "objective": objective,
                }
            ),
            options=options,
        )

    # -- import / export -----------------------------------------------------
    async def import_preview(
        self,
        *,
        file: bytes,
        filename: str,
        content_type: str = "text/csv",
        options: RequestOptions | None = None,
    ) -> ContactImportPreview:
        """Parse an upload and return its headers, sample rows, and a mapping.

        Writes nothing. Uploads are capped at 50 MB.

        Args:
            file: The raw CSV/XLSX bytes.
            filename: The filename (its extension selects the parser).
            content_type: The file's MIME type.
        """
        return await self._client.request(
            cast_to=ContactImportPreview,
            method="POST",
            path="/contacts/import/preview",
            files={"file": (filename, file, content_type)},
            options=options,
        )

    async def import_commit(
        self,
        *,
        file: bytes,
        filename: str,
        import_options: Mapping[str, Any],
        content_type: str = "text/csv",
        options: RequestOptions | None = None,
    ) -> ContactImportResult:
        """Apply a column mapping to an upload and write the rows.

        Args:
            file: The raw CSV/XLSX bytes (the same file you previewed).
            filename: The filename.
            import_options: Column mapping, dedup strategy, target campaign,
                categories, and ``segment_ids`` the imported contacts join.
                Serialized into the ``options`` form field.
            content_type: The file's MIME type.
            options: Per-request transport overrides.
        """
        return await self._client.request(
            cast_to=ContactImportResult,
            method="POST",
            path="/contacts/import/commit",
            form={"options": _json.dumps(dict(import_options))},
            files={"file": (filename, file, content_type)},
            options=options,
        )

    async def export(
        self,
        *,
        format: str = "csv",
        scope: NotGivenOr[str] = NOT_GIVEN,
        contact_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        fields: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        filename: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> bytes:
        """Export contacts and return the encoded file bytes.

        Args:
            format: ``"csv"``, ``"xlsx"``, or ``"json"``.
            scope: Which contacts to export (all, selected, or filtered).
            contact_ids: Explicit ids, for a selection export.
            filters: A search filter body, for a filtered export.
            fields: The columns to include; defaults to every core field.
            filename: A suggested download filename.

        Returns:
            The raw encoded file. Write it to disk as-is; ``xlsx`` is binary.
        """
        return await self._post(
            "/contacts/export",
            cast_to=bytes,
            body=drop_not_given(
                {
                    "format": format,
                    "scope": scope,
                    "contact_ids": contact_ids,
                    "filters": filters,
                    "fields": fields,
                    "filename": filename,
                }
            ),
            options=options,
        )

    # -- staged (background) imports -----------------------------------------
    async def create_import(
        self,
        *,
        file: bytes,
        filename: str,
        content_type: str = "text/csv",
        options: RequestOptions | None = None,
    ) -> ContactImport:
        """Upload a file once and get back a draft import with its preview.

        Unlike :meth:`import_commit`, a staged import runs in the background:
        save a mapping with :meth:`save_import_draft`, check it with
        :meth:`analyze_import`, then :meth:`start_import` and follow it with
        :meth:`retrieve_import`. Needs the ``write_contacts`` permission.
        Uploads are capped at 50 MB.

        Args:
            file: The raw CSV/XLSX bytes.
            filename: The filename (its extension selects the parser).
            content_type: The file's MIME type.
        """
        return await self._client.request(
            cast_to=ContactImport,
            method="POST",
            path="/contacts/imports",
            files={"file": (filename, file, content_type)},
            options=options,
        )

    def list_imports(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[ContactImport]:
        """List staged imports, newest first (auto-paginating).

        Needs the ``read_contacts`` permission.

        Args:
            limit: Page size, 1 to 100 (default 50).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/contacts/imports",
            model=ContactImport,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def retrieve_import(
        self, import_id: str, *, options: RequestOptions | None = None
    ) -> ContactImport:
        """Retrieve a staged import and its progress (``read_contacts``)."""
        return await self._get(
            f"/contacts/imports/{import_id}", cast_to=ContactImport, options=options
        )

    async def save_import_draft(
        self,
        import_id: str,
        *,
        import_options: Mapping[str, Any],
        options: RequestOptions | None = None,
    ) -> ContactImport:
        """Autosave a draft import's mapping and settings (``write_contacts``).

        Args:
            import_options: The column mapping, dedup strategy, target
                campaign, categories, ``segment_ids`` and the other import
                settings, as :meth:`import_commit` takes them.
        """
        return await self._patch(
            f"/contacts/imports/{import_id}",
            cast_to=ContactImport,
            body=dict(import_options),
            options=options,
        )

    async def analyze_import(
        self,
        import_id: str,
        *,
        mapping: Sequence[Mapping[str, Any]],
        has_header: bool = True,
        options: RequestOptions | None = None,
    ) -> ContactImportAnalysis:
        """Report what a draft would do under a mapping, writing nothing.

        Needs the ``write_contacts`` permission.

        Args:
            mapping: One ``{"index", "target"}`` entry per mapped column.
            has_header: Whether the first row is a header row.
        """
        return await self._post(
            f"/contacts/imports/{import_id}/analyze",
            cast_to=ContactImportAnalysis,
            body={"mapping": [dict(m) for m in mapping], "has_header": has_header},
            options=options,
        )

    async def start_import(
        self,
        import_id: str,
        *,
        import_options: Mapping[str, Any],
        options: RequestOptions | None = None,
    ) -> ContactImport:
        """Start a draft import. Needs the ``bulk_contacts`` permission.

        Starting an import that already started returns it unchanged, so a
        retry is safe.

        Args:
            import_options: The column mapping and settings to run with.
        """
        return await self._post(
            f"/contacts/imports/{import_id}/start",
            cast_to=ContactImport,
            body=dict(import_options),
            options=options,
        )

    async def cancel_import(
        self, import_id: str, *, options: RequestOptions | None = None
    ) -> ContactImport:
        """Cancel an import. Rows already written stay (``bulk_contacts``)."""
        return await self._post(
            f"/contacts/imports/{import_id}/cancel",
            cast_to=ContactImport,
            options=options,
        )

    async def download_import_failures(
        self, import_id: str, *, options: RequestOptions | None = None
    ) -> bytes:
        """Download every failed row of an import as CSV (``read_contacts``).

        Returns:
            The raw CSV bytes; write them to disk as-is.
        """
        return await self._get(
            f"/contacts/imports/{import_id}/failed.csv",
            cast_to=bytes,
            options=options,
        )

    # -- salesforce panel ----------------------------------------------------
    async def get_salesforce(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> ContactSalesforcePanel:
        """Retrieve a contact's linked Salesforce record, deals included.

        Needs the ``read_crm`` permission.
        """
        return await self._get(
            f"/contacts/{contact_id}/salesforce",
            cast_to=ContactSalesforcePanel,
            options=options,
        )

    async def sync_salesforce(
        self,
        contact_id: str,
        *,
        connection_id: NotGivenOr[str] = NOT_GIVEN,
        create_as: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactSalesforcePanel:
        """Match (or create) the contact in Salesforce and push its fields.

        Matching runs first, so a retry finds the record the first attempt
        created. Needs the ``integrations`` permission.

        Args:
            connection_id: Which Salesforce connection to sync to.
            create_as: ``"lead"`` or ``"contact"``, for a contact that has no
                record yet.
        """
        return await self._post(
            f"/contacts/{contact_id}/salesforce/sync",
            cast_to=ContactSalesforcePanel,
            body=drop_not_given(
                {"connection_id": connection_id, "create_as": create_as}
            ),
            options=options,
        )

    async def unlink_salesforce(
        self, contact_id: str, link_id: str, *, options: RequestOptions | None = None
    ) -> ContactDeleted:
        """Drop a contact's link to a Salesforce record (``integrations``)."""
        return await self._delete(
            f"/contacts/{contact_id}/salesforce/links/{link_id}",
            cast_to=ContactDeleted,
            options=options,
        )
