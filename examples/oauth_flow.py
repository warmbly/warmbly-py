"""The full OAuth2 authorization-code + PKCE flow.

Run this to act on behalf of *another* Warmbly user. It's interactive: it prints
a URL, you authorize in a browser, then paste back the redirect URL.

    python examples/oauth_flow.py
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from warmbly import Warmbly
from warmbly.oauth import OAuth2Client

# From examples/oauth_applications.py (or your dashboard):
CLIENT_ID = "wmcid_your_client_id"
CLIENT_SECRET = "wmcs_your_client_secret"
REDIRECT_URI = "https://app.example.com/oauth/callback"


def main() -> None:
    oauth = OAuth2Client(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
    )

    # 1. Build the authorization URL. PKCE (S256) and a CSRF `state` are
    #    generated for you; keep `state` and `verifier` for the next step.
    url, state, verifier = oauth.authorization_url(
        scopes=["read_campaigns", "send_campaigns"],
    )
    print("Open this URL and authorize:\n", url, "\n")

    # 2. After authorizing you're redirected to REDIRECT_URI?code=...&state=...
    redirected = input("Paste the full redirect URL you landed on: ").strip()
    params = parse_qs(urlparse(redirected).query)
    code = params["code"][0]
    returned_state = params["state"][0]

    # 3. Exchange the code for tokens. `expected_state` is compared in constant
    #    time to defend against CSRF; a mismatch raises OAuthError.
    token = oauth.exchange_code(
        code,
        code_verifier=verifier,
        state=returned_state,
        expected_state=state,
    )
    print("access token:", token.access_token)
    print("expires in:", token.expires_in, "seconds")

    # 4. Use it like any bearer credential.
    client = Warmbly(api_key=token.access_token)
    for campaign in client.campaigns.list():
        print(" campaign:", campaign.name)
    client.close()

    # 5. Refresh later (refresh tokens rotate — persist the new one).
    refreshed = oauth.refresh_token(token.refresh_token)
    print("refreshed access token:", refreshed.access_token)

    # 6. Revoke when finished.
    oauth.revoke(refreshed.access_token)
    print("revoked")


if __name__ == "__main__":
    main()
