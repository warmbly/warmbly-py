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
    )
    print("campaign:", campaign.id)

    # Add a two-step sequence.
    client.campaigns.create_step(
        campaign.id,
        type="email",
        order=1,
        subject="Quick question about {{company}}",
        body="Hi {{first_name}}, ...",
    )
    client.campaigns.create_step(
        campaign.id,
        type="email",
        order=2,
        wait_days=3,
        subject="Re: Quick question",
        body="Just following up ...",
    )
    steps = client.campaigns.list_steps(campaign.id)
    print("steps:", len(steps.data))

    # Send yourself a preview before launching.
    client.campaigns.test_email(campaign.id, to="you@example.com")

    # Launch it, then read the activity log.
    client.campaigns.start(campaign.id)
    print("started")
    for entry in client.campaigns.logs(campaign.id):
        print("  log:", entry)

    # Pause it again.
    client.campaigns.stop(campaign.id)
    print("stopped")

    client.close()


if __name__ == "__main__":
    main()
