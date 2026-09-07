"""Build a saved audience, check its size, and point a campaign at it.

A segment is a set of conditions over contacts, evaluated at read time, so it
always reflects the contacts as they are now. Linking one to a campaign makes
it a live audience source: members are enrolled as leads and kept current.
"""

from __future__ import annotations

import os

from warmbly import Warmbly


def main() -> None:
    client = Warmbly(api_key=os.environ["WARMBLY_API_KEY"])

    # Which fields can a condition name, and which operators do they take?
    for field in client.segments.fields():
        print(f"{field.field:24} {field.kind}")

    conditions = [
        {"field": "email_domain", "operator": "ends_with", "value": "acme.com"},
        {"field": "last_replied_at", "operator": "not_within_days", "value": "90"},
    ]

    # Count the audience before saving anything.
    preview = client.segments.preview(match="all", conditions=conditions)
    print("would match:", preview.contact_count)

    segment = client.segments.create(
        name="Acme, gone quiet",
        description="Acme contacts with no reply in 90 days",
        color="#ff8800",
        match="all",
        conditions=conditions,
    )
    print("segment:", segment.id, segment.contact_count)

    # Pin one contact in regardless of what the conditions say.
    client.segments.set_members(segment.id, contacts=["<contact-id>"], mode="include")

    # Link it to a campaign as a live source. This replaces the linked set, so
    # send every segment you want attached.
    linked = client.campaigns.set_segments("<campaign-id>", segment_ids=[segment.id])
    print("linked:", len(linked.data), "newly enrolled leads:", linked.added)

    # Or enrol the current members once, without linking.
    once = client.segments.add_to_campaign(segment.id, campaign_id="<campaign-id>")
    print("enrolled", once.added, "of", once.members)


if __name__ == "__main__":
    main()
