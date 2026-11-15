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
    "mask_to_scopes",
    "scopes_to_mask",
]

# The 32 permission bits, in declaration order (matches the backend bitmask).
# The ``agency_*`` bits are held only by agency API keys (``wmagency_``).
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
    "ai_agent": 1 << 22,
    "ai_research": 1 << 23,
    "connect_emails": 1 << 24,
    "manage_reports": 1 << 25,
    "agency_read": 1 << 26,
    "agency_manage_clients": 1 << 27,
    "agency_read_usage": 1 << 28,
    "agency_transfer_ai": 1 << 29,
    "import_tools": 1 << 30,
    "agency_migrate": 1 << 31,
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
    "ai_agent",
    "ai_research",
    "connect_emails",
    "manage_reports",
    "agency_read",
    "agency_manage_clients",
    "agency_read_usage",
    "agency_transfer_ai",
    "import_tools",
    "agency_migrate",
]

AGENCY_SCOPES: int = sum(
    bit for name, bit in SCOPES.items() if name.startswith("agency_")
)
"""Every agency scope. Only an agency API key holds these."""

ALL_SCOPES: int = sum(SCOPES.values()) & ~AGENCY_SCOPES
"""A bitmask granting every workspace scope (a workspace key's widest mask)."""

READ_ONLY_SCOPES: int = sum(
    bit for name, bit in SCOPES.items() if name.startswith("read_")
)
"""The backend's ``read_only`` preset: every read scope and nothing else."""

FULL_ACCESS_SCOPES: int = ALL_SCOPES & ~SCOPES["connect_emails"]
"""The backend's ``full_access`` preset: every workspace scope except
``connect_emails``, which is granted only on purpose."""

APP_GRANTABLE_SCOPES: int = ALL_SCOPES & ~(
    SCOPES["api_keys"] | SCOPES["connect_emails"]
)
"""Every scope an OAuth app may be granted. ``api_keys`` and ``connect_emails``
(mailbox credentials) stay with people."""

AGENCY_KEY_WORKSPACE_SCOPES: int = ALL_SCOPES & ~(
    SCOPES["api_keys"] | SCOPES["realtime_subscribe"] | SCOPES["connect_emails"]
)
"""The workspace scopes an agency key may use in a client workspace. It manages
no keys, opens no realtime socket and takes no mailbox credentials."""

AGENCY_KEY_GRANTABLE_SCOPES: int = AGENCY_KEY_WORKSPACE_SCOPES | AGENCY_SCOPES
"""Every scope an agency API key may carry."""

ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "read_emails": ("view_campaigns",),
    "read_campaigns": ("view_campaigns",),
    "read_contacts": ("view_contacts",),
    "read_unibox": ("access_unibox",),
    "read_analytics": ("view_analytics",),
    "write_emails": ("manage_emails",),
    "write_campaigns": ("manage_campaigns",),
    "write_contacts": ("manage_contacts",),
    "write_unibox": ("access_unibox",),
    "bulk_contacts": ("manage_contacts",),
    "bulk_campaigns": ("manage_campaigns",),
    "realtime_subscribe": (),
    "webhooks": ("manage_settings",),
    "api_keys": ("manage_api_keys",),
    "send_campaigns": ("send_campaigns",),
    "read_templates": ("view_campaigns",),
    "write_templates": ("manage_campaigns",),
    "read_crm": ("view_contacts",),
    "write_crm": ("manage_contacts",),
    "read_audit_logs": ("view_analytics",),
    "integrations": ("use_integrations",),
    "warmup_routing": ("manage_settings",),
    "ai_agent": ("use_ai",),
    "ai_research": ("view_contacts", "use_ai"),
    "connect_emails": ("manage_emails",),
    "manage_reports": ("view_analytics", "manage_campaigns"),
    "import_tools": ("manage_contacts",),
}
"""The team-role permissions a member needs to delegate each scope.

A key or OAuth grant acts for a member, so it never holds a scope the member's
role does not cover. An empty tuple means any member. The workspace owner
covers every scope. Agency scopes are absent: they follow the agency staff
role, not a workspace role.
"""


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
