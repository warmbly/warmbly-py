"""Request payload transforms."""

from __future__ import annotations

from typing import Mapping

from .._types import NotGiven

__all__ = ["drop_not_given"]


def drop_not_given(data: Mapping[str, object]) -> dict[str, object]:
    """Return a new dict with every :data:`~warmbly.NOT_GIVEN` value removed.

    Resource methods default optional parameters to ``NOT_GIVEN`` and pass the
    full argument mapping through; this strips the omitted ones so they are not
    serialized, while preserving keys whose value is an explicit ``None``.
    """
    return {
        key: value
        for key, value in data.items()
        if not isinstance(value, NotGiven)
    }
