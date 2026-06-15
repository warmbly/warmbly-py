"""Handle errors, rate limits, retries, and timeouts.

Every error inherits from ``WarmblyError``; HTTP failures map to a
status-specific subclass carrying ``.status_code``, ``.request_id``, and ``.body``.
"""

from __future__ import annotations

import httpx

from warmbly import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    Warmbly,
    WarmblyError,
)


def main() -> None:
    # Tune transport behavior: per-request timeout and automatic retries
    # (408/409/429/5xx use exponential backoff with jitter).
    client = Warmbly(
        timeout=httpx.Timeout(30.0, connect=5.0),
        max_retries=3,
    )

    # Catch a specific status...
    try:
        client.campaigns.retrieve("does-not-exist")
    except NotFoundError as err:
        print(f"not found (request {err.request_id}): {err.message}")

    # ...handle rate limits with the server-provided backoff hint...
    try:
        for _ in range(1000):
            client.api_keys.list()
    except RateLimitError as err:
        print(f"rate limited; retry after {err.retry_after}s")

    # ...or catch broad categories.
    try:
        client.campaigns.create(name="x")
    except AuthenticationError:
        print("check your API key")
    except (APITimeoutError, APIConnectionError) as err:
        print("network problem:", err)
    except WarmblyError as err:
        print("something else went wrong:", err)

    # Override retries/timeout for a single call via `options`.
    client.api_keys.list(options={"max_retries": 0, "timeout": 5.0})

    client.close()


if __name__ == "__main__":
    main()
