"""Operator availability abstraction (TZ §4.6).

Real presence/ACD integration comes later; for the MVP we use a mock provider.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum


class OperatorState(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    UNAVAILABLE = "unavailable"


class OperatorAvailabilityProvider(ABC):
    @abstractmethod
    async def get_state(self) -> OperatorState:
        raise NotImplementedError


class MockOperatorAvailability(OperatorAvailabilityProvider):
    """Deterministic availability for tests and the MVP simulation."""

    def __init__(self, state: OperatorState = OperatorState.AVAILABLE) -> None:
        self._state = state

    async def get_state(self) -> OperatorState:
        return self._state
