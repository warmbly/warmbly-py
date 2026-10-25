"""Inbox placement: send a test to a seed panel and read where it landed.

Note: ``create_test()`` sends real mail from the mailbox you name.
"""

from __future__ import annotations

from warmbly import Warmbly


def main() -> None:
    client = Warmbly()

    overview = client.placement.overview()
    for panel in overview.panels:
        print(panel.panel, "available" if panel.available else panel.reason)

    sender = next(iter(client.emails.list()), None)
    if sender is None:
        return

    # One test: a copy to every seed on the panel.
    (test,) = client.placement.create_test(
        sender_account_id=sender.id,
        subject="Quick question",
        body_plain="Hi, do you have a minute this week?",
    )
    print("started", test.id, test.status)

    # Poll for the verdicts (they arrive over a few minutes).
    detail = client.placement.retrieve_test(test.id)
    counts = detail.summary
    print("inbox rate:", counts.inbox_rate, "spam rate:", counts.spam_rate)
    for result in detail.results:
        print(result.seed, result.folder)

    # How much of the fleet has been tested recently?
    coverage = client.placement.coverage()
    print(f"{coverage.tested_7d}/{coverage.mailboxes} mailboxes tested this week")

    # Preview a batch from many senders before starting it.
    preview = client.placement.preview_batch(
        sender_scope={"type": "workspace", "untested_days": 30},
        sample={"mode": "random", "count": 10},
        subject="Quick question",
        body_plain="Hi, do you have a minute this week?",
    )
    print("would test", preview.selected, "senders,", preview.credits, "credits")

    client.close()


if __name__ == "__main__":
    main()
