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
    client.emails.track(account.id, tracking_domain="track.example.com")

    # Send a one-off message from this mailbox.
    result = client.emails.send(
        account.id,
        to="lead@example.com",
        subject="Hello from warmbly-py",
        text="Plain-text body.",
        html="<p>HTML body.</p>",
        reply_to=account.email,
    )
    print("sent:", result)

    client.close()


if __name__ == "__main__":
    main()
