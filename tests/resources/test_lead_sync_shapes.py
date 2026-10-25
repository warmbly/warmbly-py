"""Lead sync: segment targeting and the preview and spreadsheet shapes."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
import respx
from _dual import BASE_URL, dual_client, items, last, page, v  # noqa: F401

SOURCE = {
    "id": "ls_1",
    "organization_id": "org_1",
    "created_by_user_id": "usr_1",
    "provider": "google_sheets",
    "connection_id": "conn_1",
    "sheet_id": "sh_1",
    "sheet_title": "Leads",
    "tab_title": "Sheet1",
    "has_header": True,
    "column_mapping": [{"index": 0, "target": "email"}],
    "dedup": "update",
    "target_campaign_id": "cmp_1",
    "category_ids": ["cat_1"],
    "segment_ids": ["seg_1", "seg_2"],
    "subscribed_default": True,
    "status": "idle",
}


@respx.mock
@pytest.mark.anyio
async def test_lead_sync_segments_and_shapes(dual: Any) -> None:
    c = dual.lead_sync

    listing = respx.get(f"{BASE_URL}/lead-sync/sources").mock(
        return_value=httpx.Response(200, json=page([SOURCE]))
    )
    src = (await items(c.list_sources(segment_id="seg_1")))[0]
    assert list(src.segment_ids) == ["seg_1", "seg_2"]
    assert src.sheet_id == "sh_1"
    assert last(listing).url.params["segment_id"] == "seg_1"
    assert "campaign_id" not in last(listing).url.params

    create = respx.post(f"{BASE_URL}/lead-sync/sources").mock(
        return_value=httpx.Response(201, json=SOURCE)
    )
    made = await v(
        c.create_source(
            connection_id="conn_1",
            sheet_id="sh_1",
            column_mapping=[{"index": 0, "target": "email"}],
            segment_ids=["seg_1", "seg_2"],
        )
    )
    assert list(made.segment_ids) == ["seg_1", "seg_2"]
    assert json.loads(last(create).content) == {
        "connection_id": "conn_1",
        "sheet_id": "sh_1",
        "column_mapping": [{"index": 0, "target": "email"}],
        "segment_ids": ["seg_1", "seg_2"],
    }

    patch = respx.patch(f"{BASE_URL}/lead-sync/sources/ls_1").mock(
        return_value=httpx.Response(200, json=SOURCE)
    )
    await v(c.update_source("ls_1", segment_ids=[]))
    assert json.loads(last(patch).content) == {"segment_ids": []}

    respx.post(f"{BASE_URL}/lead-sync/google/spreadsheet").mock(
        return_value=httpx.Response(
            200,
            json={
                "sheet_id": "sh_1",
                "title": "Leads",
                "tabs": [{"title": "Sheet1", "index": 0}],
            },
        )
    )
    sheet = await v(c.spreadsheet(connection_id="conn_1", sheet_id="sh_1"))
    assert sheet.sheet_id == "sh_1"
    assert sheet.title == "Leads"
    assert sheet.tabs[0]["index"] == 0

    respx.post(f"{BASE_URL}/lead-sync/google/preview").mock(
        return_value=httpx.Response(
            200,
            json={
                "filename": "Leads / Sheet1",
                "format": "sheets",
                "columns": ["Email", "Name"],
                "has_header": True,
                "sample_rows": [["a@x.com", "Ada"]],
                "total_rows": 1,
                "suggested_mapping": [{"index": 0, "target": "email"}],
                "inferred_columns": [1],
                "mapping_source": "suggested",
            },
        )
    )
    pv = await v(c.preview(connection_id="conn_1", sheet_id="sh_1"))
    assert list(pv.columns) == ["Email", "Name"]
    assert pv.has_header is True
    assert pv.sample_rows[0][0] == "a@x.com"
    assert pv.total_rows == 1
    assert pv.suggested_mapping[0]["target"] == "email"
    assert list(pv.inferred_columns) == [1]
    assert pv.mapping_source == "suggested"
    assert pv.filename == "Leads / Sheet1"
    assert pv.format == "sheets"
