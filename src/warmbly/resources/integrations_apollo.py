"""The ``integrations.apollo`` resource: Apollo list imports and enrichment.

Maps to ``/v1/integrations/apollo/:id``, where ``:id`` is the id of an Apollo
*connection* (see :meth:`warmbly.resources.integrations.Integrations.create_connection`;
Apollo connects with an API key).

Every route needs the ``integrations`` API permission. Starting an enrichment
run also needs ``bulk_contacts``, because it writes contacts and spends the
workspace's Apollo credits.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions, is_given
from .._utils import drop_not_given
from .integrations import IntegrationAck

__all__ = [
    "Apollo",
    "ApolloEnrichmentRun",
    "ApolloImportPreview",
    "ApolloImportSource",
    "ApolloList",
    "ApolloOverview",
    "AsyncApollo",
]


class ApolloOverview(BaseModel):
    """The Apollo page header: the account a key acts as and what the connection did."""

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
    """A saved Apollo list of contacts, as the import picker shows it."""

    id: str
    name: str | None = None
    count: int | None = None


class ApolloImportPreview(BaseModel):
    """The first people of a list, and how many it holds.

    ``sample`` rows have ``apollo_id``, ``name``, ``email``, ``email_status``,
    ``title``, ``company``, ``already_in_warmbly`` and ``will_import``.
    """

    total: int | None = None
    sample: Sequence[dict[str, Any]] = []


class ApolloImportSource(BaseModel):
    """A saved Apollo list that feeds contacts into Warmbly.

    ``last_result`` reports one run (``read``, ``imported``, ``updated``,
    ``skipped``, ``failed``, ``no_email``, ``unverified``, ``suppressed``,
    ``already_seen``, ``truncated``, ``next_page``).
    """

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
    last_result: dict[str, Any] | None = None
    last_error: str | None = None
    total_imported: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ApolloEnrichmentRun(BaseModel):
    """One background request to enrich Warmbly contacts through Apollo.

    ``status`` is ``queued``, ``running``, ``done``, or ``error``.
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


def _source_body(**fields: Any) -> dict[str, Any]:
    return drop_not_given(
        {k: (list(v) if isinstance(v, (list, tuple)) else v) for k, v in fields.items()}
    )


class Apollo(SyncAPIResource):
    """Synchronous ``integrations.apollo`` resource."""

    def overview(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> ApolloOverview:
        """Retrieve the Apollo page header for a connection."""
        return self._get(
            f"/integrations/apollo/{connection_id}",
            cast_to=ApolloOverview,
            options=options,
        )

    def replace_key(
        self,
        connection_id: str,
        *,
        api_key: str,
        options: RequestOptions | None = None,
    ) -> ApolloOverview:
        """Check a new Apollo API key and swap it in.

        This is a PUT, so a retry converges on the same key.
        """
        return self._put(
            f"/integrations/apollo/{connection_id}/key",
            cast_to=ApolloOverview,
            body={"api_key": api_key},
            options=options,
        )

    def list_lists(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[ApolloList]:
        """List the account's saved contact lists."""
        return self._get_api_list(
            f"/integrations/apollo/{connection_id}/lists",
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
        """Read the first people of a list without importing.

        Args:
            connection_id: The Apollo connection.
            list_id: The Apollo list id.
            verified_only: Only count people with a verified email (the
                default on the server).
        """
        return self._post(
            f"/integrations/apollo/{connection_id}/import/preview",
            cast_to=ApolloImportPreview,
            body=drop_not_given({"list_id": list_id, "verified_only": verified_only}),
            options=options,
        )

    def list_import_sources(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[ApolloImportSource]:
        """List a connection's saved list imports."""
        return self._get_api_list(
            f"/integrations/apollo/{connection_id}/import-sources",
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
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
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
            list_id: The Apollo list id.
            list_name: The list's display name.
            name: A name for the saved import.
            campaign_id: A Warmbly campaign to enrol imported contacts into.
            category_ids: Categories to apply to imported contacts.
            verified_only: Only import people with a verified email.
            recurring: Re-run the import on a schedule.
            enabled: Whether the import is active.
        """
        return self._post(
            f"/integrations/apollo/{connection_id}/import-sources",
            cast_to=ApolloImportSource,
            body=_source_body(
                list_id=list_id,
                list_name=list_name,
                name=name,
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
            source_id: The saved import's id.
            name: A new name.
            campaign_id: A Warmbly campaign to enrol into; pass ``None`` to
                clear the target, omit it to leave it.
            category_ids: Categories to apply to imported contacts.
            verified_only: Only import people with a verified email.
            recurring: Re-run the import on a schedule.
            enabled: Whether the import is active.
        """
        return self._patch(
            f"/integrations/apollo/{connection_id}/import-sources/{source_id}",
            cast_to=ApolloImportSource,
            body=_source_body(
                name=name,
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
        """Run a saved list import now.

        A second request while one runs is refused with a conflict, so retries
        cannot double-run it.
        """
        return self._post(
            f"/integrations/apollo/{connection_id}/import-sources/{source_id}/run",
            cast_to=ApolloImportSource,
            options=options,
        )

    def delete_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> IntegrationAck:
        """Remove a saved list import. Contacts it brought in stay."""
        return self._delete(
            f"/integrations/apollo/{connection_id}/import-sources/{source_id}",
            cast_to=IntegrationAck,
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
            limit: How many runs, 1 to 100 (default 20).
        """
        return self._get_api_list(
            f"/integrations/apollo/{connection_id}/enrichments",
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
        """Queue an enrichment run over a contact selection.

        Needs the ``integrations`` and ``bulk_contacts`` permissions. A run
        enriches at most 5000 contacts and spends Apollo credits. A retry with
        the same idempotency key does not queue a second run.

        Args:
            connection_id: The Apollo connection.
            contact_ids: The contacts to enrich.
            select_all: Enrich every contact matching *filters* instead of
                listing ids.
            filters: The contact search body that *select_all* resolves.
            exclude: Contact ids to drop from a *select_all* selection.
            overwrite: Replace fields that already hold a value.
        """
        return self._post(
            f"/integrations/apollo/{connection_id}/enrichments",
            cast_to=ApolloEnrichmentRun,
            body=drop_not_given(
                {
                    "contact_ids": list(contact_ids)
                    if is_given(contact_ids)
                    else contact_ids,
                    "all": select_all,
                    "filters": filters,
                    "exclude": list(exclude) if is_given(exclude) else exclude,
                    "overwrite": overwrite,
                }
            ),
            options=options,
        )

    def get_enrichment(
        self,
        connection_id: str,
        run_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> ApolloEnrichmentRun:
        """Retrieve one enrichment run's progress."""
        return self._get(
            f"/integrations/apollo/{connection_id}/enrichments/{run_id}",
            cast_to=ApolloEnrichmentRun,
            options=options,
        )


class AsyncApollo(AsyncAPIResource):
    """Asynchronous ``integrations.apollo`` resource."""

    async def overview(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> ApolloOverview:
        """Retrieve the Apollo page header for a connection."""
        return await self._get(
            f"/integrations/apollo/{connection_id}",
            cast_to=ApolloOverview,
            options=options,
        )

    async def replace_key(
        self,
        connection_id: str,
        *,
        api_key: str,
        options: RequestOptions | None = None,
    ) -> ApolloOverview:
        """Check a new Apollo API key and swap it in.

        This is a PUT, so a retry converges on the same key.
        """
        return await self._put(
            f"/integrations/apollo/{connection_id}/key",
            cast_to=ApolloOverview,
            body={"api_key": api_key},
            options=options,
        )

    def list_lists(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[ApolloList]:
        """List the account's saved contact lists."""
        return self._get_api_list(
            f"/integrations/apollo/{connection_id}/lists",
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
        """Read the first people of a list without importing.

        Args:
            connection_id: The Apollo connection.
            list_id: The Apollo list id.
            verified_only: Only count people with a verified email (the
                default on the server).
        """
        return await self._post(
            f"/integrations/apollo/{connection_id}/import/preview",
            cast_to=ApolloImportPreview,
            body=drop_not_given({"list_id": list_id, "verified_only": verified_only}),
            options=options,
        )

    def list_import_sources(
        self, connection_id: str, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[ApolloImportSource]:
        """List a connection's saved list imports."""
        return self._get_api_list(
            f"/integrations/apollo/{connection_id}/import-sources",
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
        campaign_id: NotGivenOr[str] = NOT_GIVEN,
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
            list_id: The Apollo list id.
            list_name: The list's display name.
            name: A name for the saved import.
            campaign_id: A Warmbly campaign to enrol imported contacts into.
            category_ids: Categories to apply to imported contacts.
            verified_only: Only import people with a verified email.
            recurring: Re-run the import on a schedule.
            enabled: Whether the import is active.
        """
        return await self._post(
            f"/integrations/apollo/{connection_id}/import-sources",
            cast_to=ApolloImportSource,
            body=_source_body(
                list_id=list_id,
                list_name=list_name,
                name=name,
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
            source_id: The saved import's id.
            name: A new name.
            campaign_id: A Warmbly campaign to enrol into; pass ``None`` to
                clear the target, omit it to leave it.
            category_ids: Categories to apply to imported contacts.
            verified_only: Only import people with a verified email.
            recurring: Re-run the import on a schedule.
            enabled: Whether the import is active.
        """
        return await self._patch(
            f"/integrations/apollo/{connection_id}/import-sources/{source_id}",
            cast_to=ApolloImportSource,
            body=_source_body(
                name=name,
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
        """Run a saved list import now.

        A second request while one runs is refused with a conflict, so retries
        cannot double-run it.
        """
        return await self._post(
            f"/integrations/apollo/{connection_id}/import-sources/{source_id}/run",
            cast_to=ApolloImportSource,
            options=options,
        )

    async def delete_import_source(
        self,
        connection_id: str,
        source_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> IntegrationAck:
        """Remove a saved list import. Contacts it brought in stay."""
        return await self._delete(
            f"/integrations/apollo/{connection_id}/import-sources/{source_id}",
            cast_to=IntegrationAck,
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
            limit: How many runs, 1 to 100 (default 20).
        """
        return self._get_api_list(
            f"/integrations/apollo/{connection_id}/enrichments",
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
        """Queue an enrichment run over a contact selection.

        Needs the ``integrations`` and ``bulk_contacts`` permissions. A run
        enriches at most 5000 contacts and spends Apollo credits. A retry with
        the same idempotency key does not queue a second run.

        Args:
            connection_id: The Apollo connection.
            contact_ids: The contacts to enrich.
            select_all: Enrich every contact matching *filters* instead of
                listing ids.
            filters: The contact search body that *select_all* resolves.
            exclude: Contact ids to drop from a *select_all* selection.
            overwrite: Replace fields that already hold a value.
        """
        return await self._post(
            f"/integrations/apollo/{connection_id}/enrichments",
            cast_to=ApolloEnrichmentRun,
            body=drop_not_given(
                {
                    "contact_ids": list(contact_ids)
                    if is_given(contact_ids)
                    else contact_ids,
                    "all": select_all,
                    "filters": filters,
                    "exclude": list(exclude) if is_given(exclude) else exclude,
                    "overwrite": overwrite,
                }
            ),
            options=options,
        )

    async def get_enrichment(
        self,
        connection_id: str,
        run_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> ApolloEnrichmentRun:
        """Retrieve one enrichment run's progress."""
        return await self._get(
            f"/integrations/apollo/{connection_id}/enrichments/{run_id}",
            cast_to=ApolloEnrichmentRun,
            options=options,
        )
