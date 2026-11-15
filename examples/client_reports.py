"""Share campaign results with a client: a report, a public link and a schedule.

Reading reports needs ``READ_ANALYTICS``; creating, sharing and scheduling them
needs ``MANAGE_REPORTS``.
"""

from __future__ import annotations

import os

from warmbly import Warmbly


def main() -> None:
    client = Warmbly(api_key=os.environ["WARMBLY_API_KEY"])

    report = client.reports.create(
        name="Acme: monthly outreach",
        date_range="last_30_days",
        sections={"overview": True, "daily_chart": True, "campaigns": True},
    )

    # See exactly what the client will see, for any range.
    preview = client.reports.preview(report.id, range="this_month")
    if preview.overview is not None:
        print("sent:", preview.overview.sent, "replies:", preview.overview.replied)

    # The link is a bearer secret: anyone holding it can read the report.
    link = client.reports.create_link(report.id, expires_in_days=30)
    print("share this:", link.url)

    # Email it every Monday at 09:00 New York time.
    client.reports.set_schedule(
        report.id,
        recipients=["ceo@acme.example"],
        cadence="weekly",
        weekday=1,
        hour=9,
        timezone="America/New_York",
    )


if __name__ == "__main__":
    main()
