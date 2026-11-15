"""Internal utilities for the Warmbly SDK."""

from __future__ import annotations

from ._logs import logger, redact
from ._scopes import (
    AGENCY_KEY_GRANTABLE_SCOPES,
    AGENCY_KEY_WORKSPACE_SCOPES,
    AGENCY_SCOPES,
    ALL_SCOPES,
    APP_GRANTABLE_SCOPES,
    FULL_ACCESS_SCOPES,
    READ_ONLY_SCOPES,
    ROLE_PERMISSIONS,
    SCOPES,
    Scope,
    mask_to_scopes,
    scopes_to_mask,
)
from ._transform import drop_not_given

__all__ = [
    "AGENCY_KEY_GRANTABLE_SCOPES",
    "AGENCY_KEY_WORKSPACE_SCOPES",
    "AGENCY_SCOPES",
    "ALL_SCOPES",
    "APP_GRANTABLE_SCOPES",
    "FULL_ACCESS_SCOPES",
    "READ_ONLY_SCOPES",
    "ROLE_PERMISSIONS",
    "SCOPES",
    "Scope",
    "drop_not_given",
    "logger",
    "mask_to_scopes",
    "redact",
    "scopes_to_mask",
]
