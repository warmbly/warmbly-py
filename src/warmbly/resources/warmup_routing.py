"""The ``warmup_routing`` resource: premium-pool partner selection rules.

Maps to the ``/v1/warmup/routing`` route group. A rule biases which warmup
partner a mailbox is paired with — for example, "send to Gmail recipients only
from Google-classified senders". Rules are evaluated in ``priority`` order and
``weight`` scales how strongly a match is preferred.
"""

from __future__ import annotations

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncWarmupRouting",
    "WarmupRouting",
    "WarmupRoutingRule",
    "WarmupRoutingRuleDeleted",
]


class WarmupRoutingRule(BaseModel):
    """A warmup partner-selection rule.

    The two match pairs describe the sender and the recipient side; each is a
    match *type* (what to compare) plus the *value* to compare against.
    """

    id: str
    organization_id: str | None = None
    name: str | None = None
    priority: int | None = None
    sender_match_type: str | None = None
    sender_match_value: str | None = None
    recipient_match_type: str | None = None
    recipient_match_value: str | None = None
    weight: float | None = None
    enabled: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None


class WarmupRoutingRuleDeleted(BaseModel):
    """The result of deleting a rule (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class WarmupRouting(SyncAPIResource):
    """Synchronous ``warmup_routing`` resource."""

    def list(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[WarmupRoutingRule]:
        """List the organization's routing rules, in priority order."""
        return self._get_api_list(
            "/warmup/routing",
            model=WarmupRoutingRule,
            data_key="rules",
            options=options,
        )

    def create(
        self,
        *,
        name: str,
        sender_match_type: str,
        sender_match_value: str,
        recipient_match_type: str,
        recipient_match_value: str,
        priority: NotGivenOr[int] = NOT_GIVEN,
        weight: NotGivenOr[float] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> WarmupRoutingRule:
        """Create a routing rule.

        Args:
            name: A human-readable label.
            sender_match_type: What to match on the sending mailbox.
            sender_match_value: The value that must match.
            recipient_match_type: What to match on the warmup partner.
            recipient_match_value: The value that must match.
            priority: Evaluation order; lower runs first.
            weight: How strongly to prefer a match.
            enabled: Whether the rule is active.
        """
        return self._post(
            "/warmup/routing",
            cast_to=WarmupRoutingRule,
            body=drop_not_given(
                {
                    "name": name,
                    "sender_match_type": sender_match_type,
                    "sender_match_value": sender_match_value,
                    "recipient_match_type": recipient_match_type,
                    "recipient_match_value": recipient_match_value,
                    "priority": priority,
                    "weight": weight,
                    "enabled": enabled,
                }
            ),
            options=options,
        )

    def update(
        self,
        rule_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        sender_match_type: NotGivenOr[str] = NOT_GIVEN,
        sender_match_value: NotGivenOr[str] = NOT_GIVEN,
        recipient_match_type: NotGivenOr[str] = NOT_GIVEN,
        recipient_match_value: NotGivenOr[str] = NOT_GIVEN,
        priority: NotGivenOr[int] = NOT_GIVEN,
        weight: NotGivenOr[float] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> WarmupRoutingRule:
        """Update a routing rule, or toggle it with *enabled*."""
        return self._patch(
            f"/warmup/routing/{rule_id}",
            cast_to=WarmupRoutingRule,
            body=drop_not_given(
                {
                    "name": name,
                    "sender_match_type": sender_match_type,
                    "sender_match_value": sender_match_value,
                    "recipient_match_type": recipient_match_type,
                    "recipient_match_value": recipient_match_value,
                    "priority": priority,
                    "weight": weight,
                    "enabled": enabled,
                }
            ),
            options=options,
        )

    def delete(
        self, rule_id: str, *, options: RequestOptions | None = None
    ) -> WarmupRoutingRuleDeleted:
        """Delete a routing rule."""
        return self._delete(
            f"/warmup/routing/{rule_id}",
            cast_to=WarmupRoutingRuleDeleted,
            options=options,
        )


class AsyncWarmupRouting(AsyncAPIResource):
    """Asynchronous ``warmup_routing`` resource."""

    def list(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[WarmupRoutingRule]:
        """List the organization's routing rules, in priority order."""
        return self._get_api_list(
            "/warmup/routing",
            model=WarmupRoutingRule,
            data_key="rules",
            options=options,
        )

    async def create(
        self,
        *,
        name: str,
        sender_match_type: str,
        sender_match_value: str,
        recipient_match_type: str,
        recipient_match_value: str,
        priority: NotGivenOr[int] = NOT_GIVEN,
        weight: NotGivenOr[float] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> WarmupRoutingRule:
        """Create a routing rule.

        Args:
            name: A human-readable label.
            sender_match_type: What to match on the sending mailbox.
            sender_match_value: The value that must match.
            recipient_match_type: What to match on the warmup partner.
            recipient_match_value: The value that must match.
            priority: Evaluation order; lower runs first.
            weight: How strongly to prefer a match.
            enabled: Whether the rule is active.
        """
        return await self._post(
            "/warmup/routing",
            cast_to=WarmupRoutingRule,
            body=drop_not_given(
                {
                    "name": name,
                    "sender_match_type": sender_match_type,
                    "sender_match_value": sender_match_value,
                    "recipient_match_type": recipient_match_type,
                    "recipient_match_value": recipient_match_value,
                    "priority": priority,
                    "weight": weight,
                    "enabled": enabled,
                }
            ),
            options=options,
        )

    async def update(
        self,
        rule_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        sender_match_type: NotGivenOr[str] = NOT_GIVEN,
        sender_match_value: NotGivenOr[str] = NOT_GIVEN,
        recipient_match_type: NotGivenOr[str] = NOT_GIVEN,
        recipient_match_value: NotGivenOr[str] = NOT_GIVEN,
        priority: NotGivenOr[int] = NOT_GIVEN,
        weight: NotGivenOr[float] = NOT_GIVEN,
        enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> WarmupRoutingRule:
        """Update a routing rule, or toggle it with *enabled*."""
        return await self._patch(
            f"/warmup/routing/{rule_id}",
            cast_to=WarmupRoutingRule,
            body=drop_not_given(
                {
                    "name": name,
                    "sender_match_type": sender_match_type,
                    "sender_match_value": sender_match_value,
                    "recipient_match_type": recipient_match_type,
                    "recipient_match_value": recipient_match_value,
                    "priority": priority,
                    "weight": weight,
                    "enabled": enabled,
                }
            ),
            options=options,
        )

    async def delete(
        self, rule_id: str, *, options: RequestOptions | None = None
    ) -> WarmupRoutingRuleDeleted:
        """Delete a routing rule."""
        return await self._delete(
            f"/warmup/routing/{rule_id}",
            cast_to=WarmupRoutingRuleDeleted,
            options=options,
        )
