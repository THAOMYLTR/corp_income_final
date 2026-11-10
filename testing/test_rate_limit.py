"""[10/11] QPM pacing and 429 retries (src/utils/rate_limit.py), with a fake clock — no real waiting."""

import unittest

from src.utils.rate_limit import QpmPacer, call_llm, is_rate_limited, retry_after_seconds


class FakeClock:
    def __init__(self):
        self.now, self.slept = 0.0, []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


class RateLimitError(Exception):
    status_code = 429

    def __init__(self, retry_after=None):
        super().__init__("Error code: 429 - Queries-per-minute (QPM) rate limit exceeded")
        self.response = type("R", (), {"headers": {"retry-after": str(retry_after)} if retry_after else {}})()


class PacerTest(unittest.TestCase):
    def test_calls_are_spread_to_stay_under_qpm(self):
        clock = FakeClock()
        pacer = QpmPacer(30, clock=clock, sleep=clock.sleep)        # 30 / phút → 2 s apart
        for _ in range(61):
            pacer.acquire()
        self.assertAlmostEqual(clock.now, 120.0)                     # 61 calls ≈ 2 minutes, never > 30 / 60 s
        starts = list(pacer._starts)
        self.assertLessEqual(len([t for t in starts if clock.now - t < 60]), 30)

    def test_429_waits_learns_a_lower_pace_and_retries(self):
        clock = FakeClock()
        pacer = QpmPacer(None, clock=clock, sleep=clock.sleep)       # no limit known yet
        for _ in range(20):                                          # 20 calls go at once
            pacer.acquire()
        calls = {"n": 0}

        def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise RateLimitError()
            return "ok"

        self.assertEqual(call_llm(flaky, pacer=pacer, retries=5), "ok")
        self.assertEqual(calls["n"], 3)
        self.assertEqual(pacer.qpm, 12)                              # 21 calls → 16, then 16 → 12 (−20% each 429)
        self.assertTrue(all(5 <= s <= 60 for s in clock.slept))

    def test_retry_after_header_and_other_errors(self):
        self.assertEqual(retry_after_seconds(RateLimitError(12)), 12.0)
        self.assertTrue(is_rate_limited(RuntimeError("Queries-per-minute (QPM) rate limit exceeded")))
        self.assertFalse(is_rate_limited(ValueError("bad JSON")))
        clock = FakeClock()
        pacer = QpmPacer(None, clock=clock, sleep=clock.sleep)
        with self.assertRaises(ValueError):                          # not a 429 → raised at once
            call_llm(lambda: (_ for _ in ()).throw(ValueError("bad JSON")), pacer=pacer, retries=5)
        with self.assertRaises(RateLimitError):                      # 429 every time → gives up after retries
            call_llm(lambda: (_ for _ in ()).throw(RateLimitError(1)), pacer=pacer, retries=2)


if __name__ == "__main__":
    unittest.main()
