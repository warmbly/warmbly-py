"""Receive and verify webhooks, and manage webhook endpoints.

Two parts:
  1. Registering/managing endpoints via the API.
  2. Verifying inbound deliveries with ``verify_webhook_signature``.
"""

from __future__ import annotations

from warmbly import Warmbly, WarmblyError, verify_webhook_signature


def manage_endpoints() -> str:
    """Register an endpoint and return its signing secret."""
    client = Warmbly()

    endpoint = client.webhooks.create(
        url="https://app.example.com/webhooks/warmbly",
        event_types=["campaign.started", "campaign.completed", "inbox.reply_received"],
        description="Production webhook receiver",
    )
    print("endpoint:", endpoint.id)
    print("secret:", endpoint.secret)  # shown only here; store it now

    # See what event types are available. `firehose` marks the high-volume ones.
    for event_type in client.webhooks.event_types():
        print("  event type:", event_type.type, event_type.category)

    # Ask Warmbly to challenge the endpoint. It flips to verified once your
    # handler echoes the `challenge` value from the body.
    print("verification:", client.webhooks.verify(endpoint.id).status)

    # Inspect what has been delivered, and retry anything that failed.
    for delivery in client.webhooks.endpoint_deliveries(endpoint.id, status="failed"):
        print("  failed:", delivery.event_type, delivery.error_reason)
        client.webhooks.redeliver(delivery.id)

    # Rotate the signing secret when needed.
    rotated = client.webhooks.rotate_secret(endpoint.id)
    client.close()
    return rotated.secret or ""


# --- Receiving side -------------------------------------------------------
# Verify the signature before trusting any payload. Pass the RAW request body
# (never a re-serialized dict) and the `X-Warmbly-Signature` header.
#
# The header is `t=<unix>,v1=<hex>`, where the digest covers "{t}.{raw_body}".
# Folding the timestamp in is what makes a captured request un-replayable, and
# `verify_webhook_signature` enforces a 5-minute window by default.


def handle_delivery(raw_body: bytes, signature_header: str, secret: str) -> None:
    try:
        event = verify_webhook_signature(
            payload=raw_body,
            signature=signature_header,  # "t=<unix>,v1=<hex>"
            secret=secret,
        )
    except WarmblyError as exc:
        # Bad signature, malformed header, or a stale timestamp: reject it
        # (e.g. return HTTP 400).
        print("rejecting delivery:", exc)
        return

    # Trusted: dispatch on the event type.
    print("verified event:", event["event_type"])


# Example with Flask (pip install flask):
#
#     from flask import Flask, request, abort
#     app = Flask(__name__)
#
#     @app.post("/webhooks/warmbly")
#     def receive():
#         try:
#             event = verify_webhook_signature(
#                 payload=request.get_data(),                  # raw bytes
#                 signature=request.headers["X-Warmbly-Signature"],
#                 secret=ENDPOINT_SECRET,
#             )
#         except WarmblyError:
#             abort(400)
#         # X-Warmbly-Event-Id is stable across retries: dedupe on it.
#         handle(event, request.headers["X-Warmbly-Event-Id"])
#         return "", 204


if __name__ == "__main__":
    import hashlib
    import hmac
    import json
    import time

    # Demonstrate verification locally with a self-signed payload.
    secret = "whsec_demo"
    body = json.dumps({"event_type": "campaign.started", "data": {}}).encode()
    timestamp = int(time.time())
    digest = hmac.new(
        secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256
    ).hexdigest()
    handle_delivery(body, f"t={timestamp},v1={digest}", secret)
