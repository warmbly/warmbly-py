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
    "SalesforceLinkRemoved",
    "SalesforcePanelAccount",
    "SalesforcePanelConnection",
    "SalesforcePanelOpportunity",
    "SalesforcePanelRecord",
    "SalesforcePanelRef",
    "SalesforcePanelSync",
    "SalesforcePanelTask",
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
    ``esp_provider`` is the mailbox provider the address resolves to and
    ``mail_host`` is who hosts the inbox (empty until the backend sweep has
    read the domain's MX). ``verification_requested_at`` is set while a
    member-requested re-check waits to run. ``outreach`` is the contact's
    engagement across every campaign (``sent``, ``opened``, ``clicked``,
    ``replied``, ``bounced`` and a ``last_*_at`` stamp for each); it is
    populated on search rows only.
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
    verification_requested_at: str | None = None
    is_catch_all: bool | None = None
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
    """Retained for compatibility; no route returns it any more.

    :meth:`Contacts.create` and :meth:`Contacts.bulk_update` answer with a bare
    list of :class:`Contact`, and the server never sent these count fields.
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
    """The result of looking a contact up by email address or thread.

    ``match`` says how the sender resolved: ``email`` when the address is the
    contact's, ``thread`` when the thread answers a campaign send to the
    contact and the reply came from another address. It is empty when
    ``contact`` is ``None``.
    """

    contact: Contact | None = None
    match: str | None = None


class CustomFieldKeys(BaseModel):
    """Every custom-field key in use across the organization's contacts."""

    data: Sequence[str] = []


class ContactNote(BaseModel):
    """A note attached to a contact."""

    id: str
    contact_id: str | None = None
    organization_id: str | None = None
    user_id: str | None = None
    content: str | None = None
    user: dict[str, Any] | None = None
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
    automated fetcher — a mail privacy proxy, a security gateway walking the
    links — rather than a person, with ``machine_reason`` naming the rule that
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
    :meth:`Contacts.import_commit`. ``mapping_source`` is ``saved`` when the
    workspace confirmed a mapping for these exact headers before, and
    ``suggested`` otherwise. ``inferred_columns`` are the column indexes whose
    suggestion came from a model's judgment and deserve a second look.
    ``column_stats`` (background imports only) describes every column over the
    whole file with ``filled``, ``distinct`` and ``samples``.
    """

    filename: str | None = None
    format: str | None = None
    columns: Sequence[str] = []
    has_header: bool | None = None
    sample_rows: Sequence[Sequence[str]] = []
    total_rows: int | None = None
    suggested_mapping: Sequence[dict[str, Any]] = []
    inferred_columns: Sequence[int] | None = None
    column_stats: Sequence[dict[str, Any]] | None = None
    mapping_source: str | None = None


class ContactImportResult(BaseModel):
    """Per-row results from a committed import."""

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
    """One background import of a contact file.

    ``status`` moves ``draft`` (uploaded, waiting for a mapping), ``queued``,
    ``running`` and then ends in ``completed``, ``failed`` or ``cancelled``.
    ``total`` is the number of data rows and ``processed`` how many have
    settled. ``preview`` is what the column mapper shows and is carried by a
    draft only; ``failures`` are the first failed rows once the import has
    finished (the full set is :meth:`Contacts.download_import_failures`).
    ``segments_pinned`` is ``None`` when the import had no segment targets,
    otherwise whether every membership write landed.
    """

    id: str
    organization_id: str | None = None
    created_by: str | None = None
    filename: str | None = None
    format: str | None = None
    status: str | None = None
    has_header: bool | None = None
    columns: Sequence[str] | None = None
    total: int | None = None
    processed: int | None = None
    imported: int | None = None
    updated: int | None = None
    skipped: int | None = None
    failed: int | None = None
    options: dict[str, Any] | None = None
    quality: dict[str, Any] | None = None
    segments_pinned: bool | None = None
    notes: Sequence[str] | None = None
    error: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    preview: ContactImportPreview | None = None
    failures: Sequence[dict[str, Any]] | None = None


class ContactImportAnalysis(BaseModel):
    """What an import would do under a mapping, read over the whole file.

    Writes nothing. Every data row lands in exactly one of ``new``,
    ``existing``, ``duplicates_in_file``, ``invalid`` or ``conflicts``.
    ``invalid_samples`` are the first invalid or conflicting rows with a
    ``reason``. ``problem`` says why starting the import would be refused as a
    whole (a plan contact limit, too many new categories) and is empty when it
    would run.
    """

    rows: int | None = None
    new: int | None = None
    existing: int | None = None
    duplicates_in_file: int | None = None
    invalid: int | None = None
    conflicts: int | None = None
    invalid_samples: Sequence[dict[str, Any]] | None = None
    quality: dict[str, Any] | None = None
    problem: str | None = None


class ContactCampaignState(BaseModel):
    """One campaign a contact is a lead of, with its progress through it.

    ``steps`` is the flow with this contact's per-step stamps; ``next`` is the
    action the scheduler would take next, derived on read, and is ``None`` once
    the flow has ended for the contact, in which case ``ended_reason`` says
    why. ``sender_id`` and ``sender_email`` are the mailbox this lead's whole
    sequence sends from, fixed when its first email went out. ``hold`` is the
    per-lead pause (``since``, ``until``, ``reason``, ``source``), present only
    while it is live, and ``cc`` the contacts copied on every email to this
    lead. ``lead_status`` can also be ``paused``.
    """

    campaign_id: str | None = None
    campaign_name: str | None = None
    campaign_status: str | None = None
    lead_status: str | None = None
    sender_id: str | None = None
    sender_email: str | None = None
    failure_reason: str | None = None
    steps: Sequence[dict[str, Any]] = []
    completed_steps: int | None = None
    total_steps: int | None = None
    current_step: dict[str, Any] | None = None
    last_action: str | None = None
    last_action_at: str | None = None
    hold: dict[str, Any] | None = None
    cc: Sequence[dict[str, Any]] | None = None
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

    ``provider`` is ``"builtin"``, ``"millionverifier"`` or ``"cleanmylist"``.
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
    background and each contact updates as its verdict lands. ``verifier``
    (and its display name ``verifier_label``) says who runs a queued check,
    ``builtin`` or the connected provider; ``verifier_error`` says why a
    connected provider cannot be used right now, in which case the built-in
    check runs instead.
    """

    affected: int | None = None
    action: str | None = None
    queued: bool | None = None
    verifier: str | None = None
    verifier_label: str | None = None
    verifier_error: str | None = None


class SalesforcePanelConnection(BaseModel):
    """One connected Salesforce org."""

    id: str | None = None
    label: str | None = None
    environment: str | None = None
    instance_url: str | None = None


class SalesforcePanelRef(BaseModel):
    """A related Salesforce user."""

    id: str | None = None
    name: str | None = None


class SalesforcePanelAccount(BaseModel):
    """The Salesforce Account a Contact record belongs to."""

    id: str | None = None
    name: str | None = None
    url: str | None = None


class SalesforcePanelOpportunity(BaseModel):
    """An opportunity on the linked record's account."""

    id: str | None = None
    name: str | None = None
    stage: str | None = None
    amount: float | None = None
    close_date: str | None = None
    is_closed: bool | None = None
    is_won: bool | None = None
    url: str | None = None


class SalesforcePanelTask(BaseModel):
    """A recent Salesforce activity on the linked record.

    ``from_warmbly`` is ``True`` for a task Warmbly logged itself.
    """

    id: str | None = None
    subject: str | None = None
    date: str | None = None
    status: str | None = None
    owner_name: str | None = None
    url: str | None = None
    from_warmbly: bool | None = None


class SalesforcePanelSync(BaseModel):
    """The activity-outbox picture for the contact."""

    pending: int | None = None
    failed: int | None = None
    synced: int | None = None
    last_error: str | None = None


class SalesforcePanelRecord(BaseModel):
    """The Lead or Contact a Warmbly contact is linked to in one org.

    ``link_id`` is what :meth:`Contacts.unlink_salesforce` takes. ``object`` is
    ``Lead`` or ``Contact`` and ``linked_by`` says how the link was made.
    ``stale`` is ``True`` when the live read behind ``opportunities`` and
    ``tasks`` could not be refreshed; ``error`` then says why.
    """

    link_id: str | None = None
    connection_id: str | None = None
    connection_label: str | None = None
    object: str | None = None
    id: str | None = None
    url: str | None = None
    name: str | None = None
    title: str | None = None
    company: str | None = None
    email: str | None = None
    phone: str | None = None
    status: str | None = None
    owner: SalesforcePanelRef | None = None
    account: SalesforcePanelAccount | None = None
    is_converted: bool | None = None
    opted_out: bool | None = None
    lead_source: str | None = None
    opportunities: Sequence[SalesforcePanelOpportunity] | None = None
    tasks: Sequence[SalesforcePanelTask] | None = None
    linked_by: str | None = None
    last_synced_at: str | None = None
    last_pushed_at: str | None = None
    sync: SalesforcePanelSync | None = None
    stale: bool | None = None
    error: str | None = None


class ContactSalesforcePanel(BaseModel):
    """A contact's Salesforce context.

    ``connections`` are the Salesforce orgs connected to the workspace,
    ``records`` the Lead or Contact the contact is linked to in each, and
    ``can_sync`` whether a sync can be requested right now. Reading the panel
    links the contact on the way when its address matches a record nobody has
    linked yet.
    """

    connections: Sequence[SalesforcePanelConnection] | None = None
    records: Sequence[SalesforcePanelRecord] | None = None
    can_sync: bool | None = None


class SalesforceLinkRemoved(BaseModel):
    """The result of unlinking a contact from a Salesforce record (``204``)."""

    id: str | None = None
    deleted: bool | None = None


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


def _import_options(
    *,
    mapping: NotGivenOr[Sequence[Mapping[str, Any]]],
    dedup: NotGivenOr[str],
    has_header: NotGivenOr[bool],
    category_ids: NotGivenOr[Sequence[str]],
    campaign_ids: NotGivenOr[Sequence[str]],
    segment_ids: NotGivenOr[Sequence[str]],
    subscribed_default: NotGivenOr[bool],
) -> dict[str, Any]:
    """Build the mapping-and-options body of a draft save or an import start."""
    return drop_not_given(
        {
            "mapping": [dict(m) for m in mapping] if is_given(mapping) else NOT_GIVEN,
            "dedup": dedup,
            "has_header": has_header,
            "category_ids": category_ids,
            "campaign_ids": campaign_ids,
            "segment_ids": segment_ids,
            "subscribed_default": subscribed_default,
        }
    )


def _selection(
    *,
    contacts: NotGivenOr[Sequence[str]],
    select_all: NotGivenOr[bool],
    filters: NotGivenOr[Mapping[str, Any]],
    exclude: NotGivenOr[Sequence[str]],
) -> dict[str, Any]:
    """Build the bulk-selection keys: an id list, or "select all matching".

    ``select_all`` travels as the ``all`` key. A selection naming both prefers
    the filter on the server.
    """
    return drop_not_given(
        {
            "contacts": list(contacts) if is_given(contacts) else NOT_GIVEN,
            "all": select_all,
            "filters": filters,
            "exclude": list(exclude) if is_given(exclude) else NOT_GIVEN,
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
    ) -> list[Contact]:
        """Create contacts in bulk.

        Pass one mapping per contact; a single contact is a one-element
        list. An address that already exists is updated rather than
        duplicated. Returns the contacts as stored, in a bare list.

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
            cast_to=list[Contact],
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
            mail_hosts: Contacts whose inbox is hosted by any of these hosts;
                an empty string matches addresses not detected yet.
            subscribed: Filter by subscription state.
            sort_by: A column name such as ``created_at``, ``first_name`` or
                ``company``, or ``custom:<key>`` to sort by a custom field.
            reverse: Sort ascending (the default is descending).
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
        """Look a contact up by email address, by unibox thread, or both.

        Send *email* or *thread_id* (at least one). A thread resolves a sender
        who replied from an alias to the lead the thread answers; supplying
        *thread_id* needs unibox read access as well. Nothing matching is a
        ``None`` ``contact``, not an error.

        Args:
            email: The sender address. ``Name <addr>`` is accepted.
            thread_id: A unibox thread id.
            account_id: The mailbox the thread lives in.
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
            contacts: The contact ids to act on, at most 10,000 per request.
            select_all: Act on every contact matching *filters* instead of an
                id list (at most 250,000).
            filters: The contact search body that defines the selection when
                *select_all* is set.
            exclude: Ids to drop from a select-all selection.
            campaign_id: Instead of listing ids, select every lead of this
                campaign that verification refused.
        """
        return self._post(
            "/contacts/verification",
            cast_to=ContactVerificationRequested,
            body=drop_not_given(
                {
                    "action": action,
                    **_selection(
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
    ) -> list[Contact]:
        """Apply the same edit to many contacts at once.

        Returns the updated contacts as a bare list. A select-all edit answers
        with an empty list, because it can cover tens of thousands of rows.

        Args:
            contacts: The contact ids to edit, at most 10,000.
            select_all: Edit every contact matching *filters* instead of an id
                list (at most 250,000).
            filters: The contact search body that defines the selection when
                *select_all* is set.
            exclude: Ids to drop from a select-all selection.
            fields: One ``{"type", "key", "value"}`` entry per field edit.
            subscribe: Set the subscription state on every listed contact.
        """
        result = self._patch(
            "/contacts",
            cast_to=list[Contact],
            body=drop_not_given(
                {
                    **_selection(
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
        return result or []

    def bulk_delete(
        self,
        contact_ids: Sequence[str] | None = None,
        *,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactDeleted:
        """Delete many contacts at once.

        Args:
            contact_ids: The contact ids to delete (at most 10,000), sent as a
                plain array.
            select_all: Delete every contact matching *filters* instead of an
                id list (at most 250,000); sent as a selection object.
            filters: The contact search body that defines the selection when
                *select_all* is set.
            exclude: Ids to drop from a select-all selection.
        """
        body: Any = list(contact_ids or [])
        if select_all is True:
            body = _selection(
                contacts=NOT_GIVEN,
                select_all=True,
                filters=filters,
                exclude=exclude,
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
        or poll :meth:`list_research`.

        Args:
            contact_ids: The contacts to research, at most 10,000.
            select_all: Research every contact matching *filters* instead of
                an id list (at most 250,000).
            filters: The contact search body that defines the selection when
                *select_all* is set.
            exclude: Ids to drop from a select-all selection.
            objective: What to research. Defaults to a general profile.
        """
        return self._post(
            "/contacts/research/batch",
            cast_to=ResearchBatchQueued,
            body=drop_not_given(
                {
                    "contact_ids": (
                        list(contact_ids) if is_given(contact_ids) else NOT_GIVEN
                    ),
                    **_selection(
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

    # -- background imports --------------------------------------------------
    def list_imports(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[ContactImport]:
        """List background contact imports, newest first (auto-paginating).

        Requires ``READ_CONTACTS``.

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

    def create_import(
        self,
        *,
        file: bytes,
        filename: str,
        content_type: str = "text/csv",
        options: RequestOptions | None = None,
    ) -> ContactImport:
        """Upload a contact file once and get a draft import back.

        Requires ``WRITE_CONTACTS``. Nothing is written yet: the draft carries
        the ``preview`` the column mapper needs. Map the columns with
        :meth:`save_import_draft`, check the outcome with
        :meth:`analyze_import`, then run it with :meth:`start_import`. Uploads
        are capped at 50 MB.

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

    def retrieve_import(
        self, import_id: str, *, options: RequestOptions | None = None
    ) -> ContactImport:
        """Retrieve a background import and its progress. Requires ``READ_CONTACTS``."""
        return self._get(
            f"/contacts/imports/{import_id}", cast_to=ContactImport, options=options
        )

    def save_import_draft(
        self,
        import_id: str,
        *,
        mapping: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        dedup: NotGivenOr[str] = NOT_GIVEN,
        has_header: NotGivenOr[bool] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        segment_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        subscribed_default: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactImport:
        """Autosave a draft's mapping and options so a reload resumes it.

        Requires ``WRITE_CONTACTS``. Writes no contacts and is safe to repeat.
        The arguments are those of :meth:`start_import`.
        """
        return self._patch(
            f"/contacts/imports/{import_id}",
            cast_to=ContactImport,
            body=_import_options(
                mapping=mapping,
                dedup=dedup,
                has_header=has_header,
                category_ids=category_ids,
                campaign_ids=campaign_ids,
                segment_ids=segment_ids,
                subscribed_default=subscribed_default,
            ),
            options=options,
        )

    def analyze_import(
        self,
        import_id: str,
        *,
        mapping: Sequence[Mapping[str, Any]],
        has_header: bool,
        options: RequestOptions | None = None,
    ) -> ContactImportAnalysis:
        """Report what the draft would do under a mapping, writing nothing.

        Requires ``WRITE_CONTACTS``. The whole file is read, so the counts are
        exact.

        Args:
            import_id: The draft import.
            mapping: One ``{"index", "target"}`` entry per column, plus
                ``custom_key`` for a custom field and
                ``verification_provider`` for a verification column. Targets
                are ``ignore``, ``email``, ``first_name``, ``last_name``,
                ``company``, ``phone``, ``subscribed``, ``categories``,
                ``verification_status`` and ``custom``.
            has_header: Whether the first row is a header.
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
        mapping: Sequence[Mapping[str, Any]],
        has_header: bool,
        dedup: NotGivenOr[str] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        segment_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        subscribed_default: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactImport:
        """Run the import in the background. Requires ``BULK_CONTACTS``.

        Starting an import that already started returns it unchanged, so a
        retry is safe. Poll :meth:`retrieve_import` for progress.

        Args:
            import_id: The draft import.
            mapping: The column mapping, as for :meth:`analyze_import`.
            has_header: Whether the first row is a header.
            dedup: What to do when an address already exists: ``skip``,
                ``update`` or ``create_duplicate``.
            category_ids: Categories every imported contact joins.
            campaign_ids: Campaigns every imported contact joins.
            segment_ids: Segments every imported contact is pinned into.
            subscribed_default: The subscription state of new contacts when no
                column maps ``subscribed`` (the server defaults to ``True``).
        """
        return self._post(
            f"/contacts/imports/{import_id}/start",
            cast_to=ContactImport,
            body=_import_options(
                mapping=mapping,
                dedup=dedup,
                has_header=has_header,
                category_ids=category_ids,
                campaign_ids=campaign_ids,
                segment_ids=segment_ids,
                subscribed_default=subscribed_default,
            ),
            options=options,
        )

    def cancel_import(
        self, import_id: str, *, options: RequestOptions | None = None
    ) -> ContactImport:
        """Cancel a background import. Requires ``BULK_CONTACTS``.

        Rows already written stay written.
        """
        return self._post(
            f"/contacts/imports/{import_id}/cancel",
            cast_to=ContactImport,
            options=options,
        )

    def download_import_failures(
        self, import_id: str, *, options: RequestOptions | None = None
    ) -> bytes:
        """Download every failed row of an import as CSV bytes.

        Requires ``READ_CONTACTS``. :attr:`ContactImport.failures` lists only
        the first rows; this carries all of them.
        """
        return self._get(
            f"/contacts/imports/{import_id}/failed.csv",
            cast_to=bytes,
            options=options,
        )

    # -- Salesforce ----------------------------------------------------------
    def salesforce(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> ContactSalesforcePanel:
        """Return a contact's Salesforce panel: linked records and live context.

        Requires ``READ_CRM``. Reading the panel links the contact on the way
        when its address matches a Salesforce record nobody has linked yet.
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
        """Match (or create) the contact in Salesforce and push its mapped fields.

        Requires the ``INTEGRATIONS`` permission. Matching runs first, so a
        retry finds the record the first attempt created instead of creating
        another. Returns the refreshed panel.

        Args:
            contact_id: The contact to sync.
            connection_id: The Salesforce connection to sync to; omit for the
                workspace's connected org.
            create_as: ``"lead"`` or ``"contact"``, the record type to create
                when nothing matches. Defaults to the connection's setting.
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
        self,
        contact_id: str,
        link_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> SalesforceLinkRemoved:
        """Drop a contact's link to a Salesforce record.

        Requires the ``INTEGRATIONS`` permission. *link_id* is the ``link_id``
        of a record in :meth:`salesforce`. The Salesforce record itself is
        untouched.
        """
        return self._delete(
            f"/contacts/{contact_id}/salesforce/links/{link_id}",
            cast_to=SalesforceLinkRemoved,
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
    ) -> list[Contact]:
        """Create contacts in bulk.

        Pass one mapping per contact; a single contact is a one-element
        list. An address that already exists is updated rather than
        duplicated. Returns the contacts as stored, in a bare list.

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
            cast_to=list[Contact],
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
            mail_hosts: Contacts whose inbox is hosted by any of these hosts;
                an empty string matches addresses not detected yet.
            subscribed: Filter by subscription state.
            sort_by: A column name such as ``created_at``, ``first_name`` or
                ``company``, or ``custom:<key>`` to sort by a custom field.
            reverse: Sort ascending (the default is descending).
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
        """Look a contact up by email address, by unibox thread, or both.

        Send *email* or *thread_id* (at least one). A thread resolves a sender
        who replied from an alias to the lead the thread answers; supplying
        *thread_id* needs unibox read access as well. Nothing matching is a
        ``None`` ``contact``, not an error.

        Args:
            email: The sender address. ``Name <addr>`` is accepted.
            thread_id: A unibox thread id.
            account_id: The mailbox the thread lives in.
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
            contacts: The contact ids to act on, at most 10,000 per request.
            select_all: Act on every contact matching *filters* instead of an
                id list (at most 250,000).
            filters: The contact search body that defines the selection when
                *select_all* is set.
            exclude: Ids to drop from a select-all selection.
            campaign_id: Instead of listing ids, select every lead of this
                campaign that verification refused.
        """
        return await self._post(
            "/contacts/verification",
            cast_to=ContactVerificationRequested,
            body=drop_not_given(
                {
                    "action": action,
                    **_selection(
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
    ) -> list[Contact]:
        """Apply the same edit to many contacts at once.

        Returns the updated contacts as a bare list. A select-all edit answers
        with an empty list, because it can cover tens of thousands of rows.

        Args:
            contacts: The contact ids to edit, at most 10,000.
            select_all: Edit every contact matching *filters* instead of an id
                list (at most 250,000).
            filters: The contact search body that defines the selection when
                *select_all* is set.
            exclude: Ids to drop from a select-all selection.
            fields: One ``{"type", "key", "value"}`` entry per field edit.
            subscribe: Set the subscription state on every listed contact.
        """
        result = await self._patch(
            "/contacts",
            cast_to=list[Contact],
            body=drop_not_given(
                {
                    **_selection(
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
        return result or []

    async def bulk_delete(
        self,
        contact_ids: Sequence[str] | None = None,
        *,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactDeleted:
        """Delete many contacts at once.

        Args:
            contact_ids: The contact ids to delete (at most 10,000), sent as a
                plain array.
            select_all: Delete every contact matching *filters* instead of an
                id list (at most 250,000); sent as a selection object.
            filters: The contact search body that defines the selection when
                *select_all* is set.
            exclude: Ids to drop from a select-all selection.
        """
        body: Any = list(contact_ids or [])
        if select_all is True:
            body = _selection(
                contacts=NOT_GIVEN,
                select_all=True,
                filters=filters,
                exclude=exclude,
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
        or poll :meth:`list_research`.

        Args:
            contact_ids: The contacts to research, at most 10,000.
            select_all: Research every contact matching *filters* instead of
                an id list (at most 250,000).
            filters: The contact search body that defines the selection when
                *select_all* is set.
            exclude: Ids to drop from a select-all selection.
            objective: What to research. Defaults to a general profile.
        """
        return await self._post(
            "/contacts/research/batch",
            cast_to=ResearchBatchQueued,
            body=drop_not_given(
                {
                    "contact_ids": (
                        list(contact_ids) if is_given(contact_ids) else NOT_GIVEN
                    ),
                    **_selection(
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

    # -- background imports --------------------------------------------------
    def list_imports(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[ContactImport]:
        """List background contact imports, newest first (auto-paginating).

        Requires ``READ_CONTACTS``.

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

    async def create_import(
        self,
        *,
        file: bytes,
        filename: str,
        content_type: str = "text/csv",
        options: RequestOptions | None = None,
    ) -> ContactImport:
        """Upload a contact file once and get a draft import back.

        Requires ``WRITE_CONTACTS``. Nothing is written yet: the draft carries
        the ``preview`` the column mapper needs. Map the columns with
        :meth:`save_import_draft`, check the outcome with
        :meth:`analyze_import`, then run it with :meth:`start_import`. Uploads
        are capped at 50 MB.

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

    async def retrieve_import(
        self, import_id: str, *, options: RequestOptions | None = None
    ) -> ContactImport:
        """Retrieve a background import and its progress. Requires ``READ_CONTACTS``."""
        return await self._get(
            f"/contacts/imports/{import_id}", cast_to=ContactImport, options=options
        )

    async def save_import_draft(
        self,
        import_id: str,
        *,
        mapping: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        dedup: NotGivenOr[str] = NOT_GIVEN,
        has_header: NotGivenOr[bool] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        segment_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        subscribed_default: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactImport:
        """Autosave a draft's mapping and options so a reload resumes it.

        Requires ``WRITE_CONTACTS``. Writes no contacts and is safe to repeat.
        The arguments are those of :meth:`start_import`.
        """
        return await self._patch(
            f"/contacts/imports/{import_id}",
            cast_to=ContactImport,
            body=_import_options(
                mapping=mapping,
                dedup=dedup,
                has_header=has_header,
                category_ids=category_ids,
                campaign_ids=campaign_ids,
                segment_ids=segment_ids,
                subscribed_default=subscribed_default,
            ),
            options=options,
        )

    async def analyze_import(
        self,
        import_id: str,
        *,
        mapping: Sequence[Mapping[str, Any]],
        has_header: bool,
        options: RequestOptions | None = None,
    ) -> ContactImportAnalysis:
        """Report what the draft would do under a mapping, writing nothing.

        Requires ``WRITE_CONTACTS``. The whole file is read, so the counts are
        exact.

        Args:
            import_id: The draft import.
            mapping: One ``{"index", "target"}`` entry per column, plus
                ``custom_key`` for a custom field and
                ``verification_provider`` for a verification column. Targets
                are ``ignore``, ``email``, ``first_name``, ``last_name``,
                ``company``, ``phone``, ``subscribed``, ``categories``,
                ``verification_status`` and ``custom``.
            has_header: Whether the first row is a header.
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
        mapping: Sequence[Mapping[str, Any]],
        has_header: bool,
        dedup: NotGivenOr[str] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        segment_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        subscribed_default: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactImport:
        """Run the import in the background. Requires ``BULK_CONTACTS``.

        Starting an import that already started returns it unchanged, so a
        retry is safe. Poll :meth:`retrieve_import` for progress.

        Args:
            import_id: The draft import.
            mapping: The column mapping, as for :meth:`analyze_import`.
            has_header: Whether the first row is a header.
            dedup: What to do when an address already exists: ``skip``,
                ``update`` or ``create_duplicate``.
            category_ids: Categories every imported contact joins.
            campaign_ids: Campaigns every imported contact joins.
            segment_ids: Segments every imported contact is pinned into.
            subscribed_default: The subscription state of new contacts when no
                column maps ``subscribed`` (the server defaults to ``True``).
        """
        return await self._post(
            f"/contacts/imports/{import_id}/start",
            cast_to=ContactImport,
            body=_import_options(
                mapping=mapping,
                dedup=dedup,
                has_header=has_header,
                category_ids=category_ids,
                campaign_ids=campaign_ids,
                segment_ids=segment_ids,
                subscribed_default=subscribed_default,
            ),
            options=options,
        )

    async def cancel_import(
        self, import_id: str, *, options: RequestOptions | None = None
    ) -> ContactImport:
        """Cancel a background import. Requires ``BULK_CONTACTS``.

        Rows already written stay written.
        """
        return await self._post(
            f"/contacts/imports/{import_id}/cancel",
            cast_to=ContactImport,
            options=options,
        )

    async def download_import_failures(
        self, import_id: str, *, options: RequestOptions | None = None
    ) -> bytes:
        """Download every failed row of an import as CSV bytes.

        Requires ``READ_CONTACTS``. :attr:`ContactImport.failures` lists only
        the first rows; this carries all of them.
        """
        return await self._get(
            f"/contacts/imports/{import_id}/failed.csv",
            cast_to=bytes,
            options=options,
        )

    # -- Salesforce ----------------------------------------------------------
    async def salesforce(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> ContactSalesforcePanel:
        """Return a contact's Salesforce panel: linked records and live context.

        Requires ``READ_CRM``. Reading the panel links the contact on the way
        when its address matches a Salesforce record nobody has linked yet.
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
        """Match (or create) the contact in Salesforce and push its mapped fields.

        Requires the ``INTEGRATIONS`` permission. Matching runs first, so a
        retry finds the record the first attempt created instead of creating
        another. Returns the refreshed panel.

        Args:
            contact_id: The contact to sync.
            connection_id: The Salesforce connection to sync to; omit for the
                workspace's connected org.
            create_as: ``"lead"`` or ``"contact"``, the record type to create
                when nothing matches. Defaults to the connection's setting.
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
        self,
        contact_id: str,
        link_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> SalesforceLinkRemoved:
        """Drop a contact's link to a Salesforce record.

        Requires the ``INTEGRATIONS`` permission. *link_id* is the ``link_id``
        of a record in :meth:`salesforce`. The Salesforce record itself is
        untouched.
        """
        return await self._delete(
            f"/contacts/{contact_id}/salesforce/links/{link_id}",
            cast_to=SalesforceLinkRemoved,
            options=options,
        )
