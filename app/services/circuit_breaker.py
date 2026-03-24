"""
輕量級 Circuit Breaker（斷路器）

防止外部 API（Voyage / Gemini / Pinecone）連續失敗時繼續送出請求,
使系統能快速失敗並恢復。

三狀態：CLOSED → OPEN → HALF_OPEN → CLOSED
"""
import logging
import threading
import time
from enum import Enum
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """斷路器已開啟，拒絕請求"""
    def __init__(self, name: str, remaining_seconds: float):
        self.name = name
        self.remaining_seconds = remaining_seconds
        super().__init__(
            f"Circuit breaker '{name}' is OPEN. "
            f"Retry after {remaining_seconds:.0f}s."
        )


class CircuitBreaker:
    """
    Thread-safe circuit breaker.

    Parameters
    ----------
    name : str
        Identifier for this breaker (e.g. "voyage", "gemini", "pinecone").
    failure_threshold : int
        Consecutive failures before opening the circuit.
    reset_timeout : float
        Seconds to wait in OPEN state before transitioning to HALF_OPEN.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.monotonic() - self._last_failure_time >= self.reset_timeout:
                    self._state = CircuitState.HALF_OPEN
                    logger.info(f"[CircuitBreaker:{self.name}] OPEN → HALF_OPEN")
            return self._state

    def call(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute *fn* through the circuit breaker."""
        state = self.state

        if state == CircuitState.OPEN:
            remaining = self.reset_timeout - (time.monotonic() - self._last_failure_time)
            raise CircuitOpenError(self.name, max(remaining, 0))

        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    async def call_async(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute an async *fn* through the circuit breaker."""
        state = self.state

        if state == CircuitState.OPEN:
            remaining = self.reset_timeout - (time.monotonic() - self._last_failure_time)
            raise CircuitOpenError(self.name, max(remaining, 0))

        try:
            result = await fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                logger.info(f"[CircuitBreaker:{self.name}] HALF_OPEN → CLOSED (success)")
            self._failure_count = 0
            self._state = CircuitState.CLOSED

    def _on_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._failure_count >= self.failure_threshold:
                if self._state != CircuitState.OPEN:
                    logger.warning(
                        f"[CircuitBreaker:{self.name}] → OPEN "
                        f"(failures={self._failure_count})"
                    )
                self._state = CircuitState.OPEN


# ── Singleton breakers for external APIs ──
voyage_breaker = CircuitBreaker("voyage", failure_threshold=5, reset_timeout=60)
gemini_breaker = CircuitBreaker("gemini", failure_threshold=3, reset_timeout=90)
pinecone_breaker = CircuitBreaker("pinecone", failure_threshold=5, reset_timeout=60)
