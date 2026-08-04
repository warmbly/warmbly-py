"""The OAuth2 authorization-code (+PKCE) and refresh flows.

:class:`OAuth2Client` (sync) and :class:`AsyncOAuth2Client` (async) drive the
two grants Warmbly's authorization server accepts:

* **authorization_code + PKCE (S256)**: the interactive browser flow.
* **refresh_token**: exchange a (rotating) refresh token for a fresh token set.

There is no client-credentials grant: every token is bound to a user who
consented, so machine-to-machine access uses an API key instead.

This module uses ``httpx`` directly (the OAuth subsystem is permitted to), but
never lets an ``httpx`` exception escape: transport failures and RFC 6749 error
responses are both surfaced as :class:`~warmbly.OAuthError`.
"""

from __future__ import annotations

import base64
import secrets
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

import httpx

from .._exceptions import OAuthError
from .._utils import drop_not_given
from ._pkce import generate_pkce_pair
from ._tokens import OAuth2Token

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = ["AsyncOAuth2Client", "OAuth2Client"]

DEFAULT_BASE_URL = "https://api.warmbly.com"
DEFAULT_APP_URL = "https://app.warmbly.com"

_AUTHORIZE_PATH = "/oauth/authorize"
_TOKEN_PATH = "/v1/oauth/token"
_REVOKE_PATH = "/v1/oauth/revoke"


def _basic_auth_header(client_id: str, client_secret: str) -> str:
    raw = f"{client_id}:{client_secret}".encode()
    return "Basic " + base64.b64encode(raw).decode("ascii")


def _parse_token_response(payload: Any) -> OAuth2Token:
    """Turn a token-endpoint JSON body into a token, or raise on an error body.

    Args:
        payload: The parsed JSON response body.

    Returns:
        The parsed :class:`OAuth2Token`.

    Raises:
        OAuthError: If *payload* is an RFC 6749 error or is otherwise unusable.
    """
    if not isinstance(payload, dict):
        raise OAuthError(
            "invalid_response", "Token endpoint returned a non-object response."
        )
    error = payload.get("error")
    if error:
        raise OAuthError(str(error), _as_optional_str(payload.get("error_description")))
    if "access_token" not in payload:
        raise OAuthError(
            "invalid_response", "Token response did not include an access_token."
        )
    return OAuth2Token.model_validate(payload)


def _as_optional_str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _error_from_response(response: httpx.Response) -> OAuthError:
    """Build an :class:`OAuthError` from a non-success token/revoke response."""
    try:
        body = response.json()
    except ValueError:
        body = None
    if isinstance(body, dict) and body.get("error"):
        return OAuthError(
            str(body["error"]), _as_optional_str(body.get("error_description"))
        )
    return OAuthError(
        "http_error",
        f"OAuth endpoint returned HTTP {response.status_code}.",
    )


class _OAuth2ClientBase:
    """Shared configuration and request-assembly for both client variants."""

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str | None = None,
        redirect_uri: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        app_url: str = DEFAULT_APP_URL,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._base_url = base_url.rstrip("/")
        self._app_url = app_url.rstrip("/")

    # -- endpoint URLs ------------------------------------------------------
    @property
    def authorization_endpoint(self) -> str:
        """The browser authorization endpoint (on the app URL)."""
        return self._app_url + _AUTHORIZE_PATH

    @property
    def token_endpoint(self) -> str:
        """The token endpoint (on the API base URL)."""
        return self._base_url + _TOKEN_PATH

    @property
    def revocation_endpoint(self) -> str:
        """The token-revocation endpoint (on the API base URL)."""
        return self._base_url + _REVOKE_PATH

    # -- pure request assembly ---------------------------------------------
    def authorization_url(
        self, *, scopes: list[str], state: str | None = None
    ) -> tuple[str, str, str]:
        """Build the authorization-request URL with PKCE and CSRF state.

        Generates a fresh PKCE ``S256`` pair and (if not supplied) a random
        ``state`` for CSRF protection. The caller must retain the returned
        ``state`` and ``code_verifier`` to validate and complete the callback.

        Args:
            scopes: The scopes to request (space-joined into the ``scope``
                parameter).
            state: An optional caller-provided CSRF state; a 32-byte URL-safe
                random value is generated when omitted.

        Returns:
            A ``(url, state, code_verifier)`` tuple. Send the user to ``url``;
            keep ``state`` and ``code_verifier`` for :meth:`exchange_code`.
        """
        if state is None:
            state = secrets.token_urlsafe(32)
        code_verifier, code_challenge = generate_pkce_pair()
        params = {
            "response_type": "code",
            "client_id": self._client_id,
            "redirect_uri": self._require_redirect_uri(None),
            "scope": " ".join(scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        url = f"{self.authorization_endpoint}?{urlencode(params)}"
        return url, state, code_verifier

    def _require_redirect_uri(self, override: str | None) -> str:
        redirect_uri = override if override is not None else self._redirect_uri
        if not redirect_uri:
            raise OAuthError(
                "invalid_request",
                "redirect_uri is required; pass it to the client or the method.",
            )
        return redirect_uri

    def _token_request(
        self, form: Mapping[str, object]
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Return ``(headers, data)`` for a token request with client auth applied.

        Prefers HTTP Basic auth when a client secret is configured; otherwise
        the ``client_id`` is placed in the body (public client).
        """
        data: dict[str, str] = {
            key: str(value) for key, value in drop_not_given(form).items()
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if self._client_secret is not None:
            headers["Authorization"] = _basic_auth_header(
                self._client_id, self._client_secret
            )
        else:
            data["client_id"] = self._client_id
        return headers, data

    def _validate_state(self, *, state: str | None, expected_state: str | None) -> None:
        if expected_state is None:
            return
        if state is None or not secrets.compare_digest(state, expected_state):
            raise OAuthError(
                "invalid_state",
                "The state returned to the callback did not match the expected value.",
            )


class OAuth2Client(_OAuth2ClientBase):
    """Synchronous OAuth2 client for the Warmbly authorization server.

    Supports the authorization-code (+PKCE S256) and refresh-token grants, plus
    token revocation. Construct it with your application's ``client_id`` (and
    ``client_secret`` for confidential clients).
    """

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str | None = None,
        redirect_uri: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        app_url: str = DEFAULT_APP_URL,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Initialize the client.

        Args:
            client_id: The OAuth application's client id (``wmcid_`` prefix).
            client_secret: The client secret (``wmcs_``) for confidential
                clients; omit for public clients that rely on PKCE.
            redirect_uri: The default redirect URI; can be overridden per call.
            base_url: The API base URL hosting the token/revocation endpoints.
            app_url: The dashboard URL hosting the browser authorize endpoint.
            http_client: An optional pre-configured :class:`httpx.Client`; when
                given it is reused and not closed by this client.
        """
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            base_url=base_url,
            app_url=app_url,
        )
        self._http = http_client
        self._owns_http = http_client is None

    def _client(self) -> httpx.Client:
        if self._http is None:
            self._http = httpx.Client(timeout=30.0, follow_redirects=True)
        return self._http

    def close(self) -> None:
        """Close the underlying HTTP client if this instance created it."""
        if self._owns_http and self._http is not None:
            self._http.close()
            self._http = None

    def __enter__(self) -> OAuth2Client:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _post_token(self, form: Mapping[str, object]) -> OAuth2Token:
        headers, data = self._token_request(form)
        try:
            response = self._client().post(
                self.token_endpoint, data=data, headers=headers
            )
        except httpx.HTTPError as exc:
            raise OAuthError("connection_error", str(exc)) from exc
        if not response.is_success:
            raise _error_from_response(response)
        try:
            payload = response.json()
        except ValueError as exc:
            raise OAuthError(
                "invalid_response", "Token endpoint returned non-JSON."
            ) from exc
        return _parse_token_response(payload)

    def exchange_code(
        self,
        code: str,
        *,
        code_verifier: str,
        redirect_uri: str | None = None,
        state: str | None = None,
        expected_state: str | None = None,
    ) -> OAuth2Token:
        """Exchange an authorization code for a token set.

        Args:
            code: The single-use authorization code (``wmac_``) from the
                callback's ``code`` parameter.
            code_verifier: The PKCE verifier returned by
                :meth:`authorization_url`.
            redirect_uri: The redirect URI to confirm; defaults to the client's
                configured value and must match the authorization request.
            state: The ``state`` returned to the callback, for CSRF validation.
            expected_state: The ``state`` originally issued; when provided it is
                compared in constant time against *state*.

        Returns:
            The issued :class:`OAuth2Token`.

        Raises:
            OAuthError: On state mismatch (``invalid_state``), an RFC 6749 error
                response, or a transport failure.
        """
        self._validate_state(state=state, expected_state=expected_state)
        form = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._require_redirect_uri(redirect_uri),
            "code_verifier": code_verifier,
        }
        return self._post_token(form)

    def refresh_token(self, refresh_token: str) -> OAuth2Token:
        """Exchange a refresh token for a fresh token set.

        Warmbly rotates refresh tokens: the response carries a new
        ``refresh_token`` that supersedes the one passed in.

        Args:
            refresh_token: The current refresh token (``wmrt_``).

        Returns:
            The new :class:`OAuth2Token` (with a rotated ``refresh_token``).

        Raises:
            OAuthError: On ``invalid_grant`` (forcing re-authentication), any
                other RFC 6749 error, or a transport failure.
        """
        form = {"grant_type": "refresh_token", "refresh_token": refresh_token}
        return self._post_token(form)

    def revoke(self, token: str) -> None:
        """Revoke an access or refresh token (RFC 7009).

        The endpoint always reports success per RFC 7009; this returns ``None``
        and only raises on a transport failure.

        Args:
            token: The access or refresh token to revoke.

        Raises:
            OAuthError: On a transport failure reaching the endpoint.
        """
        headers, data = self._token_request({"token": token})
        try:
            self._client().post(self.revocation_endpoint, data=data, headers=headers)
        except httpx.HTTPError as exc:
            raise OAuthError("connection_error", str(exc)) from exc


class AsyncOAuth2Client(_OAuth2ClientBase):
    """Asynchronous OAuth2 client for the Warmbly authorization server.

    Async mirror of :class:`OAuth2Client`: the network methods are coroutines;
    :meth:`authorization_url` stays synchronous (it performs no I/O).
    """

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str | None = None,
        redirect_uri: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        app_url: str = DEFAULT_APP_URL,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the client.

        See :meth:`OAuth2Client.__init__` for argument semantics; *http_client*
        here is an :class:`httpx.AsyncClient`.
        """
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            base_url=base_url,
            app_url=app_url,
        )
        self._http = http_client
        self._owns_http = http_client is None

    def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        return self._http

    async def close(self) -> None:
        """Close the underlying HTTP client if this instance created it."""
        if self._owns_http and self._http is not None:
            await self._http.aclose()
            self._http = None

    async def __aenter__(self) -> AsyncOAuth2Client:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def _post_token(self, form: Mapping[str, object]) -> OAuth2Token:
        headers, data = self._token_request(form)
        try:
            response = await self._client().post(
                self.token_endpoint, data=data, headers=headers
            )
        except httpx.HTTPError as exc:
            raise OAuthError("connection_error", str(exc)) from exc
        if not response.is_success:
            raise _error_from_response(response)
        try:
            payload = response.json()
        except ValueError as exc:
            raise OAuthError(
                "invalid_response", "Token endpoint returned non-JSON."
            ) from exc
        return _parse_token_response(payload)

    async def exchange_code(
        self,
        code: str,
        *,
        code_verifier: str,
        redirect_uri: str | None = None,
        state: str | None = None,
        expected_state: str | None = None,
    ) -> OAuth2Token:
        """Exchange an authorization code for a token set.

        See :meth:`OAuth2Client.exchange_code` for argument and error semantics.
        """
        self._validate_state(state=state, expected_state=expected_state)
        form = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._require_redirect_uri(redirect_uri),
            "code_verifier": code_verifier,
        }
        return await self._post_token(form)

    async def refresh_token(self, refresh_token: str) -> OAuth2Token:
        """Exchange a refresh token for a fresh (rotated) token set.

        See :meth:`OAuth2Client.refresh_token` for argument and error semantics.
        """
        form = {"grant_type": "refresh_token", "refresh_token": refresh_token}
        return await self._post_token(form)

    async def revoke(self, token: str) -> None:
        """Revoke an access or refresh token (RFC 7009).

        See :meth:`OAuth2Client.revoke` for semantics.
        """
        headers, data = self._token_request({"token": token})
        try:
            await self._client().post(
                self.revocation_endpoint, data=data, headers=headers
            )
        except httpx.HTTPError as exc:
            raise OAuthError("connection_error", str(exc)) from exc
