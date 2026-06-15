# Exceptions

The exception tree is single-rooted at [`WarmblyError`][warmbly.WarmblyError],
so a single `except WarmblyError` catches every error the SDK raises. HTTP
failures map the backend error envelope onto per-status subclasses of
[`APIStatusError`][warmbly.APIStatusError].

```python
import warmbly

client = warmbly.Warmbly(api_key="wmbly_...")
try:
    client.campaigns.retrieve("camp_missing")
except warmbly.NotFoundError as exc:
    print(exc.status_code, exc.request_id)
except warmbly.RateLimitError as exc:
    print("retry after", exc.retry_after)
except warmbly.WarmblyError as exc:
    print("something went wrong:", exc)
```

## Base errors

### WarmblyError

::: warmbly.WarmblyError

### APIError

::: warmbly.APIError

### APIStatusError

::: warmbly.APIStatusError

## Connection errors

### APIConnectionError

::: warmbly.APIConnectionError

### APITimeoutError

::: warmbly.APITimeoutError

### APIResponseValidationError

::: warmbly.APIResponseValidationError

## Per-status errors

### BadRequestError

::: warmbly.BadRequestError

### AuthenticationError

::: warmbly.AuthenticationError

### PermissionDeniedError

::: warmbly.PermissionDeniedError

### NotFoundError

::: warmbly.NotFoundError

### ConflictError

::: warmbly.ConflictError

### UnprocessableEntityError

::: warmbly.UnprocessableEntityError

### RateLimitError

::: warmbly.RateLimitError

### InternalServerError

::: warmbly.InternalServerError

## OAuth and gateway errors

### OAuthError

::: warmbly.OAuthError

### GatewayError

::: warmbly.GatewayError
