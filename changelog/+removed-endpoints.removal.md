Removed `plans.retrieve()` and the OAuth `client_credentials` grant. Neither
exists on the server: there is no per-plan route, and the token endpoint accepts
only `authorization_code` and `refresh_token`.
