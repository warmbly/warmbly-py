"""The realtime gateway from ordinary synchronous code.

``GatewayClient`` runs the async gateway on a background thread, so your handlers
can be plain functions and the calls block. Handy for scripts and workers that
aren't built around asyncio.
"""

from __future__ import annotations

import os
from typing import Any

from warmbly import GatewayClient, GatewayEvent

ORG_ID = "org:00000000-0000-0000-0000-000000000000"


def main() -> None:
    gateway = GatewayClient(token=os.environ["WARMBLY_API_KEY"])

    # Handlers may be plain (sync) functions.
    @gateway.on_event(GatewayEvent.EMAIL_OPENED)
    def on_open(payload: dict[str, Any]) -> None:
        print("opened:", payload)

    gateway.connect()
    gateway.subscribe(ORG_ID)
    print("subscribed; listening...")

    try:
        gateway.run_forever()  # blocks until close() is called
    except KeyboardInterrupt:
        pass
    finally:
        gateway.close()


if __name__ == "__main__":
    main()
