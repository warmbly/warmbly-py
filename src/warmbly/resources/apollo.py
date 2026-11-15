"""The ``apollo`` resource: the Apollo.io list import and contact enrichment.

Maps to ``/v1/integrations/apollo/{connection_id}/...``. ``connection_id`` is
the id of an Apollo connection (see
:meth:`warmbly.resources.integrations.Integrations.list_connections`).
Enrichment writes contacts and spends the workspace's Apollo credits.

Every call needs an API key with the ``INTEGRATIONS`` permission; starting an
enrichment also needs ``BULK_CONTACTS`` and a paid plan. The Apollo key itself
is write-only: it is never returned.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGiven, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "Apollo",
    "ApolloEnrichmentRun",
    "ApolloImportPreview",
    "ApolloImportSource",
    "ApolloImportSourceDeleted",
    "ApolloList",
    "ApolloOverview",
    "ApolloRunResult",
    "AsyncApollo",
]


class ApolloOverview(BaseModel):
    """The Apollo page header for one connection.

    ``health`` is the connection's current health; ``sources`` is how many
    saved list imports it has and ``total_imported`` how many contacts they
    brought in.
    """

    connection_id: str | None = None
    label: str | None = None
    status: str | None = None
    health: str | None = None
    health_detail: str | None = None
    account_name: str | None = None
    account_email: str | None = None
    sources: int | None = None
    total_imported: int | None = None
    last_run_at: str | None = None


class ApolloList(BaseModel):
    """A saved contact list in the Apollo account."""

    id: str
    name: str | None = None
    count: int | None = None


class ApolloImportPreview(BaseModel):
    """The first people of an Apollo list and how many it holds.

    Each ``sample`` row has ``apollo_id``, ``name``, ``email``,
    ``email_status``, ``title``, ``company``, ``already_in_warmbly`` and
    ``will_import``.
    """

    total: int | None = None
    sample: Sequence[dict[str, Any]] = []


class ApolloRunResult(BaseModel):
    """What one import run did.

    ``next_page`` is where the next run resumes when ``truncated`` is set.
    """

    read: int | None = None
    imported: int | None = None
    updated: int | None = None
    skipped: int | None = None
    failed: int | None = None
    no_email: int | None = None
    unverified: int | None = None
    suppressed: int | None = None
    truncated: bool | None = None
    already_seen: int | None = None
    next_page: int | None = None


class ApolloImportSource(BaseModel):
    """A saved Apollo list import."""

    id: str
    organization_id: str | None = None
    connection_id: str | None = None
    created_by_user_id: str | None = None
    name: str | None = None
    list_id: str | None = None
    list_name: str | None = None
    campaign_id: str | None = None
    category_ids: Sequence[str] = []
    verified_only: bool | None = None
    recurring: bool | None = None
    enabled: bool | None = None
    status: str | None = None
    last_run_at: str | None = None
    last_result: ApolloRunResult | None = None
    last_error: str | None = None
    total_imported: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ApolloImportSourceDeleted(BaseModel):
    """The result of removing an import source (``204 No Content``).

    Contacts it brought in stay.
    """

    id: str | None = None
    deleted: bool | None = None


class ApolloEnrichmentRun(BaseModel):
    """A contact enrichment run and its progress.

    ``status`` is ``queued``, ``running``, ``done`` or ``error``;
    ``credits_consumed`` is what it spent on the Apollo account.
    """

    id: str
    organization_id: str | None = None
    connection_id: str | None = None
    requested_by_user_id: str | None = None
    overwrite: bool | None = None
    status: str | None = None
    total: int | None = None
    processed: int | None = None
    enriched: int | None = None
    not_found: int | None = None
    failed: int | None = None
    credits_consumed: int | None = None
    last_error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


def _source_body(
    *,
    name: NotGivenOr[str],
    list_id: NotGivenOr[str],
    list_name: NotGivenOr[str],
    campaign_id: NotGivenOr[str | None],
    category_ids: NotGivenOr[Sequence[str]],
    verified_only: NotGivenOr[bool],
    recurring: NotGivenOr[bool],
    enabled: NotGivenOr[bool],
) -> dict[str, Any]:
    """Build the body shared by creating and editing an import source."""
    return drop_not_given(
        {
            "name": name,
            "list_id": list_id,
            "list_name": list_name,
            "campaign_id": campaign_id,
            "category_ids": (
                NOT_GIVEN if isinstance(category_ids, NotGiven) else list(category_ids)
            ),
            "verified_only": verified_only,
            "recurring": recurring,
            "enabled": enabled,
        }
    )


class Apollo(SyncAPIResource):
    """Synchronous ``apollo`` resource."""

    def _path(self, connection_id: str, tail: str = "") -> str:
        return f"/integrations/apollo/{connection_id}{tail}"

    def overview(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> ApolloOverview:
        """Read the Apollo page header: account, health and import totals."""
        return self._get(
            self._path(connection_id), cast_to=ApolloOverview, options=options
        )

    def replace_key(
        self,
        connection_id: str,
        *,
        api_key: str,
        options: RequestOptions | None = None,
    ) -> ApolloOverview:
        """Check a new Apollo API key and swap it in.

        A ``PUT``, so a retry converges on the same key. The key is write-only
        and is never returned. A key Apollo rejects is refused with ``422``.

        Args:
            connection_id: The Apollo connection.
            api_key: The new Apollo API key.
        """
        return self._put(
            self._path(connection_id, "/key"),
            cast_to=ApolloOverview,
            body={"api_key": api_key},
            options=options,
        )

    def lists(
        self,
        connection_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[ApolloList]:
        """List the account's saved contact lists (returned in full)."""
        return self._get_api_list(
            self._path(connection_id, "/lists"),
            model=ApolloList,
            options=options,
        )

    def preview_import(
        self,
        connection_id: str,
        *,
        list_id: str,
        verified_only: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApolloImportPreview:
        """Read the first people of a list. Writes nothing.

        Args:
            connection_id: The Apollo connection.
            list_id: The Apollo list.
            verified_only: Skip people whose address Apollo has not verified
                (the server default is ``True``).
        """
        return self._post(
            self._path(connection_id, "/import/preview"),
            cast_to=ApolloImportPreview,
            body=drop_not_given({"list_id": list_id, "verified_only": verified_only}),
            options=options,
        )

    def list_import_sources(
        self,
        connection_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[ApolloImportSource]:
        """List a connection's saved list imports (returned in full)."""
        return self._get_api_list(
            self._path(connection_id, "/import-sources"),
            model=ApolloImportSource,
            options=options,
        )

    def create_import_source(
        self,
        connection_id: str,
        *,
        list_id: str,
        list_name: NotGivenOr[str] = NOT_GIVEN,
        name: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str | None] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        verified_only: NotGivenOr[bool] = NOT_GIVEN,
        recurring: NotGivenOr[bool] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApolloImportSource:
        """Save a list import and start its first run.

        People are deduplicated by address, so a retried create makes a second
        source whose run imports nothing new.

        Args:
            connection_id: The Apollo connection.
            list_id: The Apollo list.
            list_name: The list's display name.
            name: A display name for the import.
            campaign_id: A Warmbly campaign the imported contacts join.
            category_ids: Categories to assign.
            verified_only: Skip unverified addresses.
            recurring: Keep re-reading the list.
            enabled: Whether a recurring source runs.
        """
        return self._post(
            self._path(connection_id, "/import-sources"),
            cast_to=ApolloImportSource,
            body=_source_body(
                name=name,
                list_id=list_id,
                list_name=list_name,
                campaign_id=campaign_id,
                category_ids=category_ids,
                verified_only=verified_only,
                recurring=recurring,
                enabled=enabled,
            ),
            options=options,
        )

    def update_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str | None] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        verified_only: NotGivenOr[bool] = NOT_GIVEN,
        recurring: NotGivenOr[bool] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApolloImportSource:
        """Edit a list import's targets, filter and schedule.

        Args:
            connection_id: The Apollo connection.
            source_id: The import source.
            campaign_id: A Warmbly campaign id; ``None`` clears the target and
                leaving it out keeps it.
        """
        return self._patch(
            self._path(connection_id, f"/import-sources/{source_id}"),
            cast_to=ApolloImportSource,
            body=_source_body(
                name=name,
                list_id=NOT_GIVEN,
                list_name=NOT_GIVEN,
                campaign_id=campaign_id,
                category_ids=category_ids,
                verified_only=verified_only,
                recurring=recurring,
                enabled=enabled,
            ),
            options=options,
        )

    def run_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> ApolloImportSource:
        """Run a list import now. A run already in progress answers ``409``."""
        return self._post(
            self._path(connection_id, f"/import-sources/{source_id}/run"),
            cast_to=ApolloImportSource,
            options=options,
        )

    def delete_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> ApolloImportSourceDeleted:
        """Remove a list import. The contacts it brought in stay."""
        return self._delete(
            self._path(connection_id, f"/import-sources/{source_id}"),
            cast_to=ApolloImportSourceDeleted,
            options=options,
        )

    def list_enrichments(
        self,
        connection_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[ApolloEnrichmentRun]:
        """List a connection's recent enrichment runs.

        Args:
            connection_id: The Apollo connection.
            limit: How many runs, 1 to 100 (default 20). Not paginated.
        """
        return self._get_api_list(
            self._path(connection_id, "/enrichments"),
            model=ApolloEnrichmentRun,
            query={"limit": limit},
            options=options,
        )

    def start_enrichment(
        self,
        connection_id: str,
        *,
        contact_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        overwrite: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApolloEnrichmentRun:
        """Queue an enrichment run over a contact selection (``202``).

        Spends Apollo credits and writes contacts. At most 5000 contacts per
        run. Name the contacts by id, or by a search with *select_all*. The
        request carries an ``Idempotency-Key``; without a stable one (pass
        ``options={"idempotency_key": ...}``) a retry queues a second run,
        which only rewrites the same fields again.

        Poll :meth:`retrieve_enrichment` until ``status`` is ``done`` or
        ``error``.

        Args:
            connection_id: The Apollo connection.
            contact_ids: The contact ids to enrich.
            select_all: Switch the selection from *contact_ids* to *filters*.
            filters: The same body ``contacts.search`` takes.
            exclude: Contact ids to drop from a select-all.
            overwrite: Replace fields that already hold a value.
        """
        return self._post(
            self._path(connection_id, "/enrichments"),
            cast_to=ApolloEnrichmentRun,
            body=drop_not_given(
                {
                    "contact_ids": (
                        NOT_GIVEN
                        if isinstance(contact_ids, NotGiven)
                        else list(contact_ids)
                    ),
                    "all": select_all,
                    "filters": filters,
                    "exclude": (
                        NOT_GIVEN if isinstance(exclude, NotGiven) else list(exclude)
                    ),
                    "overwrite": overwrite,
                }
            ),
            options=options,
        )

    def retrieve_enrichment(
        self,
        connection_id: str,
        run_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> ApolloEnrichmentRun:
        """Read one enrichment run's progress."""
        return self._get(
            self._path(connection_id, f"/enrichments/{run_id}"),
            cast_to=ApolloEnrichmentRun,
            options=options,
        )


class AsyncApollo(AsyncAPIResource):
    """Asynchronous ``apollo`` resource."""

    def _path(self, connection_id: str, tail: str = "") -> str:
        return f"/integrations/apollo/{connection_id}{tail}"

    async def overview(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> ApolloOverview:
        """Read the Apollo page header: account, health and import totals."""
        return await self._get(
            self._path(connection_id), cast_to=ApolloOverview, options=options
        )

    async def replace_key(
        self,
        connection_id: str,
        *,
        api_key: str,
        options: RequestOptions | None = None,
    ) -> ApolloOverview:
        """Check a new Apollo API key and swap it in.

        A ``PUT``, so a retry converges on the same key. The key is write-only
        and is never returned. A key Apollo rejects is refused with ``422``.

        Args:
            connection_id: The Apollo connection.
            api_key: The new Apollo API key.
        """
        return await self._put(
            self._path(connection_id, "/key"),
            cast_to=ApolloOverview,
            body={"api_key": api_key},
            options=options,
        )

    def lists(
        self,
        connection_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[ApolloList]:
        """List the account's saved contact lists (returned in full)."""
        return self._get_api_list(
            self._path(connection_id, "/lists"),
            model=ApolloList,
            options=options,
        )

    async def preview_import(
        self,
        connection_id: str,
        *,
        list_id: str,
        verified_only: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApolloImportPreview:
        """Read the first people of a list. Writes nothing.

        Args:
            connection_id: The Apollo connection.
            list_id: The Apollo list.
            verified_only: Skip people whose address Apollo has not verified
                (the server default is ``True``).
        """
        return await self._post(
            self._path(connection_id, "/import/preview"),
            cast_to=ApolloImportPreview,
            body=drop_not_given({"list_id": list_id, "verified_only": verified_only}),
            options=options,
        )

    def list_import_sources(
        self,
        connection_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[ApolloImportSource]:
        """List a connection's saved list imports (returned in full)."""
        return self._get_api_list(
            self._path(connection_id, "/import-sources"),
            model=ApolloImportSource,
            options=options,
        )

    async def create_import_source(
        self,
        connection_id: str,
        *,
        list_id: str,
        list_name: NotGivenOr[str] = NOT_GIVEN,
        name: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str | None] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        verified_only: NotGivenOr[bool] = NOT_GIVEN,
        recurring: NotGivenOr[bool] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApolloImportSource:
        """Save a list import and start its first run.

        People are deduplicated by address, so a retried create makes a second
        source whose run imports nothing new.

        Args:
            connection_id: The Apollo connection.
            list_id: The Apollo list.
            list_name: The list's display name.
            name: A display name for the import.
            campaign_id: A Warmbly campaign the imported contacts join.
            category_ids: Categories to assign.
            verified_only: Skip unverified addresses.
            recurring: Keep re-reading the list.
            enabled: Whether a recurring source runs.
        """
        return await self._post(
            self._path(connection_id, "/import-sources"),
            cast_to=ApolloImportSource,
            body=_source_body(
                name=name,
                list_id=list_id,
                list_name=list_name,
                campaign_id=campaign_id,
                category_ids=category_ids,
                verified_only=verified_only,
                recurring=recurring,
                enabled=enabled,
            ),
            options=options,
        )

    async def update_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str | None] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        verified_only: NotGivenOr[bool] = NOT_GIVEN,
        recurring: NotGivenOr[bool] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApolloImportSource:
        """Edit a list import's targets, filter and schedule.

        Args:
            connection_id: The Apollo connection.
            source_id: The import source.
            campaign_id: A Warmbly campaign id; ``None`` clears the target and
                leaving it out keeps it.
        """
        return await self._patch(
            self._path(connection_id, f"/import-sources/{source_id}"),
            cast_to=ApolloImportSource,
            body=_source_body(
                name=name,
                list_id=NOT_GIVEN,
                list_name=NOT_GIVEN,
                campaign_id=campaign_id,
                category_ids=category_ids,
                verified_only=verified_only,
                recurring=recurring,
                enabled=enabled,
            ),
            options=options,
        )

    async def run_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> ApolloImportSource:
        """Run a list import now. A run already in progress answers ``409``."""
        return await self._post(
            self._path(connection_id, f"/import-sources/{source_id}/run"),
            cast_to=ApolloImportSource,
            options=options,
        )

    async def delete_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> ApolloImportSourceDeleted:
        """Remove a list import. The contacts it brought in stay."""
        return await self._delete(
            self._path(connection_id, f"/import-sources/{source_id}"),
            cast_to=ApolloImportSourceDeleted,
            options=options,
        )

    def list_enrichments(
        self,
        connection_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[ApolloEnrichmentRun]:
        """List a connection's recent enrichment runs.

        Args:
            connection_id: The Apollo connection.
            limit: How many runs, 1 to 100 (default 20). Not paginated.
        """
        return self._get_api_list(
            self._path(connection_id, "/enrichments"),
            model=ApolloEnrichmentRun,
            query={"limit": limit},
            options=options,
        )

    async def start_enrichment(
        self,
        connection_id: str,
        *,
        contact_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        select_all: NotGivenOr[bool] = NOT_GIVEN,
        filters: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        exclude: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        overwrite: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ApolloEnrichmentRun:
        """Queue an enrichment run over a contact selection (``202``).

        Spends Apollo credits and writes contacts. At most 5000 contacts per
        run. Name the contacts by id, or by a search with *select_all*. The
        request carries an ``Idempotency-Key``; without a stable one (pass
        ``options={"idempotency_key": ...}``) a retry queues a second run,
        which only rewrites the same fields again.

        Poll :meth:`retrieve_enrichment` until ``status`` is ``done`` or
        ``error``.

        Args:
            connection_id: The Apollo connection.
            contact_ids: The contact ids to enrich.
            select_all: Switch the selection from *contact_ids* to *filters*.
            filters: The same body ``contacts.search`` takes.
            exclude: Contact ids to drop from a select-all.
            overwrite: Replace fields that already hold a value.
        """
        return await self._post(
            self._path(connection_id, "/enrichments"),
            cast_to=ApolloEnrichmentRun,
            body=drop_not_given(
                {
                    "contact_ids": (
                        NOT_GIVEN
                        if isinstance(contact_ids, NotGiven)
                        else list(contact_ids)
                    ),
                    "all": select_all,
                    "filters": filters,
                    "exclude": (
                        NOT_GIVEN if isinstance(exclude, NotGiven) else list(exclude)
                    ),
                    "overwrite": overwrite,
                }
            ),
            options=options,
        )

    async def retrieve_enrichment(
        self,
        connection_id: str,
        run_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> ApolloEnrichmentRun:
        """Read one enrichment run's progress."""
        return await self._get(
            self._path(connection_id, f"/enrichments/{run_id}"),
            cast_to=ApolloEnrichmentRun,
            options=options,
        )
