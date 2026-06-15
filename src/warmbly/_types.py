"""Core type primitives shared across the SDK.

This module deliberately keeps ``httpx`` out of the public type surface except
for the :data:`Timeout` configuration alias, which callers legitimately need to
construct. Everything else is expressed in terms of the standard library so the
underlying transport can be swapped without breaking user code.
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Literal,
    Mapping,
    TypeAlias,
    TypedDict,
    TypeVar,
    Union,
)

import httpx

if TYPE_CHECKING:
    from typing import Any

__all__ = [
    "NOT_GIVEN",
    "NotGiven",
    "NotGivenOr",
    "Omit",
    "is_given",
    "Headers",
    "Query",
    "Body",
    "Timeout",
    "RequestOptions",
]

_T = TypeVar("_T")


class NotGiven:
    """A sentinel for arguments the caller did not pass.

    Distinguishes "the caller omitted this argument" from "the caller
    explicitly passed ``None``". Optional parameters default to
    :data:`NOT_GIVEN`; passing ``None`` sends an explicit null to the API.

    ``NOT_GIVEN`` is falsy, so ``if value:`` and ``if not value:`` behave
    intuitively.
    """

    def __bool__(self) -> Literal[False]:
        return False

    def __repr__(self) -> str:
        return "NOT_GIVEN"


NOT_GIVEN = NotGiven()
"""The singleton :class:`NotGiven` sentinel."""

NotGivenOr: TypeAlias = Union[_T, NotGiven]
"""``NotGivenOr[T]`` is ``T`` or the :data:`NOT_GIVEN` sentinel."""


class Omit:
    """A sentinel that removes a default header for a single request.

    ``client.get(..., extra_headers={"Authorization": Omit()})`` drops the
    default header entirely rather than overriding it with an empty value.
    """

    def __bool__(self) -> Literal[False]:
        return False

    def __repr__(self) -> str:
        return "Omit"


def is_given(value: NotGivenOr[_T]) -> bool:
    """Return ``True`` unless *value* is the :data:`NOT_GIVEN` sentinel."""
    return not isinstance(value, NotGiven)


# Transport-facing aliases. ``Omit`` in a header mapping removes that header.
Headers: TypeAlias = Mapping[str, Union[str, "Omit"]]
Query: TypeAlias = Mapping[str, object]
Body: TypeAlias = object

# Timeout configuration. Aliased to httpx's well-tested implementation; this is
# the one place an httpx type is intentionally part of the public surface.
Timeout: TypeAlias = httpx.Timeout


class RequestOptions(TypedDict, total=False):
    """Per-request overrides accepted by every resource method."""

    headers: Headers
    query: Query
    max_retries: int
    timeout: "float | Timeout | None"
    idempotency_key: str
    extra_body: "Mapping[str, Any]"
