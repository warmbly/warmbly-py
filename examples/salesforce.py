"""Run a Salesforce import and read a contact's linked records.

Needs an API key with the INTEGRATIONS permission (and READ_CRM for the
contact panel). The connection itself is created in the dashboard.
"""

from __future__ import annotations

import os

from warmbly import Warmbly


def main() -> None:
    client = Warmbly(api_key=os.environ["WARMBLY_API_KEY"])
    connection_id = os.environ["WARMBLY_SALESFORCE_CONNECTION_ID"]

    overview = client.salesforce.overview(connection_id, checks=True)
    print("health:", overview.health, "linked records:", overview.counts)

    # Preview a list view, then save it as a recurring import.
    views = list(client.salesforce.list_views(connection_id, object="Lead"))
    if views:
        preview = client.salesforce.preview_import(
            connection_id,
            source_kind="list_view",
            source_id=views[0].id or "",
            object="Lead",
        )
        print("would read", preview.total, "people")
        source = client.salesforce.create_import_source(
            connection_id,
            source_kind="list_view",
            source_id=views[0].id or "",
            object="Lead",
            recurring=True,
        )
        print("first run:", source.last_result)

    # Retry whatever failed to log in the last day.
    failed = [
        row.id
        for row in client.salesforce.list_activity(connection_id, status="failed")
    ]
    if failed:
        print("requeued:", client.salesforce.retry_activity(connection_id, ids=failed))

    # A contact's panel: linked records, opportunities and recent tasks.
    contact_id = os.environ.get("WARMBLY_CONTACT_ID")
    if contact_id:
        panel = client.contacts.salesforce(contact_id)
        for record in panel.records:
            print(record.object, record.name, record.status, record.url)


if __name__ == "__main__":
    main()
