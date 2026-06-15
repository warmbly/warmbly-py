"""Subscribe to live events over the realtime gateway (asyncio).

The token needs the ``realtime_subscribe`` scope. Reconnection, heartbeats, and
session resume are handled for you.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from warmbly import AsyncGatewayClient, GatewayEvent

ORG_ID = "org:00000000-0000-0000-0000-000000000000"


async def main() -> None:
    gateway = AsyncGatewayClient(token=os.environ["WARMBLY_API_KEY"])

    # Register handlers by event name (any topic)...
    @gateway.on_event(GatewayEvent.CAMPAIGN_STARTED)
    async def on_started(payload: dict[str, Any]) -> None:
        print("campaign started:", payload.get("campaign_id"))

    @gateway.on_event(GatewayEvent.EMAIL_OPENED)
    async def on_open(payload: dict[str, Any]) -> None:
        print("email opened:", payload)

    # ...or scope a handler to a specific (topic, event) pair.
    @gateway.on((ORG_ID, GatewayEvent.EMAIL_REPLIED))
    async def on_reply(payload: dict[str, Any]) -> None:
        print("reply on this org:", payload)

    await gateway.connect()

    # Join a topic; optionally filter events and request resume on reconnect.
    reply = await gateway.subscribe(ORG_ID, intents=["CAMPAIGN", "EMAIL"])
    print("joined; resume supported:", reply.get("resume_supported"))
    print("members online:", gateway.presence(ORG_ID))

    # Wait for a single specific event (with a timeout).
    try:
        payload = await gateway.wait_for(GatewayEvent.CAMPAIGN_COMPLETED, timeout=30)
        print("a campaign completed:", payload)
    except asyncio.TimeoutError:
        print("no completion within 30s")

    # Block and process events until interrupted (auto-reconnecting).
    try:
        await gateway.run_forever()
    finally:
        await gateway.close()


if __name__ == "__main__":
    asyncio.run(main())
