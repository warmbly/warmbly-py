from __future__ import annotations

from typing import Any, Union

import pydantic
import pytest

from warmbly._models import BaseModel, construct_type
from warmbly._types import (
    NOT_GIVEN,
    NotGiven,
    Omit,
    RequestOptions,
    is_given,
)

# --- helper models -------------------------------------------------------


class SampleModel(BaseModel):
    name: str
    count: int


class PlainModel(pydantic.BaseModel):
    """A non-warmbly pydantic model."""

    label: str


class AnotherPlainModel(pydantic.BaseModel):
    """A second distinct non-warmbly pydantic model (for Union members)."""

    other: str


# --- construct_type: None branch ----------------------------------------


def test_construct_type_none_cast() -> None:
    assert construct_type(None, {"anything": 1}) is None  # type: ignore[arg-type]


def test_construct_type_type_none() -> None:
    assert construct_type(type(None), {"anything": 1}) is None  # type: ignore[arg-type]


# --- construct_type: Union ----------------------------------------------


def test_union_first_fails_second_succeeds() -> None:
    # Validating a dict against PlainModel (missing required `label`) raises,
    # so the loop falls through to SampleModel which succeeds.
    result = construct_type(
        # Keep ``typing.Union`` here, not ``X | Y``: ``get_origin(X | Y)`` is
        # ``types.UnionType`` (not ``typing.Union``) on 3.10-3.13, which would
        # bypass the exact ``construct_type`` branch this test targets.
        Union[PlainModel, SampleModel],  # type: ignore[arg-type]  # noqa: UP007
        {"name": "a", "count": 2},
        request_id="req-1",
    )
    assert isinstance(result, SampleModel)
    assert result.name == "a"
    assert result.count == 2
    assert result.request_id == "req-1"


def test_union_truly_all_fail_returns_raw() -> None:
    # Two distinct plain pydantic models (Union does not dedupe) validated
    # against incompatible data: model_validate raises for both, exhausting
    # the loop -> raw data returned unchanged.
    data = "not-a-dict-or-model"
    result = construct_type(
        Union[PlainModel, AnotherPlainModel],  # type: ignore[arg-type]  # noqa: UP007
        data,
    )
    assert result == data


# --- construct_type: list / tuple ---------------------------------------


def test_list_of_models() -> None:
    result = construct_type(
        list[SampleModel],
        [{"name": "a", "count": 1}, {"name": "b", "count": 2}],
        request_id="rid",
    )
    assert isinstance(result, list)
    assert all(isinstance(m, SampleModel) for m in result)
    assert result[1].name == "b"
    assert result[0].request_id == "rid"


def test_tuple_of_models_preserves_type() -> None:
    result = construct_type(
        tuple[SampleModel],
        ({"name": "x", "count": 9},),
    )
    assert isinstance(result, tuple)
    assert result[0].name == "x"


def test_list_without_args_defaults_to_object() -> None:
    # bare `list` has no get_args -> defaults item_type to object (passthrough).
    result = construct_type(list, [1, 2, 3])  # type: ignore[arg-type]
    assert result == [1, 2, 3]


# --- construct_type: BaseModel ------------------------------------------


def test_basemodel_valid_attaches_request_id() -> None:
    result = construct_type(SampleModel, {"name": "z", "count": 5}, request_id="abc")
    assert isinstance(result, SampleModel)
    assert result.request_id == "abc"


def test_basemodel_invalid_dict_falls_back_to_model_construct() -> None:
    # Missing required field -> ValidationError -> model_construct(**data).
    result = construct_type(SampleModel, {"name": "only"}, request_id="r")
    assert isinstance(result, SampleModel)
    assert result.name == "only"
    assert result.request_id == "r"


def test_basemodel_invalid_nondict_falls_back_to_empty_construct() -> None:
    # Non-dict invalid input -> model_construct() with no args.
    result = construct_type(SampleModel, "not a dict", request_id="r2")
    assert isinstance(result, SampleModel)
    assert result.request_id == "r2"


# --- construct_type: plain pydantic BaseModel ---------------------------


def test_plain_pydantic_model_uses_model_validate() -> None:
    result = construct_type(PlainModel, {"label": "hi"})
    assert isinstance(result, PlainModel)
    assert result.label == "hi"
    assert not isinstance(result, BaseModel)


# --- construct_type: passthrough ----------------------------------------


def test_primitive_passthrough() -> None:
    assert construct_type(int, 7) == 7  # type: ignore[arg-type]


def test_dict_passthrough() -> None:
    data = {"a": 1}
    assert construct_type(dict, data) == data  # type: ignore[arg-type]


def test_any_passthrough() -> None:
    assert construct_type(Any, "raw") == "raw"  # type: ignore[arg-type]


# --- BaseModel conveniences ---------------------------------------------


def test_to_dict() -> None:
    m = SampleModel(name="a", count=1)
    assert m.to_dict() == {"name": "a", "count": 1}


def test_to_json_default_indent() -> None:
    m = SampleModel(name="a", count=1)
    out = m.to_json()
    assert '"name"' in out
    assert "\n" in out  # indent=2 produces newlines


def test_to_json_no_indent() -> None:
    m = SampleModel(name="a", count=1)
    out = m.to_json(indent=None)
    assert "\n" not in out


def test_extra_allow_preserves_unknown_fields() -> None:
    m = SampleModel.model_validate({"name": "a", "count": 1, "surprise": "kept"})
    assert m.to_dict()["surprise"] == "kept"


def test_populate_by_name() -> None:
    class Aliased(BaseModel):
        field_name: str = pydantic.Field(alias="fieldName")

    by_name = Aliased.model_validate({"field_name": "v"})
    by_alias = Aliased.model_validate({"fieldName": "v"})
    assert by_name.field_name == "v"
    assert by_alias.field_name == "v"


def test_request_id_default_none() -> None:
    m = SampleModel(name="a", count=1)
    assert m.request_id is None


# --- _types: NotGiven / Omit / is_given ---------------------------------


def test_not_given_is_falsy() -> None:
    assert bool(NotGiven()) is False
    assert not NOT_GIVEN


def test_not_given_repr() -> None:
    assert repr(NOT_GIVEN) == "NOT_GIVEN"
    assert repr(NotGiven()) == "NOT_GIVEN"


def test_not_given_singleton() -> None:
    assert isinstance(NOT_GIVEN, NotGiven)


def test_omit_is_falsy_and_repr() -> None:
    assert bool(Omit()) is False
    assert repr(Omit()) == "Omit"


def test_is_given_not_given() -> None:
    assert is_given(NOT_GIVEN) is False


@pytest.mark.parametrize("value", [None, 0, "", "x", 42, [], object()])
def test_is_given_everything_else(value: object) -> None:
    assert is_given(value) is True  # type: ignore[arg-type]


def test_request_options_typeddict() -> None:
    opts: RequestOptions = {
        "headers": {"X-Test": "1"},
        "query": {"q": "v"},
        "max_retries": 3,
        "timeout": 1.0,
        "idempotency_key": "key",
        "extra_body": {"b": 2},
    }
    assert opts["max_retries"] == 3
    assert RequestOptions.__total__ is False
