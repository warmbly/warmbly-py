"""Manage email accounts (mailboxes): list, warmup controls, and sending.

Note: ``send()`` delivers a real email.
"""

from __future__ import annotations

from warmbly import Warmbly


def main() -> None:
    client = Warmbly()

    # List connected mailboxes.
    accounts = list(client.emails.list())
    print(f"{len(accounts)} mailbox(es)")
    if not accounts:
        return

    account = accounts[0]
    print("using:", account.email, f"(provider={account.provider})")

    # Check the account is authenticated/healthy.
    print("auth check:", client.emails.auth_check(account.id))

    # Warmup lifecycle.
    client.emails.warmup_start(account.id)
    print("warmup started")
    client.emails.warmup_pause(account.id)
    client.emails.warmup_resume(account.id)
    print("warmup status:", client.emails.warmup_ban_status(account.id))

    # Point the tracking domain (open/click tracking) at a verified CNAME.
    status = client.emails.track(account.id, domain="track.example.com")
    print("tracking domain verified:", status.tracking_domain_verified)

    # Tag several mailboxes at once. Set semantics, so this is idempotent.
    client.emails.bulk_tag(email_ids=[account.id], add_tags=["outbound"])

    # Send a one-off message from this mailbox. The send is queued as a task,
    # so what comes back is the task, not a delivered message.
    result = client.emails.send(
        account.id,
        to=["lead@example.com"],
        subject="Hello from warmbly-py",
        body_plain="Plain-text body.",
        body_html="<p>HTML body.</p>",
    )
    print("queued:", result.task_id, "at", result.scheduled_at)

    client.close()


if __name__ == "__main__":
    main()
