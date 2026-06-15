"""Tests for the shared response model and ``construct_type`` helper."""

from __future__ import annotations

import json

import pydantic
import pytest

from warmbly import BaseModel
from warmbly._models import construct_type


class Sample(BaseModel):
    a: int
    b: str = "default"


class Nested(BaseModel):
    inner: Sample
    label: str


# ---------------------------------------------------------------------------
# BaseModel: extra='allow' + conveniences
# ---------------------------------------------------------------------------


def test_basemodel_tolerates_unknown_fields() -> None:
    model = Sample(a=1, unexpected="kept", another=42)
    # Unknown fields are preserved rather than dropped or raising.
    assert model.unexpected == "kept"
    assert model.another == 42
    assert model.a == 1


def test_basemodel_populate_by_name_and_extra_in_validate() -> None:
    model = Sample.model_validate({"a": 7, "surprise": [1, 2, 3]})
    assert model.a == 7
    assert model.surprise == [1, 2, 3]


def test_to_dict_returns_json_compatible_dict() -> None:
    model = Sample(a=1, b="x", extra="y")
    result = model.to_dict()
    assert isinstance(result, dict)
    assert result == {"a": 1, "b": "x", "extra": "y"}
    # Must be JSON-serializable.
    json.dumps(result)


def test_to_json_serializes_to_string() -> None:
    model = Sample(a=2, b="hi")
    as_str = model.to_json()
    assert isinstance(as_str, str)
    assert json.loads(as_str) == {"a": 2, "b": "hi"}


def test_to_json_indent_none_is_compact() -> None:
    model = Sample(a=2, b="hi")
    compact = model.to_json(indent=None)
    assert "\n" not in compact
    assert json.loads(compact) == {"a": 2, "b": "hi"}


def test_request_id_defaults_to_none() -> None:
    model = Sample(a=1)
    assert model.request_id is None


# ---------------------------------------------------------------------------
# construct_type: model
# ---------------------------------------------------------------------------


def test_construct_type_model_validates_and_attaches_request_id() -> None:
    model = construct_type(Sample, {"a": 5, "b": "z"}, request_id="req_123")
    assert isinstance(model, Sample)
    assert model.a == 5
    assert model.b == "z"
    assert model.request_id == "req_123"


def test_construct_type_model_request_id_optional() -> None:
    model = construct_type(Sample, {"a": 5})
    assert isinstance(model, Sample)
    assert model.request_id is None


def test_construct_type_nested_model() -> None:
    model = construct_type(
        Nested,
        {"inner": {"a": 1, "b": "deep"}, "label": "top"},
        request_id="rq",
    )
    assert isinstance(model, Nested)
    assert isinstance(model.inner, Sample)
    assert model.inner.a == 1
    assert model.label == "top"
    assert model.request_id == "rq"


# ---------------------------------------------------------------------------
# construct_type: list[Model]
# ---------------------------------------------------------------------------


def test_construct_type_list_of_models() -> None:
    items = construct_type(
        list[Sample],
        [{"a": 1}, {"a": 2, "b": "two"}],
        request_id="page_req",
    )
    assert isinstance(items, list)
    assert len(items) == 2
    assert all(isinstance(item, Sample) for item in items)
    assert items[0].a == 1
    assert items[1].b == "two"
    # The request id is propagated to each constructed element.
    assert all(item.request_id == "page_req" for item in items)


def test_construct_type_empty_list() -> None:
    items = construct_type(list[Sample], [])
    assert items == []


def test_construct_type_list_of_primitives() -> None:
    items = construct_type(list[int], [1, 2, 3])
    assert items == [1, 2, 3]


# ---------------------------------------------------------------------------
# construct_type: None
# ---------------------------------------------------------------------------


def test_construct_type_none_cast_to() -> None:
    assert construct_type(None, {"a": 1}) is None


def test_construct_type_nonetype_cast_to() -> None:
    assert construct_type(type(None), {"a": 1}) is None


# ---------------------------------------------------------------------------
# construct_type: primitive passthrough
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("cast_to", "data"),
    [
        (int, 42),
        (str, "hello"),
        (float, 3.14),
        (bool, True),
        (dict, {"raw": "dict"}),
    ],
)
def test_construct_type_primitive_passthrough(cast_to: type, data: object) -> None:
    assert construct_type(cast_to, data) == data


# ---------------------------------------------------------------------------
# construct_type: forward compatibility (validation failure -> no raise)
# ---------------------------------------------------------------------------


def test_construct_type_forward_compat_does_not_raise() -> None:
    # 'a' should be an int but the server sent a string; we must not raise.
    model = construct_type(
        Sample,
        {"a": "not-an-int", "future_field": "value"},
        request_id="fc",
    )
    assert isinstance(model, Sample)
    # Best-effort construction keeps the raw data around.
    assert model.a == "not-an-int"
    assert model.future_field == "value"
    assert model.request_id == "fc"


def test_construct_type_forward_compat_strict_validate_would_raise() -> None:
    # Sanity check: ordinary validation *would* raise for this payload, proving
    # construct_type's fallback is what saves us above.
    with pytest.raises(pydantic.ValidationError):
        Sample.model_validate({"a": "not-an-int"})


def test_construct_type_forward_compat_non_dict_payload() -> None:
    # A wholly unexpected shape (not even a dict) still produces a model.
    model = construct_type(Sample, ["unexpected", "shape"], request_id="weird")
    assert isinstance(model, Sample)
    assert model.request_id == "weird"
