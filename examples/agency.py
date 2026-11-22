"""Run client workspaces with an agency API key.

An agency key (``wmagency_...``) reads and manages its own agency through
``client.agency``. To act inside one client workspace, name it with
``organization=``; every other resource then works as it does for a workspace
key.
"""

from __future__ import annotations

import os

from warmbly import Warmbly


def main() -> None:
    key = os.environ["WARMBLY_AGENCY_KEY"]
    client = Warmbly(api_key=key)

    (agency,) = client.agency.list().data
    usage = client.agency.usage(agency.id)
    print(f"{agency.name}: {usage.total} sends this period, {usage.days_left} days left")

    for workspace in client.agency.list_clients(agency.id):
        print(workspace.organization_id, workspace.name, workspace.monthly_send_limit)

        # Act inside that client workspace with the same key.
        scoped = Warmbly(api_key=key, organization=workspace.organization_id)
        for campaign in scoped.campaigns.list(limit=5):
            print("  ", campaign.name, campaign.status)

    new_client = client.agency.create_client(agency.id, name="Acme Corp")
    client.agency.update_client(
        agency.id, new_client.organization_id, monthly_send_limit=20_000
    )


if __name__ == "__main__":
    main()
