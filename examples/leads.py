"""Find businesses on a map, enrich them, and turn them into contacts.

A search covers an area of the map and stores the businesses it finds as leads.
An enrichment run then reads each lead's website for addresses and the people
it names, and the leads you want become contacts. Searching a source the
instance pays for, and each website read, is charged to the workspace balance.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from warmbly import Warmbly


def main() -> None:
    client = Warmbly(api_key=os.environ["WARMBLY_API_KEY"])

    # Look up the place to search, then search a circle around it.
    place = next(iter(client.leads.geocode(q="Springfield, IL")))
    assert place.center is not None and place.bounds is not None
    bounds = place.bounds.to_dict()
    result = client.leads.search(
        provider="osm",
        category="bakery",
        location_label=place.label or "",
        save=True,
        name="Bakeries in Springfield",
        area={
            "kind": "circle",
            "bounds": bounds,
            "center": place.center.to_dict(),
            "radius_m": 5000,
        },
    )
    print(f"found {result.found} leads, charged ${result.charged_usd}")

    # Fetch the next page of the same search by sending its id alone.
    if result.search is not None and result.search.has_more:
        client.leads.search(search_id=result.search.id)

    # Read the leads back, with a filter. Iterating walks every page.
    wanted = {"has_website": True, "enrichment": ["none"]}
    ids = [lead.id for lead in client.leads.query(filter=wanted, sort="score")]

    # Read each website for addresses and the people it names.
    run = client.leads.enrich(lead_ids=ids[:500], verify=True, people=True)
    while run.status in {"queued", "running"}:
        time.sleep(5)
        run = client.leads.retrieve_enrichment(run.id)
    print(f"{run.emails_found} addresses, {run.people_found} people found")

    # Turn the leads that have an address into contacts and enrol them.
    added = client.leads.add_to_contacts(
        all_=True,
        filter={"has_email": True, "in_contacts": False},
        who="both",
        verified_only=True,
        campaign_ids=["<campaign-id>"],
    )
    print(f"{added.imported} new contacts, {added.updated} updated")

    # Export what is left as a spreadsheet.
    xlsx = client.leads.export(format="xlsx", all_=True, filter={"tag": "bakeries"})
    Path("leads.xlsx").write_bytes(xlsx)


if __name__ == "__main__":
    main()
