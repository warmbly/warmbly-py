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
    "CopyJudgment",
    "RenderedTemplate",
    "SpamFinding",
    "Template",
    "TemplateAnalysis",
    "TemplateDeleted",
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


class TemplateScore(BaseModel):
    """The rules-based content score for template copy.

    ``score`` runs 0 to 100, higher is safer. Each entry of ``issues`` carries
    ``severity`` (``warn`` or ``high``), ``code``, ``message``, an optional
    ``field`` (``subject`` or ``body``), the quoted ``spans`` that triggered it
    and a ``suggestion``.
    """

    score: int | None = None
    issues: Sequence[dict[str, object]] = []


class SpamFinding(BaseModel):
    """One AI finding: a fragment of the copy and why it hurts deliverability.

    ``severity`` is ``high``, ``warn`` or ``info``; ``field`` is ``subject`` or
    ``body`` (empty when it could not be anchored); ``text`` is the exact
    fragment quoted from the copy.
    """

    severity: str | None = None
    field: str | None = None
    text: str | None = None
    line: int | None = None
    excerpt: str | None = None
    issue: str | None = None
    suggestion: str | None = None
    category: str | None = None


class CopyJudgment(BaseModel):
    """How the copy reads to its recipient.

    ``reads_as`` and ``personalization`` are positions from 0 to 1 on their
    rubric, where 0 is the personal end. ``ask`` is ``one_clear_ask``,
    ``several_asks`` or ``no_ask``.
    """

    reads_as: float | None = None
    personalization: float | None = None
    ask: str | None = None
    spam_claim: float | None = None
    confidence: float | None = None
    model: str | None = None
    input_tokens: int | None = None


class TemplateAnalysis(BaseModel):
    """The AI spam analysis of template copy.

    ``rules`` is the same result :meth:`Templates.score` returns, scored from
    the same reading of the copy. ``judgment`` is present when a copy judge is
    configured. When no language model is configured the server answers with
    the rules score and the judgment, ``findings`` is empty and
    ``credits_charged`` is 0.
    """

    score: int | None = None
    verdict: str | None = None
    findings: Sequence[SpamFinding] | None = None
    suggested_subject: str | None = None
    improvements: Sequence[str] | None = None
    rules: TemplateScore | None = None
    judgment: CopyJudgment | None = None
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
        """Run the AI spam analysis on template copy. Charges AI credits.

        Names the offending words and sentences, says whether each sits in
        the subject or the body, and suggests replacements. Unlike
        :meth:`score` it spends credits, so it needs the ``WRITE_TEMPLATES``
        permission (and ``use_ai`` for a signed-in member); a depleted balance
        raises :class:`~warmbly.PaymentRequiredError`. At least one of the
        three fields must hold text, and the total is capped at 60,000
        characters.
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
        """Run the AI spam analysis on template copy. Charges AI credits.

        Names the offending words and sentences, says whether each sits in
        the subject or the body, and suggests replacements. Unlike
        :meth:`score` it spends credits, so it needs the ``WRITE_TEMPLATES``
        permission (and ``use_ai`` for a signed-in member); a depleted balance
        raises :class:`~warmbly.PaymentRequiredError`. At least one of the
        three fields must hold text, and the total is capped at 60,000
        characters.
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
