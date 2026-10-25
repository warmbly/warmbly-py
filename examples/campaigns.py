"""Build a campaign end to end: create, add sequence steps, start, inspect.

Note: ``start()`` actually begins sending mail, so run against a test org.
"""

from __future__ import annotations

from warmbly import Warmbly


def main() -> None:
    client = Warmbly()

    campaign = client.campaigns.create(
        name="Q3 outreach",
        description="Follow-up sequence for inbound leads",
        stop_on_reply=True,
        open_tracking=True,
        link_tracking=True,
        daily_limit=200,
    )
    print("campaign:", campaign.id)

    # A step can be created blank and filled in later, or written in one call.
    # Follow-ups reply in the first email's conversation by default
    # (thread_reply); pass thread_reply=False to open a new conversation.
    client.campaigns.create_step(
        campaign.id,
        subject="Quick question about {{.Company}}",
        body_html="<p>Hi {{.FirstName}}, ...</p>",
        wait_after=3,  # days to wait before the next step fires
    )
    second = client.campaigns.create_step(campaign.id)
    client.campaigns.update_step(
        campaign.id,
        second.id,
        body_html="<p>Just following up ...</p>",
        thread_reply=True,
    )
    print("steps:", [s.id for s in client.campaigns.list_steps(campaign.id)])

    # Pick a mailbox to send from and attach it to the campaign.
    account = next(iter(client.emails.list(limit=1)))
    client.campaigns.set_senders(
        campaign.id, senders=[{"email_account_id": account.id, "weight": 1}]
    )

    # Preview the merge tags against a sample contact. No side effects.
    preview = client.campaigns.preview_template(
        subject="Quick question about {{.Company}}",
        body_html="<p>Hi {{.FirstName}}, ...</p>",
    )
    print("preview subject:", preview.subject, "unresolved:", preview.unresolved)

    # Send yourself a real preview, then check the campaign is launch-ready.
    client.campaigns.send_test_email(
        campaign.id, account_id=account.id, recipient="you@example.com"
    )
    report = client.campaigns.preflight(campaign.id)
    print("preflight ready:", report.ready, "errors:", report.errors)

    # Launch it, then see what today's plan allows and read the activity log.
    client.campaigns.start(campaign.id)
    print("started")
    plan = client.campaigns.send_plan(campaign.id)
    print("projected today:", plan.projected_today, "bottleneck:", plan.bottleneck)
    for entry in client.campaigns.logs(campaign.id, limit=20):
        print("  log:", entry.event_type, entry.message)

    # Re-test inbox placement of the first email every week.
    client.campaigns.set_placement_monitor(
        campaign.id, enabled=True, interval_days=7, alert_below=60
    )

    # Pause it again.
    client.campaigns.stop(campaign.id)
    print("stopped")

    client.close()


if __name__ == "__main__":
    main()
