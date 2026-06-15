"""Async client: await calls, ``async for`` pagination, and concurrency."""

from __future__ import annotations

import asyncio

from warmbly import AsyncWarmbly


async def main() -> None:
    # `async with` closes the connection pool for you.
    async with AsyncWarmbly() as client:
        # Await single requests.
        campaign = await client.campaigns.create(name="Q3 outreach (async)")
        print("created:", campaign.id)

        # Iterate paginated lists with `async for`.
        async for key in client.api_keys.list():
            print("key:", key.name)

        # ...or await a list() to get the first page object directly.
        first_page = await client.api_keys.list(limit=10)
        print("first page size:", len(first_page.data))

        # Fan out independent requests concurrently.
        analytics, accounts, contacts = await asyncio.gather(
            client.analytics.dashboard(),
            client.emails.list(),
            client.contacts.search(limit=5),
        )
        print("dashboard:", analytics)
        print("accounts:", len(list(accounts.data)))
        print("contacts:", len(contacts.data))


if __name__ == "__main__":
    asyncio.run(main())
