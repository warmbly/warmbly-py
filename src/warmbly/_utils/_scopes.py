"""Scope <-> bitmask helpers.

Warmbly expresses API permissions both as human-readable scope strings
(``"read_campaigns"``) and as a single ``uint64`` bitmask. A scope string is
exactly the lowercased permission name, and each maps to one bit. These helpers
convert between the two representations so callers can work with readable names
while the API receives the integer mask it expects.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

__all__ = ["ALL_SCOPES", "SCOPES", "Scope", "mask_to_scopes", "scopes_to_mask"]

# The 22 permission bits, in declaration order (matches the backend bitmask).
SCOPES: dict[str, int] = {
    "read_emails": 1 << 0,
    "read_campaigns": 1 << 1,
    "read_contacts": 1 << 2,
    "read_unibox": 1 << 3,
    "read_analytics": 1 << 4,
    "write_emails": 1 << 5,
    "write_campaigns": 1 << 6,
    "write_contacts": 1 << 7,
    "write_unibox": 1 << 8,
    "bulk_contacts": 1 << 9,
    "bulk_campaigns": 1 << 10,
    "realtime_subscribe": 1 << 11,
    "webhooks": 1 << 12,
    "api_keys": 1 << 13,
    "send_campaigns": 1 << 14,
    "read_templates": 1 << 15,
    "write_templates": 1 << 16,
    "read_crm": 1 << 17,
    "write_crm": 1 << 18,
    "read_audit_logs": 1 << 19,
    "integrations": 1 << 20,
    "warmup_routing": 1 << 21,
}

Scope = Literal[
    "read_emails",
    "read_campaigns",
    "read_contacts",
    "read_unibox",
    "read_analytics",
    "write_emails",
    "write_campaigns",
    "write_contacts",
    "write_unibox",
    "bulk_contacts",
    "bulk_campaigns",
    "realtime_subscribe",
    "webhooks",
    "api_keys",
    "send_campaigns",
    "read_templates",
    "write_templates",
    "read_crm",
    "write_crm",
    "read_audit_logs",
    "integrations",
    "warmup_routing",
]

ALL_SCOPES: int = sum(SCOPES.values())
"""A bitmask granting every scope."""


def scopes_to_mask(names: Iterable[str]) -> int:
    """Convert an iterable of scope names into a ``uint64`` bitmask.

    Args:
        names: Scope strings such as ``"read_campaigns"``.

    Returns:
        The combined bitmask.

    Raises:
        ValueError: If any name is not a recognized scope.
    """
    mask = 0
    for name in names:
        try:
            mask |= SCOPES[name]
        except KeyError:
            raise ValueError(f"Unknown scope: {name!r}") from None
    return mask


def mask_to_scopes(mask: int) -> list[str]:
    """Convert a ``uint64`` bitmask into the list of scope names it grants."""
    return [name for name, bit in SCOPES.items() if mask & bit]
