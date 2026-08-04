"""Drive the CRM: pipelines and stages, deals, tasks, and the faceted searches.

Deals and tasks each expose three read paths, and picking the right one matters
at scale:

  * ``list_*``   - a cheap cursor list with a couple of filters.
  * ``search_*`` - the faceted filter, evaluated server-side.
  * ``*_summary`` - aggregates over the *same* filter, so header totals are true
    sums rather than a reduce over one page.
"""

from __future__ import annotations

from warmbly import Warmbly


def main() -> None:
    client = Warmbly()

    # A pipeline owns ordered stages; create both in one call.
    pipeline = client.crm.create_pipeline(
        name="Outbound",
        stages=[
            {"name": "New", "color": "#94a3b8"},
            {"name": "Qualified", "color": "#0ea5e9"},
            {"name": "Won", "color": "#22c55e"},
        ],
    )
    stages = {s.name: s.id for s in pipeline.stages}
    print("pipeline:", pipeline.id, "stages:", list(stages))

    # A deal always sits in exactly one stage.
    deal = client.crm.create_deal(
        name="Acme Corp",
        pipeline_id=pipeline.id,
        stage_id=stages["New"],
        value=12_000.0,
        currency="USD",
        expected_close_date="2026-03-31T00:00:00Z",
    )
    print("deal:", deal.id)

    # Moving a deal is a stage_id change; closing it is a status change.
    client.crm.update_deal(deal.id, stage_id=stages["Qualified"])
    client.crm.update_deal(deal.id, status="won")

    # Search the whole org, not just one pipeline.
    page = client.crm.search_deals(
        statuses=["open", "won"],
        min_value=1_000.0,
        sort_by="value",
        limit=50,
    )
    print("matched:", len(page.data), "of", page.pagination.get("total"))

    # Aggregate over the identical filter for the header numbers.
    totals = client.crm.deals_summary(statuses=["open", "won"], min_value=1_000.0)
    print("open:", totals.open_count, totals.open_value, totals.currency)
    if totals.mixed_currency:
        print("  (values span multiple currencies, so they are not comparable)")

    # Task types are user-managed; the first list seeds Call / Email / Meeting.
    types = {t.name: t.id for t in client.crm.list_task_types()}
    print("task types:", list(types))

    # Tasks reference their type by NAME, so deleting a type never orphans one.
    task = client.crm.create_task(
        title="Send the proposal",
        deal_id=deal.id,
        type="Email",
        priority="high",
        due_date="2026-02-01T09:00:00Z",
    )
    client.crm.update_task(task.id, status="completed")

    overdue = client.crm.tasks_summary(overdue=True)
    print("overdue tasks:", overdue.overdue_count)

    client.close()


if __name__ == "__main__":
    main()
