"""Tests for the ``forms`` resource, sync and async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"

FIELDS = [{"id": "email", "type": "email", "label": "Work email", "required": True}]


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
def test_crud_and_config(client: Warmbly) -> None:
    listing = respx.get(f"{BASE_URL}/forms").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                [
                    {
                        "id": "frm_1",
                        "name": "Demo request",
                        "status": "published",
                        "public_id": "abc123",
                        "share_url": "https://forms.acme.com/abc123",
                        "submissions_count": 4,
                    }
                ]
            ),
        )
    )
    forms = list(client.forms.list())
    assert forms[0].share_url == "https://forms.acme.com/abc123"
    assert forms[0].submissions_count == 4
    assert _last(listing).url.path == "/v1/forms"

    config = respx.get(f"{BASE_URL}/forms/config").mock(
        return_value=httpx.Response(
            200,
            json={"base_url": "https://forms.warmbly.com", "captcha_available": False},
        )
    )
    assert client.forms.config().captcha_available is False
    assert _last(config).url.path == "/v1/forms/config"

    create = respx.post(f"{BASE_URL}/forms").mock(
        return_value=httpx.Response(201, json={"id": "frm_1", "name": "Demo request"})
    )
    assert client.forms.create(name="Demo request").id == "frm_1"
    assert json.loads(_last(create).content) == {"name": "Demo request"}

    retrieve = respx.get(f"{BASE_URL}/forms/frm_1").mock(
        return_value=httpx.Response(200, json={"id": "frm_1"})
    )
    assert client.forms.retrieve("frm_1").id == "frm_1"
    assert _last(retrieve).method == "GET"

    update = respx.patch(f"{BASE_URL}/forms/frm_1").mock(
        return_value=httpx.Response(200, json={"id": "frm_1", "status": "published"})
    )
    form = client.forms.update(
        "frm_1",
        status="published",
        fields=FIELDS,
        campaign_id=None,
        category_ids=["cat_1"],
        captcha_enabled=True,
    )
    assert form.status == "published"
    assert json.loads(_last(update).content) == {
        "status": "published",
        "fields": FIELDS,
        "campaign_id": None,
        "category_ids": ["cat_1"],
        "captcha_enabled": True,
    }

    delete = respx.delete(f"{BASE_URL}/forms/frm_1").mock(
        return_value=httpx.Response(204)
    )
    assert client.forms.delete("frm_1").deleted is None
    assert _last(delete).method == "DELETE"


@respx.mock
def test_submissions_stats_and_links(client: Warmbly) -> None:
    subs = respx.get(f"{BASE_URL}/forms/frm_1/submissions").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                [
                    {
                        "id": "sub_1",
                        "data": {"email": "a@example.com"},
                        "form_id": "frm_1",
                    }
                ]
            ),
        )
    )
    submissions = list(client.forms.list_submissions("frm_1", limit=10))
    assert submissions[0].data == {"email": "a@example.com"}
    assert _last(subs).url.params.get("limit") == "10"

    delete_sub = respx.delete(f"{BASE_URL}/forms/frm_1/submissions/sub_1").mock(
        return_value=httpx.Response(204)
    )
    client.forms.delete_submission("frm_1", "sub_1")
    assert _last(delete_sub).url.path == "/v1/forms/frm_1/submissions/sub_1"

    stats = respx.get(f"{BASE_URL}/forms/frm_1/stats").mock(
        return_value=httpx.Response(
            200,
            json={
                "totals": {"views": 100, "starts": 40, "submissions": 12},
                "daily": [],
                "pages": [{"page_index": 0, "reached": 100}],
                "sources": [],
                "countries": [],
                "devices": [],
                "campaigns": [],
                "identified": [],
            },
        )
    )
    report = client.forms.stats("frm_1", range="7d")
    assert report.totals is not None
    assert report.totals.views == 100
    assert _last(stats).url.params.get("range") == "7d"

    link = respx.get(f"{BASE_URL}/forms/frm_1/links/con_1").mock(
        return_value=httpx.Response(200, json={"url": "https://f.acme.com/a?t=tok"})
    )
    assert client.forms.mint_link("frm_1", "con_1").url.endswith("?t=tok")
    assert _last(link).url.path == "/v1/forms/frm_1/links/con_1"


@respx.mock
def test_assets_and_domain(client: Warmbly) -> None:
    upload = respx.post(f"{BASE_URL}/forms/frm_1/assets/logo").mock(
        return_value=httpx.Response(200, json={"id": "frm_1", "logo_url": "u"})
    )
    form = client.forms.upload_asset(
        "frm_1",
        "logo",
        file=b"png-bytes",
        filename="logo.png",
        content_type="image/png",
    )
    assert form.logo_url == "u"
    request = _last(upload)
    assert request.method == "POST"
    assert b"logo.png" in request.content

    remove = respx.delete(f"{BASE_URL}/forms/frm_1/assets/cover").mock(
        return_value=httpx.Response(200, json={"id": "frm_1", "cover_url": ""})
    )
    assert client.forms.delete_asset("frm_1", "cover").cover_url == ""
    assert _last(remove).url.path == "/v1/forms/frm_1/assets/cover"

    read = respx.get(f"{BASE_URL}/forms/domain").mock(
        return_value=httpx.Response(
            200,
            json={"forms_domain": "", "status": "unset", "cname_target": "f.wb.com"},
        )
    )
    assert client.forms.domain().status == "unset"
    assert _last(read).url.path == "/v1/forms/domain"

    write = respx.put(f"{BASE_URL}/forms/domain").mock(
        return_value=httpx.Response(
            200, json={"forms_domain": "forms.acme.com", "status": "not_found"}
        )
    )
    assert client.forms.set_domain(forms_domain="forms.acme.com").status == "not_found"
    assert json.loads(_last(write).content) == {"forms_domain": "forms.acme.com"}

    verify = respx.post(f"{BASE_URL}/forms/domain/verify").mock(
        return_value=httpx.Response(
            200, json={"forms_domain_verified": True, "status": "verified"}
        )
    )
    assert client.forms.verify_domain().forms_domain_verified is True
    assert _last(verify).url.path == "/v1/forms/domain/verify"


@respx.mock
@pytest.mark.anyio
async def test_forms_async(aclient: AsyncWarmbly) -> None:
    listing = respx.get(f"{BASE_URL}/forms").mock(
        return_value=httpx.Response(200, json=_page([{"id": "frm_1"}]))
    )
    assert [f.id async for f in aclient.forms.list()] == ["frm_1"]
    assert _last(listing).method == "GET"

    config = respx.get(f"{BASE_URL}/forms/config").mock(
        return_value=httpx.Response(200, json={"captcha_available": True})
    )
    assert (await aclient.forms.config()).captcha_available is True
    assert _last(config).url.path == "/v1/forms/config"

    create = respx.post(f"{BASE_URL}/forms").mock(
        return_value=httpx.Response(201, json={"id": "frm_2"})
    )
    assert (await aclient.forms.create(name="B")).id == "frm_2"
    assert _last(create).method == "POST"

    retrieve = respx.get(f"{BASE_URL}/forms/frm_2").mock(
        return_value=httpx.Response(200, json={"id": "frm_2"})
    )
    assert (await aclient.forms.retrieve("frm_2")).id == "frm_2"
    assert _last(retrieve).method == "GET"

    update = respx.patch(f"{BASE_URL}/forms/frm_2").mock(
        return_value=httpx.Response(200, json={"id": "frm_2", "name": "B2"})
    )
    assert (
        await aclient.forms.update(
            "frm_2",
            name="B2",
            design={"theme": "midnight"},
            success_message="Thanks",
            redirect_url="https://acme.com/thanks",
            allowed_domains=["acme.com"],
        )
    ).name == "B2"
    assert json.loads(_last(update).content) == {
        "name": "B2",
        "design": {"theme": "midnight"},
        "success_message": "Thanks",
        "redirect_url": "https://acme.com/thanks",
        "allowed_domains": ["acme.com"],
    }

    delete = respx.delete(f"{BASE_URL}/forms/frm_2").mock(
        return_value=httpx.Response(204)
    )
    await aclient.forms.delete("frm_2")
    assert _last(delete).method == "DELETE"

    subs = respx.get(f"{BASE_URL}/forms/frm_2/submissions").mock(
        return_value=httpx.Response(200, json=_page([{"id": "sub_1"}]))
    )
    assert [s.id async for s in aclient.forms.list_submissions("frm_2")] == ["sub_1"]
    assert _last(subs).method == "GET"

    delete_sub = respx.delete(f"{BASE_URL}/forms/frm_2/submissions/sub_1").mock(
        return_value=httpx.Response(204)
    )
    await aclient.forms.delete_submission("frm_2", "sub_1")
    assert _last(delete_sub).method == "DELETE"

    stats = respx.get(f"{BASE_URL}/forms/frm_2/stats").mock(
        return_value=httpx.Response(200, json={"totals": {"views": 3}})
    )
    report = await aclient.forms.stats("frm_2")
    assert report.totals is not None
    assert report.totals.views == 3
    assert "range" not in _last(stats).url.params

    link = respx.get(f"{BASE_URL}/forms/frm_2/links/con_1").mock(
        return_value=httpx.Response(200, json={"url": "https://f/x"})
    )
    assert (await aclient.forms.mint_link("frm_2", "con_1")).url == "https://f/x"
    assert _last(link).method == "GET"

    upload = respx.post(f"{BASE_URL}/forms/frm_2/assets/background").mock(
        return_value=httpx.Response(200, json={"id": "frm_2", "background_url": "b"})
    )
    form = await aclient.forms.upload_asset(
        "frm_2", "background", file=b"jpg", filename="bg.jpg"
    )
    assert form.background_url == "b"
    assert _last(upload).method == "POST"

    remove = respx.delete(f"{BASE_URL}/forms/frm_2/assets/logo").mock(
        return_value=httpx.Response(200, json={"id": "frm_2"})
    )
    await aclient.forms.delete_asset("frm_2", "logo")
    assert _last(remove).method == "DELETE"

    read = respx.get(f"{BASE_URL}/forms/domain").mock(
        return_value=httpx.Response(200, json={"status": "verified"})
    )
    assert (await aclient.forms.domain()).status == "verified"
    assert _last(read).method == "GET"

    write = respx.put(f"{BASE_URL}/forms/domain").mock(
        return_value=httpx.Response(200, json={"forms_domain": ""})
    )
    assert (await aclient.forms.set_domain(forms_domain="")).forms_domain == ""
    assert json.loads(_last(write).content) == {"forms_domain": ""}

    verify = respx.post(f"{BASE_URL}/forms/domain/verify").mock(
        return_value=httpx.Response(200, json={"status": "wrong_target"})
    )
    assert (await aclient.forms.verify_domain()).status == "wrong_target"
    assert _last(verify).method == "POST"
