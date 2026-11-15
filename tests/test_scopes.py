"""Tests for the scope <-> bitmask helpers."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from warmbly import mask_to_scopes, scopes_to_mask
from warmbly._utils._scopes import (
    AGENCY_KEY_GRANTABLE_SCOPES,
    AGENCY_KEY_WORKSPACE_SCOPES,
    AGENCY_SCOPES,
    ALL_SCOPES,
    FULL_ACCESS_SCOPES,
    SCOPES,
)

_SCOPE_NAMES = sorted(SCOPES.keys())


# ---------------------------------------------------------------------------
# Round-trip property tests
# ---------------------------------------------------------------------------


@given(subset=st.lists(st.sampled_from(_SCOPE_NAMES), unique=True))
def test_scopes_to_mask_round_trip(subset: list[str]) -> None:
    mask = scopes_to_mask(subset)
    recovered = mask_to_scopes(mask)
    # Order-independent equality: the same set of scopes survives the trip.
    assert set(recovered) == set(subset)


@given(subset=st.sets(st.sampled_from(_SCOPE_NAMES)))
def test_mask_to_scopes_returns_only_known_scopes(subset: set[str]) -> None:
    mask = scopes_to_mask(subset)
    recovered = mask_to_scopes(mask)
    assert all(name in SCOPES for name in recovered)
    # No duplicates in the output.
    assert len(recovered) == len(set(recovered))


@given(subset=st.lists(st.sampled_from(_SCOPE_NAMES), unique=True))
def test_mask_is_pure_or_of_bits(subset: list[str]) -> None:
    mask = scopes_to_mask(subset)
    expected = 0
    for name in subset:
        expected |= SCOPES[name]
    assert mask == expected


def test_scopes_to_mask_preserves_declaration_order() -> None:
    # mask_to_scopes iterates SCOPES, so output follows declaration order.
    recovered = mask_to_scopes(ALL_SCOPES | AGENCY_SCOPES)
    assert recovered == list(SCOPES.keys())


# ---------------------------------------------------------------------------
# Concrete sanity checks
# ---------------------------------------------------------------------------


def test_empty_round_trip() -> None:
    assert scopes_to_mask([]) == 0
    assert mask_to_scopes(0) == []


def test_single_scope_bits() -> None:
    assert scopes_to_mask(["read_emails"]) == 1
    assert scopes_to_mask(["read_campaigns"]) == 2
    assert mask_to_scopes(1) == ["read_emails"]


def test_duplicate_names_collapse() -> None:
    # OR-ing the same bit twice is idempotent.
    assert scopes_to_mask(["webhooks", "webhooks"]) == SCOPES["webhooks"]


# ---------------------------------------------------------------------------
# ALL_SCOPES
# ---------------------------------------------------------------------------


def test_all_scopes_value() -> None:
    assert sum(SCOPES.values()) == ALL_SCOPES | AGENCY_SCOPES
    assert scopes_to_mask(SCOPES.keys()) == ALL_SCOPES | AGENCY_SCOPES
    assert not ALL_SCOPES & AGENCY_SCOPES


def test_all_scopes_grants_every_workspace_scope() -> None:
    assert set(mask_to_scopes(ALL_SCOPES)) == {
        name for name in SCOPES if not name.startswith("agency_")
    }


def test_scope_bit_counts() -> None:
    assert len(SCOPES) == 32
    assert bin(ALL_SCOPES).count("1") == 27
    assert mask_to_scopes(AGENCY_SCOPES) == [
        "agency_read",
        "agency_manage_clients",
        "agency_read_usage",
        "agency_transfer_ai",
        "agency_migrate",
    ]
    assert SCOPES["connect_emails"] == 1 << 24
    assert SCOPES["agency_migrate"] == 1 << 31


def test_presets_match_the_server() -> None:
    assert not FULL_ACCESS_SCOPES & SCOPES["connect_emails"]
    assert FULL_ACCESS_SCOPES & SCOPES["manage_reports"]
    assert FULL_ACCESS_SCOPES & SCOPES["import_tools"]
    assert not AGENCY_KEY_WORKSPACE_SCOPES & (
        SCOPES["api_keys"] | SCOPES["realtime_subscribe"] | SCOPES["connect_emails"]
    )
    assert AGENCY_KEY_GRANTABLE_SCOPES == AGENCY_KEY_WORKSPACE_SCOPES | AGENCY_SCOPES


# ---------------------------------------------------------------------------
# Unknown scope handling
# ---------------------------------------------------------------------------


def test_unknown_scope_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown scope"):
        scopes_to_mask(["not_a_real_scope"])


def test_unknown_scope_message_includes_name() -> None:
    with pytest.raises(ValueError, match="bogus_scope"):
        scopes_to_mask(["read_emails", "bogus_scope"])


def test_unknown_scope_does_not_chain_keyerror() -> None:
    try:
        scopes_to_mask(["nope"])
    except ValueError as exc:
        # Raised with `from None`, so no KeyError shows up in the chain.
        assert exc.__cause__ is None
    else:  # pragma: no cover - the call above must raise
        pytest.fail("expected ValueError")
