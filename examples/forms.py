"""Publish a hosted lead-capture form and read what it captured.

A submission creates or updates a contact, files it under the form's
categories, and optionally adds it to a campaign. Personalized links tie a
submission back to the contact whose email carried the link.
"""

from __future__ import annotations

import os
from pathlib import Path

from warmbly import Warmbly


def main() -> None:
    client = Warmbly(api_key=os.environ["WARMBLY_API_KEY"])

    # Does this install support a captcha at all?
    print("captcha available:", client.forms.config().captcha_available)

    form = client.forms.create(name="Demo request")

    form = client.forms.update(
        form.id,
        status="published",
        fields=[
            {"id": "email", "type": "email", "label": "Work email", "required": True},
            {"id": "name", "type": "text", "label": "Name", "map_to": "first_name"},
            {
                "id": "size",
                "type": "select",
                "label": "Team size",
                "options": ["1-10", "11-50", "51+"],
            },
        ],
        design={"theme": "midnight", "layout": "split", "button_text": "Book a demo"},
        success_message="Thanks! We'll be in touch within a day.",
        campaign_id="<campaign-id>",
    )
    print("live at:", form.share_url)

    # Brand it.
    logo = Path("logo.png")
    if logo.exists():
        client.forms.upload_asset(
            form.id,
            "logo",
            file=logo.read_bytes(),
            filename=logo.name,
            content_type="image/png",
        )

    # A link that identifies the recipient when they arrive.
    link = client.forms.mint_link(form.id, "<contact-id>")
    print("personalized link:", link.url)

    stats = client.forms.stats(form.id, range="30d")
    if stats.totals is not None:
        print(
            f"{stats.totals.views} views -> {stats.totals.starts} starts "
            f"-> {stats.totals.submissions} submissions"
        )

    for submission in client.forms.list_submissions(form.id, limit=20):
        print(submission.created_at, submission.contact_email, submission.data)


if __name__ == "__main__":
    main()
