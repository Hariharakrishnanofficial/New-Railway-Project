"""
Gemini Circuit Breaker — protects against cascading failures from AI API.
Implements the circuit breaker pattern with three states:
  - CLOSED: Normal operation, requests go through
  - OPEN: API down, immediately return fallback without calling API
  - HALF_OPEN: Testing if API recovered, allow limited requests through

Also handles API key rotation if multiple keys are configured.
"""

from __future__ import annotations

import os
import time
import logging
import threading
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class GeminiCircuitBreaker:
    """
    Circuit breaker for Gemini API calls.

    Usage:
        breaker = GeminiCircuitBreaker()
        if breaker.can_execute():
            try:
                result = call_gemini(...)
                breaker.record_success()
            except Exception:
                breaker.record_failure()
        else:
            result = fallback_response()
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 2,
    ):
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._half_open_max = half_open_max_calls
        self._half_open_calls = 0
        self._last_failure_time = 0.0
        self._lock = threading.Lock()

        # Stats
        self._total_calls = 0
        self._total_failures = 0
        self._total_fallbacks = 0

    @property
    def state(self) -> str:
        return self._state.value

    def can_execute(self) -> bool:
        """Check if a request should be allowed through."""
        with self._lock:
            self._total_calls += 1

            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                # Check if recovery timeout has elapsed
                if time.monotonic() - self._last_failure_time > self._recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info("Circuit breaker: OPEN → HALF_OPEN (testing recovery)")
                    return True
                self._total_fallbacks += 1
                return False

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self._half_open_max:
                    self._half_open_calls += 1
                    return True
                self._total_fallbacks += 1
                return False

            return False

    def record_success(self):
        """Record a successful API call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                logger.info("Circuit breaker: HALF_OPEN → CLOSED (API recovered)")
            elif self._state == CircuitState.CLOSED:
                self._failure_count = max(0, self._failure_count - 1)

    def record_failure(self):
        """Record a failed API call."""
        with self._lock:
            self._failure_count += 1
            self._total_failures += 1
            self._last_failure_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning("Circuit breaker: HALF_OPEN → OPEN (API still failing)")

            elif self._state == CircuitState.CLOSED and self._failure_count >= self._failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker: CLOSED → OPEN after {self._failure_count} failures"
                )

    def stats(self) -> dict:
        return {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "total_calls": self._total_calls,
            "total_failures": self._total_failures,
            "total_fallbacks": self._total_fallbacks,
        }


class APIKeyRotator:
    """
    Rotates between multiple Gemini API keys for load distribution and
    graceful degradation when individual keys are rate-limited.
    """

    def __init__(self):
        self._keys: list[str] = []
        self._current_index = 0
        self._lock = threading.Lock()
        self._load_keys()

    def _load_keys(self):
        """Load API keys from environment. Supports GEMINI_API_KEY and GEMINI_API_KEY_2, etc."""
        primary = os.getenv("GEMINI_API_KEY", "")
        if primary:
            self._keys.append(primary)

        # Check for additional keys
        for i in range(2, 10):
            key = os.getenv(f"GEMINI_API_KEY_{i}", "")
            if key:
                self._keys.append(key)

        if not self._keys:
            logger.warning("No Gemini API keys configured")

    def get_key(self) -> str:
        """Get the current API key."""
        with self._lock:
            if not self._keys:
                return ""
            return self._keys[self._current_index % len(self._keys)]

    def rotate(self):
        """Switch to the next API key (called after rate limit error)."""
        with self._lock:
            if len(self._keys) <= 1:
                return
            old_idx = self._current_index
            self._current_index = (self._current_index + 1) % len(self._keys)
            logger.info(f"API key rotated: key_{old_idx + 1} → key_{self._current_index + 1}")

    @property
    def key_count(self) -> int:
        return len(self._keys)


# ── Global singletons ─────────────────────────────────────────────────────────
gemini_breaker = GeminiCircuitBreaker()
key_rotator = APIKeyRotator()
