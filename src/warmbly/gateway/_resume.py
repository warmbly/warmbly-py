"""Per-topic sequence tracking and resume bookkeeping.

The gateway tags broadcast events on resumable topics (``org:*``) with a
monotonically increasing ``seq``. To recover events missed across a reconnect,
the client tracks the highest ``seq`` it has seen per topic and, when rejoining,
passes ``{"resume": {"last_seq": N}}`` in the join params. The server then
replays the buffered events and reports the outcome via a ``resumed`` or
``resume_failed`` event.

This module is pure state and small helpers, no I/O. When a resume fails the
caller is expected to fall back to a full re-sync over the REST API.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

__all__ = ["ResumeFailedCallback", "ResumeTracker"]

#: Callback invoked when the server reports that a resume could not be honored.
#: Receives the topic and the ``resume_failed`` payload so the application can
#: trigger a REST re-sync. It may be a coroutine function.
ResumeFailedCallback = Callable[[str, dict[str, Any]], Awaitable[None]]

# Topic prefixes that support sequence-based resume.
_RESUMABLE_PREFIXES = ("org:",)


class ResumeTracker:
    """Tracks the highest observed ``seq`` per topic for resume on reconnect."""

    def __init__(self) -> None:
        self._last_seq: dict[str, int] = {}

    @staticmethod
    def supports_resume(topic: str) -> bool:
        """Return whether *topic* participates in sequence-based resume."""
        return topic.startswith(_RESUMABLE_PREFIXES)

    def observe(self, topic: str, payload: dict[str, Any]) -> None:
        """Record the ``seq`` carried by an incoming event for *topic*, if any."""
        seq = payload.get("seq")
        if isinstance(seq, int):
            current = self._last_seq.get(topic)
            if current is None or seq > current:
                self._last_seq[topic] = seq

    def last_seq(self, topic: str) -> int | None:
        """Return the highest ``seq`` observed for *topic*, or ``None``."""
        return self._last_seq.get(topic)

    def join_params(
        self, topic: str, params: dict[str, Any], *, resume: bool
    ) -> dict[str, Any]:
        """Augment join *params* with a ``resume`` block when applicable.

        Args:
            topic: The topic being joined.
            params: The base join parameters.
            resume: Whether the caller wants resume behavior.

        Returns:
            A new params dict; unchanged when resume is disabled, the topic is
            not resumable, or no prior ``seq`` is known.
        """
        if not resume or not self.supports_resume(topic):
            return params
        last = self._last_seq.get(topic)
        if last is None:
            return params
        merged = dict(params)
        merged["resume"] = {"last_seq": last}
        return merged

    def apply_resumed(self, topic: str, payload: dict[str, Any]) -> None:
        """Advance the tracked ``seq`` from a ``resumed`` reply, if present."""
        current_seq = payload.get("current_seq")
        if isinstance(current_seq, int):
            existing = self._last_seq.get(topic)
            if existing is None or current_seq > existing:
                self._last_seq[topic] = current_seq

    def reset(self, topic: str) -> None:
        """Forget the tracked ``seq`` for *topic* (e.g. after a failed resume)."""
        self._last_seq.pop(topic, None)
