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
        event_types=["campaign.started", "campaign.completed", "email.replied"],
        description="Production webhook receiver",
    )
    print("endpoint:", endpoint.id)

    # See what event types are available, and inspect recent deliveries.
    print("event types:", client.webhooks.event_types())
    for delivery in client.webhooks.deliveries():
        print("  delivery:", delivery)

    # Rotate the signing secret when needed.
    rotated = client.webhooks.rotate_secret(endpoint.id)
    client.close()
    return getattr(rotated, "secret", "") or ""


# --- Receiving side -------------------------------------------------------
# Verify the signature before trusting any payload. Pass the RAW request body
# (never a re-serialized dict) and the `X-Warmbly-Signature` header.


def handle_delivery(raw_body: bytes, signature_header: str, secret: str) -> None:
    try:
        event = verify_webhook_signature(
            payload=raw_body,
            signature=signature_header,  # "sha256=<hex>"
            secret=secret,
        )
    except WarmblyError:
        # Signature mismatch — reject (e.g. return HTTP 400).
        print("invalid signature; rejecting")
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
#         handle(event)
#         return "", 204


if __name__ == "__main__":
    import hashlib
    import hmac
    import json

    # Demonstrate verification locally with a self-signed payload.
    secret = "whsec_demo"
    body = json.dumps({"event_type": "campaign.started", "data": {}}).encode()
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    handle_delivery(body, sig, secret)
