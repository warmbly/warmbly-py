"""Hand Warmbly's tools to an OpenAI-compatible agent loop.

``client.ai_tools`` exposes the same registry as the MCP endpoint over plain
HTTP. The listing reflects only what the calling credential may use, and
send-class tools — anything that puts real mail on the wire — are never
exposed here.
"""

from __future__ import annotations

import json
import os

from warmbly import Warmbly


def main() -> None:
    client = Warmbly(api_key=os.environ["WARMBLY_API_KEY"])

    # `format="openai"` returns objects usable verbatim in a `tools` array.
    tools = [tool.to_dict() for tool in client.ai_tools.list(format="openai")]
    print(json.dumps(tools, indent=2))

    # The default shape is the registry's own: name, description, input_schema.
    for tool in client.ai_tools.list():
        print(f"{tool.name}: {tool.description}")

    # Calling one: the arguments are the tool's own argument object, and the
    # result is its output, already decoded when the tool returned JSON.
    call = client.ai_tools.call("list_campaigns", arguments={"status": "active"})
    if call.data is not None:
        print(call.data.name, "->", call.data.result)


if __name__ == "__main__":
    main()
