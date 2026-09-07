"""Tests for the ``segments`` resource, sync and async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"

CONDITIONS = [{"field": "email_domain", "operator": "contains", "value": "acme.com"}]


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


def _page(data: list[dict]) -> dict:
    return {
        "data": data,
        "pagination": {"next_cursor": None, "has_more": False, "total": len(data)},
    }


def _last(route: respx.Route) -> httpx.Request:
    return route.calls.last.request


@respx.mock
def test_list_and_fields(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/segments").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                [{"id": "seg_1", "name": "Acme", "match": "all", "contact_count": 12}]
            ),
        )
    )
    segments = list(client.segments.list())
    assert [s.id for s in segments] == ["seg_1"]
    assert segments[0].contact_count == 12
    assert _last(listing).url.path == "/v1/segments"

    fields = respx.get(f"{BASE_URL}/segments/fields").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                [
                    {
                        "field": "esp_provider",
                        "label": "Email provider",
                        "kind": "enum",
                        "options": ["gmail", "outlook", "other"],
                    }
                ]
            ),
        )
    )
    catalog = list(client.segments.fields())
    assert catalog[0].kind == "enum"
    assert list(catalog[0].options) == ["gmail", "outlook", "other"]
    assert _last(fields).url.path == "/v1/segments/fields"


@respx.mock
def test_preview(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/segments/preview").mock(
        return_value=httpx.Response(200, json={"contact_count": 42})
    )

    result = client.segments.preview(
        match="any", conditions=CONDITIONS, segment_id="seg_1"
    )

    assert result.contact_count == 42
    assert json.loads(_last(route).content) == {
        "id": "seg_1",
        "match": "any",
        "conditions": CONDITIONS,
    }


@respx.mock
def test_crud(client: Warmbly) -> None:
    create = respx.post(f"{BASE_URL}/segments").mock(
        return_value=httpx.Response(201, json={"id": "seg_1", "name": "Acme"})
    )
    segment = client.segments.create(
        name="Acme", conditions=CONDITIONS, match="all", color="#ff8800"
    )
    assert segment.id == "seg_1"
    assert json.loads(_last(create).content) == {
        "name": "Acme",
        "color": "#ff8800",
        "match": "all",
        "conditions": CONDITIONS,
    }

    retrieve = respx.get(f"{BASE_URL}/segments/seg_1").mock(
        return_value=httpx.Response(200, json={"id": "seg_1", "name": "Acme"})
    )
    assert client.segments.retrieve("seg_1").name == "Acme"
    assert _last(retrieve).method == "GET"

    update = respx.patch(f"{BASE_URL}/segments/seg_1").mock(
        return_value=httpx.Response(200, json={"id": "seg_1", "name": "Renamed"})
    )
    assert client.segments.update("seg_1", name="Renamed").name == "Renamed"
    assert json.loads(_last(update).content) == {"name": "Renamed"}

    delete = respx.delete(f"{BASE_URL}/segments/seg_1").mock(
        return_value=httpx.Response(204)
    )
    assert client.segments.delete("seg_1").id is None
    assert _last(delete).method == "DELETE"


@respx.mock
def test_members_overrides_and_campaign(client: Warmbly) -> None:
    members = respx.post(f"{BASE_URL}/segments/seg_1/members").mock(
        return_value=httpx.Response(200, json={"updated": 2})
    )
    assert (
        client.segments.set_members(
            "seg_1", contacts=["c1", "c2"], mode="include"
        ).updated
        == 2
    )
    assert json.loads(_last(members).content) == {
        "contacts": ["c1", "c2"],
        "mode": "include",
    }

    lookup = respx.post(f"{BASE_URL}/segments/seg_1/members/lookup").mock(
        return_value=httpx.Response(200, json={"data": {"c1": "include"}})
    )
    modes = client.segments.member_modes("seg_1", contacts=["c1"])
    assert modes.data == {"c1": "include"}
    assert json.loads(_last(lookup).content) == {"contacts": ["c1"]}

    overrides = respx.get(f"{BASE_URL}/segments/seg_1/overrides").mock(
        return_value=httpx.Response(
            200, json=_page([{"contact_id": "c1", "mode": "exclude"}])
        )
    )
    pinned = list(client.segments.overrides("seg_1"))
    assert pinned[0].mode == "exclude"
    assert _last(overrides).url.path == "/v1/segments/seg_1/overrides"

    add = respx.post(f"{BASE_URL}/segments/seg_1/add-to-campaign").mock(
        return_value=httpx.Response(
            200, json={"campaign_id": "camp_1", "added": 3, "members": 9}
        )
    )
    result = client.segments.add_to_campaign("seg_1", campaign_id="camp_1")
    assert (result.added, result.members) == (3, 9)
    assert json.loads(_last(add).content) == {"campaign_id": "camp_1"}


@respx.mock
@pytest.mark.anyio
async def test_segments_async(aclient: AsyncWarmbly) -> None:
    listing = respx.get(f"{BASE_URL}/segments").mock(
        return_value=httpx.Response(200, json=_page([{"id": "seg_1"}]))
    )
    assert [s.id async for s in aclient.segments.list()] == ["seg_1"]
    assert _last(listing).url.path == "/v1/segments"

    fields = respx.get(f"{BASE_URL}/segments/fields").mock(
        return_value=httpx.Response(200, json=_page([{"field": "email"}]))
    )
    page = await aclient.segments.fields()
    assert page.data[0].field == "email"
    assert _last(fields).method == "GET"

    preview = respx.post(f"{BASE_URL}/segments/preview").mock(
        return_value=httpx.Response(200, json={"contact_count": 7})
    )
    assert (
        await aclient.segments.preview(match="all", conditions=CONDITIONS)
    ).contact_count == 7
    assert json.loads(_last(preview).content) == {
        "match": "all",
        "conditions": CONDITIONS,
    }

    create = respx.post(f"{BASE_URL}/segments").mock(
        return_value=httpx.Response(201, json={"id": "seg_2"})
    )
    assert (
        await aclient.segments.create(name="B", conditions=CONDITIONS)
    ).id == "seg_2"
    assert _last(create).method == "POST"

    retrieve = respx.get(f"{BASE_URL}/segments/seg_2").mock(
        return_value=httpx.Response(200, json={"id": "seg_2"})
    )
    assert (await aclient.segments.retrieve("seg_2")).id == "seg_2"
    assert _last(retrieve).method == "GET"

    update = respx.patch(f"{BASE_URL}/segments/seg_2").mock(
        return_value=httpx.Response(200, json={"id": "seg_2", "match": "any"})
    )
    assert (await aclient.segments.update("seg_2", match="any")).match == "any"
    assert json.loads(_last(update).content) == {"match": "any"}

    delete = respx.delete(f"{BASE_URL}/segments/seg_2").mock(
        return_value=httpx.Response(204)
    )
    await aclient.segments.delete("seg_2")
    assert _last(delete).method == "DELETE"

    members = respx.post(f"{BASE_URL}/segments/seg_2/members").mock(
        return_value=httpx.Response(200, json={"updated": 1})
    )
    assert (
        await aclient.segments.set_members("seg_2", contacts=["c1"], mode="auto")
    ).updated == 1
    assert _last(members).method == "POST"

    lookup = respx.post(f"{BASE_URL}/segments/seg_2/members/lookup").mock(
        return_value=httpx.Response(200, json={"data": {"c1": "auto"}})
    )
    assert (await aclient.segments.member_modes("seg_2", contacts=["c1"])).data == {
        "c1": "auto"
    }
    assert _last(lookup).url.path == "/v1/segments/seg_2/members/lookup"

    overrides = respx.get(f"{BASE_URL}/segments/seg_2/overrides").mock(
        return_value=httpx.Response(200, json=_page([{"contact_id": "c1"}]))
    )
    assert [o.contact_id async for o in aclient.segments.overrides("seg_2")] == ["c1"]
    assert _last(overrides).method == "GET"

    add = respx.post(f"{BASE_URL}/segments/seg_2/add-to-campaign").mock(
        return_value=httpx.Response(200, json={"campaign_id": "camp_1", "added": 1})
    )
    assert (
        await aclient.segments.add_to_campaign("seg_2", campaign_id="camp_1")
    ).added == 1
    assert _last(add).url.path == "/v1/segments/seg_2/add-to-campaign"
