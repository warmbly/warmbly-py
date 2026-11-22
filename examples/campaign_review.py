"""Review a campaign's leads before anything goes out.

With review on, each new lead waits until someone approves it. This example
turns review on, checks readiness, writes the AI copy ahead, personalizes one
lead's first email and approves the leads that are ready.

Needs ``read_campaigns``, ``read_contacts`` and ``write_campaigns``; approving
also needs ``send_campaigns``. Writing AI copy is charged to the balance.
"""

from __future__ import annotations

import sys

from warmbly import Warmbly


def main(campaign_id: str) -> None:
    client = Warmbly()
    campaigns = client.campaigns

    change = campaigns.set_review(campaign_id, enabled=True)
    print(f"review on, {change.held} leads held")

    summary = campaigns.review(campaign_id)
    if summary.counts is not None:
        print(f"{summary.counts.waiting} waiting, {summary.counts.started} started")
    for field in summary.missing:
        print(f"{field.leads} leads have no {field.field}")
    for issue in summary.template_errors:
        print(f"step {issue.position} does not render: {issue.message}")

    # Write the first email's AI copy ahead, one pass at a time.
    after: str | None = None
    while True:
        result = (
            campaigns.write_review_ai(campaign_id, waiting_only=True, after=after)
            if after
            else campaigns.write_review_ai(campaign_id, waiting_only=True)
        )
        print(f"wrote {result.written}, {result.remaining} left")
        if result.stopped or not result.remaining or not result.next:
            break
        after = result.next

    ready: list[str] = []
    for lead in campaigns.list_review_leads(campaign_id, status="waiting"):
        if lead.missing:
            continue
        ready.append(lead.contact_id)

    if ready:
        emails = campaigns.lead_emails(campaign_id, ready[0])
        first = emails.steps[0]
        campaigns.personalize_lead_email(
            campaign_id,
            ready[0],
            first.step_id,
            subject=first.subject or "",
            body_html=(first.body_html or "") + "<p>P.S. Loved your last post.</p>",
        )
        approved = campaigns.approve_review_leads(campaign_id, contact_ids=ready)
        print(f"approved {approved.released} leads")


if __name__ == "__main__":
    main(sys.argv[1])
