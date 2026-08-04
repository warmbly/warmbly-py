"""The ``generation`` resource: the AI writing assistant.

Maps to the ``/v1/generation`` route group: write a draft from a prompt, rewrite
a selected passage, or resolve a personalization variable for one contact.

Every call charges AI credits and returns what it cost, so a client can show
the running balance without a second request. An exhausted balance surfaces as
:class:`~warmbly.PaymentRequiredError`; an org-level usage cap surfaces as
:class:`~warmbly.RateLimitError`.

None of these endpoints send email.
"""

from __future__ import annotations

from .._models import BaseModel
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncGeneration",
    "GeneratedText",
    "Generation",
]


class GeneratedText(BaseModel):
    """Generated text, plus what the call cost.

    ``credits_remaining`` is the balance *after* this call, so it can be shown
    without a follow-up read.
    """

    text: str | None = None
    credits_remaining: int | None = None
    credits_charged: int | None = None
    tokens_used: int | None = None
    model: str | None = None


class Generation(SyncAPIResource):
    """Synchronous ``generation`` resource."""

    def write(
        self,
        *,
        prompt: str,
        tone: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> GeneratedText:
        """Draft new copy from a prompt. Charges AI credits.

        Args:
            prompt: What to write.
            tone: The voice to write in.
        """
        return self._post(
            "/generation/write",
            cast_to=GeneratedText,
            body=drop_not_given({"prompt": prompt, "tone": tone}),
            options=options,
        )

    def edit(
        self,
        *,
        text: str,
        instruction: str,
        context: NotGivenOr[str] = NOT_GIVEN,
        tone: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> GeneratedText:
        """Rewrite a passage under an instruction. Charges AI credits.

        Args:
            text: The passage to rewrite.
            instruction: How to change it.
            context: The surrounding draft, so the rewrite fits its
                neighbours.
            tone: The voice to write in.
        """
        return self._post(
            "/generation/edit",
            cast_to=GeneratedText,
            body=drop_not_given(
                {
                    "text": text,
                    "instruction": instruction,
                    "context": context,
                    "tone": tone,
                }
            ),
            options=options,
        )

    def ai_variable(
        self,
        *,
        prompt: str,
        mode: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        tone: NotGivenOr[str] = NOT_GIVEN,
        web_search: NotGivenOr[bool] = NOT_GIVEN,
        context_before: NotGivenOr[str] = NOT_GIVEN,
        context_after: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> GeneratedText:
        """Resolve a personalization variable for one contact.

        Args:
            prompt: What the variable should produce.
            mode: ``"instant"`` for a straight completion, or ``"research"`` to
                let the model gather context first (costs more).
            contact_id: The contact to personalize for.
            tone: The voice to write in.
            web_search: Allow the model to search the web in research mode.
            context_before: The email text preceding the variable.
            context_after: The email text following it.
        """
        return self._post(
            "/generation/ai-variable",
            cast_to=GeneratedText,
            body=drop_not_given(
                {
                    "prompt": prompt,
                    "mode": mode,
                    "contact_id": contact_id,
                    "tone": tone,
                    "web_search": web_search,
                    "context_before": context_before,
                    "context_after": context_after,
                }
            ),
            options=options,
        )


class AsyncGeneration(AsyncAPIResource):
    """Asynchronous ``generation`` resource."""

    async def write(
        self,
        *,
        prompt: str,
        tone: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> GeneratedText:
        """Draft new copy from a prompt. Charges AI credits.

        Args:
            prompt: What to write.
            tone: The voice to write in.
        """
        return await self._post(
            "/generation/write",
            cast_to=GeneratedText,
            body=drop_not_given({"prompt": prompt, "tone": tone}),
            options=options,
        )

    async def edit(
        self,
        *,
        text: str,
        instruction: str,
        context: NotGivenOr[str] = NOT_GIVEN,
        tone: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> GeneratedText:
        """Rewrite a passage under an instruction. Charges AI credits.

        Args:
            text: The passage to rewrite.
            instruction: How to change it.
            context: The surrounding draft, so the rewrite fits its
                neighbours.
            tone: The voice to write in.
        """
        return await self._post(
            "/generation/edit",
            cast_to=GeneratedText,
            body=drop_not_given(
                {
                    "text": text,
                    "instruction": instruction,
                    "context": context,
                    "tone": tone,
                }
            ),
            options=options,
        )

    async def ai_variable(
        self,
        *,
        prompt: str,
        mode: NotGivenOr[str] = NOT_GIVEN,
        contact_id: NotGivenOr[str] = NOT_GIVEN,
        tone: NotGivenOr[str] = NOT_GIVEN,
        web_search: NotGivenOr[bool] = NOT_GIVEN,
        context_before: NotGivenOr[str] = NOT_GIVEN,
        context_after: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> GeneratedText:
        """Resolve a personalization variable for one contact.

        Args:
            prompt: What the variable should produce.
            mode: ``"instant"`` for a straight completion, or ``"research"`` to
                let the model gather context first (costs more).
            contact_id: The contact to personalize for.
            tone: The voice to write in.
            web_search: Allow the model to search the web in research mode.
            context_before: The email text preceding the variable.
            context_after: The email text following it.
        """
        return await self._post(
            "/generation/ai-variable",
            cast_to=GeneratedText,
            body=drop_not_given(
                {
                    "prompt": prompt,
                    "mode": mode,
                    "contact_id": contact_id,
                    "tone": tone,
                    "web_search": web_search,
                    "context_before": context_before,
                    "context_after": context_after,
                }
            ),
            options=options,
        )
