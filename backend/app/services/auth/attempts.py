"""AuthAttemptService — in-memory failed-attempt tracking + lockout.

Lockout uses HTTP 423 (Locked). The clock is injectable (module-level) so tests
do not depend on real time. NOTE: in-memory and per-process; production with
multiple workers should back this with Redis.
"""
from __future__ import annotations

import time
from collections.abc import Callable

MAX_ATTEMPTS = 5
LOCK_SECONDS = 15 * 60

_now: Callable[[], float] = time.time


def set_clock(fn: Callable[[], float]) -> None:
    global _now
    _now = fn


def reset_clock() -> None:
    global _now
    _now = time.time


class AuthAttemptService:
    _store: dict[str, dict] = {}

    @classmethod
    def is_locked(cls, key: str) -> bool:
        entry = cls._store.get(key.lower())
        return bool(entry) and _now() < entry["locked_until"]

    @classmethod
    def record_failure(cls, key: str) -> bool:
        """Record a failed attempt. Returns True if this caused a lock."""
        k = key.lower()
        entry = cls._store.setdefault(k, {"count": 0, "locked_until": 0.0})
        if _now() < entry["locked_until"]:
            return False  # already locked; no change
        if entry["count"] >= MAX_ATTEMPTS:
            entry["count"] = 0  # previous lock expired -> fresh window
        entry["count"] += 1
        if entry["count"] >= MAX_ATTEMPTS:
            entry["locked_until"] = _now() + LOCK_SECONDS
            return True
        return False

    @classmethod
    def reset(cls, key: str) -> None:
        cls._store.pop(key.lower(), None)

    @classmethod
    def reset_all(cls) -> None:
        cls._store.clear()
