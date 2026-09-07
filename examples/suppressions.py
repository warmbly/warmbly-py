"""Read and edit the workspace suppression list.

An entry is an address, or a whole domain, that campaign mail never goes to,
whatever put it there: a bounce, a complaint, a recipient's own opt-out, or a
manual add. Lifting an entry is what re-enables sending, so it is audited.
"""

from __future__ import annotations

import os

from warmbly import Warmbly


def main() -> None:
    client = Warmbly(api_key=os.environ["WARMBLY_API_KEY"])

    # Add addresses and whole domains in one call. A bare string is the value;
    # a mapping lets each entry carry its own reason.
    result = client.suppressions.add(
        entries=[
            "no-thanks@example.com",
            {"value": "@rival.com", "reason": "competitor"},
        ],
        reason="Imported from the CRM do-not-contact list",
    )
    print("added:", result.added, "rejected:", list(result.skipped))

    # Iterating walks every page.
    for entry in client.suppressions.list(q="example"):
        print(f"{entry.email:40} {entry.kind:6} {entry.source} {entry.reason or ''}")

    # Lifting a suppression puts the recipient back in scope for campaigns.
    client.suppressions.remove("<suppression-id>")


if __name__ == "__main__":
    main()
