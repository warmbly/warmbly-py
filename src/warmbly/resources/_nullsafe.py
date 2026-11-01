"""A response model that tolerates ``null`` where the server means "empty".

Go marshals a nil slice or map as ``null``. A model field declared as a
sequence or mapping with an empty default would reject that and make the whole
response fall back to an unvalidated shape, so :class:`NullSafeModel` drops
``null`` values for those fields before validation and lets the default apply.
"""

from __future__ import annotations

from typing import Any

from pydantic import model_validator

from .._models import BaseModel

__all__ = ["NullSafeModel"]


class NullSafeModel(BaseModel):
    """A :class:`~warmbly._models.BaseModel` that reads ``null`` collections as empty."""

    @model_validator(mode="before")
    @classmethod
    def _drop_null_collections(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        collections = {
            name
            for name, field in cls.model_fields.items()
            if not field.is_required() and field.default is not None
        }
        if not collections:
            return data
        return {k: v for k, v in data.items() if not (v is None and k in collections)}
