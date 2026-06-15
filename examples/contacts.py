"""Search, add, import, and annotate contacts."""

from __future__ import annotations

from warmbly import Warmbly


def main() -> None:
    client = Warmbly()

    # Search (this is the "list" for contacts — it's a POST that supports
    # free-text, filters, and cursor pagination).
    results = client.contacts.search(query="acme.com", limit=25)
    print("matches:", len(results.data))

    # Add a couple of contacts.
    added = client.contacts.create(
        contacts=[
            {"email": "jane@acme.com", "first_name": "Jane", "company": "Acme"},
            {"email": "john@acme.com", "first_name": "John", "company": "Acme"},
        ],
    )
    print("added:", added)

    # Look one up by email, then attach a note.
    contact = client.contacts.lookup(email="jane@acme.com")
    client.contacts.create_note(contact.id, body="Met at the conference.")
    for note in client.contacts.list_notes(contact.id):
        print("  note:", note)

    # Timeline and deals for the contact.
    print("timeline:", client.contacts.timeline(contact.id))
    print("deals:", client.contacts.deals(contact.id))

    # Bulk-import from a list (preview first, then commit).
    rows = [{"email": "lead1@example.com"}, {"email": "lead2@example.com"}]
    preview = client.contacts.import_preview(contacts=rows)
    print("import preview:", preview)
    client.contacts.import_commit(contacts=rows)

    client.close()


if __name__ == "__main__":
    main()
