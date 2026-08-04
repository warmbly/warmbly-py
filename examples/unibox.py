"""Work the unified inbox: read, label, reply, compose, and schedule.

The unibox is message-centric, not thread-centric: ``list()`` returns one
preview row per conversation, ``retrieve()`` opens a single message, and
``thread()`` expands the whole conversation.

Note: ``reply()`` and ``compose()`` send real mail, so run against a test org.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from warmbly import PaymentRequiredError, Warmbly


def main() -> None:
    client = Warmbly()

    # What is waiting: unread, awaiting a reply from us, newest first.
    overview = client.unibox.overview()
    print("unread:", overview.unread, "awaiting reply:", overview.awaiting_reply)

    inbox = list(client.unibox.list(unseen=True, direction="received", limit=20))
    if not inbox:
        print("nothing unread")
        client.close()
        return

    first = inbox[0]
    print("subject:", first.subject, "from:", first.from_addr)

    # Expand the conversation, oldest first.
    for message in client.unibox.thread(thread_id=first.thread_id or ""):
        print("  ", message.internal_date, message.subject)

    # Label the conversation. PUT semantics: this is the desired final set.
    client.unibox.set_thread_labels(thread_id=first.thread_id or "", category_ids=[])

    # Let the assistant draft a reply. This charges AI credits and never sends.
    try:
        draft = client.unibox.draft_reply(
            thread_id=first.thread_id or "",
            instruction="Short, friendly, offer a call.",
        )
    except PaymentRequiredError:
        print("out of AI credits; writing the reply by hand")
        draft_text = "Thanks for getting back to me!"
    else:
        # The model asks a clarifying question when the prompt is too thin.
        draft_text = draft.text or f"(needs input: {draft.question})"
        print("draft cost:", draft.credits_charged, "credits")

    # Send it from the mailbox that received the message.
    sent = client.unibox.reply(
        email_account_id=first.email_id or "",
        to=list(first.from_addr),
        subject=f"Re: {first.subject}",
        body_plain=draft_text,
        thread_id=first.thread_id,
    )
    print("queued:", sent.task_id)

    # Or schedule a brand-new email, letting the server pick the best mailbox.
    tomorrow = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    composed = client.unibox.compose(
        to=["lead@example.com"],
        subject="Following up",
        body_plain="Circling back on this.",
        send_mode="scheduled",
        scheduled_at=tomorrow,
    )
    print("auto-picked mailbox:", composed.account_email, composed.picked_reason)

    # Scheduled sends can be reviewed and cancelled until they fire.
    for pending in client.unibox.list_scheduled():
        print("  scheduled:", pending.subject, "at", pending.scheduled_at)

    # Mark what we read, and snooze the rest until Monday.
    client.unibox.mark_seen(email_ids=[m.id for m in inbox])
    client.unibox.snooze(thread_id=first.thread_id or "", snoozed_until=tomorrow)

    client.close()


if __name__ == "__main__":
    main()
