"""The ``contacts`` resource — search, manage, import/export, and enrich contacts.

Maps to the ``/v1/contacts`` route group. The collection is queried via
``POST /contacts/search`` (not a plain ``GET``), so the listing entrypoint is
:meth:`Contacts.search`. Bulk create/update/delete operate on the collection
endpoint itself, while per-contact reads and the CRM sub-resources (emails,
timeline, notes, activities, deals) hang off ``/contacts/{id}/...``.
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
    "AsyncContacts",
    "Contact",
    "ContactActivity",
    "ContactDeal",
    "ContactDeleted",
    "ContactEmail",
    "ContactExport",
    "ContactImportPreview",
    "ContactImportResult",
    "ContactNote",
    "ContactNoteDeleted",
    "ContactSearchResult",
    "ContactTimelineEntry",
    "Contacts",
    "ContactsBulkResult",
]


class Contact(BaseModel):
    """A contact (lead) belonging to an organization."""

    id: str
    campaign_id: str | None = None
    organization_id: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ContactSearchResult(BaseModel):
    """A page of contacts returned by ``POST /contacts/search``."""

    data: Sequence[Contact] = []
    total: int | None = None
    next_cursor: str | None = None
    has_more: bool | None = None


class ContactsBulkResult(BaseModel):
    """The outcome of a bulk create, update, or delete operation."""

    created: int | None = None
    updated: int | None = None
    deleted: int | None = None
    skipped: int | None = None
    failed: int | None = None
    data: Sequence[Contact] = []
    errors: Sequence[dict[str, Any]] = []


class ContactDeleted(BaseModel):
    """The result of deleting a single contact."""

    id: str | None = None
    status: str | None = None
    deleted: bool | None = None


class ContactExport(BaseModel):
    """A handle to an export job or its inlined payload."""

    id: str | None = None
    status: str | None = None
    format: str | None = None
    url: str | None = None
    download_url: str | None = None
    total: int | None = None
    created_at: str | None = None


class ContactImportPreview(BaseModel):
    """A dry-run summary of an import before committing it."""

    token: str | None = None
    total: int | None = None
    valid: int | None = None
    invalid: int | None = None
    duplicates: int | None = None
    columns: Sequence[str] = []
    sample: Sequence[dict[str, Any]] = []
    errors: Sequence[dict[str, Any]] = []


class ContactImportResult(BaseModel):
    """The outcome of committing an import."""

    id: str | None = None
    status: str | None = None
    imported: int | None = None
    updated: int | None = None
    skipped: int | None = None
    failed: int | None = None
    errors: Sequence[dict[str, Any]] = []


class ContactEmail(BaseModel):
    """An email exchanged with a contact."""

    id: str
    contact_id: str | None = None
    campaign_id: str | None = None
    email_account_id: str | None = None
    direction: str | None = None
    subject: str | None = None
    status: str | None = None
    sent_at: str | None = None
    created_at: str | None = None


class ContactTimelineEntry(BaseModel):
    """A single event on a contact's activity timeline."""

    id: str
    contact_id: str | None = None
    type: str | None = None
    title: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = {}
    occurred_at: str | None = None
    created_at: str | None = None


class ContactNote(BaseModel):
    """A free-form note attached to a contact."""

    id: str
    contact_id: str | None = None
    organization_id: str | None = None
    author_id: str | None = None
    body: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ContactNoteDeleted(BaseModel):
    """The result of deleting a contact note."""

    id: str | None = None
    status: str | None = None
    deleted: bool | None = None


class ContactActivity(BaseModel):
    """An activity record associated with a contact."""

    id: str
    contact_id: str | None = None
    type: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = {}
    created_at: str | None = None


class ContactDeal(BaseModel):
    """A CRM deal linked to a contact."""

    id: str
    contact_id: str | None = None
    organization_id: str | None = None
    pipeline_id: str | None = None
    stage: str | None = None
    name: str | None = None
    value: float | None = None
    currency: str | None = None
    status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class Contacts(SyncAPIResource):
    """Synchronous ``contacts`` resource."""

    def search(
        self,
        *,
        query: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        filters: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
        sort: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactSearchResult:
        """Search contacts (the collection listing entrypoint).

        Args:
            query: A free-text search string.
            campaign_id: Restrict results to a single campaign.
            status: Restrict results to contacts in this status.
            filters: Additional structured filter criteria.
            sort: A sort expression (e.g. ``"created_at:desc"``).
            limit: The maximum number of contacts to return.
            cursor: The pagination cursor from a previous response.
            options: Per-request overrides.

        Returns:
            A :class:`ContactSearchResult` carrying the matched contacts and
            pagination metadata.
        """
        body = drop_not_given(
            {
                "query": query,
                "campaign_id": campaign_id,
                "status": status,
                "filters": filters,
                "sort": sort,
                "limit": limit,
                "cursor": cursor,
            }
        )
        return self._post(
            "/contacts/search", cast_to=ContactSearchResult, body=body, options=options
        )

    def create(
        self,
        *,
        contacts: Sequence[dict[str, Any]],
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactsBulkResult:
        """Add one or more contacts.

        Args:
            contacts: The list of contact objects to add. Each entry typically
                carries ``email`` plus optional ``first_name``, ``last_name``,
                ``company``, and custom fields.
            campaign_id: Optionally associate the new contacts with a campaign.
            options: Per-request overrides.

        Returns:
            A :class:`ContactsBulkResult` summarizing the operation.
        """
        body = drop_not_given({"contacts": contacts, "campaign_id": campaign_id})
        return self._post(
            "/contacts", cast_to=ContactsBulkResult, body=body, options=options
        )

    def bulk_delete(
        self,
        *,
        ids: Sequence[str],
        options: RequestOptions | None = None,
    ) -> ContactsBulkResult:
        """Delete multiple contacts by id.

        Args:
            ids: The ids of the contacts to delete.
            options: Per-request overrides.
        """
        return self._delete(
            "/contacts",
            cast_to=ContactsBulkResult,
            body={"ids": ids},
            options=options,
        )

    def bulk_update(
        self,
        *,
        ids: Sequence[str],
        update: dict[str, Any],
        options: RequestOptions | None = None,
    ) -> ContactsBulkResult:
        """Apply the same field updates to multiple contacts.

        Args:
            ids: The ids of the contacts to update.
            update: The field changes to apply to every targeted contact.
            options: Per-request overrides.
        """
        return self._patch(
            "/contacts",
            cast_to=ContactsBulkResult,
            body={"ids": ids, "update": update},
            options=options,
        )

    def export(
        self,
        *,
        format: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        filters: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactExport:
        """Start an export of contacts matching the given criteria.

        Args:
            format: The export format (e.g. ``"csv"``).
            campaign_id: Restrict the export to a single campaign.
            status: Restrict the export to contacts in this status.
            ids: Export only this explicit set of contact ids.
            filters: Additional structured filter criteria.
            options: Per-request overrides.
        """
        body = drop_not_given(
            {
                "format": format,
                "campaign_id": campaign_id,
                "status": status,
                "ids": ids,
                "filters": filters,
            }
        )
        return self._post(
            "/contacts/export", cast_to=ContactExport, body=body, options=options
        )

    def import_preview(
        self,
        *,
        contacts: NotGivenOr[Sequence[dict[str, Any]]] = NOT_GIVEN,
        file_url: NotGivenOr[str] = NOT_GIVEN,
        mapping: NotGivenOr[dict[str, str]] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactImportPreview:
        """Dry-run an import to validate rows before committing.

        Args:
            contacts: Inline contact rows to preview.
            file_url: A reference to a previously uploaded file to preview.
            mapping: A column-to-field mapping applied to the source rows.
            campaign_id: The campaign the contacts would be imported into.
            options: Per-request overrides.

        Returns:
            A :class:`ContactImportPreview` with validation counts and a sample.
            Carry its ``token`` into :meth:`import_commit`.
        """
        body = drop_not_given(
            {
                "contacts": contacts,
                "file_url": file_url,
                "mapping": mapping,
                "campaign_id": campaign_id,
            }
        )
        return self._post(
            "/contacts/import/preview",
            cast_to=ContactImportPreview,
            body=body,
            options=options,
        )

    def import_commit(
        self,
        *,
        token: NotGivenOr[str] = NOT_GIVEN,
        contacts: NotGivenOr[Sequence[dict[str, Any]]] = NOT_GIVEN,
        file_url: NotGivenOr[str] = NOT_GIVEN,
        mapping: NotGivenOr[dict[str, str]] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactImportResult:
        """Commit a previewed import.

        Args:
            token: The ``token`` returned by :meth:`import_preview`.
            contacts: Inline contact rows to import (when not using a token).
            file_url: A reference to a previously uploaded file to import.
            mapping: A column-to-field mapping applied to the source rows.
            campaign_id: The campaign to import the contacts into.
            options: Per-request overrides.
        """
        body = drop_not_given(
            {
                "token": token,
                "contacts": contacts,
                "file_url": file_url,
                "mapping": mapping,
                "campaign_id": campaign_id,
            }
        )
        return self._post(
            "/contacts/import/commit",
            cast_to=ContactImportResult,
            body=body,
            options=options,
        )

    def lookup(self, *, email: str, options: RequestOptions | None = None) -> Contact:
        """Look up a single contact by email address.

        Args:
            email: The email address to look up.
            options: Per-request overrides.
        """
        return self._get(
            "/contacts/lookup",
            cast_to=Contact,
            query={"email": email},
            options=options,
        )

    def retrieve(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> Contact:
        """Retrieve a single contact by id."""
        return self._get(f"/contacts/{contact_id}", cast_to=Contact, options=options)

    def update(
        self,
        contact_id: str,
        *,
        email: NotGivenOr[str] = NOT_GIVEN,
        first_name: NotGivenOr[str] = NOT_GIVEN,
        last_name: NotGivenOr[str] = NOT_GIVEN,
        company: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Contact:
        """Update a single contact's fields.

        Args:
            contact_id: The id of the contact to update.
            email: A new email address.
            first_name: A new first name.
            last_name: A new last name.
            company: A new company.
            status: A new status.
            campaign_id: Reassign the contact to a campaign.
            options: Per-request overrides.
        """
        body = drop_not_given(
            {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "company": company,
                "status": status,
                "campaign_id": campaign_id,
            }
        )
        return self._patch(
            f"/contacts/{contact_id}", cast_to=Contact, body=body, options=options
        )

    def delete(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> ContactDeleted:
        """Delete a single contact by id."""
        return self._delete(
            f"/contacts/{contact_id}", cast_to=ContactDeleted, options=options
        )

    def emails(
        self,
        contact_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[ContactEmail]:
        """List emails exchanged with a contact (auto-paginating)."""
        return self._get_api_list(
            f"/contacts/{contact_id}/emails",
            model=ContactEmail,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def timeline(
        self,
        contact_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[ContactTimelineEntry]:
        """List a contact's timeline entries (auto-paginating)."""
        return self._get_api_list(
            f"/contacts/{contact_id}/timeline",
            model=ContactTimelineEntry,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def list_notes(
        self,
        contact_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[ContactNote]:
        """List a contact's notes (auto-paginating)."""
        return self._get_api_list(
            f"/contacts/{contact_id}/notes",
            model=ContactNote,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def create_note(
        self,
        contact_id: str,
        *,
        body: str,
        options: RequestOptions | None = None,
    ) -> ContactNote:
        """Add a note to a contact.

        Args:
            contact_id: The id of the contact to annotate.
            body: The note text.
            options: Per-request overrides.
        """
        return self._post(
            f"/contacts/{contact_id}/notes",
            cast_to=ContactNote,
            body={"body": body},
            options=options,
        )

    def update_note(
        self,
        contact_id: str,
        note_id: str,
        *,
        body: str,
        options: RequestOptions | None = None,
    ) -> ContactNote:
        """Edit an existing note on a contact.

        Args:
            contact_id: The id of the contact that owns the note.
            note_id: The id of the note to edit.
            body: The replacement note text.
            options: Per-request overrides.
        """
        return self._patch(
            f"/contacts/{contact_id}/notes/{note_id}",
            cast_to=ContactNote,
            body={"body": body},
            options=options,
        )

    def delete_note(
        self,
        contact_id: str,
        note_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> ContactNoteDeleted:
        """Delete a note from a contact."""
        return self._delete(
            f"/contacts/{contact_id}/notes/{note_id}",
            cast_to=ContactNoteDeleted,
            options=options,
        )

    def activities(
        self,
        contact_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[ContactActivity]:
        """List a contact's activity records (auto-paginating)."""
        return self._get_api_list(
            f"/contacts/{contact_id}/activities",
            model=ContactActivity,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def deals(
        self,
        contact_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[ContactDeal]:
        """List the CRM deals linked to a contact (auto-paginating)."""
        return self._get_api_list(
            f"/contacts/{contact_id}/deals",
            model=ContactDeal,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )


class AsyncContacts(AsyncAPIResource):
    """Asynchronous ``contacts`` resource."""

    async def search(
        self,
        *,
        query: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        filters: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
        sort: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactSearchResult:
        """Search contacts (the collection listing entrypoint).

        Args:
            query: A free-text search string.
            campaign_id: Restrict results to a single campaign.
            status: Restrict results to contacts in this status.
            filters: Additional structured filter criteria.
            sort: A sort expression (e.g. ``"created_at:desc"``).
            limit: The maximum number of contacts to return.
            cursor: The pagination cursor from a previous response.
            options: Per-request overrides.

        Returns:
            A :class:`ContactSearchResult` carrying the matched contacts and
            pagination metadata.
        """
        body = drop_not_given(
            {
                "query": query,
                "campaign_id": campaign_id,
                "status": status,
                "filters": filters,
                "sort": sort,
                "limit": limit,
                "cursor": cursor,
            }
        )
        return await self._post(
            "/contacts/search", cast_to=ContactSearchResult, body=body, options=options
        )

    async def create(
        self,
        *,
        contacts: Sequence[dict[str, Any]],
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactsBulkResult:
        """Add one or more contacts.

        Args:
            contacts: The list of contact objects to add. Each entry typically
                carries ``email`` plus optional ``first_name``, ``last_name``,
                ``company``, and custom fields.
            campaign_id: Optionally associate the new contacts with a campaign.
            options: Per-request overrides.

        Returns:
            A :class:`ContactsBulkResult` summarizing the operation.
        """
        body = drop_not_given({"contacts": contacts, "campaign_id": campaign_id})
        return await self._post(
            "/contacts", cast_to=ContactsBulkResult, body=body, options=options
        )

    async def bulk_delete(
        self,
        *,
        ids: Sequence[str],
        options: RequestOptions | None = None,
    ) -> ContactsBulkResult:
        """Delete multiple contacts by id.

        Args:
            ids: The ids of the contacts to delete.
            options: Per-request overrides.
        """
        return await self._delete(
            "/contacts",
            cast_to=ContactsBulkResult,
            body={"ids": ids},
            options=options,
        )

    async def bulk_update(
        self,
        *,
        ids: Sequence[str],
        update: dict[str, Any],
        options: RequestOptions | None = None,
    ) -> ContactsBulkResult:
        """Apply the same field updates to multiple contacts.

        Args:
            ids: The ids of the contacts to update.
            update: The field changes to apply to every targeted contact.
            options: Per-request overrides.
        """
        return await self._patch(
            "/contacts",
            cast_to=ContactsBulkResult,
            body={"ids": ids, "update": update},
            options=options,
        )

    async def export(
        self,
        *,
        format: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        filters: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactExport:
        """Start an export of contacts matching the given criteria.

        Args:
            format: The export format (e.g. ``"csv"``).
            campaign_id: Restrict the export to a single campaign.
            status: Restrict the export to contacts in this status.
            ids: Export only this explicit set of contact ids.
            filters: Additional structured filter criteria.
            options: Per-request overrides.
        """
        body = drop_not_given(
            {
                "format": format,
                "campaign_id": campaign_id,
                "status": status,
                "ids": ids,
                "filters": filters,
            }
        )
        return await self._post(
            "/contacts/export", cast_to=ContactExport, body=body, options=options
        )

    async def import_preview(
        self,
        *,
        contacts: NotGivenOr[Sequence[dict[str, Any]]] = NOT_GIVEN,
        file_url: NotGivenOr[str] = NOT_GIVEN,
        mapping: NotGivenOr[dict[str, str]] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactImportPreview:
        """Dry-run an import to validate rows before committing.

        Args:
            contacts: Inline contact rows to preview.
            file_url: A reference to a previously uploaded file to preview.
            mapping: A column-to-field mapping applied to the source rows.
            campaign_id: The campaign the contacts would be imported into.
            options: Per-request overrides.

        Returns:
            A :class:`ContactImportPreview` with validation counts and a sample.
            Carry its ``token`` into :meth:`import_commit`.
        """
        body = drop_not_given(
            {
                "contacts": contacts,
                "file_url": file_url,
                "mapping": mapping,
                "campaign_id": campaign_id,
            }
        )
        return await self._post(
            "/contacts/import/preview",
            cast_to=ContactImportPreview,
            body=body,
            options=options,
        )

    async def import_commit(
        self,
        *,
        token: NotGivenOr[str] = NOT_GIVEN,
        contacts: NotGivenOr[Sequence[dict[str, Any]]] = NOT_GIVEN,
        file_url: NotGivenOr[str] = NOT_GIVEN,
        mapping: NotGivenOr[dict[str, str]] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ContactImportResult:
        """Commit a previewed import.

        Args:
            token: The ``token`` returned by :meth:`import_preview`.
            contacts: Inline contact rows to import (when not using a token).
            file_url: A reference to a previously uploaded file to import.
            mapping: A column-to-field mapping applied to the source rows.
            campaign_id: The campaign to import the contacts into.
            options: Per-request overrides.
        """
        body = drop_not_given(
            {
                "token": token,
                "contacts": contacts,
                "file_url": file_url,
                "mapping": mapping,
                "campaign_id": campaign_id,
            }
        )
        return await self._post(
            "/contacts/import/commit",
            cast_to=ContactImportResult,
            body=body,
            options=options,
        )

    async def lookup(
        self, *, email: str, options: RequestOptions | None = None
    ) -> Contact:
        """Look up a single contact by email address.

        Args:
            email: The email address to look up.
            options: Per-request overrides.
        """
        return await self._get(
            "/contacts/lookup",
            cast_to=Contact,
            query={"email": email},
            options=options,
        )

    async def retrieve(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> Contact:
        """Retrieve a single contact by id."""
        return await self._get(
            f"/contacts/{contact_id}", cast_to=Contact, options=options
        )

    async def update(
        self,
        contact_id: str,
        *,
        email: NotGivenOr[str] = NOT_GIVEN,
        first_name: NotGivenOr[str] = NOT_GIVEN,
        last_name: NotGivenOr[str] = NOT_GIVEN,
        company: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Contact:
        """Update a single contact's fields.

        Args:
            contact_id: The id of the contact to update.
            email: A new email address.
            first_name: A new first name.
            last_name: A new last name.
            company: A new company.
            status: A new status.
            campaign_id: Reassign the contact to a campaign.
            options: Per-request overrides.
        """
        body = drop_not_given(
            {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "company": company,
                "status": status,
                "campaign_id": campaign_id,
            }
        )
        return await self._patch(
            f"/contacts/{contact_id}", cast_to=Contact, body=body, options=options
        )

    async def delete(
        self, contact_id: str, *, options: RequestOptions | None = None
    ) -> ContactDeleted:
        """Delete a single contact by id."""
        return await self._delete(
            f"/contacts/{contact_id}", cast_to=ContactDeleted, options=options
        )

    def emails(
        self,
        contact_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[ContactEmail]:
        """List emails exchanged with a contact (auto-paginating)."""
        return self._get_api_list(
            f"/contacts/{contact_id}/emails",
            model=ContactEmail,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def timeline(
        self,
        contact_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[ContactTimelineEntry]:
        """List a contact's timeline entries (auto-paginating)."""
        return self._get_api_list(
            f"/contacts/{contact_id}/timeline",
            model=ContactTimelineEntry,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def list_notes(
        self,
        contact_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[ContactNote]:
        """List a contact's notes (auto-paginating)."""
        return self._get_api_list(
            f"/contacts/{contact_id}/notes",
            model=ContactNote,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def create_note(
        self,
        contact_id: str,
        *,
        body: str,
        options: RequestOptions | None = None,
    ) -> ContactNote:
        """Add a note to a contact.

        Args:
            contact_id: The id of the contact to annotate.
            body: The note text.
            options: Per-request overrides.
        """
        return await self._post(
            f"/contacts/{contact_id}/notes",
            cast_to=ContactNote,
            body={"body": body},
            options=options,
        )

    async def update_note(
        self,
        contact_id: str,
        note_id: str,
        *,
        body: str,
        options: RequestOptions | None = None,
    ) -> ContactNote:
        """Edit an existing note on a contact.

        Args:
            contact_id: The id of the contact that owns the note.
            note_id: The id of the note to edit.
            body: The replacement note text.
            options: Per-request overrides.
        """
        return await self._patch(
            f"/contacts/{contact_id}/notes/{note_id}",
            cast_to=ContactNote,
            body={"body": body},
            options=options,
        )

    async def delete_note(
        self,
        contact_id: str,
        note_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> ContactNoteDeleted:
        """Delete a note from a contact."""
        return await self._delete(
            f"/contacts/{contact_id}/notes/{note_id}",
            cast_to=ContactNoteDeleted,
            options=options,
        )

    def activities(
        self,
        contact_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[ContactActivity]:
        """List a contact's activity records (auto-paginating)."""
        return self._get_api_list(
            f"/contacts/{contact_id}/activities",
            model=ContactActivity,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def deals(
        self,
        contact_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[ContactDeal]:
        """List the CRM deals linked to a contact (auto-paginating)."""
        return self._get_api_list(
            f"/contacts/{contact_id}/deals",
            model=ContactDeal,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )
