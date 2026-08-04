`verify_webhook_signature` now implements the scheme the gateway actually uses:
`X-Warmbly-Signature: t=<unix>,v1=<hex>`, digesting `"{t}.{raw_body}"`. It
previously computed a bare `sha256=<hex>` over the body alone and would have
rejected every real delivery. It also enforces a 300-second replay window
(override with `tolerance=`) and accepts multiple `v1` digests during a secret
rotation.
