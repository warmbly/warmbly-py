"""The transport core shared by the sync and async clients.

This module is the single place that speaks HTTP (via ``httpx``). It owns the
connection pool, header/auth assembly, the retry loop with exponential backoff
and jitter, idempotency-key injection, response parsing into models, and the
mapping of failures onto the SDK exception tree. ``httpx`` types never escape
into a public signature or a raised exception, so the transport can be replaced
without breaking callers.
"""

from __future__ import annotations

import asyncio
import email.utils
import random
import time
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING, Any, TypeVar

import httpx

from ._exceptions import (
    APIConnectionError,
    APITimeoutError,
    make_status_error,
)
from ._models import construct_type
from ._pagination import AsyncCursorPage, AsyncPaginator, SyncCursorPage
from ._types import NOT_GIVEN, NotGiven, Omit, RequestOptions, Timeout
from ._utils import drop_not_given, logger
from ._utils._logs import redact, redact_headers

if TYPE_CHECKING:
    from ._pagination import ModelT

_T = TypeVar("_T")

DEFAULT_MAX_RETRIES = 2
DEFAULT_TIMEOUT = httpx.Timeout(timeout=60.0, connect=5.0)
DEFAULT_CONNECTION_LIMITS = httpx.Limits(
    max_connections=100, max_keepalive_connections=20
)

INITIAL_RETRY_DELAY = 0.5
MAX_RETRY_DELAY = 8.0
MAX_SERVER_RETRY_AFTER = 60.0

# Methods that are inherently safe to retry. POST is retried only when it
# carries an Idempotency-Key.
_IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})
_RETRY_STATUS = frozenset({408, 409, 429})


def _user_agent() -> str:
    try:
        return f"warmbly-python/{version('warmbly')}"
    except PackageNotFoundError:  # pragma: no cover - source checkout
        return "warmbly-python/0.0.0+dev"


def _parse_retry_after(
    headers: Mapping[str, str], body: object | None = None
) -> float | None:
    """Return seconds to wait from ``Retry-After`` or a ``retry_after`` body."""
    if isinstance(body, dict):
        value = body.get("retry_after")
        if isinstance(value, (int, float)):
            return float(value)
    raw = headers.get("retry-after") or headers.get("Retry-After")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        pass
    try:
        parsed = email.utils.parsedate_to_datetime(raw)
    except (ValueError, TypeError):  # pragma: no cover - malformed header
        return None
    delta = parsed.timestamp() - time.time()
    return max(delta, 0.0)


@dataclass
class _PreparedRequest:
    method: str
    url: str
    headers: dict[str, str]
    params: dict[str, Any] | None
    json: Any | None
    data: Mapping[str, Any] | None
    files: Mapping[str, Any] | None
    timeout: float | Timeout | None
    max_retries: int
    has_idempotency_key: bool


class BaseClient:
    """Configuration and transport-agnostic helpers shared by both clients."""

    def __init__(
        self,
        *,
        base_url: str,
        timeout: float | Timeout | None,
        max_retries: int,
        custom_headers: Mapping[str, str] | None = None,
    ) -> None:
        self._base_url = str(base_url).rstrip("/") + "/"
        self._timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
        self._max_retries = max_retries
        self._custom_headers = dict(custom_headers or {})

    # -- overridable auth ---------------------------------------------------
    @property
    def auth_headers(self) -> dict[str, str]:
        """Authentication headers injected on every request (subclass hook)."""
        return {}

    # -- pure request assembly ---------------------------------------------
    def _build_url(self, path: str) -> str:
        return self._base_url + path.lstrip("/")

    def _build_headers(
        self,
        method: str,
        options: RequestOptions,
        *,
        has_json_body: bool,
        is_form: bool,
    ) -> tuple[dict[str, str], bool]:
        headers: dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": _user_agent(),
        }
        if has_json_body:
            headers["Content-Type"] = "application/json"
        headers.update(self._custom_headers)
        headers.update(self.auth_headers)

        extra = options.get("headers") or {}
        omitted_idempotency = False
        for key, value in extra.items():
            if isinstance(value, Omit):
                _pop_header(headers, key)
                if key.lower() == "idempotency-key":
                    omitted_idempotency = True
            else:
                _set_header(headers, key, value)

        has_idempotency = _get_header(headers, "idempotency-key") is not None
        if (
            method == "POST"
            and not is_form
            and not has_idempotency
            and not omitted_idempotency
        ):
            idem = options.get("idempotency_key")
            headers["Idempotency-Key"] = idem if idem else str(uuid.uuid4())
            has_idempotency = True
        return headers, has_idempotency

    def _clean_query(
        self, query: Mapping[str, object] | None, options: RequestOptions
    ) -> dict[str, Any] | None:
        merged: dict[str, Any] = {}
        if query:
            merged.update(query)
        extra = options.get("query")
        if extra:
            merged.update(extra)
        cleaned = {
            key: value
            for key, value in drop_not_given(merged).items()
            if value is not None
        }
        return cleaned or None

    def _prepare(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
        form_body: Mapping[str, Any] | None = None,
        files: Mapping[str, Any] | None = None,
        query: Mapping[str, object] | None = None,
        options: RequestOptions | None = None,
    ) -> _PreparedRequest:
        method = method.upper()
        options = options or RequestOptions()
        has_json_body = json_body is not None
        # Multipart counts as a form: httpx sets its own Content-Type (with the
        # boundary), and an Idempotency-Key on a file upload buys nothing.
        is_form = form_body is not None or files is not None
        headers, has_idempotency = self._build_headers(
            method, options, has_json_body=has_json_body, is_form=is_form
        )
        json_payload = (
            drop_not_given(json_body) if isinstance(json_body, Mapping) else json_body
        )
        timeout = options.get("timeout", NOT_GIVEN)
        resolved_timeout = self._timeout if isinstance(timeout, NotGiven) else timeout
        prepared = _PreparedRequest(
            method=method,
            url=self._build_url(path),
            headers=headers,
            params=self._clean_query(query, options),
            json=json_payload,
            data=dict(form_body) if form_body is not None else None,
            files=dict(files) if files is not None else None,
            timeout=resolved_timeout,
            max_retries=options.get("max_retries", self._max_retries),
            has_idempotency_key=has_idempotency,
        )
        logger.debug(
            "request %s %s headers=%s json=%s params=%s",
            prepared.method,
            prepared.url,
            redact_headers(prepared.headers),
            redact(prepared.json),
            redact(prepared.params),
        )
        return prepared

    # -- retry policy -------------------------------------------------------
    def _should_retry(
        self, method: str, status_code: int, *, has_idempotency_key: bool
    ) -> bool:
        if method not in _IDEMPOTENT_METHODS and not has_idempotency_key:
            return False
        return status_code in _RETRY_STATUS or status_code >= 500

    def _retry_delay(self, attempt: int, headers: Mapping[str, str] | None) -> float:
        if headers is not None:
            server = _parse_retry_after(headers)
            if server is not None and 0 < server <= MAX_SERVER_RETRY_AFTER:
                return server
        base = min(INITIAL_RETRY_DELAY * 2.0**attempt, MAX_RETRY_DELAY)
        return base * (1 - 0.25 * random.random())  # 0.75x-1.0x jitter

    # -- response handling --------------------------------------------------
    def _parse_response(self, response: httpx.Response, cast_to: type[_T]) -> _T:
        request_id = response.headers.get("x-request-id")
        if response.status_code == 204:
            return construct_type(cast_to, None, request_id=request_id)
        # A few endpoints stream a file rather than JSON (contact export).
        # Asking for bytes hands back the body verbatim, so binary formats
        # survive intact.
        if cast_to is bytes:
            return response.content  # type: ignore[return-value]
        data = _safe_json(response)
        logger.debug(
            "response %s %s request_id=%s",
            response.status_code,
            response.request.url,
            request_id,
        )
        return construct_type(cast_to, data, request_id=request_id)

    def _build_status_error(self, response: httpx.Response) -> Exception:
        request_id = response.headers.get("x-request-id")
        body = _safe_json(response)
        retry_after = _parse_retry_after(response.headers, body)
        logger.debug(
            "error %s request_id=%s body=%s",
            response.status_code,
            request_id,
            redact(body),
        )
        return make_status_error(
            status_code=response.status_code,
            request_id=request_id,
            headers=dict(response.headers),
            body=body,
            retry_after=retry_after,
        )

    def _page_fields(
        self, response: httpx.Response, data_key: str = "data"
    ) -> tuple[list[Any], str | None, bool, int | None, str | None]:
        request_id = response.headers.get("x-request-id")
        payload = _safe_json(response)
        # A handful of endpoints return the collection as a bare JSON array
        # rather than an envelope; treat that as a single, final page.
        if isinstance(payload, list):
            return list(payload), None, False, None, request_id
        if not isinstance(payload, dict):
            return [], None, False, None, request_id
        data = payload.get(data_key) or []
        pagination = payload.get("pagination") or {}
        return (
            list(data),
            pagination.get("next_cursor"),
            bool(pagination.get("has_more", False)),
            pagination.get("total"),
            request_id,
        )


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return response.text or None


def _set_header(headers: dict[str, str], key: str, value: str) -> None:
    _pop_header(headers, key)
    headers[key] = value


def _pop_header(headers: dict[str, str], key: str) -> None:
    for existing in [k for k in headers if k.lower() == key.lower()]:
        headers.pop(existing)


def _get_header(headers: Mapping[str, str], key: str) -> str | None:
    for existing, value in headers.items():
        if existing.lower() == key.lower():
            return value
    return None


# ---------------------------------------------------------------------------
# Synchronous client
# ---------------------------------------------------------------------------
class SyncAPIClient(BaseClient):
    """Synchronous transport built on :class:`httpx.Client`."""

    _http: httpx.Client

    def __init__(
        self,
        *,
        base_url: str,
        timeout: float | Timeout | None = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        custom_headers: Mapping[str, str] | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            custom_headers=custom_headers,
        )
        self._http = http_client or httpx.Client(
            timeout=self._timeout,
            limits=DEFAULT_CONNECTION_LIMITS,
            follow_redirects=True,
        )

    def close(self) -> None:
        """Close the underlying connection pool."""
        self._http.close()

    def __enter__(self) -> SyncAPIClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _send(self, prepared: _PreparedRequest) -> httpx.Response:
        remaining = prepared.max_retries
        attempt = 0
        while True:
            try:
                response = self._http.request(
                    prepared.method,
                    prepared.url,
                    headers=prepared.headers,
                    params=prepared.params,
                    json=prepared.json,
                    data=prepared.data,
                    files=prepared.files,
                    timeout=prepared.timeout,
                )
            except httpx.TimeoutException as exc:
                if remaining > 0:
                    remaining, attempt = remaining - 1, attempt + 1
                    time.sleep(self._retry_delay(attempt, None))
                    continue
                raise APITimeoutError(cause=exc) from exc
            except httpx.HTTPError as exc:
                if remaining > 0:
                    remaining, attempt = remaining - 1, attempt + 1
                    time.sleep(self._retry_delay(attempt, None))
                    continue
                raise APIConnectionError(cause=exc) from exc

            if response.is_success:
                return response
            if remaining > 0 and self._should_retry(
                prepared.method,
                response.status_code,
                has_idempotency_key=prepared.has_idempotency_key,
            ):
                remaining, attempt = remaining - 1, attempt + 1
                time.sleep(self._retry_delay(attempt, response.headers))
                response.close()
                continue
            raise self._build_status_error(response)

    def request(
        self,
        *,
        cast_to: type[_T],
        method: str,
        path: str,
        body: Any | None = None,
        form: Mapping[str, Any] | None = None,
        files: Mapping[str, Any] | None = None,
        query: Mapping[str, object] | None = None,
        options: RequestOptions | None = None,
    ) -> _T:
        prepared = self._prepare(
            method,
            path,
            json_body=body,
            form_body=form,
            files=files,
            query=query,
            options=options,
        )
        return self._parse_response(self._send(prepared), cast_to)

    def get(self, path: str, *, cast_to: type[_T], **kwargs: Any) -> _T:
        return self.request(cast_to=cast_to, method="GET", path=path, **kwargs)

    def post(self, path: str, *, cast_to: type[_T], **kwargs: Any) -> _T:
        return self.request(cast_to=cast_to, method="POST", path=path, **kwargs)

    def patch(self, path: str, *, cast_to: type[_T], **kwargs: Any) -> _T:
        return self.request(cast_to=cast_to, method="PATCH", path=path, **kwargs)

    def put(self, path: str, *, cast_to: type[_T], **kwargs: Any) -> _T:
        return self.request(cast_to=cast_to, method="PUT", path=path, **kwargs)

    def delete(self, path: str, *, cast_to: type[_T], **kwargs: Any) -> _T:
        return self.request(cast_to=cast_to, method="DELETE", path=path, **kwargs)

    def get_api_list(
        self,
        path: str,
        *,
        model: type[ModelT],
        query: Mapping[str, object] | None = None,
        options: RequestOptions | None = None,
        data_key: str = "data",
    ) -> SyncCursorPage[ModelT]:
        base_query = dict(query or {})

        def fetch(cursor: str | None) -> SyncCursorPage[ModelT]:
            merged = dict(base_query)
            if cursor is not None:
                merged["cursor"] = cursor
            prepared = self._prepare("GET", path, query=merged, options=options)
            response = self._send(prepared)
            data, next_cursor, has_more, total, request_id = self._page_fields(
                response, data_key
            )
            items = [
                construct_type(model, item, request_id=request_id) for item in data
            ]
            return SyncCursorPage(
                data=items,
                next_cursor=next_cursor,
                has_more=has_more,
                total=total,
                fetch_next=lambda c: fetch(c),
            )

        return fetch(None)


# ---------------------------------------------------------------------------
# Asynchronous client
# ---------------------------------------------------------------------------
class AsyncAPIClient(BaseClient):
    """Asynchronous transport built on :class:`httpx.AsyncClient`."""

    _http: httpx.AsyncClient

    def __init__(
        self,
        *,
        base_url: str,
        timeout: float | Timeout | None = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        custom_headers: Mapping[str, str] | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            custom_headers=custom_headers,
        )
        self._http = http_client or httpx.AsyncClient(
            timeout=self._timeout,
            limits=DEFAULT_CONNECTION_LIMITS,
            follow_redirects=True,
        )

    async def close(self) -> None:
        """Close the underlying connection pool."""
        await self._http.aclose()

    async def __aenter__(self) -> AsyncAPIClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def _send(self, prepared: _PreparedRequest) -> httpx.Response:
        remaining = prepared.max_retries
        attempt = 0
        while True:
            try:
                response = await self._http.request(
                    prepared.method,
                    prepared.url,
                    headers=prepared.headers,
                    params=prepared.params,
                    json=prepared.json,
                    data=prepared.data,
                    files=prepared.files,
                    timeout=prepared.timeout,
                )
            except httpx.TimeoutException as exc:
                if remaining > 0:
                    remaining, attempt = remaining - 1, attempt + 1
                    await asyncio.sleep(self._retry_delay(attempt, None))
                    continue
                raise APITimeoutError(cause=exc) from exc
            except httpx.HTTPError as exc:
                if remaining > 0:
                    remaining, attempt = remaining - 1, attempt + 1
                    await asyncio.sleep(self._retry_delay(attempt, None))
                    continue
                raise APIConnectionError(cause=exc) from exc

            if response.is_success:
                return response
            if remaining > 0 and self._should_retry(
                prepared.method,
                response.status_code,
                has_idempotency_key=prepared.has_idempotency_key,
            ):
                remaining, attempt = remaining - 1, attempt + 1
                await asyncio.sleep(self._retry_delay(attempt, response.headers))
                await response.aclose()
                continue
            raise self._build_status_error(response)

    async def request(
        self,
        *,
        cast_to: type[_T],
        method: str,
        path: str,
        body: Any | None = None,
        form: Mapping[str, Any] | None = None,
        files: Mapping[str, Any] | None = None,
        query: Mapping[str, object] | None = None,
        options: RequestOptions | None = None,
    ) -> _T:
        prepared = self._prepare(
            method,
            path,
            json_body=body,
            form_body=form,
            files=files,
            query=query,
            options=options,
        )
        return self._parse_response(await self._send(prepared), cast_to)

    async def get(self, path: str, *, cast_to: type[_T], **kwargs: Any) -> _T:
        return await self.request(cast_to=cast_to, method="GET", path=path, **kwargs)

    async def post(self, path: str, *, cast_to: type[_T], **kwargs: Any) -> _T:
        return await self.request(cast_to=cast_to, method="POST", path=path, **kwargs)

    async def patch(self, path: str, *, cast_to: type[_T], **kwargs: Any) -> _T:
        return await self.request(cast_to=cast_to, method="PATCH", path=path, **kwargs)

    async def put(self, path: str, *, cast_to: type[_T], **kwargs: Any) -> _T:
        return await self.request(cast_to=cast_to, method="PUT", path=path, **kwargs)

    async def delete(self, path: str, *, cast_to: type[_T], **kwargs: Any) -> _T:
        return await self.request(cast_to=cast_to, method="DELETE", path=path, **kwargs)

    def get_api_list(
        self,
        path: str,
        *,
        model: type[ModelT],
        query: Mapping[str, object] | None = None,
        options: RequestOptions | None = None,
        data_key: str = "data",
    ) -> AsyncPaginator[ModelT]:
        base_query = dict(query or {})

        async def fetch(cursor: str | None) -> AsyncCursorPage[ModelT]:
            merged = dict(base_query)
            if cursor is not None:
                merged["cursor"] = cursor
            prepared = self._prepare("GET", path, query=merged, options=options)
            response = await self._send(prepared)
            data, next_cursor, has_more, total, request_id = self._page_fields(
                response, data_key
            )
            items = [
                construct_type(model, item, request_id=request_id) for item in data
            ]
            return AsyncCursorPage(
                data=items,
                next_cursor=next_cursor,
                has_more=has_more,
                total=total,
                fetch_next=lambda c: fetch(c),
            )

        # Returned un-awaited so callers can both `await` it and `async for` it.
        return AsyncPaginator(fetch)
