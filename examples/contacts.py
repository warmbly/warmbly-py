"""Search, add, import, and annotate contacts."""

from __future__ import annotations

import pathlib

from warmbly import Warmbly


def main() -> None:
    client = Warmbly()

    # Search is the list endpoint for contacts: a POST, because the filter is
    # far richer than a query string. Paging is explicit — carry the cursor
    # from `pagination` into the next call.
    results = client.contacts.search(query="acme.com", subscribed=True, limit=25)
    print("matches:", len(results.data), "of", results.pagination.get("total"))

    # Add a couple of contacts. The endpoint takes an array, and an address
    # that already exists is updated rather than duplicated.
    added = client.contacts.create(
        [
            {"email": "jane@acme.com", "first_name": "Jane", "company": "Acme"},
            {"email": "john@acme.com", "first_name": "John", "company": "Acme"},
        ]
    )
    print("added:", added.created, "updated:", added.updated)

    # Look one up by email, then attach a note.
    found = client.contacts.lookup(email="jane@acme.com")
    assert found.contact is not None
    contact_id = found.contact.id

    client.contacts.create_note(contact_id, content="Met at the conference.")
    for note in client.contacts.list_notes(contact_id):
        print("  note:", note.content)

    # The full record carries the engagement roll-up and suppression state.
    detail = client.contacts.retrieve(contact_id)
    print("engagement:", detail.engagement, "suppressed:", detail.suppression)

    # Timeline and deals for the contact.
    print("timeline:", [t.type for t in client.contacts.timeline(contact_id)])
    print("deals:", list(client.contacts.list_deals(contact_id)))

    # Bulk-import from a CSV: preview the parse, then commit with a mapping.
    csv_bytes = pathlib.Path("leads.csv").read_bytes()
    preview = client.contacts.import_preview(file=csv_bytes, filename="leads.csv")
    print("import preview:", preview.headers, preview.total_rows)

    result = client.contacts.import_commit(
        file=csv_bytes,
        filename="leads.csv",
        import_options={
            "column_mapping": preview.suggested_mapping,
            "dedup": "update",
        },
    )
    print("imported:", result.imported, "updated:", result.updated)

    # Export the matching set back out. `xlsx` is binary; write it verbatim.
    blob = client.contacts.export(format="csv", scope="all")
    pathlib.Path("contacts-export.csv").write_bytes(blob)

    client.close()


if __name__ == "__main__":
    main()
