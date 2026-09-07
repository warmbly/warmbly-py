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
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncContacts",
    "Contact",
    "ContactActivity",
    "ContactCampaignState",
    "ContactDeleted",
    "ContactDetail",
    "ContactImportPreview",
    "ContactImportResult",
    "ContactLookup",
    "ContactNote",
    "ContactNoteDeleted",
    "ContactResearchRun",
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
    ``esp_provider`` is the mailbox provider the address resolves to.
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
    esp_provider: str | None = None
    esp_resolved_at: str | None = None
    campaign_lead: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ContactDetail(Contact):
    """A contact plus its engagement roll-up and first-touch attribution.

    ``suppression`` is non-``None`` when the address is suppressed, in which
    case campaigns skip it. ``verification`` explains the verdict: the reasons
    behind it and the observations it was scored from. ``source`` is where the
    contact first came from (``manual``, ``campaign``, ``import``,
    ``sheet_sync``, ``api``, ``ai_assistant``, ``form``, ``automation``, or
    ``unknown`` for a row created before attribution existed) and never
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
    """The result of looking a contact up by email address."""

    contact: Contact | None = None


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
    :meth:`Contacts.import_commit`.
    """

    filename: str | None = None
    format: str | None = None
    columns: Sequence[str] = []
    has_header: bool | None = None
    sample_rows: Sequence[Sequence[str]] = []
    total_rows: int | None = None
    suggested_mapping: Sequence[dict[str, Any]] = []


class ContactImportResult(BaseModel):
    """Per-row results from a committed import."""

    total: int | None = None
    imported: int | None = None
    updated: int | None = None
    skipped: int | None = None
    failed: int | None = None
    errors: Sequence[dict[str, Any]] = []
    errors_truncated: bool | None = None
    quality: dict[str, Any] | None = None
    started_at: str | None = None
    ended_at: str | None = None


class ContactCampaignState(BaseModel):
    """One campaign a contact is a lead of, with its progress through it.

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
    background and each contact updates as its verdict lands.
    """

    affected: int | None = None
    action: str | None = None
    queued: bool | None = None


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
            subscribed: Filter by subscription state.
            sort_by: e.g. ``"first_name ASC"`` or ``"campaign_count DESC"``.
            reverse: Invert the sort direction.
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
        self, *, email: str, options: RequestOptions | None = None
    ) -> ContactLookup:
        """Look a contact up by email address."""
        return self._get(
            "/contacts/lookup",
            cast_to=ContactLookup,
            query={"email": email},
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
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactVerificationRequested:
        """Re-check contacts, or record a manual verdict on them.

        Args:
            action: ``"verify"`` to queue a background re-check,
                ``"mark_deliverable"`` or ``"mark_undeliverable"`` to record a
                verdict outright.
            contacts: The contact ids to act on, at most 1000 per request.
            campaign_id: Instead of listing ids, select every lead of this
                campaign that verification refused.
        """
        return self._post(
            "/contacts/verification",
            cast_to=ContactVerificationRequested,
            body=drop_not_given(
                {
                    "action": action,
                    "contacts": contacts,
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
        contacts: Sequence[str],
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
            contacts: The contact ids to edit.
            fields: One ``{"type", "key", "value"}`` entry per field edit.
            subscribe: Set the subscription state on every listed contact.
        """
        return self._patch(
            "/contacts",
            cast_to=ContactsAdded,
            body=drop_not_given(
                {
                    "contacts": list(contacts),
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
        contact_ids: Sequence[str],
        *,
        options: RequestOptions | None = None,
    ) -> ContactDeleted:
        """Delete many contacts at once.

        Args:
            contact_ids: The contact ids to delete, sent as a plain array.
        """
        return self._delete(
            "/contacts",
            cast_to=ContactDeleted,
            body=list(contact_ids),
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
        contact_ids: Sequence[str],
        objective: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ResearchBatchQueued:
        """Queue AI research for many contacts. Charges credits per run.

        Runs asynchronously: watch the ``AI_RESEARCH_PROGRESS`` gateway event,
        or poll :meth:`list_research`.
        """
        return self._post(
            "/contacts/research/batch",
            cast_to=ResearchBatchQueued,
            body=drop_not_given(
                {"contact_ids": list(contact_ids), "objective": objective}
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
            subscribed: Filter by subscription state.
            sort_by: e.g. ``"first_name ASC"`` or ``"campaign_count DESC"``.
            reverse: Invert the sort direction.
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
        self, *, email: str, options: RequestOptions | None = None
    ) -> ContactLookup:
        """Look a contact up by email address."""
        return await self._get(
            "/contacts/lookup",
            cast_to=ContactLookup,
            query={"email": email},
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
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactVerificationRequested:
        """Re-check contacts, or record a manual verdict on them.

        Args:
            action: ``"verify"`` to queue a background re-check,
                ``"mark_deliverable"`` or ``"mark_undeliverable"`` to record a
                verdict outright.
            contacts: The contact ids to act on, at most 1000 per request.
            campaign_id: Instead of listing ids, select every lead of this
                campaign that verification refused.
        """
        return await self._post(
            "/contacts/verification",
            cast_to=ContactVerificationRequested,
            body=drop_not_given(
                {
                    "action": action,
                    "contacts": contacts,
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
        contacts: Sequence[str],
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
            contacts: The contact ids to edit.
            fields: One ``{"type", "key", "value"}`` entry per field edit.
            subscribe: Set the subscription state on every listed contact.
        """
        return await self._patch(
            "/contacts",
            cast_to=ContactsAdded,
            body=drop_not_given(
                {
                    "contacts": list(contacts),
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
        contact_ids: Sequence[str],
        *,
        options: RequestOptions | None = None,
    ) -> ContactDeleted:
        """Delete many contacts at once.

        Args:
            contact_ids: The contact ids to delete, sent as a plain array.
        """
        return await self._delete(
            "/contacts",
            cast_to=ContactDeleted,
            body=list(contact_ids),
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
        contact_ids: Sequence[str],
        objective: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ResearchBatchQueued:
        """Queue AI research for many contacts. Charges credits per run.

        Runs asynchronously: watch the ``AI_RESEARCH_PROGRESS`` gateway event,
        or poll :meth:`list_research`.
        """
        return await self._post(
            "/contacts/research/batch",
            cast_to=ResearchBatchQueued,
            body=drop_not_given(
                {"contact_ids": list(contact_ids), "objective": objective}
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
