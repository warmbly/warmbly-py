"""Tests for the ``leads`` and ``email_images`` resources, sync and async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"
LEAD_ID = "5b3f6c1e-0a41-4a53-9c1f-2f6f9d0d1a11"
PERSON_ID = "9a1c2d3e-4f50-4a61-8b72-0c1d2e3f4a55"
SEARCH_ID = "c0ffee00-1111-4222-8333-444455556666"
RUN_ID = "d1d1d1d1-2222-4333-8444-555566667777"


@pytest.fixture
def client() -> Iterator[Warmbly]:
    c = Warmbly(api_key="wmbly_test", base_url=BASE_URL, max_retries=0)
    yield c
    c.close()


@pytest.fixture
async def aclient() -> AsyncIterator[AsyncWarmbly]:
    async with AsyncWarmbly(
        api_key="wmbly_test", base_url=BASE_URL, max_retries=0
    ) as c:
        yield c


def _last(route: respx.Route) -> httpx.Request:
    return route.calls.last.request


def _body(route: respx.Route) -> Any:
    return json.loads(_last(route).content)


PERSON: dict[str, Any] = {
    "id": PERSON_ID,
    "lead_id": LEAD_ID,
    "name": "Ada Lovelace",
    "first_name": "Ada",
    "last_name": "Lovelace",
    "title": "Owner",
    "seniority": "owner",
    "email": "ada@acme-bakery.example",
    "email_source": "pattern",
    "email_status": "guessed",
    "email_confidence": 62,
    "linkedin_url": "https://linkedin.com/in/ada",
    "phone": "",
    "source": "manual",
    "source_url": "",
    "contact_id": None,
    "created_at": "2026-11-01T10:00:00Z",
    "updated_at": "2026-11-01T10:00:00Z",
}

LEAD: dict[str, Any] = {
    "id": LEAD_ID,
    "provider": "osm",
    "external_id": "node/1",
    "name": "Acme Bakery",
    "category": "bakery",
    "categories": ["bakery", "cafe"],
    "address": "1 Main St, Springfield",
    "street": "1 Main St",
    "city": "Springfield",
    "region": "IL",
    "postcode": "62701",
    "country": "US",
    "latitude": 39.78,
    "longitude": -89.65,
    "phone": "+1 555 0100",
    "website": "https://acme-bakery.example",
    "domain": "acme-bakery.example",
    "email": "hello@acme-bakery.example",
    "emails": [
        {
            "email": "hello@acme-bakery.example",
            "source": "website",
            "url": "https://acme-bakery.example/contact",
            "domain_match": True,
            "status": "valid",
        }
    ],
    "socials": {"facebook": "https://facebook.com/acme"},
    "rating": 4.6,
    "review_count": 120,
    "price_level": None,
    "hours": ["Mon 07:00-17:00"],
    "business_status": "operational",
    "maps_url": "",
    "description": "",
    "chain": "",
    "site": {
        "reachable": True,
        "final_url": "https://acme-bakery.example/",
        "https": True,
        "title": "Acme Bakery",
        "signals": ["wordpress"],
        "phones": [],
        "pages": 4,
        "email_pattern": "first.last",
        "accepts_all": False,
        "checked_at": "2026-11-01T09:00:00Z",
    },
    "score": 71,
    "status": "new",
    "enrichment_status": "done",
    "enriched_at": "2026-11-01T09:00:00Z",
    "contact_id": None,
    "tags": ["bakeries"],
    "notes": "",
    "people_count": 1,
    "people": [PERSON],
    "first_seen_at": "2026-10-30T09:00:00Z",
    "last_seen_at": "2026-11-01T09:00:00Z",
    "created_at": "2026-10-30T09:00:00Z",
    "updated_at": "2026-11-01T09:00:00Z",
}

SEARCH: dict[str, Any] = {
    "id": SEARCH_ID,
    "created_by_user_id": None,
    "name": "Bakeries in Springfield",
    "provider": "osm",
    "query": "bakery",
    "category": "bakery",
    "location_label": "Springfield, IL",
    "area": {
        "kind": "circle",
        "bounds": {"south": 39.7, "west": -89.7, "north": 39.8, "east": -89.6},
        "center": {"lat": 39.75, "lng": -89.65},
        "radius_m": 5000,
    },
    "saved": False,
    "result_count": 1,
    "pages_fetched": 1,
    "has_more": True,
    "last_run_at": "2026-11-01T09:00:00Z",
    "created_at": "2026-11-01T09:00:00Z",
    "updated_at": "2026-11-01T09:00:00Z",
}

RUN: dict[str, Any] = {
    "id": RUN_ID,
    "requested_by_user_id": None,
    "verify": True,
    "people": True,
    "status": "running",
    "total": 10,
    "processed": 4,
    "emails_found": 3,
    "people_found": 2,
    "no_website": 1,
    "failed": 0,
    "charged_usd": 0.08,
    "last_error": "",
    "started_at": "2026-11-01T09:00:00Z",
    "finished_at": None,
    "created_at": "2026-11-01T09:00:00Z",
    "updated_at": "2026-11-01T09:00:00Z",
}


def _check_lead(lead: Any) -> None:
    assert lead.id == LEAD_ID
    assert lead.provider == "osm"
    assert lead.categories == ["bakery", "cafe"]
    assert lead.emails[0].domain_match is True
    assert lead.socials == {"facebook": "https://facebook.com/acme"}
    assert lead.rating == 4.6
    assert lead.review_count == 120
    assert lead.price_level is None
    assert lead.site is not None
    assert lead.site.email_pattern == "first.last"
    assert lead.enrichment_status == "done"
    assert lead.people[0].seniority == "owner"
    assert lead.people[0].contact_id is None


# -- config, geocode ---------------------------------------------------------


CONFIG: dict[str, Any] = {
    "providers": [
        {
            "id": "osm",
            "name": "OpenStreetMap",
            "description": "Free",
            "available": True,
            "key_source": "none",
            "needs_key": False,
            "page_size": 100,
            "max_pages": 5,
            "cost_usd": 0,
            "fields": ["name", "phone"],
        }
    ],
    "categories": [{"id": "bakery", "label": "Bakery", "group": "Food"}],
    "default_provider": "osm",
    "enrich_cost_usd": 0.02,
    "person_email_cost_usd": 0.02,
    "export_columns": [{"key": "name", "label": "Name"}],
    "person_columns": [{"key": "person_name", "label": "Person"}],
    "default_export_columns": ["name"],
    "map": {"style_light": "https://l.example", "style_dark": "https://d.example"},
}

GEOCODE: dict[str, Any] = {
    "data": [
        {
            "label": "Springfield",
            "detail": "Illinois, United States",
            "kind": "city",
            "center": {"lat": 39.8, "lng": -89.6},
            "bounds": {"south": 39.7, "west": -89.7, "north": 39.9, "east": -89.5},
        }
    ]
}


@respx.mock
def test_config_and_geocode_sync(client: Warmbly) -> None:
    config = respx.get(f"{BASE_URL}/leads/config").mock(
        return_value=httpx.Response(200, json=CONFIG)
    )
    out = client.leads.config()
    assert _last(config).method == "GET"
    assert out.default_provider == "osm"
    assert out.providers[0].key_source == "none"
    assert out.providers[0].fields == ["name", "phone"]
    assert out.categories[0].group == "Food"
    assert out.export_columns[0].key == "name"
    assert out.person_columns[0].label == "Person"
    assert out.map is not None
    assert out.map.style_dark == "https://d.example"
    assert out.enrich_cost_usd == 0.02

    geo = respx.get(f"{BASE_URL}/leads/geocode").mock(
        return_value=httpx.Response(200, json=GEOCODE)
    )
    places = list(client.leads.geocode(q="Springfield", lat=39.1, lng=-89.2, lang="en"))
    params = _last(geo).url.params
    assert params["q"] == "Springfield"
    assert params["lat"] == "39.1"
    assert params["lng"] == "-89.2"
    assert params["lang"] == "en"
    assert places[0].center is not None
    assert places[0].center.lat == 39.8
    assert places[0].bounds is not None
    assert places[0].bounds.east == -89.5
    list(client.leads.geocode(q="x"))
    assert "lat" not in _last(geo).url.params


@respx.mock
@pytest.mark.anyio
async def test_config_and_geocode_async(aclient: AsyncWarmbly) -> None:
    config = respx.get(f"{BASE_URL}/leads/config").mock(
        return_value=httpx.Response(200, json=CONFIG)
    )
    out = await aclient.leads.config()
    assert _last(config).url.path == "/v1/leads/config"
    assert out.providers[0].page_size == 100

    geo = respx.get(f"{BASE_URL}/leads/geocode").mock(
        return_value=httpx.Response(200, json=GEOCODE)
    )
    places = [p async for p in aclient.leads.geocode(q="Springfield", lang="de")]
    assert places[0].label == "Springfield"
    assert _last(geo).url.params["lang"] == "de"


# -- search ------------------------------------------------------------------

SEARCH_RESULT: dict[str, Any] = {
    "search": SEARCH,
    "leads": [LEAD],
    "found": 1,
    "outside_area": 0,
    "charged_usd": 0.04,
}

AREA = {
    "kind": "circle",
    "bounds": {"south": 39.7, "west": -89.7, "north": 39.8, "east": -89.6},
    "center": {"lat": 39.75, "lng": -89.65},
    "radius_m": 5000,
}


@respx.mock
def test_search_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/leads/search").mock(
        return_value=httpx.Response(200, json=SEARCH_RESULT)
    )
    out = client.leads.search(
        provider="osm",
        area=AREA,
        query="bakery",
        category="bakery",
        location_label="Springfield, IL",
        save=True,
        name="Bakeries in Springfield",
        language="en",
        options={"idempotency_key": "search-1"},
    )
    request = _last(route)
    assert request.headers["Idempotency-Key"] == "search-1"
    assert _body(route) == {
        "provider": "osm",
        "query": "bakery",
        "category": "bakery",
        "location_label": "Springfield, IL",
        "area": AREA,
        "save": True,
        "name": "Bakeries in Springfield",
        "language": "en",
    }
    assert out.found == 1
    assert out.outside_area == 0
    assert out.charged_usd == 0.04
    assert out.search is not None
    assert out.search.area is not None
    assert out.search.area.kind == "circle"
    assert out.search.area.center is not None
    assert out.search.area.center.lng == -89.65
    assert out.search.has_more is True
    _check_lead(out.leads[0])

    client.leads.search(search_id=SEARCH_ID)
    assert _body(route) == {"search_id": SEARCH_ID}
    assert _last(route).headers["Idempotency-Key"]


@respx.mock
@pytest.mark.anyio
async def test_search_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/leads/search").mock(
        return_value=httpx.Response(200, json=SEARCH_RESULT)
    )
    out = await aclient.leads.search(provider="osm", area=AREA, query="bakery")
    assert _body(route) == {"provider": "osm", "query": "bakery", "area": AREA}
    _check_lead(out.leads[0])
    assert out.search is not None
    assert out.search.id == SEARCH_ID


# -- searches ---------------------------------------------------------------


@respx.mock
def test_searches_sync(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/leads/searches").mock(
        return_value=httpx.Response(200, json={"data": [SEARCH]})
    )
    found = list(client.leads.list_searches(saved=True))
    assert _last(listing).url.params["saved"] == "true"
    assert found[0].location_label == "Springfield, IL"
    list(client.leads.list_searches())
    assert "saved" not in _last(listing).url.params

    patch = respx.patch(f"{BASE_URL}/leads/searches/{SEARCH_ID}").mock(
        return_value=httpx.Response(200, json={**SEARCH, "saved": True})
    )
    updated = client.leads.update_search(SEARCH_ID, name="Keep", saved=True)
    assert _body(patch) == {"name": "Keep", "saved": True}
    assert updated.saved is True

    delete = respx.delete(f"{BASE_URL}/leads/searches/{SEARCH_ID}").mock(
        return_value=httpx.Response(204)
    )
    assert client.leads.delete_search(SEARCH_ID).deleted is None
    assert _last(delete).method == "DELETE"


@respx.mock
@pytest.mark.anyio
async def test_searches_async(aclient: AsyncWarmbly) -> None:
    listing = respx.get(f"{BASE_URL}/leads/searches").mock(
        return_value=httpx.Response(200, json={"data": [SEARCH]})
    )
    assert [s.id async for s in aclient.leads.list_searches(saved=True)] == [SEARCH_ID]
    assert _last(listing).url.params["saved"] == "true"

    patch = respx.patch(f"{BASE_URL}/leads/searches/{SEARCH_ID}").mock(
        return_value=httpx.Response(200, json=SEARCH)
    )
    assert (await aclient.leads.update_search(SEARCH_ID, saved=False)).id == SEARCH_ID
    assert _body(patch) == {"saved": False}

    delete = respx.delete(f"{BASE_URL}/leads/searches/{SEARCH_ID}").mock(
        return_value=httpx.Response(204)
    )
    await aclient.leads.delete_search(SEARCH_ID)
    assert _last(delete).url.path == f"/v1/leads/searches/{SEARCH_ID}"


# -- query, points, facets, retrieve, export ---------------------------------


def _query_page(
    leads: list[dict[str, Any]], next_cursor: str | None, total: int
) -> dict[str, Any]:
    return {
        "data": leads,
        "pagination": {
            "next_cursor": next_cursor,
            "has_more": next_cursor is not None,
            "total": total,
        },
    }


@respx.mock
def test_query_pages_sync(client: Warmbly) -> None:
    second = {**LEAD, "id": "second"}
    route = respx.post(f"{BASE_URL}/leads/query").mock(
        side_effect=[
            httpx.Response(200, json=_query_page([LEAD], "OFFSET1", 2)),
            httpx.Response(200, json=_query_page([second], None, 2)),
        ]
    )
    page = client.leads.query(
        filter={"has_email": True},
        sort="score",
        limit=1,
        options={"idempotency_key": "ignored"},
    )
    assert page.total == 2
    assert [lead.id for lead in page] == [LEAD_ID, "second"]
    first, follow = route.calls[0].request, route.calls[1].request
    assert json.loads(first.content) == {
        "filter": {"has_email": True},
        "sort": "score",
        "limit": 1,
    }
    assert json.loads(follow.content) == {
        "filter": {"has_email": True},
        "sort": "score",
        "limit": 1,
        "cursor": "OFFSET1",
    }
    # A read: no idempotency key is sent, whatever the options say.
    assert "Idempotency-Key" not in first.headers
    assert "Idempotency-Key" not in follow.headers

    respx.post(f"{BASE_URL}/leads/query").mock(
        return_value=httpx.Response(200, json=_query_page([LEAD], None, 1))
    )
    start = list(client.leads.query(cursor="OFFSET9"))
    _check_lead(start[0])


@respx.mock
@pytest.mark.anyio
async def test_query_pages_async(aclient: AsyncWarmbly) -> None:
    second = {**LEAD, "id": "second"}
    route = respx.post(f"{BASE_URL}/leads/query").mock(
        side_effect=[
            httpx.Response(200, json=_query_page([LEAD], "OFFSET1", 2)),
            httpx.Response(200, json=_query_page([second], None, 2)),
        ]
    )
    ids = [lead.id async for lead in aclient.leads.query(filter={"q": "bak"})]
    assert ids == [LEAD_ID, "second"]
    assert json.loads(route.calls[0].request.content) == {"filter": {"q": "bak"}}
    assert json.loads(route.calls[1].request.content) == {
        "filter": {"q": "bak"},
        "cursor": "OFFSET1",
    }
    assert "Idempotency-Key" not in route.calls[0].request.headers

    respx.post(f"{BASE_URL}/leads/query").mock(
        return_value=httpx.Response(200, json=_query_page([LEAD], None, 1))
    )
    first_page = await aclient.leads.query(cursor="OFFSET9", options={"timeout": 5})
    assert first_page.total == 1
    _check_lead(first_page.data[0])
    last = respx.calls.last.request
    assert json.loads(last.content) == {"cursor": "OFFSET9"}


POINTS: dict[str, Any] = {
    "data": [
        {
            "id": LEAD_ID,
            "name": "Acme Bakery",
            "category": "bakery",
            "latitude": 39.78,
            "longitude": -89.65,
            "status": "new",
            "score": 71,
            "has_email": True,
            "has_website": True,
            "has_phone": True,
            "rating": 4.6,
            "review_count": 120,
            "in_contacts": False,
        }
    ],
    "truncated": False,
}
FACETS: dict[str, Any] = {
    "categories": [{"value": "bakery", "count": 3}],
    "tags": [{"value": "bakeries", "count": 2}],
    "cities": [{"value": "Springfield", "count": 3}],
}


@respx.mock
def test_points_facets_retrieve_export_sync(client: Warmbly) -> None:
    points = respx.post(f"{BASE_URL}/leads/points").mock(
        return_value=httpx.Response(200, json=POINTS)
    )
    out = client.leads.points(filter={"statuses": ["new"]})
    assert _body(points) == {"filter": {"statuses": ["new"]}}
    assert "Idempotency-Key" not in _last(points).headers
    assert out.truncated is False
    assert out.data[0].has_website is True
    assert out.data[0].review_count == 120

    facets = respx.post(f"{BASE_URL}/leads/facets").mock(
        return_value=httpx.Response(200, json=FACETS)
    )
    f = client.leads.facets()
    assert _body(facets) == {}
    assert f.categories[0].count == 3
    assert f.tags[0].value == "bakeries"
    assert f.cities[0].value == "Springfield"

    get = respx.get(f"{BASE_URL}/leads/{LEAD_ID}").mock(
        return_value=httpx.Response(200, json=LEAD)
    )
    _check_lead(client.leads.retrieve(LEAD_ID))
    assert _last(get).method == "GET"

    export = respx.post(f"{BASE_URL}/leads/export").mock(
        return_value=httpx.Response(
            200,
            content=b"PK\x03\x04binary",
            headers={
                "content-type": "application/octet-stream",
                "content-disposition": 'attachment; filename="leads.xlsx"',
            },
        )
    )
    blob = client.leads.export(
        format="xlsx",
        columns=["name", "email"],
        rows="people",
        lead_ids=[LEAD_ID],
        all_=False,
        filter={"tag": "bakeries"},
    )
    assert blob == b"PK\x03\x04binary"
    assert _body(export) == {
        "lead_ids": [LEAD_ID],
        "all": False,
        "filter": {"tag": "bakeries"},
        "format": "xlsx",
        "columns": ["name", "email"],
        "rows": "people",
    }
    assert "Idempotency-Key" not in _last(export).headers


@respx.mock
@pytest.mark.anyio
async def test_points_facets_retrieve_export_async(aclient: AsyncWarmbly) -> None:
    points = respx.post(f"{BASE_URL}/leads/points").mock(
        return_value=httpx.Response(200, json=POINTS)
    )
    out = await aclient.leads.points()
    assert _body(points) == {}
    assert out.data[0].in_contacts is False

    facets = respx.post(f"{BASE_URL}/leads/facets").mock(
        return_value=httpx.Response(200, json=FACETS)
    )
    f = await aclient.leads.facets(filter={"q": "bak"})
    assert _body(facets) == {"filter": {"q": "bak"}}
    assert f.cities[0].count == 3

    respx.get(f"{BASE_URL}/leads/{LEAD_ID}").mock(
        return_value=httpx.Response(200, json=LEAD)
    )
    _check_lead(await aclient.leads.retrieve(LEAD_ID))

    export = respx.post(f"{BASE_URL}/leads/export").mock(
        return_value=httpx.Response(200, content=b"name\nAcme\n")
    )
    assert await aclient.leads.export(all_=True, filter={"q": "a"}) == b"name\nAcme\n"
    assert _body(export) == {"all": True, "filter": {"q": "a"}}


# -- editing -----------------------------------------------------------------


@respx.mock
def test_update_delete_many_sync(client: Warmbly) -> None:
    patch = respx.patch(f"{BASE_URL}/leads/{LEAD_ID}").mock(
        return_value=httpx.Response(200, json={**LEAD, "status": "saved"})
    )
    lead = client.leads.update(
        LEAD_ID,
        status="saved",
        notes="call back",
        tags=["a"],
        add_tags=["b"],
        remove_tags=["c"],
    )
    assert _body(patch) == {
        "status": "saved",
        "notes": "call back",
        "tags": ["a"],
        "add_tags": ["b"],
        "remove_tags": ["c"],
    }
    assert lead.status == "saved"

    bulk = respx.patch(f"{BASE_URL}/leads").mock(
        return_value=httpx.Response(200, json={"updated": 2})
    )
    done = client.leads.update_many(lead_ids=[LEAD_ID, "x"], status="dismissed")
    assert _body(bulk) == {"lead_ids": [LEAD_ID, "x"], "status": "dismissed"}
    assert done.updated == 2
    client.leads.update_many(all_=True, filter={"q": "a"}, add_tags=["t"])
    assert _body(bulk) == {"all": True, "filter": {"q": "a"}, "add_tags": ["t"]}

    gone = respx.delete(f"{BASE_URL}/leads").mock(
        return_value=httpx.Response(200, json={"deleted": 3})
    )
    assert client.leads.delete_many(lead_ids=[LEAD_ID]).deleted == 3
    assert _last(gone).method == "DELETE"
    assert _body(gone) == {"lead_ids": [LEAD_ID]}


@respx.mock
@pytest.mark.anyio
async def test_update_delete_many_async(aclient: AsyncWarmbly) -> None:
    patch = respx.patch(f"{BASE_URL}/leads/{LEAD_ID}").mock(
        return_value=httpx.Response(200, json=LEAD)
    )
    _check_lead(await aclient.leads.update(LEAD_ID, notes="n"))
    assert _body(patch) == {"notes": "n"}

    bulk = respx.patch(f"{BASE_URL}/leads").mock(
        return_value=httpx.Response(200, json={"updated": 5})
    )
    done = await aclient.leads.update_many(all_=True, tags=["x"])
    assert done.updated == 5
    assert _body(bulk) == {"all": True, "tags": ["x"]}

    gone = respx.delete(f"{BASE_URL}/leads").mock(
        return_value=httpx.Response(200, json={"deleted": 1})
    )
    out = await aclient.leads.delete_many(all_=True, filter={"statuses": ["dismissed"]})
    assert out.deleted == 1
    assert _body(gone) == {"all": True, "filter": {"statuses": ["dismissed"]}}


# -- enrichment --------------------------------------------------------------


@respx.mock
def test_enrichment_sync(client: Warmbly) -> None:
    enrich = respx.post(f"{BASE_URL}/leads/enrich").mock(
        return_value=httpx.Response(202, json=RUN)
    )
    run = client.leads.enrich(
        lead_ids=[LEAD_ID],
        verify=False,
        people=True,
        options={"idempotency_key": "enrich-1"},
    )
    assert _last(enrich).headers["Idempotency-Key"] == "enrich-1"
    assert _body(enrich) == {"lead_ids": [LEAD_ID], "verify": False, "people": True}
    assert run.id == RUN_ID
    assert run.status == "running"
    assert run.processed == 4
    assert run.emails_found == 3
    assert run.charged_usd == 0.08
    assert run.finished_at is None

    listing = respx.get(f"{BASE_URL}/leads/enrichments").mock(
        return_value=httpx.Response(200, json={"data": [RUN]})
    )
    assert [r.id for r in client.leads.list_enrichments()] == [RUN_ID]
    assert _last(listing).method == "GET"

    one = respx.get(f"{BASE_URL}/leads/enrichments/{RUN_ID}").mock(
        return_value=httpx.Response(200, json=RUN)
    )
    assert client.leads.retrieve_enrichment(RUN_ID).people_found == 2
    assert _last(one).url.path == f"/v1/leads/enrichments/{RUN_ID}"


@respx.mock
@pytest.mark.anyio
async def test_enrichment_async(aclient: AsyncWarmbly) -> None:
    enrich = respx.post(f"{BASE_URL}/leads/enrich").mock(
        return_value=httpx.Response(202, json=RUN)
    )
    run = await aclient.leads.enrich(all_=True, filter={"has_website": True})
    assert _body(enrich) == {"all": True, "filter": {"has_website": True}}
    assert run.total == 10

    respx.get(f"{BASE_URL}/leads/enrichments").mock(
        return_value=httpx.Response(200, json={"data": [RUN]})
    )
    assert [r.id async for r in aclient.leads.list_enrichments()] == [RUN_ID]

    respx.get(f"{BASE_URL}/leads/enrichments/{RUN_ID}").mock(
        return_value=httpx.Response(200, json=RUN)
    )
    assert (await aclient.leads.retrieve_enrichment(RUN_ID)).no_website == 1


# -- contacts ----------------------------------------------------------------

ADDED: dict[str, Any] = {
    "selected": 10,
    "imported": 6,
    "updated": 2,
    "skipped": 1,
    "failed": 0,
    "no_email": 1,
    "unverified": 0,
    "suppressed": 0,
    "guessed": 1,
    "people": 3,
    "errors": [{"line": 4, "reason": "bad address"}],
}


@respx.mock
def test_add_to_contacts_sync(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/leads/contacts").mock(
        return_value=httpx.Response(200, json=ADDED)
    )
    out = client.leads.add_to_contacts(
        lead_ids=[LEAD_ID],
        who="both",
        campaign_ids=["c1"],
        category_ids=["k1"],
        segment_ids=["s1"],
        verified_only=True,
        include_guessed=True,
        keep_existing=True,
        skip_active_in_other_campaigns=True,
    )
    assert _body(route) == {
        "lead_ids": [LEAD_ID],
        "who": "both",
        "campaign_ids": ["c1"],
        "category_ids": ["k1"],
        "segment_ids": ["s1"],
        "verified_only": True,
        "include_guessed": True,
        "keep_existing": True,
        "skip_active_in_other_campaigns": True,
    }
    assert out.selected == 10
    assert out.imported == 6
    assert out.no_email == 1
    assert out.people == 3
    assert out.errors[0]["line"] == 4


@respx.mock
@pytest.mark.anyio
async def test_add_to_contacts_async(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/leads/contacts").mock(
        return_value=httpx.Response(200, json=ADDED)
    )
    out = await aclient.leads.add_to_contacts(all_=True, filter={"has_email": True})
    assert _body(route) == {"all": True, "filter": {"has_email": True}}
    assert out.updated == 2
    assert out.guessed == 1


# -- people ------------------------------------------------------------------


@respx.mock
def test_people_sync(client: Warmbly) -> None:
    add = respx.post(f"{BASE_URL}/leads/{LEAD_ID}/people").mock(
        return_value=httpx.Response(200, json=PERSON)
    )
    person = client.leads.add_person(
        LEAD_ID,
        name="Ada Lovelace",
        first_name="Ada",
        last_name="Lovelace",
        title="Owner",
        email="ada@acme-bakery.example",
        linkedin_url="https://linkedin.com/in/ada",
        phone="+1 555 0101",
    )
    assert _body(add) == {
        "name": "Ada Lovelace",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "title": "Owner",
        "email": "ada@acme-bakery.example",
        "linkedin_url": "https://linkedin.com/in/ada",
        "phone": "+1 555 0101",
    }
    assert person.email_status == "guessed"
    assert person.email_confidence == 62
    assert person.lead_id == LEAD_ID

    patch = respx.patch(f"{BASE_URL}/leads/{LEAD_ID}/people/{PERSON_ID}").mock(
        return_value=httpx.Response(200, json={**PERSON, "title": "CEO"})
    )
    assert client.leads.update_person(LEAD_ID, PERSON_ID, title="CEO").title == "CEO"
    assert _body(patch) == {"title": "CEO"}

    find = respx.post(f"{BASE_URL}/leads/{LEAD_ID}/people/{PERSON_ID}/find-email").mock(
        return_value=httpx.Response(200, json=PERSON)
    )
    assert client.leads.find_person_email(LEAD_ID, PERSON_ID).email_source == "pattern"
    assert _last(find).method == "POST"

    delete = respx.delete(f"{BASE_URL}/leads/{LEAD_ID}/people/{PERSON_ID}").mock(
        return_value=httpx.Response(204)
    )
    assert client.leads.delete_person(LEAD_ID, PERSON_ID).deleted is None
    assert _last(delete).method == "DELETE"


@respx.mock
@pytest.mark.anyio
async def test_people_async(aclient: AsyncWarmbly) -> None:
    add = respx.post(f"{BASE_URL}/leads/{LEAD_ID}/people").mock(
        return_value=httpx.Response(200, json=PERSON)
    )
    person = await aclient.leads.add_person(LEAD_ID, name="Ada Lovelace")
    assert _body(add) == {"name": "Ada Lovelace"}
    assert person.seniority == "owner"

    patch = respx.patch(f"{BASE_URL}/leads/{LEAD_ID}/people/{PERSON_ID}").mock(
        return_value=httpx.Response(200, json=PERSON)
    )
    await aclient.leads.update_person(LEAD_ID, PERSON_ID, email="ada@x.example")
    assert _body(patch) == {"email": "ada@x.example"}

    respx.post(f"{BASE_URL}/leads/{LEAD_ID}/people/{PERSON_ID}/find-email").mock(
        return_value=httpx.Response(200, json=PERSON)
    )
    assert (await aclient.leads.find_person_email(LEAD_ID, PERSON_ID)).id == PERSON_ID

    respx.delete(f"{BASE_URL}/leads/{LEAD_ID}/people/{PERSON_ID}").mock(
        return_value=httpx.Response(204)
    )
    await aclient.leads.delete_person(LEAD_ID, PERSON_ID)


# -- email images ------------------------------------------------------------

IMAGE: dict[str, Any] = {
    "id": "1f1f1f1f-0000-4000-8000-000000000001",
    "organization_id": "0a0a0a0a-0000-4000-8000-000000000002",
    "user_id": None,
    "filename": "logo.png",
    "mime_type": "image/png",
    "size": 2048,
    "width": 400,
    "height": 120,
    "url": "https://cdn.example/email-images/logo.png",
    "created_at": "2026-11-01T09:00:00Z",
}


@respx.mock
def test_email_images_sync(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/email-images").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [IMAGE],
                    "pagination": {"next_cursor": "C2", "has_more": True},
                },
            ),
            httpx.Response(
                200,
                json={
                    "data": [{**IMAGE, "id": "b"}],
                    "pagination": {"next_cursor": None, "has_more": False},
                },
            ),
        ]
    )
    images = list(client.email_images.list(limit=1))
    assert [i.id for i in images] == [IMAGE["id"], "b"]
    assert images[0].mime_type == "image/png"
    assert images[0].width == 400
    assert images[0].user_id is None
    assert listing.calls[0].request.url.params["limit"] == "1"
    assert listing.calls[1].request.url.params["cursor"] == "C2"

    upload = respx.post(f"{BASE_URL}/email-images").mock(
        return_value=httpx.Response(201, json=IMAGE)
    )
    image = client.email_images.upload(
        file=b"\x89PNG", filename="logo.png", content_type="image/png"
    )
    request = _last(upload)
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert b'name="file"; filename="logo.png"' in request.content
    assert b"image/png" in request.content
    assert "Idempotency-Key" not in request.headers
    assert image.url == "https://cdn.example/email-images/logo.png"

    delete = respx.delete(f"{BASE_URL}/email-images/{IMAGE['id']}").mock(
        return_value=httpx.Response(204)
    )
    assert client.email_images.delete(IMAGE["id"]).deleted is None
    assert _last(delete).method == "DELETE"


@respx.mock
@pytest.mark.anyio
async def test_email_images_async(aclient: AsyncWarmbly) -> None:
    listing = respx.get(f"{BASE_URL}/email-images").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [IMAGE],
                "pagination": {"next_cursor": None, "has_more": False},
            },
        )
    )
    assert [i.id async for i in aclient.email_images.list(cursor="C1")] == [IMAGE["id"]]
    assert _last(listing).url.params["cursor"] == "C1"

    upload = respx.post(f"{BASE_URL}/email-images").mock(
        return_value=httpx.Response(201, json=IMAGE)
    )
    image = await aclient.email_images.upload(file=b"GIF89a", filename="a.gif")
    assert b'filename="a.gif"' in _last(upload).content
    assert image.height == 120

    delete = respx.delete(f"{BASE_URL}/email-images/{IMAGE['id']}").mock(
        return_value=httpx.Response(204)
    )
    await aclient.email_images.delete(IMAGE["id"])
    assert _last(delete).url.path == f"/v1/email-images/{IMAGE['id']}"
