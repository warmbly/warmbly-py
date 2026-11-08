"""Run inbox placement tests and read where each copy landed.

A placement test sends a template or a campaign step from one of your
mailboxes to a panel of seed inboxes. Past the workspace's monthly free
allowance a test costs money, so a create call names the most you agree to
pay with ``max_usd``; a refused request sends and charges nothing.
"""

from __future__ import annotations

import os

from warmbly import Warmbly


def main() -> None:
    client = Warmbly(api_key=os.environ["WARMBLY_API_KEY"])

    overview = client.placement.overview().data
    if overview is not None and overview.usage is not None:
        print("free tests used:", overview.usage.used, "of", overview.usage.limit)

    # One test from one mailbox. "compare" runs it tracked and untracked.
    created = client.placement.create_test(
        sender_account_id=os.environ["WARMBLY_SENDER_ID"],
        subject="Quick question",
        body_plain="Hi, do you have a minute this week?",
        tracking="compare",
        max_usd=1.0,
    )
    for test in created.data:
        print("started", test.id, test.status)

    # Read the verdicts as they arrive.
    detail = client.placement.retrieve_test(created.data[0].id).data
    if detail is not None:
        for result in detail.results:
            print(f"{result.family or '':18} {result.folder}")

    # Test from many mailboxes at once. Preview first: it starts nothing.
    batch_args = {
        "sender_scope": {"type": "workspace", "untested_days": 30},
        "sample": {"mode": "per_domain", "count": 1},
        "subject": "Quick question",
        "body_plain": "Hi, do you have a minute this week?",
    }
    preview = client.placement.preview_batch(**batch_args).data
    if preview is not None:
        print("senders:", preview.selected, "cost (USD):", preview.cost_usd)

    batch = client.placement.create_batch(max_usd=2.0, **batch_args).data
    if batch is not None:
        # Worst inbox rate first.
        for sender in client.placement.list_batch_senders(batch.id, sort="worst"):
            print(sender.sender_email, sender.status)

    # Schedule a campaign's first step to be re-tested weekly.
    client.campaigns.put_placement_monitor(
        os.environ["WARMBLY_CAMPAIGN_ID"], interval_days=7, alert_below=70
    )


if __name__ == "__main__":
    main()
