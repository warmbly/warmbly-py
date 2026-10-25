A `503` with code `ai_not_configured` is no longer retried, since it means the deployment has no AI provider. Other `503` responses are still retried, honoring `Retry-After`.
