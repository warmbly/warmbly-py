"""The ``unibox`` resource: the organization-wide unified inbox.

Maps to the ``/v1/unibox`` route group. The unibox is message-centric rather
than thread-centric: :meth:`Unibox.list` returns one preview row per
conversation, :meth:`Unibox.retrieve` opens a single message by id, and
:meth:`Unibox.thread` expands the full conversation. On top of that sit the
write paths (reply, compose, mark-seen, labels, snoozes, scheduled sends),
autosaved compose drafts, and the inbox agent's pending drafts.

The AI draft endpoints (:meth:`Unibox.draft_reply`, :meth:`Unibox.draft_compose`)
consume AI credits and never send; an exhausted balance surfaces as
:class:`~warmbly.PaymentRequiredError`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pydantic import Field

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions, is_given
from .._utils import drop_not_given

__all__ = [
    "AgentDraft",
    "AgentDraftDiscarded",
    "AsyncUnibox",
    "ComposeCandidates",
    "ComposeDraft",
    "ComposeDraftDeleted",
    "ComposeDraftSaved",
    "ComposeResult",
    "GeneratedDraft",
    "Message",
    "MessagePreview",
    "ScheduledSend",
    "ScheduledSendCancelled",
    "SeenResult",
    "SendResult",
    "Snooze",
    "SnoozeDeleted",
    "ThreadLabels",
    "Unibox",
    "UniboxOverview",
    "UnseenCount",
]


class MessagePreview(BaseModel):
    """One row of the inbox list: a message stripped down to its preview."""

    id: str
    email_id: str | None = None
    thread_id: str | None = None
    from_addr: Sequence[str] = []
    to_addr: Sequence[str] = []
    subject: str | None = None
    snippet: str | None = None
    internal_date: str | None = None
    seen: bool | None = None
    message_count: int | None = None
    has_unread: bool | None = None
    labels: Sequence[dict[str, Any]] = []


class Message(BaseModel):
    """A full stored message, as returned by :meth:`Unibox.retrieve`.

    Distinct from :class:`MessagePreview`, which is the row shape the list and
    thread endpoints return: this one carries the addresses under their header
    names and the message body. ``body_truncated`` marks a message whose stored
    body could not be read, in which case ``body_plain`` holds only the preview
    snippet — show a notice rather than presenting it as the whole message.
    ``body_html`` is sanitized for display before it leaves the API.
    """

    id: str
    thread_id: str | None = None
    parent_id: str | None = None
    message_id: str | None = None
    gmail_id: str | None = None
    uid: int | None = None
    mod_seq: int | None = None
    flags: Sequence[str] = []
    from_: Sequence[str] = Field(default=[], alias="from")
    to: Sequence[str] = []
    cc: Sequence[str] = []
    bcc: Sequence[str] = []
    reply_to: Sequence[str] = Field(default=[], alias="ReplyTo")
    in_reply_to: Sequence[str] = []
    subject: str | None = None
    size: int | None = None
    date: str | None = None
    internal_date: str | None = None
    body_plain: str | None = None
    body_html: str | None = None
    body_truncated: bool | None = None


class UnseenCount(BaseModel):
    """The unread count for the organization, or for one mailbox."""

    count: int | None = None


class UniboxOverview(BaseModel):
    """Roll-up counts behind the inbox scope rail and metric strip.

    ``folders`` carries an ``{"folder", "unread", "total"}`` entry per
    canonical folder (``inbox``, ``sent``, ``drafts``, ``archive``, ``spam``,
    ``trash``).
    """

    total: int | None = None
    unread: int | None = None
    today: int | None = None
    week: int | None = None
    snoozed: int | None = None
    awaiting_reply: int | None = None
    awaiting_agent_draft: int | None = None
    scheduled_pending: int | None = None
    scheduled_pending_max: int | None = None
    folders: Sequence[dict[str, Any]] = []
    mailboxes: Sequence[dict[str, Any]] = []
    tags: Sequence[dict[str, Any]] = []
    categories: Sequence[dict[str, Any]] = []
    generated_at: str | None = None
    window_today_start: str | None = None
    window_week_start: str | None = None


class ThreadLabels(BaseModel):
    """The conversation labels attached to a thread."""

    data: Sequence[dict[str, Any]] = []


class SeenResult(BaseModel):
    """The echo of a bulk mark-seen request."""

    email_ids: Sequence[str] = []
    seen: bool | None = None


class SendResult(BaseModel):
    """The result of queueing a send (reply, compose, or agent-draft approval).

    A send is always queued as a task, so ``task_id`` identifies the queued
    work and ``scheduled_at`` is when it fires: for ``send_mode="instant"``
    that is effectively now.
    """

    task_id: str | None = None
    scheduled_at: str | None = None
    send_mode: str | None = None


class ComposeResult(SendResult):
    """The result of a compose send, including which mailbox was chosen.

    In ``auto`` mode the server picks the mailbox and explains the choice in
    ``picked_reason``.
    """

    account_id: str | None = None
    account_email: str | None = None
    auto: bool | None = None
    picked_reason: str | None = None


class ComposeCandidates(BaseModel):
    """Scored mailbox candidates for composing to a given recipient.

    ``suppression`` is non-``None`` when the recipient is on the organization's
    suppression list; sending to them will be refused.
    """

    accounts: Sequence[dict[str, Any]] = []
    recommended_account_id: str | None = None
    recommended_reason: str | None = None
    contact: dict[str, Any] | None = None
    suppression: dict[str, Any] | None = None


class GeneratedDraft(BaseModel):
    """An AI-generated draft, plus what it cost.

    Exactly one of ``text`` and ``question`` is set: the model returns a
    clarifying ``question`` when the prompt is too thin to draft from.
    """

    text: str | None = None
    question: str | None = None
    credits_remaining: int | None = None
    credits_charged: int | None = None
    tokens_used: int | None = None
    model: str | None = None
    grounding: dict[str, Any] | None = None


class ComposeDraft(BaseModel):
    """An autosaved compose draft (permissive)."""

    id: str
    email_account_id: str | None = None
    to: Sequence[str] = []
    cc: Sequence[str] = []
    bcc: Sequence[str] = []
    subject: str | None = None
    body: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ComposeDraftSaved(BaseModel):
    """The id echoed back by an autosave upsert."""

    id: str | None = None


class ComposeDraftDeleted(BaseModel):
    """The result of deleting a compose draft."""

    deleted: bool | None = None


class AgentDraft(BaseModel):
    """A reply the inbox agent drafted and is holding for human review."""

    id: str
    organization_id: str | None = None
    thread_id: str | None = None
    email_id: str | None = None
    email_account_id: str | None = None
    subject: str | None = None
    body: str | None = None
    status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class AgentDraftDiscarded(BaseModel):
    """The result of discarding an agent draft."""

    status: str | None = None


class Snooze(BaseModel):
    """A thread hidden from the inbox until ``snoozed_until``."""

    id: str | None = None
    user_id: str | None = None
    thread_id: str | None = None
    snoozed_until: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SnoozeDeleted(BaseModel):
    """The result of un-snoozing a thread (``204 No Content``)."""

    thread_id: str | None = None
    deleted: bool | None = None


class ScheduledSend(BaseModel):
    """A queued send awaiting its scheduled time."""

    task_id: str | None = None
    scheduled_at: str | None = None
    created_at: str | None = None
    account_id: str | None = None
    account_email: str | None = None
    account_name: str | None = None
    to: Sequence[str] = []
    cc: Sequence[str] = []
    bcc: Sequence[str] = []
    subject: str | None = None
    snippet: str | None = None
    thread_id: str | None = None


class ScheduledSendCancelled(BaseModel):
    """The result of cancelling a scheduled send (``204 No Content``)."""

    task_id: str | None = None
    cancelled: bool | None = None


def _list_query(
    *,
    limit: NotGivenOr[int],
    cursor: NotGivenOr[str],
    email_ids: NotGivenOr[Sequence[str]],
    folder: NotGivenOr[str],
    direction: NotGivenOr[str],
    from_: NotGivenOr[str],
    address: NotGivenOr[str],
    subject: NotGivenOr[str],
    unseen: NotGivenOr[bool],
    snoozed: NotGivenOr[str],
    awaiting_reply: NotGivenOr[bool],
    agent_drafts: NotGivenOr[bool],
    uncategorized: NotGivenOr[bool],
    category_ids: NotGivenOr[Sequence[str]],
    since: NotGivenOr[str],
    until: NotGivenOr[str],
) -> dict[str, Any]:
    """Build the ``GET /unibox`` query string.

    The endpoint takes comma-joined id lists and lowercase ``"true"`` for its
    boolean filters, so the joining/stringifying happens here rather than in
    every caller.
    """
    return {
        "limit": limit,
        "cursor": cursor,
        "email_ids": ",".join(email_ids) if is_given(email_ids) else NOT_GIVEN,
        "folder": folder,
        "direction": direction,
        "from": from_,
        "address": address,
        "subject": subject,
        "unseen": "true" if unseen is True else NOT_GIVEN,
        "snoozed": snoozed,
        "awaiting_reply": "true" if awaiting_reply is True else NOT_GIVEN,
        "agent_drafts": "true" if agent_drafts is True else NOT_GIVEN,
        "uncategorized": "true" if uncategorized is True else NOT_GIVEN,
        "category_ids": (
            ",".join(category_ids) if is_given(category_ids) else NOT_GIVEN
        ),
        "since": since,
        "until": until,
    }


def _reply_body(
    *,
    email_account_id: str,
    to: Sequence[str],
    subject: str,
    body_html: NotGivenOr[str],
    body_plain: NotGivenOr[str],
    cc: NotGivenOr[Sequence[str]],
    bcc: NotGivenOr[Sequence[str]],
    in_reply_to: NotGivenOr[Sequence[str]],
    thread_id: NotGivenOr[str],
    send_mode: NotGivenOr[str],
    scheduled_at: NotGivenOr[str],
) -> dict[str, Any]:
    return drop_not_given(
        {
            "email_account_id": email_account_id,
            "to": list(to),
            "cc": list(cc) if is_given(cc) else NOT_GIVEN,
            "bcc": list(bcc) if is_given(bcc) else NOT_GIVEN,
            "subject": subject,
            "body_html": body_html,
            "body_plain": body_plain,
            "in_reply_to": list(in_reply_to) if is_given(in_reply_to) else NOT_GIVEN,
            "thread_id": thread_id,
            "send_mode": send_mode,
            "scheduled_at": scheduled_at,
        }
    )


def _compose_body(
    *,
    to: Sequence[str],
    subject: str,
    email_account_id: NotGivenOr[str],
    from_tag_id: NotGivenOr[str],
    body_html: NotGivenOr[str],
    body_plain: NotGivenOr[str],
    cc: NotGivenOr[Sequence[str]],
    bcc: NotGivenOr[Sequence[str]],
    send_mode: NotGivenOr[str],
    scheduled_at: NotGivenOr[str],
) -> dict[str, Any]:
    return drop_not_given(
        {
            "email_account_id": email_account_id,
            "from_tag_id": from_tag_id,
            "to": list(to),
            "cc": list(cc) if is_given(cc) else NOT_GIVEN,
            "bcc": list(bcc) if is_given(bcc) else NOT_GIVEN,
            "subject": subject,
            "body_html": body_html,
            "body_plain": body_plain,
            "send_mode": send_mode,
            "scheduled_at": scheduled_at,
        }
    )


def _draft_body(
    *,
    email_account_id: NotGivenOr[str],
    to: NotGivenOr[Sequence[str]],
    cc: NotGivenOr[Sequence[str]],
    bcc: NotGivenOr[Sequence[str]],
    subject: NotGivenOr[str],
    body: NotGivenOr[str],
) -> dict[str, Any]:
    return drop_not_given(
        {
            "email_account_id": email_account_id,
            "to": list(to) if is_given(to) else NOT_GIVEN,
            "cc": list(cc) if is_given(cc) else NOT_GIVEN,
            "bcc": list(bcc) if is_given(bcc) else NOT_GIVEN,
            "subject": subject,
            "body": body,
        }
    )


class Unibox(SyncAPIResource):
    """Synchronous ``unibox`` resource."""

    # -- reading ------------------------------------------------------------
    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        email_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        folder: NotGivenOr[str] = NOT_GIVEN,
        direction: NotGivenOr[str] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        address: NotGivenOr[str] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        unseen: NotGivenOr[bool] = NOT_GIVEN,
        snoozed: NotGivenOr[str] = NOT_GIVEN,
        awaiting_reply: NotGivenOr[bool] = NOT_GIVEN,
        agent_drafts: NotGivenOr[bool] = NOT_GIVEN,
        uncategorized: NotGivenOr[bool] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        since: NotGivenOr[str] = NOT_GIVEN,
        until: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[MessagePreview]:
        """List inbox messages, newest first (auto-paginating).

        Args:
            limit: Page size.
            cursor: Pagination cursor.
            email_ids: Restrict to these mailbox (email account) ids.
            folder: Canonical folder scope: ``inbox``, ``sent``, ``drafts``,
                ``archive``, ``spam`` or ``trash``. Omit for every folder
                except ``spam`` and ``trash``.
            direction: ``"sent"`` or ``"received"``.
            from_: Match the sender address.
            address: Match either side of the conversation.
            subject: Match the subject.
            unseen: Only unread messages.
            snoozed: ``"only"`` or ``"exclude"`` to include or hide snoozed
                threads.
            awaiting_reply: Only threads waiting on a reply from you.
            agent_drafts: Only threads with a pending inbox-agent draft.
            uncategorized: Only threads carrying no conversation labels.
            category_ids: Only threads carrying any of these labels.
            since: Lower bound on the message date (RFC 3339).
            until: Upper bound on the message date (RFC 3339).
        """
        return self._get_api_list(
            "/unibox",
            model=MessagePreview,
            query=_list_query(
                limit=limit,
                cursor=cursor,
                email_ids=email_ids,
                folder=folder,
                direction=direction,
                from_=from_,
                address=address,
                subject=subject,
                unseen=unseen,
                snoozed=snoozed,
                awaiting_reply=awaiting_reply,
                agent_drafts=agent_drafts,
                uncategorized=uncategorized,
                category_ids=category_ids,
                since=since,
                until=until,
            ),
            options=options,
        )

    def retrieve(
        self, message_id: str, *, options: RequestOptions | None = None
    ) -> Message:
        """Retrieve a single message by id."""
        return self._get(f"/unibox/{message_id}", cast_to=Message, options=options)

    def thread(
        self,
        *,
        thread_id: NotGivenOr[str] = NOT_GIVEN,
        email_id: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[MessagePreview]:
        """List a conversation's messages, oldest first (auto-paginating).

        Rows carry the same shape as the inbox list; fetch a message with
        :meth:`retrieve` for its body.

        Args:
            thread_id: The thread to expand.
            email_id: The mailbox the thread belongs to. Omit to read the
                thread across every mailbox in the organization.
        """
        return self._get_api_list(
            "/unibox/thread",
            model=MessagePreview,
            query={
                "thread_id": thread_id,
                "email_id": email_id,
                "limit": limit,
                "cursor": cursor,
            },
            options=options,
        )

    def count(
        self,
        *,
        email_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> UnseenCount:
        """Return the unread count, optionally scoped to one mailbox."""
        return self._get(
            "/unibox/count",
            cast_to=UnseenCount,
            query={"email_id": email_id},
            options=options,
        )

    def overview(self, *, options: RequestOptions | None = None) -> UniboxOverview:
        """Return the inbox roll-up (unread, today, week, snoozed, per-mailbox)."""
        return self._get("/unibox/overview", cast_to=UniboxOverview, options=options)

    # -- labels + read state -------------------------------------------------
    def list_thread_labels(
        self, *, thread_id: str, options: RequestOptions | None = None
    ) -> ThreadLabels:
        """Return the conversation labels on a thread."""
        return self._get(
            "/unibox/thread/labels",
            cast_to=ThreadLabels,
            query={"thread_id": thread_id},
            options=options,
        )

    def set_thread_labels(
        self,
        *,
        thread_id: str,
        category_ids: Sequence[str],
        options: RequestOptions | None = None,
    ) -> ThreadLabels:
        """Replace a thread's conversation labels wholesale.

        This is a ``PUT``: *category_ids* is the desired final set, so retries
        are safe and passing an empty list clears every label.
        """
        return self._put(
            "/unibox/thread/labels",
            cast_to=ThreadLabels,
            body={"thread_id": thread_id, "category_ids": list(category_ids)},
            options=options,
        )

    def mark_seen(
        self,
        *,
        email_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        folder: NotGivenOr[str] = NOT_GIVEN,
        seen: bool = True,
        options: RequestOptions | None = None,
    ) -> SeenResult:
        """Mark up to 500 messages as read or unread.

        Args:
            email_ids: The message ids to update (max 500).
            folder: Instead of listing ids, mark every unread message in this
                folder across the whole workspace.
            seen: ``True`` to mark read, ``False`` to mark unread.
        """
        return self._patch(
            "/unibox/seen",
            cast_to=SeenResult,
            body=drop_not_given(
                {
                    "email_ids": (
                        list(email_ids) if is_given(email_ids) else NOT_GIVEN
                    ),
                    "folder": folder,
                    "seen": seen,
                }
            ),
            options=options,
        )

    # -- sending -------------------------------------------------------------
    def reply(
        self,
        *,
        email_account_id: str,
        to: Sequence[str],
        subject: str,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        cc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        bcc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        in_reply_to: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        thread_id: NotGivenOr[str] = NOT_GIVEN,
        send_mode: NotGivenOr[str] = NOT_GIVEN,
        scheduled_at: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SendResult:
        """Send a reply from a connected mailbox.

        Args:
            email_account_id: The mailbox to send from.
            to: Recipient addresses (at least one).
            subject: The reply subject.
            body_html: The HTML body.
            body_plain: The plain-text body.
            in_reply_to: ``Message-ID`` values this reply threads under.
            thread_id: The thread being replied to.
            send_mode: ``"instant"`` (the default) or ``"scheduled"``.
            scheduled_at: When to send, for ``send_mode="scheduled"``
                (RFC 3339).
        """
        return self._post(
            "/unibox/reply",
            cast_to=SendResult,
            body=_reply_body(
                email_account_id=email_account_id,
                to=to,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                cc=cc,
                bcc=bcc,
                in_reply_to=in_reply_to,
                thread_id=thread_id,
                send_mode=send_mode,
                scheduled_at=scheduled_at,
            ),
            options=options,
        )

    def draft_reply(
        self,
        *,
        thread_id: str,
        instruction: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> GeneratedDraft:
        """Generate a reply draft grounded in the thread. Charges AI credits.

        Never sends: pass the returned ``text`` to :meth:`reply` when you are
        happy with it.
        """
        return self._post(
            "/unibox/reply/draft",
            cast_to=GeneratedDraft,
            body=drop_not_given({"thread_id": thread_id, "instruction": instruction}),
            options=options,
        )

    def compose_candidates(
        self,
        *,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ComposeCandidates:
        """Score the mailboxes available for composing to *to*.

        Args:
            to: The recipient address. Omit for an unscored mailbox list.
        """
        return self._get(
            "/unibox/compose/candidates",
            cast_to=ComposeCandidates,
            query={"to": to},
            options=options,
        )

    def compose(
        self,
        *,
        to: Sequence[str],
        subject: str,
        email_account_id: NotGivenOr[str] = NOT_GIVEN,
        from_tag_id: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        cc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        bcc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        send_mode: NotGivenOr[str] = NOT_GIVEN,
        scheduled_at: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ComposeResult:
        """Send a brand-new outbound email.

        Omit *email_account_id* to let the server pick the best mailbox
        (auto mode); pass *from_tag_id* to restrict that choice to a mailbox
        tag.
        """
        return self._post(
            "/unibox/compose",
            cast_to=ComposeResult,
            body=_compose_body(
                to=to,
                subject=subject,
                email_account_id=email_account_id,
                from_tag_id=from_tag_id,
                body_html=body_html,
                body_plain=body_plain,
                cc=cc,
                bcc=bcc,
                send_mode=send_mode,
                scheduled_at=scheduled_at,
            ),
            options=options,
        )

    def draft_compose(
        self,
        *,
        to: NotGivenOr[str] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        instruction: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> GeneratedDraft:
        """Generate a cold-outreach draft for *to*. Charges AI credits.

        Grounded in the contact record, prior history, and the organization's
        voice profile. Never sends.
        """
        return self._post(
            "/unibox/compose/draft",
            cast_to=GeneratedDraft,
            body=drop_not_given(
                {"to": to, "subject": subject, "instruction": instruction}
            ),
            options=options,
        )

    # -- autosaved compose drafts -------------------------------------------
    def list_drafts(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[ComposeDraft]:
        """List your autosaved compose drafts."""
        return self._get_api_list("/unibox/drafts", model=ComposeDraft, options=options)

    def save_draft(
        self,
        draft_id: str,
        *,
        email_account_id: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        cc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        bcc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ComposeDraftSaved:
        """Upsert an autosaved compose draft.

        *draft_id* is client-generated, which makes the call idempotent and
        safe to fire from a debounced autosave.
        """
        return self._put(
            f"/unibox/drafts/{draft_id}",
            cast_to=ComposeDraftSaved,
            body=_draft_body(
                email_account_id=email_account_id,
                to=to,
                cc=cc,
                bcc=bcc,
                subject=subject,
                body=body,
            ),
            options=options,
        )

    def delete_draft(
        self, draft_id: str, *, options: RequestOptions | None = None
    ) -> ComposeDraftDeleted:
        """Delete an autosaved compose draft."""
        return self._delete(
            f"/unibox/drafts/{draft_id}", cast_to=ComposeDraftDeleted, options=options
        )

    # -- inbox agent drafts --------------------------------------------------
    def list_agent_drafts(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[AgentDraft]:
        """List the inbox agent's pending drafts, newest first."""
        return self._get_api_list(
            "/unibox/agent-drafts", model=AgentDraft, options=options
        )

    def approve_agent_draft(
        self,
        draft_id: str,
        *,
        body: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SendResult:
        """Approve an agent draft and send it.

        Args:
            draft_id: The draft to approve.
            body: An edited body to send instead of the drafted one.
        """
        return self._post(
            f"/unibox/agent-drafts/{draft_id}/approve",
            cast_to=SendResult,
            body=drop_not_given({"body": body}),
            options=options,
        )

    def discard_agent_draft(
        self, draft_id: str, *, options: RequestOptions | None = None
    ) -> AgentDraftDiscarded:
        """Discard an agent draft without sending."""
        return self._post(
            f"/unibox/agent-drafts/{draft_id}/discard",
            cast_to=AgentDraftDiscarded,
            options=options,
        )

    # -- snoozes -------------------------------------------------------------
    def list_snoozes(
        self, *, options: RequestOptions | None = None
    ) -> SyncCursorPage[Snooze]:
        """List your active thread snoozes."""
        return self._get_api_list("/unibox/snoozes", model=Snooze, options=options)

    def snooze(
        self,
        *,
        thread_id: str,
        snoozed_until: str,
        options: RequestOptions | None = None,
    ) -> Snooze:
        """Hide a thread from the inbox until *snoozed_until* (RFC 3339).

        Snoozing an already-snoozed thread moves the wake time rather than
        creating a second snooze.
        """
        return self._post(
            "/unibox/snooze",
            cast_to=Snooze,
            body={"thread_id": thread_id, "snoozed_until": snoozed_until},
            options=options,
        )

    def unsnooze(
        self, *, thread_id: str, options: RequestOptions | None = None
    ) -> SnoozeDeleted:
        """Un-snooze a thread. Succeeds even if it was not snoozed."""
        return self._delete(
            "/unibox/snooze",
            cast_to=SnoozeDeleted,
            query={"thread_id": thread_id},
            options=options,
        )

    # -- scheduled sends -----------------------------------------------------
    def list_scheduled(
        self,
        *,
        thread_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[ScheduledSend]:
        """List pending scheduled sends, optionally scoped to one thread."""
        return self._get_api_list(
            "/unibox/scheduled",
            model=ScheduledSend,
            query={"thread_id": thread_id},
            options=options,
        )

    def cancel_scheduled(
        self, task_id: str, *, options: RequestOptions | None = None
    ) -> ScheduledSendCancelled:
        """Cancel a pending scheduled send."""
        return self._delete(
            f"/unibox/scheduled/{task_id}",
            cast_to=ScheduledSendCancelled,
            options=options,
        )


class AsyncUnibox(AsyncAPIResource):
    """Asynchronous ``unibox`` resource."""

    # -- reading ------------------------------------------------------------
    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        email_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        folder: NotGivenOr[str] = NOT_GIVEN,
        direction: NotGivenOr[str] = NOT_GIVEN,
        from_: NotGivenOr[str] = NOT_GIVEN,
        address: NotGivenOr[str] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        unseen: NotGivenOr[bool] = NOT_GIVEN,
        snoozed: NotGivenOr[str] = NOT_GIVEN,
        awaiting_reply: NotGivenOr[bool] = NOT_GIVEN,
        agent_drafts: NotGivenOr[bool] = NOT_GIVEN,
        uncategorized: NotGivenOr[bool] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        since: NotGivenOr[str] = NOT_GIVEN,
        until: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[MessagePreview]:
        """List inbox messages, newest first (auto-paginating).

        Args:
            limit: Page size.
            cursor: Pagination cursor.
            email_ids: Restrict to these mailbox (email account) ids.
            folder: Canonical folder scope: ``inbox``, ``sent``, ``drafts``,
                ``archive``, ``spam`` or ``trash``. Omit for every folder
                except ``spam`` and ``trash``.
            direction: ``"sent"`` or ``"received"``.
            from_: Match the sender address.
            address: Match either side of the conversation.
            subject: Match the subject.
            unseen: Only unread messages.
            snoozed: ``"only"`` or ``"exclude"`` to include or hide snoozed
                threads.
            awaiting_reply: Only threads waiting on a reply from you.
            agent_drafts: Only threads with a pending inbox-agent draft.
            uncategorized: Only threads carrying no conversation labels.
            category_ids: Only threads carrying any of these labels.
            since: Lower bound on the message date (RFC 3339).
            until: Upper bound on the message date (RFC 3339).
        """
        return self._get_api_list(
            "/unibox",
            model=MessagePreview,
            query=_list_query(
                limit=limit,
                cursor=cursor,
                email_ids=email_ids,
                folder=folder,
                direction=direction,
                from_=from_,
                address=address,
                subject=subject,
                unseen=unseen,
                snoozed=snoozed,
                awaiting_reply=awaiting_reply,
                agent_drafts=agent_drafts,
                uncategorized=uncategorized,
                category_ids=category_ids,
                since=since,
                until=until,
            ),
            options=options,
        )

    async def retrieve(
        self, message_id: str, *, options: RequestOptions | None = None
    ) -> Message:
        """Retrieve a single message by id."""
        return await self._get(
            f"/unibox/{message_id}", cast_to=Message, options=options
        )

    def thread(
        self,
        *,
        thread_id: NotGivenOr[str] = NOT_GIVEN,
        email_id: NotGivenOr[str] = NOT_GIVEN,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[MessagePreview]:
        """List a conversation's messages, oldest first (auto-paginating).

        Rows carry the same shape as the inbox list; fetch a message with
        :meth:`retrieve` for its body.

        Args:
            thread_id: The thread to expand.
            email_id: The mailbox the thread belongs to. Omit to read the
                thread across every mailbox in the organization.
        """
        return self._get_api_list(
            "/unibox/thread",
            model=MessagePreview,
            query={
                "thread_id": thread_id,
                "email_id": email_id,
                "limit": limit,
                "cursor": cursor,
            },
            options=options,
        )

    async def count(
        self,
        *,
        email_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> UnseenCount:
        """Return the unread count, optionally scoped to one mailbox."""
        return await self._get(
            "/unibox/count",
            cast_to=UnseenCount,
            query={"email_id": email_id},
            options=options,
        )

    async def overview(
        self, *, options: RequestOptions | None = None
    ) -> UniboxOverview:
        """Return the inbox roll-up (unread, today, week, snoozed, per-mailbox)."""
        return await self._get(
            "/unibox/overview", cast_to=UniboxOverview, options=options
        )

    # -- labels + read state -------------------------------------------------
    async def list_thread_labels(
        self, *, thread_id: str, options: RequestOptions | None = None
    ) -> ThreadLabels:
        """Return the conversation labels on a thread."""
        return await self._get(
            "/unibox/thread/labels",
            cast_to=ThreadLabels,
            query={"thread_id": thread_id},
            options=options,
        )

    async def set_thread_labels(
        self,
        *,
        thread_id: str,
        category_ids: Sequence[str],
        options: RequestOptions | None = None,
    ) -> ThreadLabels:
        """Replace a thread's conversation labels wholesale.

        This is a ``PUT``: *category_ids* is the desired final set, so retries
        are safe and passing an empty list clears every label.
        """
        return await self._put(
            "/unibox/thread/labels",
            cast_to=ThreadLabels,
            body={"thread_id": thread_id, "category_ids": list(category_ids)},
            options=options,
        )

    async def mark_seen(
        self,
        *,
        email_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        folder: NotGivenOr[str] = NOT_GIVEN,
        seen: bool = True,
        options: RequestOptions | None = None,
    ) -> SeenResult:
        """Mark up to 500 messages as read or unread.

        Args:
            email_ids: The message ids to update (max 500).
            folder: Instead of listing ids, mark every unread message in this
                folder across the whole workspace.
            seen: ``True`` to mark read, ``False`` to mark unread.
        """
        return await self._patch(
            "/unibox/seen",
            cast_to=SeenResult,
            body=drop_not_given(
                {
                    "email_ids": (
                        list(email_ids) if is_given(email_ids) else NOT_GIVEN
                    ),
                    "folder": folder,
                    "seen": seen,
                }
            ),
            options=options,
        )

    # -- sending -------------------------------------------------------------
    async def reply(
        self,
        *,
        email_account_id: str,
        to: Sequence[str],
        subject: str,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        cc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        bcc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        in_reply_to: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        thread_id: NotGivenOr[str] = NOT_GIVEN,
        send_mode: NotGivenOr[str] = NOT_GIVEN,
        scheduled_at: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SendResult:
        """Send a reply from a connected mailbox.

        Args:
            email_account_id: The mailbox to send from.
            to: Recipient addresses (at least one).
            subject: The reply subject.
            body_html: The HTML body.
            body_plain: The plain-text body.
            in_reply_to: ``Message-ID`` values this reply threads under.
            thread_id: The thread being replied to.
            send_mode: ``"instant"`` (the default) or ``"scheduled"``.
            scheduled_at: When to send, for ``send_mode="scheduled"``
                (RFC 3339).
        """
        return await self._post(
            "/unibox/reply",
            cast_to=SendResult,
            body=_reply_body(
                email_account_id=email_account_id,
                to=to,
                subject=subject,
                body_html=body_html,
                body_plain=body_plain,
                cc=cc,
                bcc=bcc,
                in_reply_to=in_reply_to,
                thread_id=thread_id,
                send_mode=send_mode,
                scheduled_at=scheduled_at,
            ),
            options=options,
        )

    async def draft_reply(
        self,
        *,
        thread_id: str,
        instruction: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> GeneratedDraft:
        """Generate a reply draft grounded in the thread. Charges AI credits.

        Never sends: pass the returned ``text`` to :meth:`reply` when you are
        happy with it.
        """
        return await self._post(
            "/unibox/reply/draft",
            cast_to=GeneratedDraft,
            body=drop_not_given({"thread_id": thread_id, "instruction": instruction}),
            options=options,
        )

    async def compose_candidates(
        self,
        *,
        to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ComposeCandidates:
        """Score the mailboxes available for composing to *to*.

        Args:
            to: The recipient address. Omit for an unscored mailbox list.
        """
        return await self._get(
            "/unibox/compose/candidates",
            cast_to=ComposeCandidates,
            query={"to": to},
            options=options,
        )

    async def compose(
        self,
        *,
        to: Sequence[str],
        subject: str,
        email_account_id: NotGivenOr[str] = NOT_GIVEN,
        from_tag_id: NotGivenOr[str] = NOT_GIVEN,
        body_html: NotGivenOr[str] = NOT_GIVEN,
        body_plain: NotGivenOr[str] = NOT_GIVEN,
        cc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        bcc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        send_mode: NotGivenOr[str] = NOT_GIVEN,
        scheduled_at: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ComposeResult:
        """Send a brand-new outbound email.

        Omit *email_account_id* to let the server pick the best mailbox
        (auto mode); pass *from_tag_id* to restrict that choice to a mailbox
        tag.
        """
        return await self._post(
            "/unibox/compose",
            cast_to=ComposeResult,
            body=_compose_body(
                to=to,
                subject=subject,
                email_account_id=email_account_id,
                from_tag_id=from_tag_id,
                body_html=body_html,
                body_plain=body_plain,
                cc=cc,
                bcc=bcc,
                send_mode=send_mode,
                scheduled_at=scheduled_at,
            ),
            options=options,
        )

    async def draft_compose(
        self,
        *,
        to: NotGivenOr[str] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        instruction: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> GeneratedDraft:
        """Generate a cold-outreach draft for *to*. Charges AI credits.

        Grounded in the contact record, prior history, and the organization's
        voice profile. Never sends.
        """
        return await self._post(
            "/unibox/compose/draft",
            cast_to=GeneratedDraft,
            body=drop_not_given(
                {"to": to, "subject": subject, "instruction": instruction}
            ),
            options=options,
        )

    # -- autosaved compose drafts -------------------------------------------
    def list_drafts(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[ComposeDraft]:
        """List your autosaved compose drafts."""
        return self._get_api_list("/unibox/drafts", model=ComposeDraft, options=options)

    async def save_draft(
        self,
        draft_id: str,
        *,
        email_account_id: NotGivenOr[str] = NOT_GIVEN,
        to: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        cc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        bcc: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        subject: NotGivenOr[str] = NOT_GIVEN,
        body: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> ComposeDraftSaved:
        """Upsert an autosaved compose draft.

        *draft_id* is client-generated, which makes the call idempotent and
        safe to fire from a debounced autosave.
        """
        return await self._put(
            f"/unibox/drafts/{draft_id}",
            cast_to=ComposeDraftSaved,
            body=_draft_body(
                email_account_id=email_account_id,
                to=to,
                cc=cc,
                bcc=bcc,
                subject=subject,
                body=body,
            ),
            options=options,
        )

    async def delete_draft(
        self, draft_id: str, *, options: RequestOptions | None = None
    ) -> ComposeDraftDeleted:
        """Delete an autosaved compose draft."""
        return await self._delete(
            f"/unibox/drafts/{draft_id}", cast_to=ComposeDraftDeleted, options=options
        )

    # -- inbox agent drafts --------------------------------------------------
    def list_agent_drafts(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[AgentDraft]:
        """List the inbox agent's pending drafts, newest first."""
        return self._get_api_list(
            "/unibox/agent-drafts", model=AgentDraft, options=options
        )

    async def approve_agent_draft(
        self,
        draft_id: str,
        *,
        body: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SendResult:
        """Approve an agent draft and send it.

        Args:
            draft_id: The draft to approve.
            body: An edited body to send instead of the drafted one.
        """
        return await self._post(
            f"/unibox/agent-drafts/{draft_id}/approve",
            cast_to=SendResult,
            body=drop_not_given({"body": body}),
            options=options,
        )

    async def discard_agent_draft(
        self, draft_id: str, *, options: RequestOptions | None = None
    ) -> AgentDraftDiscarded:
        """Discard an agent draft without sending."""
        return await self._post(
            f"/unibox/agent-drafts/{draft_id}/discard",
            cast_to=AgentDraftDiscarded,
            options=options,
        )

    # -- snoozes -------------------------------------------------------------
    def list_snoozes(
        self, *, options: RequestOptions | None = None
    ) -> AsyncPaginator[Snooze]:
        """List your active thread snoozes."""
        return self._get_api_list("/unibox/snoozes", model=Snooze, options=options)

    async def snooze(
        self,
        *,
        thread_id: str,
        snoozed_until: str,
        options: RequestOptions | None = None,
    ) -> Snooze:
        """Hide a thread from the inbox until *snoozed_until* (RFC 3339).

        Snoozing an already-snoozed thread moves the wake time rather than
        creating a second snooze.
        """
        return await self._post(
            "/unibox/snooze",
            cast_to=Snooze,
            body={"thread_id": thread_id, "snoozed_until": snoozed_until},
            options=options,
        )

    async def unsnooze(
        self, *, thread_id: str, options: RequestOptions | None = None
    ) -> SnoozeDeleted:
        """Un-snooze a thread. Succeeds even if it was not snoozed."""
        return await self._delete(
            "/unibox/snooze",
            cast_to=SnoozeDeleted,
            query={"thread_id": thread_id},
            options=options,
        )

    # -- scheduled sends -----------------------------------------------------
    def list_scheduled(
        self,
        *,
        thread_id: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[ScheduledSend]:
        """List pending scheduled sends, optionally scoped to one thread."""
        return self._get_api_list(
            "/unibox/scheduled",
            model=ScheduledSend,
            query={"thread_id": thread_id},
            options=options,
        )

    async def cancel_scheduled(
        self, task_id: str, *, options: RequestOptions | None = None
    ) -> ScheduledSendCancelled:
        """Cancel a pending scheduled send."""
        return await self._delete(
            f"/unibox/scheduled/{task_id}",
            cast_to=ScheduledSendCancelled,
            options=options,
        )
