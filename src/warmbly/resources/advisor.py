"""The ``advisor`` resource: continuous deliverability and setup checks.

Maps to the ``/v1/advisor`` route group. The Advisor runs detectors across the
organization and surfaces findings on the row they are about — a mailbox
missing DMARC, a campaign with no unsubscribe header, and so on. Each finding
carries a severity, an explanation, and often an ``action`` the server can
apply for you.

Findings are stateful: apply, undo, snooze, or dismiss one and the state sticks
until the underlying condition clears and recurs, so telling the Advisor "this
is fine" does not have to be repeated weekly.

The autopilot toggle and the agent-fix path are session-only and therefore
absent here.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "Advisor",
    "AdvisorAck",
    "AdvisorFinding",
    "AdvisorSettings",
    "AdvisorSummary",
    "AsyncAdvisor",
]


class AdvisorFinding(BaseModel):
    """One Advisor recommendation.

    ``action`` is present when the Advisor can fix the finding itself; call
    :meth:`Advisor.apply` to run it and :meth:`Advisor.undo` to revert.
    ``agent_fixable`` marks findings only the AI assistant can resolve.
    """

    id: str
    organization_id: str | None = None
    detector_key: str | None = None
    category: str | None = None
    severity: str | None = None
    surface: str | None = None
    status: str | None = None
    impact: int | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    entity_label: str | None = None
    parent_type: str | None = None
    parent_id: str | None = None
    title: str | None = None
    group_title: str | None = None
    detail: str | None = None
    remedy: str | None = None
    steps: Sequence[str] = []
    agent_fixable: bool | None = None
    narrated: bool | None = None
    snippets: Sequence[dict[str, Any]] = []
    evidence: dict[str, Any] | None = None
    action: dict[str, Any] | None = None
    first_seen_at: str | None = None
    last_seen_at: str | None = None
    resolved_at: str | None = None
    snoozed_until: str | None = None
    dismissed_at: str | None = None
    dismiss_reason: str | None = None
    applied_at: str | None = None
    applied_by: str | None = None
    applied_result: str | None = None


class AdvisorSummary(BaseModel):
    """Counts by severity and by surface, plus the overall health score."""

    score: int | None = None
    total: int | None = None
    critical: int | None = None
    high: int | None = None
    medium: int | None = None
    low: int | None = None
    surfaces: Sequence[dict[str, Any]] = []


class AdvisorSettings(BaseModel):
    """The organization's Advisor configuration.

    ``autopilot`` lets the Advisor apply safe fixes without asking; it can only
    be changed from a browser session, so this SDK reads it but cannot set it.
    """

    organization_id: str | None = None
    enabled: bool | None = None
    muted_categories: Sequence[str] = []
    muted_detectors: Sequence[str] = []
    min_severity: str | None = None
    autopilot: bool | None = None
    autopilot_actor_id: str | None = None
    updated_at: str | None = None


class AdvisorAck(BaseModel):
    """A bare acknowledgement from snooze, dismiss, or feedback."""

    ok: bool | None = None


class Advisor(SyncAPIResource):
    """Synchronous ``advisor`` resource."""

    def list(
        self,
        *,
        surface: NotGivenOr[str] = NOT_GIVEN,
        category: NotGivenOr[str] = NOT_GIVEN,
        entity_type: NotGivenOr[str] = NOT_GIVEN,
        entity_id: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[AdvisorFinding]:
        """List open findings.

        Args:
            surface: Restrict to one surface (where the finding is shown).
            category: Restrict to one detector category.
            entity_type: Restrict to findings about one kind of entity.
            entity_id: Restrict to findings about one specific entity.
            limit: Maximum findings to return.
        """
        return self._get_api_list(
            "/advisor/recommendations",
            model=AdvisorFinding,
            query={
                "surface": surface,
                "category": category,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "limit": limit,
            },
            options=options,
        )

    def summary(self, *, options: RequestOptions | None = None) -> AdvisorSummary:
        """Return the health score and per-severity counts."""
        return self._get("/advisor/summary", cast_to=AdvisorSummary, options=options)

    def refresh(self, *, options: RequestOptions | None = None) -> AdvisorSummary:
        """Re-run the detectors and return the refreshed summary.

        Evaluation happens in the background when the findings are stale, so
        the returned summary may still reflect the previous pass.
        """
        return self._post("/advisor/refresh", cast_to=AdvisorSummary, options=options)

    def settings(self, *, options: RequestOptions | None = None) -> AdvisorSettings:
        """Read the organization's Advisor configuration."""
        return self._get("/advisor/settings", cast_to=AdvisorSettings, options=options)

    def apply(
        self, finding_id: str, *, options: RequestOptions | None = None
    ) -> AdvisorFinding:
        """Apply a finding's suggested fix. This changes real configuration."""
        return self._post(
            f"/advisor/recommendations/{finding_id}/apply",
            cast_to=AdvisorFinding,
            options=options,
        )

    def undo(
        self, finding_id: str, *, options: RequestOptions | None = None
    ) -> AdvisorFinding:
        """Revert a previously applied fix."""
        return self._post(
            f"/advisor/recommendations/{finding_id}/undo",
            cast_to=AdvisorFinding,
            options=options,
        )

    def snooze(
        self, finding_id: str, *, days: int, options: RequestOptions | None = None
    ) -> AdvisorAck:
        """Hide a finding for *days* days."""
        return self._post(
            f"/advisor/recommendations/{finding_id}/snooze",
            cast_to=AdvisorAck,
            body={"days": days},
            options=options,
        )

    def dismiss(
        self,
        finding_id: str,
        *,
        reason: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AdvisorAck:
        """Dismiss a finding until its condition clears and recurs."""
        return self._post(
            f"/advisor/recommendations/{finding_id}/dismiss",
            cast_to=AdvisorAck,
            body=drop_not_given({"reason": reason}),
            options=options,
        )

    def feedback(
        self,
        finding_id: str,
        *,
        helpful: bool,
        reason: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AdvisorAck:
        """Tell the Advisor whether a finding was useful.

        Args:
            helpful: Whether the finding was worth surfacing.
            reason: Optional free-text explanation.
        """
        return self._post(
            f"/advisor/recommendations/{finding_id}/feedback",
            cast_to=AdvisorAck,
            body=drop_not_given({"helpful": helpful, "reason": reason}),
            options=options,
        )


class AsyncAdvisor(AsyncAPIResource):
    """Asynchronous ``advisor`` resource."""

    def list(
        self,
        *,
        surface: NotGivenOr[str] = NOT_GIVEN,
        category: NotGivenOr[str] = NOT_GIVEN,
        entity_type: NotGivenOr[str] = NOT_GIVEN,
        entity_id: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[AdvisorFinding]:
        """List open findings.

        Args:
            surface: Restrict to one surface (where the finding is shown).
            category: Restrict to one detector category.
            entity_type: Restrict to findings about one kind of entity.
            entity_id: Restrict to findings about one specific entity.
            limit: Maximum findings to return.
        """
        return self._get_api_list(
            "/advisor/recommendations",
            model=AdvisorFinding,
            query={
                "surface": surface,
                "category": category,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "limit": limit,
            },
            options=options,
        )

    async def summary(self, *, options: RequestOptions | None = None) -> AdvisorSummary:
        """Return the health score and per-severity counts."""
        return await self._get(
            "/advisor/summary", cast_to=AdvisorSummary, options=options
        )

    async def refresh(self, *, options: RequestOptions | None = None) -> AdvisorSummary:
        """Re-run the detectors and return the refreshed summary.

        Evaluation happens in the background when the findings are stale, so
        the returned summary may still reflect the previous pass.
        """
        return await self._post(
            "/advisor/refresh", cast_to=AdvisorSummary, options=options
        )

    async def settings(
        self, *, options: RequestOptions | None = None
    ) -> AdvisorSettings:
        """Read the organization's Advisor configuration."""
        return await self._get(
            "/advisor/settings", cast_to=AdvisorSettings, options=options
        )

    async def apply(
        self, finding_id: str, *, options: RequestOptions | None = None
    ) -> AdvisorFinding:
        """Apply a finding's suggested fix. This changes real configuration."""
        return await self._post(
            f"/advisor/recommendations/{finding_id}/apply",
            cast_to=AdvisorFinding,
            options=options,
        )

    async def undo(
        self, finding_id: str, *, options: RequestOptions | None = None
    ) -> AdvisorFinding:
        """Revert a previously applied fix."""
        return await self._post(
            f"/advisor/recommendations/{finding_id}/undo",
            cast_to=AdvisorFinding,
            options=options,
        )

    async def snooze(
        self, finding_id: str, *, days: int, options: RequestOptions | None = None
    ) -> AdvisorAck:
        """Hide a finding for *days* days."""
        return await self._post(
            f"/advisor/recommendations/{finding_id}/snooze",
            cast_to=AdvisorAck,
            body={"days": days},
            options=options,
        )

    async def dismiss(
        self,
        finding_id: str,
        *,
        reason: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AdvisorAck:
        """Dismiss a finding until its condition clears and recurs."""
        return await self._post(
            f"/advisor/recommendations/{finding_id}/dismiss",
            cast_to=AdvisorAck,
            body=drop_not_given({"reason": reason}),
            options=options,
        )

    async def feedback(
        self,
        finding_id: str,
        *,
        helpful: bool,
        reason: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AdvisorAck:
        """Tell the Advisor whether a finding was useful.

        Args:
            helpful: Whether the finding was worth surfacing.
            reason: Optional free-text explanation.
        """
        return await self._post(
            f"/advisor/recommendations/{finding_id}/feedback",
            cast_to=AdvisorAck,
            body=drop_not_given({"helpful": helpful, "reason": reason}),
            options=options,
        )
