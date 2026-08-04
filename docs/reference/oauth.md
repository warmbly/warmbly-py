# OAuth2

The `warmbly.oauth` subsystem implements the two OAuth2 grants Warmbly's
authorization server accepts — **authorization_code + PKCE (S256)** and
**refresh_token** — plus token revocation, secure token storage, and
auto-refreshing token management. Token-endpoint and transport errors surface
as [`OAuthError`][warmbly.OAuthError].

There is no client-credentials grant: every token is bound to a user who
consented, so machine-to-machine access uses an API key instead.

```python
from warmbly.oauth import OAuth2Client

oauth = OAuth2Client(
    client_id="wmcid_...",
    client_secret="wmcs_...",
    redirect_uri="https://app.example.com/callback",
)
url, state, verifier = oauth.authorization_url(scopes=["read_campaigns"])
# ... redirect the user to `url`, capture `code` and `state` on callback ...
token = oauth.exchange_code(
    code, code_verifier=verifier, state=state, expected_state=state
)
print(token.access_token)
```

## Clients

### OAuth2Client

::: warmbly.oauth.OAuth2Client

### AsyncOAuth2Client

::: warmbly.oauth.AsyncOAuth2Client

## Tokens

### OAuth2Token

::: warmbly.oauth.OAuth2Token

### TokenManager

::: warmbly.oauth.TokenManager

### AsyncTokenManager

::: warmbly.oauth.AsyncTokenManager

## Token storage

### TokenStorage

::: warmbly.oauth.TokenStorage

### MemoryTokenStorage

::: warmbly.oauth.MemoryTokenStorage

### FileTokenStorage

::: warmbly.oauth.FileTokenStorage

### KeyringTokenStorage

::: warmbly.oauth.KeyringTokenStorage

## PKCE helpers

::: warmbly.oauth.generate_pkce_pair

::: warmbly.oauth.challenge_for_verifier

::: warmbly.oauth.verify_pkce
