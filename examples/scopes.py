"""Work with scopes as readable names instead of raw bitmask integers.

API keys and OAuth2 apps take a ``permissions``/``scopes`` integer. The helpers
let you build and inspect that integer from scope strings.
"""

from __future__ import annotations

from warmbly import mask_to_scopes, scopes_to_mask


def main() -> None:
    # Build a permission bitmask from human-readable scope names.
    mask = scopes_to_mask(
        [
            "read_campaigns",
            "write_campaigns",
            "send_campaigns",
            "realtime_subscribe",
        ]
    )
    print("bitmask:", mask)

    # ...and turn a bitmask back into the scopes it grants.
    print("scopes:", mask_to_scopes(mask))

    # Unknown scope names raise ValueError, so typos fail fast.
    try:
        scopes_to_mask(["read_campaigns", "not_a_real_scope"])
    except ValueError as err:
        print("rejected:", err)


if __name__ == "__main__":
    main()
