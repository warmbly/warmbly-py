"""The ``leads`` resource: the map-based lead finder.

Maps to the ``/v1/leads`` route group. A *lead* is a business found on a map:
a search over an ``area`` (a bounding box, a circle, or a polygon) against one
of the finder's sources stores what it finds, a background *enrichment* run
then reads each lead's website for addresses, socials and the people it names,
and the leads you want are turned into contacts.

Leads are prospect contacts, so the contact permissions gate this group:
``READ_CONTACTS`` for reads, ``WRITE_CONTACTS`` for searching and editing, and
``BULK_CONTACTS`` for the calls that act on a selection.

A *selection* names a set of leads: pass ``lead_ids`` (at most 5000), or
``all_=True`` together with a ``filter``. A ``filter`` is a mapping with any of
``search_id``, ``q``, ``statuses``, ``providers``, ``category``, ``tag``,
``has_email``, ``has_website``, ``has_phone``, ``has_socials``, ``has_people``,
``in_contacts``, ``enrichment``, ``min_rating``, ``min_reviews``,
``max_reviews``, ``min_score``, ``bounds`` and ``exclude_chains``.

Some calls spend workspace balance: a search through a source the instance pays
for (``charged_usd`` on the result), each website read of an enrichment run, and
an address lookup for a person. ``search`` and ``enrich`` carry an idempotency
key like every other side-effectful call, so a retry replays the first answer.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

from .._models import BaseModel, construct_type
from .._pagination import AsyncCursorPage, AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, Omit, RequestOptions, is_given
from .._utils import drop_not_given

__all__ = [
    "AsyncLeads",
    "Lead",
    "LeadArea",
    "LeadBounds",
    "LeadCategory",
    "LeadEmail",
    "LeadEnrichmentRun",
    "LeadExportColumn",
    "LeadFacet",
    "LeadFacets",
    "LeadFinderConfig",
    "LeadGeocodeResult",
    "LeadLatLng",
    "LeadMapConfig",
    "LeadPerson",
    "LeadPersonColumn",
    "LeadPersonDeleted",
    "LeadPoint",
    "LeadPoints",
    "LeadProviderInfo",
    "LeadSearch",
    "LeadSearchDeleted",
    "LeadSearchResult",
    "LeadSite",
    "Leads",
    "LeadsAddedToContacts",
    "LeadsDeleted",
    "LeadsUpdated",
]


class LeadLatLng(BaseModel):
    """One point on the map."""

    lat: float | None = None
    lng: float | None = None


class LeadBounds(BaseModel):
    """A south-west to north-east rectangle."""

    south: float | None = None
    west: float | None = None
    north: float | None = None
    east: float | None = None


class LeadArea(BaseModel):
    """The part of the map a search covers.

    ``kind`` is ``bbox``, ``circle`` or ``polygon``. ``bounds`` is always set:
    for a circle or polygon it is the shape's bounding box. ``center`` and
    ``radius_m`` describe a circle, ``polygon`` the points of a polygon.
    """

    kind: str | None = None
    bounds: LeadBounds | None = None
    center: LeadLatLng | None = None
    radius_m: float | None = None
    polygon: Sequence[LeadLatLng] = []


class LeadEmail(BaseModel):
    """One address found for a lead and what checking it said.

    ``source`` is ``"website"`` when read off the business's own site, else the
    provider that listed it.
    """

    email: str | None = None
    source: str | None = None
    url: str | None = None
    domain_match: bool | None = None
    status: str | None = None
    sub_status: str | None = None


class LeadSite(BaseModel):
    """What reading a lead's website found besides addresses.

    ``email_pattern`` is how the domain builds a person's address
    (``"first.last"``). ``accepts_all`` is set when the domain's mail server
    accepts any address, so a guessed address cannot be confirmed.
    ``found_website`` is set when the listing had no website and the finder
    confirmed one worked out from the business's name.
    """

    reachable: bool | None = None
    final_url: str | None = None
    https: bool | None = None
    title: str | None = None
    description: str | None = None
    platform: str | None = None
    signals: Sequence[str] = []
    phones: Sequence[str] = []
    pages: int | None = None
    email_pattern: str | None = None
    accepts_all: bool | None = None
    found_website: bool | None = None
    error: str | None = None
    checked_at: str | None = None


class LeadPerson(BaseModel):
    """One person who works at a lead's business.

    ``seniority`` is ``owner``, ``executive``, ``manager`` or ``staff``.
    ``email_source`` is ``website``, ``pattern`` or ``manual`` (empty when there
    is no address), and ``email_status`` is ``guessed`` for a pattern-built
    address nothing could confirm. ``source`` is where the person was found:
    ``schema``, ``page``, ``imprint``, ``email``, ``linkedin`` or ``manual``.
    """

    id: str
    lead_id: str | None = None
    name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    title: str | None = None
    seniority: str | None = None
    email: str | None = None
    email_source: str | None = None
    email_status: str | None = None
    email_confidence: int | None = None
    linkedin_url: str | None = None
    phone: str | None = None
    source: str | None = None
    source_url: str | None = None
    contact_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class Lead(BaseModel):
    """One business in a workspace's lead finder.

    ``provider`` is ``osm``, ``google_places``, ``foursquare`` or
    ``outscraper``. ``status`` is ``new``, ``saved``, ``contacted`` or
    ``dismissed``; ``enrichment_status`` is ``none``, ``queued``, ``done``,
    ``no_website`` or ``failed``. ``contact_id`` is set once the lead has been
    added to contacts. ``people`` is loaded only where one lead is read in
    full (:meth:`Leads.retrieve`); elsewhere ``people_count`` says how many.
    """

    id: str
    provider: str | None = None
    external_id: str | None = None
    name: str | None = None
    category: str | None = None
    categories: Sequence[str] = []
    address: str | None = None
    street: str | None = None
    city: str | None = None
    region: str | None = None
    postcode: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    phone: str | None = None
    website: str | None = None
    domain: str | None = None
    email: str | None = None
    emails: Sequence[LeadEmail] = []
    socials: dict[str, str] = {}
    rating: float | None = None
    review_count: int | None = None
    price_level: int | None = None
    hours: Sequence[str] = []
    business_status: str | None = None
    maps_url: str | None = None
    description: str | None = None
    chain: str | None = None
    site: LeadSite | None = None
    score: int | None = None
    status: str | None = None
    enrichment_status: str | None = None
    enriched_at: str | None = None
    contact_id: str | None = None
    tags: Sequence[str] = []
    notes: str | None = None
    people_count: int | None = None
    people: Sequence[LeadPerson] = []
    first_seen_at: str | None = None
    last_seen_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class LeadSearch(BaseModel):
    """One search someone ran on the lead finder map.

    ``has_more`` says the source has another page; pass ``search_id`` to
    :meth:`Leads.search` to fetch it. ``saved`` searches are kept in the
    saved list, the rest are recents.
    """

    id: str
    created_by_user_id: str | None = None
    name: str | None = None
    provider: str | None = None
    query: str | None = None
    category: str | None = None
    location_label: str | None = None
    area: LeadArea | None = None
    saved: bool | None = None
    result_count: int | None = None
    pages_fetched: int | None = None
    has_more: bool | None = None
    last_run_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class LeadSearchResult(BaseModel):
    """One page of a search.

    ``found`` is how many leads the page returned, ``outside_area`` how many of
    those fell outside the searched area, and ``charged_usd`` what the page
    cost the workspace (``0`` when nothing is charged).
    """

    search: LeadSearch | None = None
    leads: Sequence[Lead] = []
    found: int | None = None
    outside_area: int | None = None
    charged_usd: float | None = None


class LeadEnrichmentRun(BaseModel):
    """One background pass reading leads' websites.

    ``status`` is the run's lifecycle state; ``processed`` counts toward
    ``total``. ``charged_usd`` is what the run has cost so far, net of refunds.
    """

    id: str
    requested_by_user_id: str | None = None
    verify: bool | None = None
    people: bool | None = None
    status: str | None = None
    total: int | None = None
    processed: int | None = None
    emails_found: int | None = None
    people_found: int | None = None
    no_website: int | None = None
    failed: int | None = None
    charged_usd: float | None = None
    last_error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class LeadPoint(BaseModel):
    """One pin on the map."""

    id: str
    name: str | None = None
    category: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    status: str | None = None
    score: int | None = None
    has_email: bool | None = None
    has_website: bool | None = None
    has_phone: bool | None = None
    rating: float | None = None
    review_count: int | None = None
    in_contacts: bool | None = None


class LeadPoints(BaseModel):
    """The pins for the map. ``truncated`` is set when the cap (5000) was hit."""

    data: Sequence[LeadPoint] = []
    truncated: bool | None = None


class LeadFacet(BaseModel):
    """One value of a filterable field and how many leads carry it."""

    value: str | None = None
    count: int | None = None


class LeadFacets(BaseModel):
    """The values the filter panel offers for the current scope."""

    categories: Sequence[LeadFacet] = []
    tags: Sequence[LeadFacet] = []
    cities: Sequence[LeadFacet] = []


class LeadsUpdated(BaseModel):
    """How many leads a bulk edit changed."""

    updated: int | None = None


class LeadsDeleted(BaseModel):
    """How many leads a bulk delete removed."""

    deleted: int | None = None


class LeadsAddedToContacts(BaseModel):
    """What became of a selection added to contacts.

    ``selected`` is the selection size; the rest account for it: ``imported``
    new contacts, ``updated`` existing ones, and the ones left out
    (``skipped``, ``failed``, ``no_email``, ``unverified``, ``suppressed``).
    ``guessed`` and ``people`` count pattern-built addresses and people
    included. ``errors`` lists per-row failures, capped.
    """

    selected: int | None = None
    imported: int | None = None
    updated: int | None = None
    skipped: int | None = None
    failed: int | None = None
    no_email: int | None = None
    unverified: int | None = None
    suppressed: int | None = None
    guessed: int | None = None
    people: int | None = None
    errors: Sequence[dict[str, Any]] = []


class LeadGeocodeResult(BaseModel):
    """One place a location search matched."""

    label: str | None = None
    detail: str | None = None
    kind: str | None = None
    center: LeadLatLng | None = None
    bounds: LeadBounds | None = None


class LeadSearchDeleted(BaseModel):
    """The result of deleting a search (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class LeadPersonDeleted(BaseModel):
    """The result of removing a person from a lead (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class LeadProviderInfo(BaseModel):
    """A lead source and whether this workspace can search it.

    ``key_source`` is ``none``, ``workspace`` or ``instance``. ``cost_usd`` is
    the price of one result page (``0`` when nothing is charged).
    """

    id: str | None = None
    name: str | None = None
    description: str | None = None
    available: bool | None = None
    key_source: str | None = None
    needs_key: bool | None = None
    page_size: int | None = None
    max_pages: int | None = None
    cost_usd: float | None = None
    fields: Sequence[str] = []
    integration: str | None = None


class LeadCategory(BaseModel):
    """A business category the finder can search for."""

    id: str | None = None
    label: str | None = None
    group: str | None = None


class LeadExportColumn(BaseModel):
    """A column an export can include."""

    key: str | None = None
    label: str | None = None


class LeadPersonColumn(BaseModel):
    """A leading column of a one-row-per-person export."""

    key: str | None = None
    label: str | None = None


class LeadMapConfig(BaseModel):
    """The vector map style the dashboard draws."""

    style_light: str | None = None
    style_dark: str | None = None


class LeadFinderConfig(BaseModel):
    """The providers, categories, prices and map style of the finder."""

    providers: Sequence[LeadProviderInfo] = []
    categories: Sequence[LeadCategory] = []
    default_provider: str | None = None
    enrich_cost_usd: float | None = None
    person_email_cost_usd: float | None = None
    export_columns: Sequence[LeadExportColumn] = []
    person_columns: Sequence[LeadPersonColumn] = []
    default_export_columns: Sequence[str] = []
    map: LeadMapConfig | None = None


def _read(options: RequestOptions | None) -> RequestOptions:
    """Drop the idempotency key from a read that happens to be a ``POST``.

    ``query``, ``points``, ``facets`` and ``export`` only read, and a replayed
    answer would be stale, so no key is sent for them.
    """
    merged = cast(RequestOptions, dict(options or {}))
    headers: dict[str, Any] = dict(merged.get("headers") or {})
    headers["Idempotency-Key"] = Omit()
    merged["headers"] = headers
    return merged


def _selection(
    *,
    lead_ids: NotGivenOr[Sequence[str]],
    all_: NotGivenOr[bool],
    filter: NotGivenOr[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build the selection part shared by every bulk body."""
    return drop_not_given(
        {
            "lead_ids": list(lead_ids) if is_given(lead_ids) else NOT_GIVEN,
            "all": all_,
            "filter": filter,
        }
    )


def _patch_fields(
    *,
    status: NotGivenOr[str],
    notes: NotGivenOr[str],
    tags: NotGivenOr[Sequence[str]],
    add_tags: NotGivenOr[Sequence[str]],
    remove_tags: NotGivenOr[Sequence[str]],
) -> dict[str, Any]:
    """Build the editable part of a lead (omitted fields are left alone)."""
    return drop_not_given(
        {
            "status": status,
            "notes": notes,
            "tags": tags,
            "add_tags": add_tags,
            "remove_tags": remove_tags,
        }
    )


def _person_fields(
    *,
    name: NotGivenOr[str],
    first_name: NotGivenOr[str],
    last_name: NotGivenOr[str],
    title: NotGivenOr[str],
    email: NotGivenOr[str],
    linkedin_url: NotGivenOr[str],
    phone: NotGivenOr[str],
) -> dict[str, Any]:
    """Build a person body (create sends what is given, edit sends the diff)."""
    return drop_not_given(
        {
            "name": name,
            "first_name": first_name,
            "last_name": last_name,
            "title": title,
            "email": email,
            "linkedin_url": linkedin_url,
            "phone": phone,
        }
    )


def _query_body(
    *,
    filter: NotGivenOr[Mapping[str, Any]],
    sort: NotGivenOr[str],
    limit: NotGivenOr[int],
) -> dict[str, Any]:
    return drop_not_given({"filter": filter, "sort": sort, "limit": limit})


class Leads(SyncAPIResource):
    """Synchronous ``leads`` resource."""

    # -- finder setup ---------------------------------------------------------
    def config(self, *, options: RequestOptions | None = None) -> LeadFinderConfig:
        """List the providers, categories, prices and map style of the finder.

        Requires the ``READ_CONTACTS`` permission.
        """
        return self._get("/leads/config", cast_to=LeadFinderConfig, options=options)

    def geocode(
        self,
        *,
        q: str,
        lat: NotGivenOr[float] = NOT_GIVEN,
        lng: NotGivenOr[float] = NOT_GIVEN,
        lang: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[LeadGeocodeResult]:
        """Look up a typed location for the map (up to six matches).

        Requires the ``READ_CONTACTS`` permission.

        Args:
            q: The location text (at most 200 characters).
            lat: Bias results toward this latitude. Send with ``lng``.
            lng: Bias results toward this longitude. Send with ``lat``.
            lang: Result language: ``"en"``, ``"de"`` or ``"fr"``.
        """
        return self._get_api_list(
            "/leads/geocode",
            model=LeadGeocodeResult,
            query={"q": q, "lat": lat, "lng": lng, "lang": lang},
            options=options,
        )

    # -- searching ------------------------------------------------------------
    def search(
        self,
        *,
        provider: NotGivenOr[str] = NOT_GIVEN,
        area: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        query: NotGivenOr[str] = NOT_GIVEN,
        category: NotGivenOr[str] = NOT_GIVEN,
        location_label: NotGivenOr[str] = NOT_GIVEN,
        save: NotGivenOr[bool] = NOT_GIVEN,
        name: NotGivenOr[str] = NOT_GIVEN,
        language: NotGivenOr[str] = NOT_GIVEN,
        search_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadSearchResult:
        """Run one page of a source search and store what it finds.

        To fetch the next page of a search, send ``search_id`` alone. A search
        through a source the instance pays for charges the workspace balance
        (``charged_usd`` on the result). A retry with the same idempotency key
        replays the stored answer instead of searching, and charging, again.

        Requires the ``WRITE_CONTACTS`` permission.

        Args:
            provider: ``"osm"``, ``"google_places"``, ``"foursquare"`` or
                ``"outscraper"``.
            area: The part of the map to cover: ``{"kind": "bbox" | "circle" |
                "polygon", "bounds": {"south", "west", "north", "east"},
                "center": {"lat", "lng"}, "radius_m": ..., "polygon": [...]}``.
            query: Free-text search phrase.
            category: A category id from :meth:`config`.
            location_label: The label of the searched place, kept on the search.
            save: Keep the search in the saved list.
            name: A name for the saved search.
            language: Result language hint.
            search_id: An earlier search whose next page to fetch.
        """
        return self._post(
            "/leads/search",
            cast_to=LeadSearchResult,
            body=drop_not_given(
                {
                    "search_id": search_id,
                    "provider": provider,
                    "query": query,
                    "category": category,
                    "location_label": location_label,
                    "area": area,
                    "save": save,
                    "name": name,
                    "language": language,
                }
            ),
            options=options,
        )

    def list_searches(
        self,
        *,
        saved: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[LeadSearch]:
        """List recent searches, or only the saved ones.

        Requires the ``READ_CONTACTS`` permission.

        Args:
            saved: ``True`` for the saved searches only.
        """
        return self._get_api_list(
            "/leads/searches",
            model=LeadSearch,
            query={"saved": "true" if saved is True else NOT_GIVEN},
            options=options,
        )

    def update_search(
        self,
        search_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        saved: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadSearch:
        """Rename a search or move it in or out of the saved list.

        Requires the ``WRITE_CONTACTS`` permission.
        """
        return self._patch(
            f"/leads/searches/{search_id}",
            cast_to=LeadSearch,
            body=drop_not_given({"name": name, "saved": saved}),
            options=options,
        )

    def delete_search(
        self, search_id: str, *, options: RequestOptions | None = None
    ) -> LeadSearchDeleted:
        """Delete a search. The leads it found stay.

        Requires the ``WRITE_CONTACTS`` permission.
        """
        return self._delete(
            f"/leads/searches/{search_id}", cast_to=LeadSearchDeleted, options=options
        )

    # -- reading leads --------------------------------------------------------
    def query(
        self,
        *,
        filter: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        sort: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[Lead]:
        """List leads matching a filter, a page at a time (auto-paginating).

        A read that carries its filter in a ``POST`` body.

        Requires the ``READ_CONTACTS`` permission.

        Args:
            filter: The lead filter (see the module docs for its keys).
            sort: ``"recent"`` (default), ``"score"``, ``"rating"``,
                ``"reviews"`` or ``"name"``.
            limit: Page size, 1 to 200 (default 50).
            cursor: An opaque cursor from a previous page.
        """
        return self._query_page(
            _query_body(filter=filter, sort=sort, limit=limit),
            cursor if isinstance(cursor, str) else None,
            options,
        )

    def _query_page(
        self,
        body: dict[str, Any],
        cursor: str | None,
        options: RequestOptions | None,
    ) -> SyncCursorPage[Lead]:
        payload = dict(body)
        if cursor is not None:
            payload["cursor"] = cursor
        prepared = self._client._prepare(
            "POST", "/leads/query", json_body=payload, options=_read(options)
        )
        response = self._client._send(prepared)
        data, next_cursor, has_more, total, request_id = self._client._page_fields(
            response
        )
        return SyncCursorPage(
            data=[construct_type(Lead, item, request_id=request_id) for item in data],
            next_cursor=next_cursor,
            has_more=has_more,
            total=total,
            fetch_next=lambda c: self._query_page(body, c, options),
        )

    def points(
        self,
        *,
        filter: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadPoints:
        """Return the map pins for a filter (at most 5000; see ``truncated``).

        Requires the ``READ_CONTACTS`` permission.
        """
        return self._post(
            "/leads/points",
            cast_to=LeadPoints,
            body=drop_not_given({"filter": filter}),
            options=_read(options),
        )

    def facets(
        self,
        *,
        filter: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadFacets:
        """Return the category, tag and city values the filter panel offers.

        Requires the ``READ_CONTACTS`` permission.
        """
        return self._post(
            "/leads/facets",
            cast_to=LeadFacets,
            body=drop_not_given({"filter": filter}),
            options=_read(options),
        )

    def retrieve(self, lead_id: str, *, options: RequestOptions | None = None) -> Lead:
        """Retrieve one lead, with the ``people`` found at it.

        Requires the ``READ_CONTACTS`` permission.
        """
        return self._get(f"/leads/{lead_id}", cast_to=Lead, options=options)

    def export(
        self,
        *,
        format: NotGivenOr[str] = NOT_GIVEN,
        columns: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        rows: NotGivenOr[str] = NOT_GIVEN,
        lead_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        all_: NotGivenOr[bool] = NOT_GIVEN,
        filter: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> bytes:
        """Export the selected leads and return the encoded file bytes.

        Requires the ``READ_CONTACTS`` permission.

        Args:
            format: ``"csv"`` (default), ``"xlsx"`` or ``"json"``.
            columns: Column keys from :meth:`config` (``export_columns``);
                defaults to ``default_export_columns``.
            rows: ``"leads"`` (one row per business, default) or ``"people"``
                (one row per person).
            lead_ids: The leads to export (at most 5000).
            all_: Export every lead matching ``filter``.
            filter: The lead filter for an ``all_`` selection.

        Returns:
            The raw file. Write it to disk as-is; ``xlsx`` is binary.
        """
        return self._post(
            "/leads/export",
            cast_to=bytes,
            body={
                **_selection(lead_ids=lead_ids, all_=all_, filter=filter),
                **drop_not_given({"format": format, "columns": columns, "rows": rows}),
            },
            options=_read(options),
        )

    # -- editing leads --------------------------------------------------------
    def update(
        self,
        lead_id: str,
        *,
        status: NotGivenOr[str] = NOT_GIVEN,
        notes: NotGivenOr[str] = NOT_GIVEN,
        tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        add_tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        remove_tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Lead:
        """Edit one lead's status, notes or tags.

        Requires the ``WRITE_CONTACTS`` permission.

        Args:
            lead_id: The lead id.
            status: ``"new"``, ``"saved"``, ``"contacted"`` or ``"dismissed"``.
            notes: Replacement notes.
            tags: Replace the whole tag list.
            add_tags: Tags to add.
            remove_tags: Tags to remove.
        """
        return self._patch(
            f"/leads/{lead_id}",
            cast_to=Lead,
            body=_patch_fields(
                status=status,
                notes=notes,
                tags=tags,
                add_tags=add_tags,
                remove_tags=remove_tags,
            ),
            options=options,
        )

    def update_many(
        self,
        *,
        lead_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        all_: NotGivenOr[bool] = NOT_GIVEN,
        filter: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        notes: NotGivenOr[str] = NOT_GIVEN,
        tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        add_tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        remove_tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadsUpdated:
        """Edit many leads at once. Setting values converges, so a retry is safe.

        Requires the ``BULK_CONTACTS`` permission.

        Args:
            lead_ids: The leads to edit (at most 5000).
            all_: Edit every lead matching ``filter``.
            filter: The lead filter for an ``all_`` selection.
            status: ``"new"``, ``"saved"``, ``"contacted"`` or ``"dismissed"``.
            notes: Replacement notes.
            tags: Replace the whole tag list.
            add_tags: Tags to add.
            remove_tags: Tags to remove.
        """
        return self._patch(
            "/leads",
            cast_to=LeadsUpdated,
            body={
                **_selection(lead_ids=lead_ids, all_=all_, filter=filter),
                **_patch_fields(
                    status=status,
                    notes=notes,
                    tags=tags,
                    add_tags=add_tags,
                    remove_tags=remove_tags,
                ),
            },
            options=options,
        )

    def delete_many(
        self,
        *,
        lead_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        all_: NotGivenOr[bool] = NOT_GIVEN,
        filter: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadsDeleted:
        """Delete the selected leads. Deleting what is gone is a no-op.

        Requires the ``BULK_CONTACTS`` permission.

        Args:
            lead_ids: The leads to delete (at most 5000).
            all_: Delete every lead matching ``filter``.
            filter: The lead filter for an ``all_`` selection.
        """
        return self._delete(
            "/leads",
            cast_to=LeadsDeleted,
            body=_selection(lead_ids=lead_ids, all_=all_, filter=filter),
            options=options,
        )

    # -- enrichment -----------------------------------------------------------
    def enrich(
        self,
        *,
        lead_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        all_: NotGivenOr[bool] = NOT_GIVEN,
        filter: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        verify: NotGivenOr[bool] = NOT_GIVEN,
        people: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadEnrichmentRun:
        """Start a background run reading the selected leads' websites.

        Answers ``202`` with the run; follow it with :meth:`retrieve_enrichment`.
        Each website read is charged to the workspace balance (refunded when
        the site never answers). A retry with the same idempotency key returns
        the same run.

        Requires the ``BULK_CONTACTS`` permission.

        Args:
            lead_ids: The leads to enrich (at most 5000).
            all_: Enrich every lead matching ``filter``.
            filter: The lead filter for an ``all_`` selection.
            verify: Check the addresses found (default ``True``).
            people: Also find the people each site names and work out their
                addresses (default ``True``).
        """
        return self._post(
            "/leads/enrich",
            cast_to=LeadEnrichmentRun,
            body={
                **_selection(lead_ids=lead_ids, all_=all_, filter=filter),
                **drop_not_given({"verify": verify, "people": people}),
            },
            options=options,
        )

    def list_enrichments(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[LeadEnrichmentRun]:
        """List the enrichment runs still going.

        Requires the ``READ_CONTACTS`` permission.
        """
        return self._get_api_list(
            "/leads/enrichments", model=LeadEnrichmentRun, options=options
        )

    def retrieve_enrichment(
        self, run_id: str, *, options: RequestOptions | None = None
    ) -> LeadEnrichmentRun:
        """Retrieve one enrichment run's progress.

        Requires the ``READ_CONTACTS`` permission.
        """
        return self._get(
            f"/leads/enrichments/{run_id}", cast_to=LeadEnrichmentRun, options=options
        )

    # -- contacts -------------------------------------------------------------
    def add_to_contacts(
        self,
        *,
        lead_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        all_: NotGivenOr[bool] = NOT_GIVEN,
        filter: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        who: NotGivenOr[str] = NOT_GIVEN,
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        segment_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        verified_only: NotGivenOr[bool] = NOT_GIVEN,
        include_guessed: NotGivenOr[bool] = NOT_GIVEN,
        keep_existing: NotGivenOr[bool] = NOT_GIVEN,
        skip_active_in_other_campaigns: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadsAddedToContacts:
        """Import the selected leads as contacts.

        A contact that already exists is updated, so a retry adds nobody twice.

        Requires the ``BULK_CONTACTS`` permission.

        Args:
            lead_ids: The leads to import (at most 5000).
            all_: Import every lead matching ``filter``.
            filter: The lead filter for an ``all_`` selection.
            who: ``"business"`` (each lead's own address, default),
                ``"people"`` (the people found at each lead) or ``"both"``.
            campaign_ids: Campaigns to enrol the contacts in.
            category_ids: Categories to tag them with.
            segment_ids: Segments to pin them into.
            verified_only: Keep out every address that did not check as valid.
            include_guessed: Include people whose address was worked out but
                not confirmed.
            keep_existing: Leave a contact already in the workspace as it is;
                it still gets the segments, labels and campaigns.
            skip_active_in_other_campaigns: Enrol nobody another campaign is
                emailing.
        """
        return self._post(
            "/leads/contacts",
            cast_to=LeadsAddedToContacts,
            body={
                **_selection(lead_ids=lead_ids, all_=all_, filter=filter),
                **drop_not_given(
                    {
                        "who": who,
                        "campaign_ids": campaign_ids,
                        "category_ids": category_ids,
                        "segment_ids": segment_ids,
                        "verified_only": verified_only,
                        "include_guessed": include_guessed,
                        "keep_existing": keep_existing,
                        "skip_active_in_other_campaigns": skip_active_in_other_campaigns,
                    }
                ),
            },
            options=options,
        )

    # -- people ---------------------------------------------------------------
    def add_person(
        self,
        lead_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        first_name: NotGivenOr[str] = NOT_GIVEN,
        last_name: NotGivenOr[str] = NOT_GIVEN,
        title: NotGivenOr[str] = NOT_GIVEN,
        email: NotGivenOr[str] = NOT_GIVEN,
        linkedin_url: NotGivenOr[str] = NOT_GIVEN,
        phone: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadPerson:
        """Add someone to a lead.

        Send ``name``, or ``first_name`` and ``last_name``. Without an
        ``email`` the finder works out the address at the lead's domain, which
        is charged to the workspace balance (refunded when none turns up).
        People are matched by name, so adding someone again lands on the same
        person, but a retried lookup charges again.

        Requires the ``WRITE_CONTACTS`` permission.
        """
        return self._post(
            f"/leads/{lead_id}/people",
            cast_to=LeadPerson,
            body=_person_fields(
                name=name,
                first_name=first_name,
                last_name=last_name,
                title=title,
                email=email,
                linkedin_url=linkedin_url,
                phone=phone,
            ),
            options=options,
        )

    def update_person(
        self,
        lead_id: str,
        person_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        first_name: NotGivenOr[str] = NOT_GIVEN,
        last_name: NotGivenOr[str] = NOT_GIVEN,
        title: NotGivenOr[str] = NOT_GIVEN,
        email: NotGivenOr[str] = NOT_GIVEN,
        linkedin_url: NotGivenOr[str] = NOT_GIVEN,
        phone: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadPerson:
        """Edit someone on a lead. Omitted fields are left alone.

        Requires the ``WRITE_CONTACTS`` permission.
        """
        return self._patch(
            f"/leads/{lead_id}/people/{person_id}",
            cast_to=LeadPerson,
            body=_person_fields(
                name=name,
                first_name=first_name,
                last_name=last_name,
                title=title,
                email=email,
                linkedin_url=linkedin_url,
                phone=phone,
            ),
            options=options,
        )

    def delete_person(
        self, lead_id: str, person_id: str, *, options: RequestOptions | None = None
    ) -> LeadPersonDeleted:
        """Remove someone from a lead.

        Requires the ``WRITE_CONTACTS`` permission.
        """
        return self._delete(
            f"/leads/{lead_id}/people/{person_id}",
            cast_to=LeadPersonDeleted,
            options=options,
        )

    def find_person_email(
        self, lead_id: str, person_id: str, *, options: RequestOptions | None = None
    ) -> LeadPerson:
        """Work out a person's address at the lead's domain again.

        Charged to the workspace balance (refunded when none turns up), and
        charged again if retried, so retry only after reading the person back.

        Requires the ``WRITE_CONTACTS`` permission.
        """
        return self._post(
            f"/leads/{lead_id}/people/{person_id}/find-email",
            cast_to=LeadPerson,
            options=options,
        )


class AsyncLeads(AsyncAPIResource):
    """Asynchronous ``leads`` resource."""

    # -- finder setup ---------------------------------------------------------
    async def config(
        self, *, options: RequestOptions | None = None
    ) -> LeadFinderConfig:
        """List the providers, categories, prices and map style of the finder.

        Requires the ``READ_CONTACTS`` permission.
        """
        return await self._get(
            "/leads/config", cast_to=LeadFinderConfig, options=options
        )

    def geocode(
        self,
        *,
        q: str,
        lat: NotGivenOr[float] = NOT_GIVEN,
        lng: NotGivenOr[float] = NOT_GIVEN,
        lang: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[LeadGeocodeResult]:
        """Look up a typed location for the map (up to six matches).

        Requires the ``READ_CONTACTS`` permission.

        Args:
            q: The location text (at most 200 characters).
            lat: Bias results toward this latitude. Send with ``lng``.
            lng: Bias results toward this longitude. Send with ``lat``.
            lang: Result language: ``"en"``, ``"de"`` or ``"fr"``.
        """
        return self._get_api_list(
            "/leads/geocode",
            model=LeadGeocodeResult,
            query={"q": q, "lat": lat, "lng": lng, "lang": lang},
            options=options,
        )

    # -- searching ------------------------------------------------------------
    async def search(
        self,
        *,
        provider: NotGivenOr[str] = NOT_GIVEN,
        area: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        query: NotGivenOr[str] = NOT_GIVEN,
        category: NotGivenOr[str] = NOT_GIVEN,
        location_label: NotGivenOr[str] = NOT_GIVEN,
        save: NotGivenOr[bool] = NOT_GIVEN,
        name: NotGivenOr[str] = NOT_GIVEN,
        language: NotGivenOr[str] = NOT_GIVEN,
        search_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadSearchResult:
        """Run one page of a source search and store what it finds.

        To fetch the next page of a search, send ``search_id`` alone. A search
        through a source the instance pays for charges the workspace balance
        (``charged_usd`` on the result). A retry with the same idempotency key
        replays the stored answer instead of searching, and charging, again.

        Requires the ``WRITE_CONTACTS`` permission.

        Args:
            provider: ``"osm"``, ``"google_places"``, ``"foursquare"`` or
                ``"outscraper"``.
            area: The part of the map to cover: ``{"kind": "bbox" | "circle" |
                "polygon", "bounds": {"south", "west", "north", "east"},
                "center": {"lat", "lng"}, "radius_m": ..., "polygon": [...]}``.
            query: Free-text search phrase.
            category: A category id from :meth:`config`.
            location_label: The label of the searched place, kept on the search.
            save: Keep the search in the saved list.
            name: A name for the saved search.
            language: Result language hint.
            search_id: An earlier search whose next page to fetch.
        """
        return await self._post(
            "/leads/search",
            cast_to=LeadSearchResult,
            body=drop_not_given(
                {
                    "search_id": search_id,
                    "provider": provider,
                    "query": query,
                    "category": category,
                    "location_label": location_label,
                    "area": area,
                    "save": save,
                    "name": name,
                    "language": language,
                }
            ),
            options=options,
        )

    def list_searches(
        self,
        *,
        saved: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[LeadSearch]:
        """List recent searches, or only the saved ones.

        Requires the ``READ_CONTACTS`` permission.

        Args:
            saved: ``True`` for the saved searches only.
        """
        return self._get_api_list(
            "/leads/searches",
            model=LeadSearch,
            query={"saved": "true" if saved is True else NOT_GIVEN},
            options=options,
        )

    async def update_search(
        self,
        search_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        saved: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadSearch:
        """Rename a search or move it in or out of the saved list.

        Requires the ``WRITE_CONTACTS`` permission.
        """
        return await self._patch(
            f"/leads/searches/{search_id}",
            cast_to=LeadSearch,
            body=drop_not_given({"name": name, "saved": saved}),
            options=options,
        )

    async def delete_search(
        self, search_id: str, *, options: RequestOptions | None = None
    ) -> LeadSearchDeleted:
        """Delete a search. The leads it found stay.

        Requires the ``WRITE_CONTACTS`` permission.
        """
        return await self._delete(
            f"/leads/searches/{search_id}", cast_to=LeadSearchDeleted, options=options
        )

    # -- reading leads --------------------------------------------------------
    def query(
        self,
        *,
        filter: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        sort: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[Lead]:
        """List leads matching a filter, a page at a time (auto-paginating).

        A read that carries its filter in a ``POST`` body.

        Requires the ``READ_CONTACTS`` permission.

        Args:
            filter: The lead filter (see the module docs for its keys).
            sort: ``"recent"`` (default), ``"score"``, ``"rating"``,
                ``"reviews"`` or ``"name"``.
            limit: Page size, 1 to 200 (default 50).
            cursor: An opaque cursor from a previous page.
        """
        body = _query_body(filter=filter, sort=sort, limit=limit)
        start = cursor if isinstance(cursor, str) else None

        async def fetch(page_cursor: str | None) -> AsyncCursorPage[Lead]:
            payload = dict(body)
            token = page_cursor if page_cursor is not None else start
            if token is not None:
                payload["cursor"] = token
            prepared = self._client._prepare(
                "POST", "/leads/query", json_body=payload, options=_read(options)
            )
            response = await self._client._send(prepared)
            data, next_cursor, has_more, total, request_id = self._client._page_fields(
                response
            )
            return AsyncCursorPage(
                data=[
                    construct_type(Lead, item, request_id=request_id) for item in data
                ],
                next_cursor=next_cursor,
                has_more=has_more,
                total=total,
                fetch_next=fetch,
            )

        return AsyncPaginator(fetch)

    async def points(
        self,
        *,
        filter: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadPoints:
        """Return the map pins for a filter (at most 5000; see ``truncated``).

        Requires the ``READ_CONTACTS`` permission.
        """
        return await self._post(
            "/leads/points",
            cast_to=LeadPoints,
            body=drop_not_given({"filter": filter}),
            options=_read(options),
        )

    async def facets(
        self,
        *,
        filter: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadFacets:
        """Return the category, tag and city values the filter panel offers.

        Requires the ``READ_CONTACTS`` permission.
        """
        return await self._post(
            "/leads/facets",
            cast_to=LeadFacets,
            body=drop_not_given({"filter": filter}),
            options=_read(options),
        )

    async def retrieve(
        self, lead_id: str, *, options: RequestOptions | None = None
    ) -> Lead:
        """Retrieve one lead, with the ``people`` found at it.

        Requires the ``READ_CONTACTS`` permission.
        """
        return await self._get(f"/leads/{lead_id}", cast_to=Lead, options=options)

    async def export(
        self,
        *,
        format: NotGivenOr[str] = NOT_GIVEN,
        columns: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        rows: NotGivenOr[str] = NOT_GIVEN,
        lead_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        all_: NotGivenOr[bool] = NOT_GIVEN,
        filter: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> bytes:
        """Export the selected leads and return the encoded file bytes.

        Requires the ``READ_CONTACTS`` permission.

        Args:
            format: ``"csv"`` (default), ``"xlsx"`` or ``"json"``.
            columns: Column keys from :meth:`config` (``export_columns``);
                defaults to ``default_export_columns``.
            rows: ``"leads"`` (one row per business, default) or ``"people"``
                (one row per person).
            lead_ids: The leads to export (at most 5000).
            all_: Export every lead matching ``filter``.
            filter: The lead filter for an ``all_`` selection.

        Returns:
            The raw file. Write it to disk as-is; ``xlsx`` is binary.
        """
        return await self._post(
            "/leads/export",
            cast_to=bytes,
            body={
                **_selection(lead_ids=lead_ids, all_=all_, filter=filter),
                **drop_not_given({"format": format, "columns": columns, "rows": rows}),
            },
            options=_read(options),
        )

    # -- editing leads --------------------------------------------------------
    async def update(
        self,
        lead_id: str,
        *,
        status: NotGivenOr[str] = NOT_GIVEN,
        notes: NotGivenOr[str] = NOT_GIVEN,
        tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        add_tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        remove_tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Lead:
        """Edit one lead's status, notes or tags.

        Requires the ``WRITE_CONTACTS`` permission.

        Args:
            lead_id: The lead id.
            status: ``"new"``, ``"saved"``, ``"contacted"`` or ``"dismissed"``.
            notes: Replacement notes.
            tags: Replace the whole tag list.
            add_tags: Tags to add.
            remove_tags: Tags to remove.
        """
        return await self._patch(
            f"/leads/{lead_id}",
            cast_to=Lead,
            body=_patch_fields(
                status=status,
                notes=notes,
                tags=tags,
                add_tags=add_tags,
                remove_tags=remove_tags,
            ),
            options=options,
        )

    async def update_many(
        self,
        *,
        lead_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        all_: NotGivenOr[bool] = NOT_GIVEN,
        filter: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        notes: NotGivenOr[str] = NOT_GIVEN,
        tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        add_tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        remove_tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadsUpdated:
        """Edit many leads at once. Setting values converges, so a retry is safe.

        Requires the ``BULK_CONTACTS`` permission.

        Args:
            lead_ids: The leads to edit (at most 5000).
            all_: Edit every lead matching ``filter``.
            filter: The lead filter for an ``all_`` selection.
            status: ``"new"``, ``"saved"``, ``"contacted"`` or ``"dismissed"``.
            notes: Replacement notes.
            tags: Replace the whole tag list.
            add_tags: Tags to add.
            remove_tags: Tags to remove.
        """
        return await self._patch(
            "/leads",
            cast_to=LeadsUpdated,
            body={
                **_selection(lead_ids=lead_ids, all_=all_, filter=filter),
                **_patch_fields(
                    status=status,
                    notes=notes,
                    tags=tags,
                    add_tags=add_tags,
                    remove_tags=remove_tags,
                ),
            },
            options=options,
        )

    async def delete_many(
        self,
        *,
        lead_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        all_: NotGivenOr[bool] = NOT_GIVEN,
        filter: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadsDeleted:
        """Delete the selected leads. Deleting what is gone is a no-op.

        Requires the ``BULK_CONTACTS`` permission.

        Args:
            lead_ids: The leads to delete (at most 5000).
            all_: Delete every lead matching ``filter``.
            filter: The lead filter for an ``all_`` selection.
        """
        return await self._delete(
            "/leads",
            cast_to=LeadsDeleted,
            body=_selection(lead_ids=lead_ids, all_=all_, filter=filter),
            options=options,
        )

    # -- enrichment -----------------------------------------------------------
    async def enrich(
        self,
        *,
        lead_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        all_: NotGivenOr[bool] = NOT_GIVEN,
        filter: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        verify: NotGivenOr[bool] = NOT_GIVEN,
        people: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadEnrichmentRun:
        """Start a background run reading the selected leads' websites.

        Answers ``202`` with the run; follow it with :meth:`retrieve_enrichment`.
        Each website read is charged to the workspace balance (refunded when
        the site never answers). A retry with the same idempotency key returns
        the same run.

        Requires the ``BULK_CONTACTS`` permission.

        Args:
            lead_ids: The leads to enrich (at most 5000).
            all_: Enrich every lead matching ``filter``.
            filter: The lead filter for an ``all_`` selection.
            verify: Check the addresses found (default ``True``).
            people: Also find the people each site names and work out their
                addresses (default ``True``).
        """
        return await self._post(
            "/leads/enrich",
            cast_to=LeadEnrichmentRun,
            body={
                **_selection(lead_ids=lead_ids, all_=all_, filter=filter),
                **drop_not_given({"verify": verify, "people": people}),
            },
            options=options,
        )

    def list_enrichments(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[LeadEnrichmentRun]:
        """List the enrichment runs still going.

        Requires the ``READ_CONTACTS`` permission.
        """
        return self._get_api_list(
            "/leads/enrichments", model=LeadEnrichmentRun, options=options
        )

    async def retrieve_enrichment(
        self, run_id: str, *, options: RequestOptions | None = None
    ) -> LeadEnrichmentRun:
        """Retrieve one enrichment run's progress.

        Requires the ``READ_CONTACTS`` permission.
        """
        return await self._get(
            f"/leads/enrichments/{run_id}", cast_to=LeadEnrichmentRun, options=options
        )

    # -- contacts -------------------------------------------------------------
    async def add_to_contacts(
        self,
        *,
        lead_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        all_: NotGivenOr[bool] = NOT_GIVEN,
        filter: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        who: NotGivenOr[str] = NOT_GIVEN,
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        segment_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        verified_only: NotGivenOr[bool] = NOT_GIVEN,
        include_guessed: NotGivenOr[bool] = NOT_GIVEN,
        keep_existing: NotGivenOr[bool] = NOT_GIVEN,
        skip_active_in_other_campaigns: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadsAddedToContacts:
        """Import the selected leads as contacts.

        A contact that already exists is updated, so a retry adds nobody twice.

        Requires the ``BULK_CONTACTS`` permission.

        Args:
            lead_ids: The leads to import (at most 5000).
            all_: Import every lead matching ``filter``.
            filter: The lead filter for an ``all_`` selection.
            who: ``"business"`` (each lead's own address, default),
                ``"people"`` (the people found at each lead) or ``"both"``.
            campaign_ids: Campaigns to enrol the contacts in.
            category_ids: Categories to tag them with.
            segment_ids: Segments to pin them into.
            verified_only: Keep out every address that did not check as valid.
            include_guessed: Include people whose address was worked out but
                not confirmed.
            keep_existing: Leave a contact already in the workspace as it is;
                it still gets the segments, labels and campaigns.
            skip_active_in_other_campaigns: Enrol nobody another campaign is
                emailing.
        """
        return await self._post(
            "/leads/contacts",
            cast_to=LeadsAddedToContacts,
            body={
                **_selection(lead_ids=lead_ids, all_=all_, filter=filter),
                **drop_not_given(
                    {
                        "who": who,
                        "campaign_ids": campaign_ids,
                        "category_ids": category_ids,
                        "segment_ids": segment_ids,
                        "verified_only": verified_only,
                        "include_guessed": include_guessed,
                        "keep_existing": keep_existing,
                        "skip_active_in_other_campaigns": skip_active_in_other_campaigns,
                    }
                ),
            },
            options=options,
        )

    # -- people ---------------------------------------------------------------
    async def add_person(
        self,
        lead_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        first_name: NotGivenOr[str] = NOT_GIVEN,
        last_name: NotGivenOr[str] = NOT_GIVEN,
        title: NotGivenOr[str] = NOT_GIVEN,
        email: NotGivenOr[str] = NOT_GIVEN,
        linkedin_url: NotGivenOr[str] = NOT_GIVEN,
        phone: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadPerson:
        """Add someone to a lead.

        Send ``name``, or ``first_name`` and ``last_name``. Without an
        ``email`` the finder works out the address at the lead's domain, which
        is charged to the workspace balance (refunded when none turns up).
        People are matched by name, so adding someone again lands on the same
        person, but a retried lookup charges again.

        Requires the ``WRITE_CONTACTS`` permission.
        """
        return await self._post(
            f"/leads/{lead_id}/people",
            cast_to=LeadPerson,
            body=_person_fields(
                name=name,
                first_name=first_name,
                last_name=last_name,
                title=title,
                email=email,
                linkedin_url=linkedin_url,
                phone=phone,
            ),
            options=options,
        )

    async def update_person(
        self,
        lead_id: str,
        person_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        first_name: NotGivenOr[str] = NOT_GIVEN,
        last_name: NotGivenOr[str] = NOT_GIVEN,
        title: NotGivenOr[str] = NOT_GIVEN,
        email: NotGivenOr[str] = NOT_GIVEN,
        linkedin_url: NotGivenOr[str] = NOT_GIVEN,
        phone: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> LeadPerson:
        """Edit someone on a lead. Omitted fields are left alone.

        Requires the ``WRITE_CONTACTS`` permission.
        """
        return await self._patch(
            f"/leads/{lead_id}/people/{person_id}",
            cast_to=LeadPerson,
            body=_person_fields(
                name=name,
                first_name=first_name,
                last_name=last_name,
                title=title,
                email=email,
                linkedin_url=linkedin_url,
                phone=phone,
            ),
            options=options,
        )

    async def delete_person(
        self, lead_id: str, person_id: str, *, options: RequestOptions | None = None
    ) -> LeadPersonDeleted:
        """Remove someone from a lead.

        Requires the ``WRITE_CONTACTS`` permission.
        """
        return await self._delete(
            f"/leads/{lead_id}/people/{person_id}",
            cast_to=LeadPersonDeleted,
            options=options,
        )

    async def find_person_email(
        self, lead_id: str, person_id: str, *, options: RequestOptions | None = None
    ) -> LeadPerson:
        """Work out a person's address at the lead's domain again.

        Charged to the workspace balance (refunded when none turns up), and
        charged again if retried, so retry only after reading the person back.

        Requires the ``WRITE_CONTACTS`` permission.
        """
        return await self._post(
            f"/leads/{lead_id}/people/{person_id}/find-email",
            cast_to=LeadPerson,
            options=options,
        )
