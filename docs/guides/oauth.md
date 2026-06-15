# OAuth2

Use OAuth2 when your application needs to act **on behalf of another Warmbly
user or organization** rather than as itself. The
`warmbly.oauth` subsystem implements the RFC 9700-sanctioned
grants against Warmbly's authorization server:

- **authorization_code + PKCE (S256)** — the interactive browser flow.
- **refresh_token** — exchange a (rotating) refresh token for a fresh token set.
- **client_credentials** — machine-to-machine, with no user present.

It also provides token revocation, pluggable token storage, and an
auto-refreshing token manager.

```python
from warmbly.oauth import OAuth2Client
```

All network errors and RFC 6749 error responses surface as
[`OAuthError`][warmbly.OAuthError], which carries `.error` (the machine-readable
code) and `.error_description`.

## Creating the client

Construct an `OAuth2Client` with your application's `client_id`, and — for a
*confidential* client — its `client_secret`. *Public* clients (for example a
desktop or single-page app that cannot keep a secret) omit `client_secret` and
rely on PKCE alone.

```python
from warmbly.oauth import OAuth2Client

oauth = OAuth2Client(
    client_id="wmcid_...",
    client_secret="wmcs_...",                       # omit for a public client
    redirect_uri="https://app.example.com/callback",
)
```

When a `client_secret` is configured the client authenticates to the token
endpoint with HTTP Basic auth; without one, the `client_id` is sent in the
request body.

Additional constructor options:

| Argument | Default | Purpose |
| -------- | ------- | ------- |
| `base_url` | `https://api.warmbly.com` | Hosts the token & revocation endpoints (`/v1/oauth/token`, `/v1/oauth/revoke`). |
| `app_url` | `https://app.warmbly.com` | Hosts the browser `/oauth/authorize` endpoint. |
| `http_client` | created internally | Supply a pre-configured `httpx.Client` to reuse; the client will not close one you pass in. |

The client owns an HTTP connection; close it when you are done (or use it as a
context manager):

```python
with OAuth2Client(client_id="wmcid_...", client_secret="wmcs_...",
                  redirect_uri="https://app.example.com/callback") as oauth:
    ...  # use oauth here
# the underlying HTTP client is closed on exit
```

## The authorization-code + PKCE flow

### 1. Build the authorization URL

[`OAuth2Client.authorization_url`][warmbly.oauth.OAuth2Client] generates a
fresh PKCE `S256` pair and a random CSRF `state`, and returns the URL plus the
two values you must keep:

```python
url, state, verifier = oauth.authorization_url(
    scopes=["read_campaigns", "write_campaigns"],
)
```

It returns a `(url, state, code_verifier)` tuple:

- **`url`** — redirect the user's browser here.
- **`state`** — store it (e.g. in the user's session) to validate the callback.
- **`code_verifier`** — store it too; you need it to redeem the code.

The `scopes` list uses the same scope strings described in the
[Authentication guide](auth.md#scopes-and-permission-bitmasks). You may also
pass your own `state=` if you want to manage it yourself.

### 2. Redirect, then handle the callback

Send the user to `url`. After they approve, Warmbly redirects back to your
`redirect_uri` with `code` and `state` query parameters.

### 3. Exchange the code for tokens

Call [`exchange_code`][warmbly.oauth.OAuth2Client.exchange_code] with the `code`
from the callback, the `code_verifier` you stored, and the `state` for CSRF
validation. Passing `expected_state` makes the client compare the returned
`state` in constant time and raise `OAuthError("invalid_state", ...)` on a
mismatch:

```python
token = oauth.exchange_code(
    code,                          # the `code` query param from the callback
    code_verifier=verifier,        # the verifier from step 1
    state=returned_state,          # the `state` query param from the callback
    expected_state=state,          # the state you stored in step 1
)

print(token.access_token)          # wmat_...
print(token.refresh_token)         # wmrt_...
print(token.expires_in)            # 3600
print(token.scopes)                # ['read_campaigns', 'write_campaigns']
```

The returned [`OAuth2Token`][warmbly.oauth.OAuth2Token] exposes
`access_token`, `token_type` (`"Bearer"`), `expires_in`, `refresh_token`,
`scope`/`scopes`, and a computed `expires_at` (an absolute Unix timestamp). Its
`is_expired(skew=...)` method reports whether the access token is at or within
`skew` seconds of expiry.

### 4. Use the access token

Hand the access token to a regular API client (it goes in the same `api_key`
slot — see [Authentication](auth.md)):

```python
from warmbly import Warmbly

api = Warmbly(api_key=token.access_token)
for campaign in api.campaigns.list():
    print(campaign.id)
```

!!! note "PKCE helper"
    `authorization_url` generates the PKCE pair for you. If you need to do it
    yourself, [`generate_pkce_pair()`][warmbly.oauth.generate_pkce_pair] returns
    a `(verifier, challenge)` tuple using `S256`.

## Refreshing tokens

Access tokens last one hour. Exchange a refresh token for a fresh token set with
[`refresh_token`][warmbly.oauth.OAuth2Client.refresh_token]:

```python
new_token = oauth.refresh_token(token.refresh_token)
```

!!! warning "Refresh tokens rotate"
    Warmbly **rotates** refresh tokens: each refresh returns a *new*
    `refresh_token` and invalidates the one you sent. Always persist the new
    token set and discard the old refresh token. A failed refresh raises
    `OAuthError` (for example `invalid_grant`), which means the user must
    re-authenticate. The [TokenManager](#automatic-refresh-with-tokenmanager)
    handles all of this for you.

## Client-credentials grant

For machine-to-machine access with no user, use
[`client_credentials`][warmbly.oauth.OAuth2Client.client_credentials]:

```python
token = oauth.client_credentials(scopes=["read_analytics"])
api = Warmbly(api_key=token.access_token)
```

This grant typically does not return a refresh token; obtain a new token when
the current one expires.

## Revoking a token

Revoke an access or refresh token with
[`revoke`][warmbly.oauth.OAuth2Client.revoke]. Per RFC 7009 the endpoint always
reports success, so this returns `None` and only raises on a transport failure:

```python
oauth.revoke(token.refresh_token)   # revoking a refresh token revokes the grant
```

## Token storage

The SDK provides three interchangeable storage backends, all implementing the
[`TokenStorage`][warmbly.oauth.TokenStorage] protocol (`load()`, `save(token)`,
`clear()`):

| Backend | Persistence | Notes |
| ------- | ----------- | ----- |
| [`MemoryTokenStorage`][warmbly.oauth.MemoryTokenStorage] | Process memory only | Good for tests and short-lived scripts. |
| [`FileTokenStorage`][warmbly.oauth.FileTokenStorage] | A JSON file | Written with `0600` (owner-only) permissions. |
| [`KeyringTokenStorage`][warmbly.oauth.KeyringTokenStorage] | OS secret store | Uses the optional `keyring` package; falls back to a file when `keyring` is not installed. |

```python
from warmbly.oauth import (
    MemoryTokenStorage,
    FileTokenStorage,
    KeyringTokenStorage,
)

# In-memory (optionally seeded with an existing token):
storage = MemoryTokenStorage(token)

# JSON file with 0600 permissions:
storage = FileTokenStorage("~/.warmbly/token.json")

# OS keychain (service/username let you store multiple accounts):
storage = KeyringTokenStorage(service="warmbly", username="alice@example.com")

storage.save(token)
loaded = storage.load()             # OAuth2Token | None
storage.clear()
```

## Automatic refresh with TokenManager

[`TokenManager`][warmbly.oauth.TokenManager] (and its async counterpart
[`AsyncTokenManager`][warmbly.oauth.AsyncTokenManager]) keep a valid access token
available: it loads the stored token, refreshes ahead of expiry, serializes
concurrent refreshes behind a lock (so rotating refresh tokens do not race), and
persists the rotated token back to storage.

Wire it with a storage backend and a refresh function — `oauth.refresh_token`
fits the required signature directly:

```python
from warmbly import Warmbly
from warmbly.oauth import OAuth2Client, FileTokenStorage, TokenManager

oauth = OAuth2Client(client_id="wmcid_...", client_secret="wmcs_...")
storage = FileTokenStorage("~/.warmbly/token.json")
storage.save(token)                 # seed with the token from exchange_code

manager = TokenManager(storage, oauth.refresh_token)

# Always returns a currently-valid access token, refreshing if needed:
api = Warmbly(api_key=manager.access_token())
```

`access_token()` (and `get_token()`, which returns the full `OAuth2Token`)
refresh transparently when the stored token is within the default 60-second
expiry skew; pass `skew=` to the constructor to tune that window. They raise
`OAuthError` if nothing is stored (`no_token`), if the token is expired but
carries no refresh token (`no_refresh_token`), or if the refresh itself fails.

!!! tip "Fetch the token right before each call"
    Because the access token is short-lived, fetch it from the manager just
    before constructing or using a client, rather than caching it for a long
    time:

    ```python
    api = Warmbly(api_key=manager.access_token())
    ```

The async manager mirrors this, awaiting an async refresh function:

```python
from warmbly import AsyncWarmbly
from warmbly.oauth import AsyncOAuth2Client, FileTokenStorage, AsyncTokenManager

oauth = AsyncOAuth2Client(client_id="wmcid_...", client_secret="wmcs_...")
manager = AsyncTokenManager(FileTokenStorage("~/.warmbly/token.json"),
                            oauth.refresh_token)

api = AsyncWarmbly(api_key=await manager.access_token())
```

See the [Async guide](async.md) for the asynchronous client and OAuth client.

## Managing OAuth2 applications

To use OAuth2 you first register an *application* (an OAuth client). You can do
that programmatically through the `oauth_applications` resource on an
authenticated API client (an API key with the `api_keys` permission, for
example). The plaintext `client_secret` is returned **only** on create and
`rotate_secret` — store it immediately.

### Create an application

```python
from warmbly import Warmbly, scopes_to_mask

client = Warmbly(api_key="wmbly_...")

app = client.oauth_applications.create(
    name="My Integration",
    scopes=scopes_to_mask(["read_campaigns", "write_campaigns"]),
    redirect_uris=["https://app.example.com/callback"],
    description="Syncs campaigns into our dashboard",
    website_url="https://example.com",
)

print(app.client_id)        # wmcid_... — use this in OAuth2Client
print(app.client_secret)    # wmcs_... — shown ONCE; store it now
```

Note that `scopes` is the integer bitmask
([`scopes_to_mask`][warmbly.scopes_to_mask]), not a list of strings.

### List, retrieve, update, delete

```python
for app in client.oauth_applications.list():
    print(app.id, app.name)

app = client.oauth_applications.retrieve("app_123")

client.oauth_applications.update(
    "app_123",
    redirect_uris=["https://app.example.com/callback", "https://app.example.com/cb2"],
    scopes=scopes_to_mask(["read_campaigns", "write_campaigns", "send_campaigns"]),
)

client.oauth_applications.delete("app_123")
```

### Rotate the client secret

If a secret is leaked, rotate it. The new secret is returned once:

```python
result = client.oauth_applications.rotate_secret("app_123")
print(result.client_secret)   # the new wmcs_... — store it now
```

### Webhook signing secret

Applications that receive webhooks have a signing secret you can read or rotate:

```python
secret = client.oauth_applications.webhook_secret("app_123")
print(secret.webhook_secret)

rotated = client.oauth_applications.rotate_webhook_secret("app_123")
print(rotated.webhook_secret)
```

See the [Webhooks guide](webhooks.md) for verifying webhook signatures with
[`verify_webhook_signature`][warmbly.verify_webhook_signature].
