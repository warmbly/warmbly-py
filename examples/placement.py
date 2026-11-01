"""Run an inbox placement test and watch where the copies land.

A test sends one copy from one of your mailboxes to a panel of seed inboxes and
reports whether each landed in the inbox, a Gmail tab, spam, or nowhere. A batch
runs the same test from many senders at once.
"""

from __future__ import annotations

import os
import time

from warmbly import Warmbly


def main() -> None:
    client = Warmbly(api_key=os.environ["WARMBLY_API_KEY"])

    # What can this workspace test on, and how much of the month is left?
    overview = client.placement.overview().data
    for panel in overview.panels:
        print(panel.panel, "available" if panel.available else panel.reason)
    print("used", overview.usage.used, "of", overview.usage.limit)

    # Start a test from one mailbox. Past the monthly allowance the call is
    # refused unless you agree to a price with max_credits.
    started = client.placement.create_test(
        sender_account_id="<mailbox-id>",
        subject="Quick question",
        body_plain="Hi, do you have a minute this week?",
        tracking="compare",  # send it tracked and untracked
    )
    test_id = started.data[0].id

    # Poll until every copy has a verdict.
    while True:
        test = client.placement.retrieve_test(test_id).data
        if test.status != "running":
            break
        time.sleep(30)
    print("inbox rate:", test.summary.inbox_rate, "spam rate:", test.summary.spam_rate)
    for result in test.results:
        print(f"{result.family_label:20} {result.folder}")

    # Or test a whole campaign's senders, after checking what it would cost.
    plan = {
        "sender_scope": {"type": "campaign", "campaign_id": "<campaign-id>"},
        "sample": {"mode": "per_domain", "count": 1},
        "campaign_id": "<campaign-id>",
    }
    preview = client.placement.preview_batch(**plan).data
    print(
        preview.selected,
        "senders,",
        preview.tests,
        "tests,",
        preview.credits,
        "credits",
    )
    batch = client.placement.create_batch(**plan, max_credits=preview.credits).data
    for sender in client.placement.list_batch_senders(batch.id, sort="worst"):
        print(sender.sender_email, sender.status, sender.summary.inbox_rate)

    # Re-test a campaign's first step every week and alert below 70% inbox.
    client.campaigns.set_placement_monitor(
        "<campaign-id>", interval_days=7, alert_below=70, pause_on_alert=True
    )


if __name__ == "__main__":
    main()
