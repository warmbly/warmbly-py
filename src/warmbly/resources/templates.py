"""The ``templates`` resource: reusable reply templates.

Maps to the ``/v1/templates`` route group. A template bundles a reusable
``subject`` plus HTML and plain-text bodies under a human-readable ``name``.
Bodies may contain ``{{.Key}}`` placeholders, which :meth:`Templates.render`
expands against a caller-supplied variable map.

Templates are ordered within the organization; :meth:`Templates.reorder`
rewrites that order in one call.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncTemplates",
    "RenderedTemplate",
    "Template",
    "TemplateAnalysis",
    "TemplateDeleted",
    "TemplateFinding",
    "TemplateIssue",
    "TemplateIssueSpan",
    "TemplateJudgment",
    "TemplateList",
    "TemplateScore",
    "Templates",
]


class Template(BaseModel):
    """A reusable reply template."""

    id: str
    organization_id: str | None = None
    user_id: str | None = None
    name: str | None = None
    subject: str | None = None
    body_html: str | None = None
    body_plain: str | None = None
    position: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class TemplateDeleted(BaseModel):
    """The result of deleting a template (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None
    status: str | None = None


class RenderedTemplate(BaseModel):
    """A template with its placeholders expanded."""

    subject: str | None = None
    body_html: str | None = None
    body_plain: str | None = None


class TemplateList(BaseModel):
    """A full template list, as returned by :meth:`Templates.reorder`."""

    data: Sequence[Template] = []


class TemplateIssueSpan(BaseModel):
    """The exact fragment of the copy that triggered an issue.

    ``field`` is ``subject`` or ``body``, ``line`` the 1-based line of that
    field the fragment sits on (absent when unknown) and ``excerpt`` the whole
    line, for context.
    """

    field: str | None = None
    text: str | None = None
    line: int | None = None
    excerpt: str | None = None


class TemplateIssue(BaseModel):
    """One advisory content problem found by the rules score.

    ``severity`` is ``warn`` or ``high``. ``field`` is ``subject`` or ``body``
    when the issue lives in exactly one of them and absent when it spans both
    or describes the send as a whole.
    """

    severity: str | None = None
    code: str | None = None
    message: str | None = None
    field: str | None = None
    spans: Sequence[TemplateIssueSpan] = []
    suggestion: str | None = None


class TemplateScore(BaseModel):
    """An advisory 0-100 content-safety score for template content.

    Higher is safer. The score never blocks sending; ``issues`` say what
    lowered it and where.
    """

    score: int | None = None
    issues: Sequence[TemplateIssue] = []


class TemplateFinding(BaseModel):
    """One located problem the AI spam analysis found in the copy.

    ``severity`` is ``high``, ``warn`` or ``info``; ``field`` is ``subject`` or
    ``body`` (absent when it could not be anchored); ``text`` quotes the
    offending fragment and ``suggestion`` says what to write instead.
    ``category`` is a coarse grouping such as ``trigger_word``, ``tone``,
    ``formatting``, ``links``, ``structure`` or ``authenticity``.
    """

    severity: str | None = None
    field: str | None = None
    text: str | None = None
    line: int | None = None
    excerpt: str | None = None
    issue: str | None = None
    suggestion: str | None = None
    category: str | None = None


class TemplateJudgment(BaseModel):
    """How the copy reads to its recipient, as judged by a language model.

    ``reads_as`` and ``personalization`` are 0-1 positions where ``0`` is the
    personal end; ``spam_claim`` is 0-1; ``ask`` names whether the copy makes a
    clear request; ``confidence`` is the lowest confidence across the answers.
    """

    reads_as: float | None = None
    personalization: float | None = None
    ask: str | None = None
    spam_claim: float | None = None
    confidence: float | None = None
    model: str | None = None
    input_tokens: int | None = None


class TemplateAnalysis(BaseModel):
    """The result of an AI spam analysis of template content.

    ``score`` and ``verdict`` summarise the copy, ``findings`` locate each
    problem, ``suggested_subject`` is a rewritten subject (absent when the
    current one is fine) and ``improvements`` are copy-level suggestions with
    nothing specific to quote. ``rules`` is the rules-based
    :class:`TemplateScore` of the same copy, and ``judgment`` how it reads to a
    recipient (absent when that judge is unavailable). When no language model
    is configured on the deployment only the judgment answers, ``findings`` is
    empty and ``credits_charged`` is ``0``.
    """

    score: int | None = None
    verdict: str | None = None
    findings: Sequence[TemplateFinding] = []
    suggested_subject: str | None = None
    improvements: Sequence[str] = []
    rules: TemplateScore | None = None
    judgment: TemplateJudgment | None = None
    model: str | None = None
    tokens_used: int | None = None
    credits_remaining: int | None = None
    credits_charged: int | None = None


class Templates(SyncAPIResource):
    """Synchronous ``templates`` resource."""

    def list(
        self,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[Template]:
        """List templates in their configured order.

        Args:
            q: Optional search string matched against the template name.
        """
        return self._get_api_list(
            "/templates", model=Template, query={"q": q}, options=options
        )

    def create(
        self,
        *,
        name: str,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Template:
        """Create a template.

        Args:
            name: A human-readable label for the template.
            subject: The email subject line.
            body_html: The HTML body.
            body_plain: The plain-text body.
        """
        body = drop_not_given(
            {
                "name": name,
                "subject": subject,
                "body_html": body_html,
                "body_plain": body_plain,
            }
        )
        return self._post("/templates", cast_to=Template, body=body, options=options)

    def retrieve(
        self, template_id: str, *, options: RequestOptions | None = None
    ) -> Template:
        """Retrieve a single template by id."""
        return self._get(f"/templates/{template_id}", cast_to=Template, options=options)

    def update(
        self,
        template_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Template:
        """Update a template's name, subject, or bodies."""
        body = drop_not_given(
            {
                "name": name,
                "subject": subject,
                "body_html": body_html,
                "body_plain": body_plain,
            }
        )
        return self._patch(
            f"/templates/{template_id}",
            cast_to=Template,
            body=body,
            options=options,
        )

    def delete(
        self, template_id: str, *, options: RequestOptions | None = None
    ) -> TemplateDeleted:
        """Delete a template."""
        return self._delete(
            f"/templates/{template_id}", cast_to=TemplateDeleted, options=options
        )

    def duplicate(
        self, template_id: str, *, options: RequestOptions | None = None
    ) -> Template:
        """Copy a template, returning the new copy."""
        return self._post(
            f"/templates/{template_id}/duplicate", cast_to=Template, options=options
        )

    def render(
        self,
        template_id: str,
        *,
        variables: Mapping[str, str] | None = None,
        options: RequestOptions | None = None,
    ) -> RenderedTemplate:
        """Expand a template's ``{{.Key}}`` placeholders.

        Args:
            template_id: The template to render.
            variables: The placeholder values. Placeholders with no value
                render empty.
        """
        return self._post(
            f"/templates/{template_id}/render",
            cast_to=RenderedTemplate,
            body={"variables": dict(variables or {})},
            options=options,
        )

    def reorder(
        self, *, ids: Sequence[str], options: RequestOptions | None = None
    ) -> TemplateList:
        """Reposition templates in the given order.

        Args:
            ids: Template ids in their desired order. Templates not listed
                keep their position.

        Returns:
            The full, re-ordered template list.
        """
        return self._patch(
            "/templates/reorder",
            cast_to=TemplateList,
            body={"ids": list(ids)},
            options=options,
        )

    def score(
        self,
        *,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> TemplateScore:
        """Score arbitrary template content before saving it.

        Takes raw content rather than a template id, so a composer can score
        a draft that does not exist yet.
        """
        body = drop_not_given(
            {
                "subject": subject,
                "body_html": body_html,
                "body_plain": body_plain,
            }
        )
        return self._post(
            "/templates/score", cast_to=TemplateScore, body=body, options=options
        )

    def analyze(
        self,
        *,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> TemplateAnalysis:
        """Analyze template content for spam signals with AI.

        Where :meth:`score` says how safe the copy is, this says which word or
        sentence is the problem, whether it is in the subject or the body, and
        what to write instead. It spends AI credits (the result reports
        ``credits_charged`` and ``credits_remaining``) and sends an idempotency
        key, so a retry does not charge twice. Needs the ``write_templates``
        permission, plus the AI assistant for a member session. At least one of
        the three fields must have content, and together they may not exceed
        60,000 characters.

        Args:
            subject: The subject line.
            body_html: The HTML body.
            body_plain: The plain-text body.
        """
        body = drop_not_given(
            {
                "subject": subject,
                "body_html": body_html,
                "body_plain": body_plain,
            }
        )
        return self._post(
            "/templates/analyze", cast_to=TemplateAnalysis, body=body, options=options
        )


class AsyncTemplates(AsyncAPIResource):
    """Asynchronous ``templates`` resource."""

    def list(
        self,
        *,
        q: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[Template]:
        """List templates in their configured order.

        Args:
            q: Optional search string matched against the template name.
        """
        return self._get_api_list(
            "/templates", model=Template, query={"q": q}, options=options
        )

    async def create(
        self,
        *,
        name: str,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Template:
        """Create a template.

        Args:
            name: A human-readable label for the template.
            subject: The email subject line.
            body_html: The HTML body.
            body_plain: The plain-text body.
        """
        body = drop_not_given(
            {
                "name": name,
                "subject": subject,
                "body_html": body_html,
                "body_plain": body_plain,
            }
        )
        return await self._post(
            "/templates", cast_to=Template, body=body, options=options
        )

    async def retrieve(
        self, template_id: str, *, options: RequestOptions | None = None
    ) -> Template:
        """Retrieve a single template by id."""
        return await self._get(
            f"/templates/{template_id}", cast_to=Template, options=options
        )

    async def update(
        self,
        template_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Template:
        """Update a template's name, subject, or bodies."""
        body = drop_not_given(
            {
                "name": name,
                "subject": subject,
                "body_html": body_html,
                "body_plain": body_plain,
            }
        )
        return await self._patch(
            f"/templates/{template_id}",
            cast_to=Template,
            body=body,
            options=options,
        )

    async def delete(
        self, template_id: str, *, options: RequestOptions | None = None
    ) -> TemplateDeleted:
        """Delete a template."""
        return await self._delete(
            f"/templates/{template_id}", cast_to=TemplateDeleted, options=options
        )

    async def duplicate(
        self, template_id: str, *, options: RequestOptions | None = None
    ) -> Template:
        """Copy a template, returning the new copy."""
        return await self._post(
            f"/templates/{template_id}/duplicate", cast_to=Template, options=options
        )

    async def render(
        self,
        template_id: str,
        *,
        variables: Mapping[str, str] | None = None,
        options: RequestOptions | None = None,
    ) -> RenderedTemplate:
        """Expand a template's ``{{.Key}}`` placeholders.

        Args:
            template_id: The template to render.
            variables: The placeholder values. Placeholders with no value
                render empty.
        """
        return await self._post(
            f"/templates/{template_id}/render",
            cast_to=RenderedTemplate,
            body={"variables": dict(variables or {})},
            options=options,
        )

    async def reorder(
        self, *, ids: Sequence[str], options: RequestOptions | None = None
    ) -> TemplateList:
        """Reposition templates in the given order.

        Args:
            ids: Template ids in their desired order. Templates not listed
                keep their position.

        Returns:
            The full, re-ordered template list.
        """
        return await self._patch(
            "/templates/reorder",
            cast_to=TemplateList,
            body={"ids": list(ids)},
            options=options,
        )

    async def score(
        self,
        *,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> TemplateScore:
        """Score arbitrary template content before saving it.

        Takes raw content rather than a template id, so a composer can score
        a draft that does not exist yet.
        """
        body = drop_not_given(
            {
                "subject": subject,
                "body_html": body_html,
                "body_plain": body_plain,
            }
        )
        return await self._post(
            "/templates/score", cast_to=TemplateScore, body=body, options=options
        )

    async def analyze(
        self,
        *,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> TemplateAnalysis:
        """Analyze template content for spam signals with AI.

        Where :meth:`score` says how safe the copy is, this says which word or
        sentence is the problem, whether it is in the subject or the body, and
        what to write instead. It spends AI credits (the result reports
        ``credits_charged`` and ``credits_remaining``) and sends an idempotency
        key, so a retry does not charge twice. Needs the ``write_templates``
        permission, plus the AI assistant for a member session. At least one of
        the three fields must have content, and together they may not exceed
        60,000 characters.

        Args:
            subject: The subject line.
            body_html: The HTML body.
            body_plain: The plain-text body.
        """
        body = drop_not_given(
            {
                "subject": subject,
                "body_html": body_html,
                "body_plain": body_plain,
            }
        )
        return await self._post(
            "/templates/analyze", cast_to=TemplateAnalysis, body=body, options=options
        )
