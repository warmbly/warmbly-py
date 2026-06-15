"""Per-topic presence state derived from the gateway's presence events.

The gateway publishes presence as an initial ``presence_state`` snapshot
followed by incremental ``presence_diff`` deltas (``{"joins": ..., "leaves":
...}``). Each tracked key maps to a record of ``{"metas": [...]}`` where every
meta describes one connected client (``{online_at, name, avatar, page,
resource, action}``).

This module keeps that state in memory and exposes a read-only view per topic.
It performs no I/O; pushing ``presence:update`` is the connection layer's job.
"""

from __future__ import annotations

from typing import Any

__all__ = ["PresenceTracker"]


class PresenceTracker:
    """Maintains presence state per topic from ``presence_state``/``presence_diff``."""

    def __init__(self) -> None:
        # topic -> key -> {"metas": [meta, ...], ...}
        self._state: dict[str, dict[str, dict[str, Any]]] = {}

    def apply(self, topic: str, event: str, payload: dict[str, Any]) -> None:
        """Apply a presence event to the tracked state.

        Args:
            topic: The topic the presence event belongs to.
            event: Either ``presence_state`` or ``presence_diff``.
            payload: The event payload.
        """
        if event == "presence_state":
            self._apply_state(topic, payload)
        elif event == "presence_diff":
            self._apply_diff(topic, payload)

    def _apply_state(self, topic: str, payload: dict[str, Any]) -> None:
        # A presence_state payload is the full {key: {metas: [...]}} snapshot.
        snapshot: dict[str, dict[str, Any]] = {}
        for key, record in payload.items():
            if isinstance(record, dict):
                snapshot[key] = dict(record)
        self._state[topic] = snapshot

    def _apply_diff(self, topic: str, payload: dict[str, Any]) -> None:
        topic_state = self._state.setdefault(topic, {})
        leaves = payload.get("leaves")
        if isinstance(leaves, dict):
            for key in leaves:
                topic_state.pop(key, None)
        joins = payload.get("joins")
        if isinstance(joins, dict):
            for key, record in joins.items():
                if isinstance(record, dict):
                    topic_state[key] = dict(record)

    def presence(self, topic: str) -> dict[str, dict[str, Any]]:
        """Return a copy of the current presence map for *topic*.

        Args:
            topic: The topic to read presence for.

        Returns:
            A mapping of presence key to its record (``{"metas": [...]}``). An
            empty dict is returned for topics with no known presence.
        """
        return {key: dict(record) for key, record in self._state.get(topic, {}).items()}

    def clear(self, topic: str) -> None:
        """Drop all presence state for *topic* (e.g. after leaving)."""
        self._state.pop(topic, None)
