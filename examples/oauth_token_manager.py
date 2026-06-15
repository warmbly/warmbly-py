"""Persist OAuth2 tokens and refresh them automatically.

``TokenManager`` keeps a valid access token on hand: it refreshes (using the
rotating refresh token) shortly before expiry and writes the new token set back
to storage. Requires the ``oauth`` extra for ``keyring`` (optional).

    pip install "warmbly[oauth]"
"""

from __future__ import annotations

from warmbly import Warmbly
from warmbly.oauth import FileTokenStorage, OAuth2Client, OAuth2Token, TokenManager

CLIENT_ID = "wmcid_your_client_id"
CLIENT_SECRET = "wmcs_your_client_secret"


def main() -> None:
    oauth = OAuth2Client(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

    # Store tokens in a 0600 (owner-only) JSON file. Swap for
    # KeyringTokenStorage to use the OS keychain, or MemoryTokenStorage in tests.
    storage = FileTokenStorage("~/.warmbly/acme-token.json")

    # Seed storage once after the initial authorization-code exchange:
    # storage.save(token_from_exchange_code)
    # (See oauth_flow.py.) For client-credentials apps you can seed it like so:
    storage.save(oauth.client_credentials(scopes=["read_campaigns"]))

    # The manager refreshes via this callback and persists the rotated token.
    def refresh(refresh_token: str) -> OAuth2Token:
        return oauth.refresh_token(refresh_token)

    manager = TokenManager(storage, refresh, skew=60)

    # Always returns a currently-valid access token, refreshing if needed.
    client = Warmbly(api_key=manager.access_token())
    print("authenticated; campaigns:")
    for campaign in client.campaigns.list():
        print(" -", campaign.name)
    client.close()


if __name__ == "__main__":
    main()
