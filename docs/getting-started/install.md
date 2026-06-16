# Install

## Requirements

warmbly-py supports **Python 3.10 and newer** (3.10, 3.11, 3.12, 3.13, 3.14).

## Install from PyPI

```bash
pip install warmbly
```

This pulls in everything you need for the REST client, the realtime gateway,
and webhook verification.

## The `oauth` extra

Interactive OAuth2 flows work out of the box, but storing tokens in your
operating system's keychain requires an extra dependency. Install it with the
`oauth` extra:

```bash
pip install "warmbly[oauth]"
```

The extra adds [`keyring`](https://pypi.org/project/keyring/), which powers
`warmbly.oauth.KeyringTokenStorage`. Without it, in-memory and encrypted-file
token storage (`MemoryTokenStorage` / `FileTokenStorage`) still work. See the
[OAuth2 guide](../guides/oauth.md).

!!! tip "Use a virtual environment"
    Install into a project-local virtual environment to keep dependencies
    isolated:

    ```bash
    python -m venv .venv
    source .venv/bin/activate      # Windows: .venv\Scripts\activate
    pip install "warmbly[oauth]"
    ```

## Verify the install

Confirm the package imports and check the version:

```bash
python -c "import warmbly; print(warmbly.__version__)"
```

You can also confirm the top-level names are importable:

```python
from warmbly import Warmbly, AsyncWarmbly
from warmbly.oauth import OAuth2Client
from warmbly import AsyncGatewayClient, verify_webhook_signature

print("warmbly is ready")
```

If those imports succeed, you're set. Head to the
[Quickstart](quickstart.md) to make your first API call.
