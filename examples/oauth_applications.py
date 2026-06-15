"""Register and manage OAuth2 applications (clients).

This is how you obtain a ``client_id`` / ``client_secret`` to drive the
authorization-code flow in ``oauth_flow.py``. The ``client_secret`` is returned
only on create and on rotate.
"""

from __future__ import annotations

from warmbly import Warmbly, scopes_to_mask


def main() -> None:
    client = Warmbly()

    app = client.oauth_applications.create(
        name="Acme Integration",
        scopes=scopes_to_mask(["read_campaigns", "send_campaigns"]),
        redirect_uris=["https://app.example.com/oauth/callback"],
        website_url="https://app.example.com",
        description="Lets Acme launch campaigns on a user's behalf.",
    )
    print("client_id:", app.client_id)
    # The client secret is shown only once — store it securely, don't log it.
    client_secret = app.client_secret  # save to your secrets manager now
    print("client_secret received:", "yes" if client_secret else "no")

    # List the org's registered apps.
    for existing in client.oauth_applications.list():
        print(f"  {existing.name}: {existing.client_id} ({existing.status})")

    # Update redirect URIs.
    client.oauth_applications.update(
        app.id,
        redirect_uris=[
            "https://app.example.com/oauth/callback",
            "https://staging.example.com/oauth/callback",
        ],
    )

    # Rotate the client secret (invalidates the old one).
    rotated = client.oauth_applications.rotate_secret(app.id)
    # Persist the rotated secret securely; never log its value.
    print("client_secret rotated:", "yes" if rotated.client_secret else "no")

    # Fetch the webhook signing secret for app-scoped webhooks.
    wh = client.oauth_applications.webhook_secret(app.id)
    print("webhook secret present:", wh.webhook_secret is not None)

    client.close()


if __name__ == "__main__":
    main()
