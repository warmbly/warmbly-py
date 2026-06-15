"""The shared response model and the response-construction helper.

Every response object subclasses :class:`BaseModel`, which is configured for
*forward compatibility*: unknown fields are preserved (``extra="allow"``) so a
server that adds fields never breaks an older SDK. :func:`construct_type` turns
raw JSON into the requested model (or primitive), attaching the originating
``X-Request-Id`` to models for support and debugging.
"""

from __future__ import annotations

from typing import Any, TypeVar, Union, get_args, get_origin

import pydantic
from pydantic import ConfigDict

__all__ = ["BaseModel", "construct_type"]

_T = TypeVar("_T")


class BaseModel(pydantic.BaseModel):
    """Base class for all Warmbly response models.

    Configured to tolerate unknown fields and to allow population by either
    field name or alias. Adds :meth:`to_dict`/:meth:`to_json` conveniences and
    carries the response's request id on :attr:`_request_id`.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        protected_namespaces=(),
    )

    _request_id: str | None = pydantic.PrivateAttr(default=None)

    @property
    def request_id(self) -> str | None:
        """The ``X-Request-Id`` of the response that produced this object."""
        return self._request_id

    def to_dict(self) -> dict[str, Any]:
        """Return the model as a JSON-compatible ``dict``."""
        return self.model_dump(mode="json")

    def to_json(self, *, indent: int | None = 2) -> str:
        """Return the model serialized to a JSON string."""
        return self.model_dump_json(indent=indent)


def construct_type(
    cast_to: type[_T],
    data: object,
    *,
    request_id: str | None = None,
) -> _T:
    """Build *cast_to* from raw *data*, tolerating unexpected shapes.

    Handles ``BaseModel`` subclasses (validated, request id attached), typed
    containers such as ``list[Model]``, ``None``, and primitive pass-throughs.
    On a validation error the data is returned best-effort rather than raising,
    so a single unexpected field never breaks an otherwise usable response.
    """
    if cast_to is None or cast_to is type(None):
        return None  # type: ignore[return-value]

    origin = get_origin(cast_to)

    # Unions: try each member, fall back to the raw data.
    if origin is Union:
        for arg in get_args(cast_to):
            try:
                return construct_type(arg, data, request_id=request_id)  # type: ignore[no-any-return]
            except Exception:  # noqa: BLE001 - lenient on purpose
                continue
        return data  # type: ignore[return-value]

    # Typed sequences, e.g. list[Model].
    if origin in (list, tuple) and isinstance(data, (list, tuple)):
        (item_type,) = get_args(cast_to) or (object,)
        built = [
            construct_type(item_type, item, request_id=request_id) for item in data
        ]
        return origin(built)  # type: ignore[no-any-return]

    if isinstance(cast_to, type) and issubclass(cast_to, BaseModel):
        try:
            model = cast_to.model_validate(data)
        except pydantic.ValidationError:
            # Forward-compat: never crash on an unexpected payload shape.
            model = cast_to.model_construct(**data) if isinstance(data, dict) else cast_to.model_construct()
        model._request_id = request_id
        return model  # type: ignore[return-value]

    if isinstance(cast_to, type) and issubclass(cast_to, pydantic.BaseModel):
        return cast_to.model_validate(data)  # type: ignore[return-value]

    # Primitives / dict / Any: pass through unchanged.
    return data  # type: ignore[return-value]
