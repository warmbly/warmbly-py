"""The ``emails`` resource: manage email accounts (mailboxes).

Maps to the ``/v1/emails`` route group. An :class:`EmailAccount` is a connected
mailbox (Gmail, Outlook, or SMTP/IMAP) that campaigns send from and that the
warmup engine drives. This resource covers account lifecycle, tracking-domain
configuration, warmup control (start/pause/resume/stop, ban status, appeals),
deliverability auth checks, address verification, and sending one-off emails
from an account.
"""

from __future__ import annotations

from collections.abc import Sequence

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncEmails",
    "EmailAccount",
    "EmailAuthCheck",
    "EmailSendResult",
    "EmailVerification",
    "Emails",
    "WarmupAppeal",
    "WarmupBanStatus",
]


class EmailAccount(BaseModel):
    """A connected email account (mailbox)."""

    id: str
    user_id: str | None = None
    organization_id: str | None = None
    email: str | None = None
    name: str | None = None
    provider: str | None = None
    status: str | None = None
    warmup: bool | None = None
    tracking_domain: str | None = None
    tracking_domain_verified: bool | None = None
    timezone: str | None = None
    tags: Sequence[str] = []
    last_synced_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class EmailAuthCheck(BaseModel):
    """The result of a deliverability authentication check for an account."""

    email_account_id: str | None = None
    spf: bool | None = None
    dkim: bool | None = None
    dmarc: bool | None = None
    mx: bool | None = None
    status: str | None = None
    checked_at: str | None = None


class EmailVerification(BaseModel):
    """The result of verifying an email address (deliverability/validity)."""

    email: str | None = None
    valid: bool | None = None
    deliverable: bool | None = None
    reason: str | None = None
    status: str | None = None


class WarmupBanStatus(BaseModel):
    """The warmup ban / blocklist status for an account."""

    email_account_id: str | None = None
    banned: bool | None = None
    reason: str | None = None
    blocklists: Sequence[str] = []
    banned_at: str | None = None
    can_appeal: bool | None = None


class WarmupAppeal(BaseModel):
    """The result of submitting a warmup ban appeal."""

    id: str | None = None
    email_account_id: str | None = None
    status: str | None = None
    message: str | None = None
    created_at: str | None = None


class EmailSendResult(BaseModel):
    """The result of sending an email from an account."""

    id: str | None = None
    message_id: str | None = None
    email_account_id: str | None = None
    status: str | None = None
    sent_at: str | None = None


class Emails(SyncAPIResource):
    """Synchronous ``emails`` resource."""

    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[EmailAccount]:
        """List connected email accounts (auto-paginating).

        Args:
            limit: Maximum number of accounts per page.
            cursor: Opaque pagination cursor from a previous page.
            options: Per-request overrides.
        """
        return self._get_api_list(
            "/emails",
            model=EmailAccount,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    def retrieve(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccount:
        """Retrieve a single email account by id.

        Args:
            email_id: The account id.
            options: Per-request overrides.
        """
        return self._get(f"/emails/{email_id}", cast_to=EmailAccount, options=options)

    def update(
        self,
        email_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        timezone: NotGivenOr[str] = NOT_GIVEN,
        tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> EmailAccount:
        """Update an account's editable metadata.

        Args:
            email_id: The account id.
            name: A new display name for the account.
            timezone: An IANA timezone (e.g. ``"America/New_York"``).
            tags: Replacement list of tags.
            options: Per-request overrides.
        """
        body = drop_not_given(
            {
                "name": name,
                "timezone": timezone,
                "tags": tags,
            }
        )
        return self._patch(
            f"/emails/{email_id}", cast_to=EmailAccount, body=body, options=options
        )

    def delete(self, email_id: str, *, options: RequestOptions | None = None) -> None:
        """Disconnect and delete an email account.

        Args:
            email_id: The account id.
            options: Per-request overrides.
        """
        return self._delete(f"/emails/{email_id}", cast_to=type(None), options=options)

    def track(
        self,
        email_id: str,
        *,
        tracking_domain: str,
        options: RequestOptions | None = None,
    ) -> EmailAccount:
        """Set the custom open/click tracking domain for an account.

        Args:
            email_id: The account id.
            tracking_domain: The custom tracking domain to use.
            options: Per-request overrides.
        """
        body = drop_not_given({"tracking_domain": tracking_domain})
        return self._patch(
            f"/emails/{email_id}/track",
            cast_to=EmailAccount,
            body=body,
            options=options,
        )

    def warmup_start(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccount:
        """Start warmup for an account.

        Args:
            email_id: The account id.
            options: Per-request overrides.
        """
        return self._post(
            f"/emails/{email_id}/warmup/start", cast_to=EmailAccount, options=options
        )

    def warmup_pause(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccount:
        """Pause warmup for an account.

        Args:
            email_id: The account id.
            options: Per-request overrides.
        """
        return self._post(
            f"/emails/{email_id}/warmup/pause", cast_to=EmailAccount, options=options
        )

    def warmup_resume(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccount:
        """Resume a paused warmup for an account.

        Args:
            email_id: The account id.
            options: Per-request overrides.
        """
        return self._post(
            f"/emails/{email_id}/warmup/resume", cast_to=EmailAccount, options=options
        )

    def warmup_stop(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccount:
        """Stop warmup for an account.

        Args:
            email_id: The account id.
            options: Per-request overrides.
        """
        return self._post(
            f"/emails/{email_id}/warmup/stop", cast_to=EmailAccount, options=options
        )

    def warmup_ban_status(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> WarmupBanStatus:
        """Get the warmup ban / blocklist status for an account.

        Args:
            email_id: The account id.
            options: Per-request overrides.
        """
        return self._get(
            f"/emails/{email_id}/warmup/ban-status",
            cast_to=WarmupBanStatus,
            options=options,
        )

    def warmup_appeal(
        self,
        email_id: str,
        *,
        message: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> WarmupAppeal:
        """Submit an appeal against a warmup ban for an account.

        Args:
            email_id: The account id.
            message: An optional explanation supporting the appeal.
            options: Per-request overrides.
        """
        body = drop_not_given({"message": message})
        return self._post(
            f"/emails/{email_id}/warmup/appeal",
            cast_to=WarmupAppeal,
            body=body,
            options=options,
        )

    def auth_check(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAuthCheck:
        """Run a deliverability authentication check (SPF/DKIM/DMARC/MX).

        Args:
            email_id: The account id.
            options: Per-request overrides.
        """
        return self._get(
            f"/emails/{email_id}/auth-check",
            cast_to=EmailAuthCheck,
            options=options,
        )

    def verify(
        self, *, email: str, options: RequestOptions | None = None
    ) -> EmailVerification:
        """Verify an email address for validity and deliverability.

        Args:
            email: The email address to verify.
            options: Per-request overrides.
        """
        body = drop_not_given({"email": email})
        return self._post(
            "/emails/verify", cast_to=EmailVerification, body=body, options=options
        )

    def send(
        self,
        email_id: str,
        *,
        to: str,
        subject: str,
        text: NotGivenOr[str] = NOT_GIVEN,
        html: NotGivenOr[str] = NOT_GIVEN,
        reply_to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> EmailSendResult:
        """Send a one-off email from this account.

        Args:
            email_id: The id of the account to send from.
            to: The recipient address.
            subject: The email subject.
            text: The plain-text body.
            html: The HTML body.
            reply_to: An optional ``Reply-To`` address.
            options: Per-request overrides.
        """
        body = drop_not_given(
            {
                "to": to,
                "subject": subject,
                "text": text,
                "html": html,
                "reply_to": reply_to,
            }
        )
        return self._post(
            f"/emails/{email_id}/send",
            cast_to=EmailSendResult,
            body=body,
            options=options,
        )


class AsyncEmails(AsyncAPIResource):
    """Asynchronous ``emails`` resource."""

    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[EmailAccount]:
        """List connected email accounts (auto-paginating).

        Args:
            limit: Maximum number of accounts per page.
            cursor: Opaque pagination cursor from a previous page.
            options: Per-request overrides.
        """
        return self._get_api_list(
            "/emails",
            model=EmailAccount,
            query={"limit": limit, "cursor": cursor},
            options=options,
        )

    async def retrieve(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccount:
        """Retrieve a single email account by id.

        Args:
            email_id: The account id.
            options: Per-request overrides.
        """
        return await self._get(
            f"/emails/{email_id}", cast_to=EmailAccount, options=options
        )

    async def update(
        self,
        email_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        timezone: NotGivenOr[str] = NOT_GIVEN,
        tags: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> EmailAccount:
        """Update an account's editable metadata.

        Args:
            email_id: The account id.
            name: A new display name for the account.
            timezone: An IANA timezone (e.g. ``"America/New_York"``).
            tags: Replacement list of tags.
            options: Per-request overrides.
        """
        body = drop_not_given(
            {
                "name": name,
                "timezone": timezone,
                "tags": tags,
            }
        )
        return await self._patch(
            f"/emails/{email_id}", cast_to=EmailAccount, body=body, options=options
        )

    async def delete(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> None:
        """Disconnect and delete an email account.

        Args:
            email_id: The account id.
            options: Per-request overrides.
        """
        return await self._delete(
            f"/emails/{email_id}", cast_to=type(None), options=options
        )

    async def track(
        self,
        email_id: str,
        *,
        tracking_domain: str,
        options: RequestOptions | None = None,
    ) -> EmailAccount:
        """Set the custom open/click tracking domain for an account.

        Args:
            email_id: The account id.
            tracking_domain: The custom tracking domain to use.
            options: Per-request overrides.
        """
        body = drop_not_given({"tracking_domain": tracking_domain})
        return await self._patch(
            f"/emails/{email_id}/track",
            cast_to=EmailAccount,
            body=body,
            options=options,
        )

    async def warmup_start(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccount:
        """Start warmup for an account.

        Args:
            email_id: The account id.
            options: Per-request overrides.
        """
        return await self._post(
            f"/emails/{email_id}/warmup/start", cast_to=EmailAccount, options=options
        )

    async def warmup_pause(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccount:
        """Pause warmup for an account.

        Args:
            email_id: The account id.
            options: Per-request overrides.
        """
        return await self._post(
            f"/emails/{email_id}/warmup/pause", cast_to=EmailAccount, options=options
        )

    async def warmup_resume(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccount:
        """Resume a paused warmup for an account.

        Args:
            email_id: The account id.
            options: Per-request overrides.
        """
        return await self._post(
            f"/emails/{email_id}/warmup/resume", cast_to=EmailAccount, options=options
        )

    async def warmup_stop(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAccount:
        """Stop warmup for an account.

        Args:
            email_id: The account id.
            options: Per-request overrides.
        """
        return await self._post(
            f"/emails/{email_id}/warmup/stop", cast_to=EmailAccount, options=options
        )

    async def warmup_ban_status(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> WarmupBanStatus:
        """Get the warmup ban / blocklist status for an account.

        Args:
            email_id: The account id.
            options: Per-request overrides.
        """
        return await self._get(
            f"/emails/{email_id}/warmup/ban-status",
            cast_to=WarmupBanStatus,
            options=options,
        )

    async def warmup_appeal(
        self,
        email_id: str,
        *,
        message: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> WarmupAppeal:
        """Submit an appeal against a warmup ban for an account.

        Args:
            email_id: The account id.
            message: An optional explanation supporting the appeal.
            options: Per-request overrides.
        """
        body = drop_not_given({"message": message})
        return await self._post(
            f"/emails/{email_id}/warmup/appeal",
            cast_to=WarmupAppeal,
            body=body,
            options=options,
        )

    async def auth_check(
        self, email_id: str, *, options: RequestOptions | None = None
    ) -> EmailAuthCheck:
        """Run a deliverability authentication check (SPF/DKIM/DMARC/MX).

        Args:
            email_id: The account id.
            options: Per-request overrides.
        """
        return await self._get(
            f"/emails/{email_id}/auth-check",
            cast_to=EmailAuthCheck,
            options=options,
        )

    async def verify(
        self, *, email: str, options: RequestOptions | None = None
    ) -> EmailVerification:
        """Verify an email address for validity and deliverability.

        Args:
            email: The email address to verify.
            options: Per-request overrides.
        """
        body = drop_not_given({"email": email})
        return await self._post(
            "/emails/verify", cast_to=EmailVerification, body=body, options=options
        )

    async def send(
        self,
        email_id: str,
        *,
        to: str,
        subject: str,
        text: NotGivenOr[str] = NOT_GIVEN,
        html: NotGivenOr[str] = NOT_GIVEN,
        reply_to: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> EmailSendResult:
        """Send a one-off email from this account.

        Args:
            email_id: The id of the account to send from.
            to: The recipient address.
            subject: The email subject.
            text: The plain-text body.
            html: The HTML body.
            reply_to: An optional ``Reply-To`` address.
            options: Per-request overrides.
        """
        body = drop_not_given(
            {
                "to": to,
                "subject": subject,
                "text": text,
                "html": html,
                "reply_to": reply_to,
            }
        )
        return await self._post(
            f"/emails/{email_id}/send",
            cast_to=EmailSendResult,
            body=body,
            options=options,
        )
