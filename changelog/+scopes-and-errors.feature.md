Added the `ai_agent` and `ai_research` scopes, exported `SCOPES`, `ALL_SCOPES`,
`READ_ONLY_SCOPES`, and `FULL_ACCESS_SCOPES`, and mapped the status codes the
API returns but the SDK ignored: `PaymentRequiredError` (402, out of AI
credits), `NotImplementedAPIError` (501), and `ServiceUnavailableError` (503).
