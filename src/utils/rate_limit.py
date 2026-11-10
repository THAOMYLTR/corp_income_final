"""[10/11] Điều tiết số lần gọi LLM / phút để không bị 429 "Queries-per-minute (QPM) rate limit
exceeded" — và khi vẫn bị 429 thì tự chờ rồi gọi lại, không bỏ sót hồ sơ.

Every LLM call (phân loại, trích xuất M1–M9, đánh giá, viết báo cáo) goes through ``call_llm``:

1. Before a call: ``sleep_needed`` = how long to wait so that
   - no more than ``qpm`` calls start in any 60 seconds (sliding window), and
   - calls are spread out, at least 60 / qpm seconds apart (no burst at the start of a minute).
2. On a 429: wait ``Retry-After`` if the server sends it, else until the oldest call of the last
   minute leaves the window (5–60 s); lower ``qpm`` to 80% of the calls made in the last minute
   (or of the current pace, if higher), then call again — up to LLM_RATE_LIMIT_RETRIES times.

QPM to start with: LLM_REQUESTS_PER_MINUTE (.env). 0 / empty = no pacing until the first 429,
then the pace learned from it. One pacer for the whole run, shared by the worker threads.
"""

from __future__ import annotations

import os
import threading
import time
from collections import deque
from typing import Any, Callable, TypeVar

from src.llm_errors import error_chain

T = TypeVar("T")

WINDOW_SECONDS = 60.0
LEARNED_SHARE = 0.8                  # after a 429: pace = 80% of the calls seen in the last minute
MIN_WAIT, MAX_WAIT = 5.0, 60.0       # wait after a 429 when the server gives no Retry-After


def _env_number(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, "") or default)
    except ValueError:
        return default


def is_rate_limited(exc: BaseException) -> bool:
    """429 / "rate limit" / "QPM" anywhere in the exception chain."""

    for error in error_chain(exc):
        if getattr(error, "status_code", None) == 429:
            return True
        text = f"{type(error).__name__} {error}".lower()
        if "429" in text or "rate limit" in text or "ratelimit" in text or "qpm" in text:
            return True
    return False


def retry_after_seconds(exc: BaseException) -> float | None:
    """The server's Retry-After header (seconds), if any."""

    for error in error_chain(exc):
        headers = getattr(getattr(error, "response", None), "headers", None) or {}
        value = headers.get("retry-after") or headers.get("Retry-After")
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            continue
    return None


class QpmPacer:
    """Sliding-window pacer, thread-safe. ``qpm`` None = not known yet (no waiting)."""

    def __init__(self, qpm: float | None = None, clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self.qpm = qpm if qpm and qpm > 0 else None
        self._clock, self._sleep = clock, sleep
        self._lock = threading.Lock()
        self._starts: deque[float] = deque()          # start time of each call in the last minute
        self._next_free = 0.0                         # earliest start of the next call (spacing)

    def _forget_old(self, now: float) -> None:
        while self._starts and now - self._starts[0] >= WINDOW_SECONDS:
            self._starts.popleft()

    def sleep_needed(self, now: float) -> float:
        """Seconds to wait before the next call may start (0 = go)."""

        self._forget_old(now)
        if not self.qpm:
            return 0.0
        wait = max(0.0, self._next_free - now)                          # spacing 60 / qpm
        if len(self._starts) >= self.qpm:                               # window full
            wait = max(wait, self._starts[0] + WINDOW_SECONDS - now)
        return wait

    def acquire(self) -> None:
        """Block until a call may start, then book it."""

        while True:
            with self._lock:
                now = self._clock()
                wait = self.sleep_needed(now)
                if wait <= 0:
                    self._starts.append(now)
                    if self.qpm:
                        self._next_free = now + WINDOW_SECONDS / self.qpm
                    return
            self._sleep(min(wait, MAX_WAIT))

    def rate_limited(self, retry_after: float | None) -> float:
        """Learn a lower pace from a 429 and return how long to wait before calling again."""

        with self._lock:
            now = self._clock()
            self._forget_old(now)
            # 80% of what got through: the calls of the last minute, or the current pace if higher
            # (a 2nd 429 right after a full wait lowers the pace by 20% again, not to 1)
            seen = max(len(self._starts), self.qpm or 0)
            self.qpm = max(1.0, int(seen * LEARNED_SHARE))
            if retry_after is not None:
                wait = retry_after
            elif self._starts:
                wait = self._starts[0] + WINDOW_SECONDS - now
            else:
                wait = MIN_WAIT
            wait = min(max(wait, MIN_WAIT), MAX_WAIT)
            self._next_free = max(self._next_free, now + wait)
            return wait


PACER = QpmPacer(_env_number("LLM_REQUESTS_PER_MINUTE", 0))


def call_llm(fn: Callable[[], T], pacer: QpmPacer | None = None, retries: int | None = None) -> T:
    """Run one LLM call under the pacer; on 429 wait (computed) and try again.

    Other errors are raised at once, as before. After ``retries`` 429s in a row the last
    error is raised (the step then reports it like any other failure).
    """

    pacer = pacer or PACER
    retries = int(_env_number("LLM_RATE_LIMIT_RETRIES", 8)) if retries is None else retries
    for attempt in range(retries + 1):
        pacer.acquire()
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — only 429 is retried
            if not is_rate_limited(exc) or attempt == retries:
                raise
            pacer._sleep(pacer.rate_limited(retry_after_seconds(exc)))
    raise RuntimeError("unreachable")
