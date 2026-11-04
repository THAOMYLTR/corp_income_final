"""[05/11] Token counter used by the notebook (tổng token / chi phí của một lần chạy)."""

import unittest
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace as NS

from src.utils.token_usage import TokenUsage


def response(model, tokens_in, tokens_out, new_client=True):
    if new_client:
        message = NS(usage_metadata={"input_tokens": tokens_in, "output_tokens": tokens_out},
                     response_metadata={"model_name": model})
        return NS(llm_output={}, generations=[[NS(message=message)]])
    return NS(llm_output={"model_name": model,
                          "token_usage": {"prompt_tokens": tokens_in, "completion_tokens": tokens_out}},
              generations=[[NS(message=NS(usage_metadata=None, response_metadata={}))]])


class TokenUsageTest(unittest.TestCase):
    def test_counts_per_model_across_threads_and_prices(self):
        usage = TokenUsage()
        calls = [response("claude-sonnet", 1000, 200)] * 50 + [response("gpt-4o", 3000, 500, new_client=False)] * 10
        with ThreadPoolExecutor(8) as pool:
            list(pool.map(usage.on_llm_end, calls))
        self.assertEqual(usage.by_model["claude-sonnet"], {"calls": 50, "input": 50_000, "output": 10_000})
        self.assertEqual(usage.totals(), {"calls": 60, "input": 80_000, "output": 15_000})
        cost = usage.cost({"claude-sonnet": (3.0, 15.0), "*": (2.5, 10.0)})
        self.assertAlmostEqual(cost, 0.05 * 3 + 0.01 * 15 + 0.03 * 2.5 + 0.005 * 10)
        self.assertIsNone(usage.cost({"claude-sonnet": (3.0, 15.0)}))      # gpt-4o has no price
        self.assertIn("TỔNG | 60 | 80,000 | 15,000 | 95,000", usage.report())
        usage.reset()
        self.assertEqual(usage.totals(), {"calls": 0, "input": 0, "output": 0})


if __name__ == "__main__":
    unittest.main()
