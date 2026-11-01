"""The ``ai_tools`` resource: the REST tool surface for external AI agents.

Maps to the ``/v1/ai/tools`` route group, which exposes the same shared tool
registry as the MCP endpoint to agents that speak plain HTTP (OpenAI-style
function calling, Hermes, or anything else). The list reflects only the tools
the calling credential may actually use, and send-class tools — anything that
puts real mail on the wire — are never exposed here.

Ask for ``format="openai"`` to get objects usable verbatim in an
OpenAI-compatible ``tools`` array::

    tools = [t.to_dict() for t in client.ai_tools.list(format="openai")]
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AITools",
    "AgentTool",
    "AgentToolCall",
    "AgentToolOutput",
    "AsyncAITools",
]


class AgentTool(BaseModel):
    """One callable tool.

    In the default (``warmbly``) format the tool is described by ``name``,
    ``description`` and ``input_schema``. In the ``openai`` format the same
    tool arrives as ``type="function"`` plus a ``function`` object holding the
    name, description and ``parameters`` schema.
    """

    name: str | None = None
    description: str | None = None
    input_schema: dict[str, Any] | None = None
    type: str | None = None
    function: dict[str, Any] | None = None


class AgentToolOutput(BaseModel):
    """A tool's output.

    ``result`` is the tool's own JSON when it returned JSON (they all do
    today), and the raw string otherwise.
    """

    name: str | None = None
    result: Any = None


class AgentToolCall(BaseModel):
    """The envelope a tool call returns."""

    data: AgentToolOutput | None = None


class AITools(SyncAPIResource):
    """Synchronous ``ai_tools`` resource."""

    def list(
        self,
        *,
        format: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[AgentTool]:
        """List the tools this credential may call.

        Args:
            format: ``"warmbly"`` (default) for the registry shape, or
                ``"openai"`` (aliases: ``"hermes"``, ``"functions"``) for
                OpenAI function-calling objects.

        Raises:
            PermissionDeniedError: The credential is an API key limited to
                specific mailboxes, or a member session whose role does not
                include the AI assistant.
        """
        return self._get_api_list(
            "/ai/tools",
            model=AgentTool,
            query=drop_not_given({"format": format}),
            options=options,
        )

    def call(
        self,
        name: str,
        *,
        arguments: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> AgentToolCall:
        """Call a tool by name.

        Args:
            name: The tool name, as listed by :meth:`list`.
            arguments: The tool's argument object. Omit it for a tool that
                takes none.

        Raises:
            NotFoundError: The tool does not exist, or is send-class and so is
                never callable over this surface.
            PermissionDeniedError: The credential lacks the tool's permission;
                the credential is an API key limited to specific mailboxes
                (the tools act across the whole workspace, so use the REST
                endpoints instead); a member session's role does not include
                the AI assistant; or the change needs a fresh confirmation
                (error code ``reauth_required``).
            UnprocessableEntityError: The tool failed with a message meant for
                the caller, for the agent to read and react to. Any other
                tool failure arrives as a server error.
        """
        return self._post(
            f"/ai/tools/{name}/call",
            cast_to=AgentToolCall,
            body=dict(arguments) if arguments is not None else {},
            options=options,
        )


class AsyncAITools(AsyncAPIResource):
    """Asynchronous ``ai_tools`` resource."""

    def list(
        self,
        *,
        format: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[AgentTool]:
        """List the tools this credential may call.

        Args:
            format: ``"warmbly"`` (default) for the registry shape, or
                ``"openai"`` (aliases: ``"hermes"``, ``"functions"``) for
                OpenAI function-calling objects.

        Raises:
            PermissionDeniedError: The credential is an API key limited to
                specific mailboxes, or a member session whose role does not
                include the AI assistant.
        """
        return self._get_api_list(
            "/ai/tools",
            model=AgentTool,
            query=drop_not_given({"format": format}),
            options=options,
        )

    async def call(
        self,
        name: str,
        *,
        arguments: Mapping[str, Any] | None = None,
        options: RequestOptions | None = None,
    ) -> AgentToolCall:
        """Call a tool by name.

        Args:
            name: The tool name, as listed by :meth:`list`.
            arguments: The tool's argument object. Omit it for a tool that
                takes none.

        Raises:
            NotFoundError: The tool does not exist, or is send-class and so is
                never callable over this surface.
            PermissionDeniedError: The credential lacks the tool's permission;
                the credential is an API key limited to specific mailboxes
                (the tools act across the whole workspace, so use the REST
                endpoints instead); a member session's role does not include
                the AI assistant; or the change needs a fresh confirmation
                (error code ``reauth_required``).
            UnprocessableEntityError: The tool failed with a message meant for
                the caller, for the agent to read and react to. Any other
                tool failure arrives as a server error.
        """
        return await self._post(
            f"/ai/tools/{name}/call",
            cast_to=AgentToolCall,
            body=dict(arguments) if arguments is not None else {},
            options=options,
        )
