"""Internal utilities for the Warmbly SDK."""

from __future__ import annotations

from ._logs import logger, redact
from ._scopes import (
    ALL_SCOPES,
    FULL_ACCESS_SCOPES,
    READ_ONLY_SCOPES,
    SCOPES,
    Scope,
    mask_to_scopes,
    scopes_to_mask,
)
from ._transform import drop_not_given

__all__ = [
    "ALL_SCOPES",
    "FULL_ACCESS_SCOPES",
    "READ_ONLY_SCOPES",
    "SCOPES",
    "Scope",
    "drop_not_given",
    "logger",
    "mask_to_scopes",
    "redact",
    "scopes_to_mask",
]
