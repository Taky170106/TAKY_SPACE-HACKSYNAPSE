"""Event store — normalized, in-memory security-event history (§11 ingestion).

Track B needs recent events per device to build windowed features. This is the
"store" step: validated SecurityEvents land here keyed by device, newest last.
In-memory is fine for the prototype (§5); swap for SQLite later if needed.
"""
from __future__ import annotations

import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from app.schemas import EventType, SecurityEvent

# Events that mark a *legitimately authorized* content update landing on a device.
_AUTHORIZED_UPDATE_EVENTS = {
    EventType.content_hash_match,
}


class EventStore:
    def __init__(self, max_per_device: int = 1000) -> None:
        self._events: dict[str, deque[SecurityEvent]] = defaultdict(
            lambda: deque(maxlen=max_per_device)
        )
        self._lock = threading.Lock()

    def add(self, event: SecurityEvent) -> None:
        with self._lock:
            self._events[event.device_id].append(event)

    def add_many(self, events: list[SecurityEvent]) -> None:
        for ev in events:
            self.add(ev)

    def devices(self) -> list[str]:
        with self._lock:
            return list(self._events.keys())

    def recent(
        self,
        device_id: str,
        window_seconds: int,
        now: datetime | None = None,
    ) -> list[SecurityEvent]:
        """Events for `device_id` in `(now - window_seconds, now]`.

        Bounded on BOTH sides: events after `now` are excluded so a window
        anchored in the past can't see the future (important for replay/testing).
        """
        now = now or datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=window_seconds)
        with self._lock:
            return [
                e
                for e in self._events.get(device_id, ())
                if cutoff <= e.timestamp <= now
            ]

    def last_authorized_update(
        self, device_id: str, now: datetime | None = None
    ) -> datetime | None:
        """Timestamp of the most recent authorized content update at/before `now`."""
        with self._lock:
            for ev in reversed(self._events.get(device_id, ())):
                if now is not None and ev.timestamp > now:
                    continue
                if ev.event_type in _AUTHORIZED_UPDATE_EVENTS and ev.authorized:
                    return ev.timestamp
        return None
