"""Tests for the ``email_images`` resource."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx

from warmbly import AsyncWarmbly, Warmbly

BASE_URL = "https://api.warmbly.com/v1"

# Built from models.EmailImage (StorageKey is json:"-").
IMAGE: dict[str, Any] = {
    "id": "img_1",
    "organization_id": "org_1",
    "user_id": "usr_1",
    "filename": "logo.png",
    "mime_type": "image/png",
    "size": 2048,
    "width": 640,
    "height": 480,
    "url": "https://cdn.example.com/email-images/org_1/abc.png",
    "created_at": "2026-01-01T00:00:00Z",
}


@pytest.fixture
def client() -> Warmbly:
    return Warmbly(api_key="wmbly_test", base_url=BASE_URL, max_retries=0)


@pytest.fixture
def aclient() -> AsyncWarmbly:
    return AsyncWarmbly(api_key="wmbly_test", base_url=BASE_URL, max_retries=0)


def _assert_image(img: Any) -> None:
    assert img.id == "img_1"
    assert img.organization_id == "org_1"
    assert img.user_id == "usr_1"
    assert img.filename == "logo.png"
    assert img.mime_type == "image/png"
    assert img.size == 2048
    assert (img.width, img.height) == (640, 480)
    assert img.url == "https://cdn.example.com/email-images/org_1/abc.png"
    assert img.created_at == "2026-01-01T00:00:00Z"


@respx.mock
def test_list_pages_and_decodes(client: Warmbly) -> None:
    route = respx.get(f"{BASE_URL}/email-images").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [IMAGE],
                    "pagination": {"next_cursor": "c2", "has_more": True},
                },
            ),
            httpx.Response(
                200,
                json={
                    "data": [{**IMAGE, "id": "img_2", "user_id": None}],
                    "pagination": {"next_cursor": None, "has_more": False},
                },
            ),
        ]
    )

    images = list(client.email_images.list(limit=1))

    assert [i.id for i in images] == ["img_1", "img_2"]
    first, second = (c.request for c in route.calls)
    assert first.method == "GET"
    assert first.url.path == "/v1/email-images"
    assert first.url.params["limit"] == "1"
    assert second.url.params["cursor"] == "c2"
    _assert_image(images[0])
    assert images[1].user_id is None


@pytest.mark.anyio
@respx.mock
async def test_async_list(aclient: AsyncWarmbly) -> None:
    route = respx.get(f"{BASE_URL}/email-images").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [IMAGE],
                "pagination": {"next_cursor": None, "has_more": False},
            },
        )
    )

    images = [i async for i in aclient.email_images.list(cursor="abc")]

    assert route.calls.last.request.url.params["cursor"] == "abc"
    _assert_image(images[0])


@respx.mock
def test_upload_multipart(client: Warmbly) -> None:
    route = respx.post(f"{BASE_URL}/email-images").mock(
        return_value=httpx.Response(201, json=IMAGE)
    )

    img = client.email_images.upload(
        file=b"\x89PNG-bytes", filename="logo.png", content_type="image/png"
    )

    request = route.calls.last.request
    assert request.method == "POST"
    assert request.url.path == "/v1/email-images"
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert b'name="file"; filename="logo.png"' in request.content
    assert b"Content-Type: image/png" in request.content
    assert b"\x89PNG-bytes" in request.content
    _assert_image(img)


@pytest.mark.anyio
@respx.mock
async def test_async_upload(aclient: AsyncWarmbly) -> None:
    route = respx.post(f"{BASE_URL}/email-images").mock(
        return_value=httpx.Response(201, json=IMAGE)
    )

    img = await aclient.email_images.upload(
        file=b"GIF89a", filename="a.gif", content_type="image/gif"
    )

    assert b'filename="a.gif"' in route.calls.last.request.content
    _assert_image(img)


@respx.mock
def test_delete_handles_204(client: Warmbly) -> None:
    route = respx.delete(f"{BASE_URL}/email-images/img_1").mock(
        return_value=httpx.Response(204)
    )

    result = client.email_images.delete("img_1")

    assert route.calls.last.request.method == "DELETE"
    assert route.calls.last.request.url.path == "/v1/email-images/img_1"
    assert result is not None


@pytest.mark.anyio
@respx.mock
async def test_async_delete(aclient: AsyncWarmbly) -> None:
    route = respx.delete(f"{BASE_URL}/email-images/img_1").mock(
        return_value=httpx.Response(204)
    )
    await aclient.email_images.delete("img_1")
    assert route.calls.last.request.url.path == "/v1/email-images/img_1"


def test_unknown_fields_never_raise() -> None:
    from warmbly._models import construct_type
    from warmbly.resources.email_images import EmailImage

    img = construct_type(EmailImage, {"id": "i", "brand_new": 1, "width": "oops"})
    assert img is not None
