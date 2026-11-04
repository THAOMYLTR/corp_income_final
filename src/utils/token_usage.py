"""[05/11] Đếm token của mọi lần gọi LLM trong một lần chạy, và quy ra tiền.

Every LLM made by ``src.config.build_llm`` reports to ``TOKEN_USAGE`` (a LangChain callback),
so the count covers all agents and the worker threads, with or without MLflow.

Notebook:
    from src.utils.token_usage import TOKEN_USAGE
    TOKEN_USAGE.reset()
    result = supervisor.process(...)
    print(TOKEN_USAGE.report(PRICES_USD_PER_1M))
"""

from __future__ import annotations

import threading
from typing import Any

try:
    from langchain_core.callbacks import BaseCallbackHandler
except ImportError:                       # offline test stubs
    BaseCallbackHandler = object          # type: ignore[assignment,misc]


class TokenUsage(BaseCallbackHandler):
    """Input / output tokens and number of calls, per model (thread-safe)."""

    def __init__(self) -> None:
        super().__init__()
        self._lock = threading.Lock()
        self.by_model: dict[str, dict[str, int]] = {}

    def reset(self) -> None:
        with self._lock:
            self.by_model = {}

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        output = getattr(response, "llm_output", None) or {}
        model = str(output.get("model_name") or output.get("model") or "")
        found_in, found_out = 0, 0
        for generations in getattr(response, "generations", None) or []:
            for generation in generations:
                message = getattr(generation, "message", None)
                usage = getattr(message, "usage_metadata", None) or {}
                found_in += int(usage.get("input_tokens") or 0)
                found_out += int(usage.get("output_tokens") or 0)
                meta = getattr(message, "response_metadata", None) or {}
                model = model or str(meta.get("model_name") or meta.get("model") or "")
        if not (found_in or found_out):                    # older clients: llm_output only
            usage = output.get("token_usage") or output.get("usage") or {}
            found_in = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
            found_out = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
        with self._lock:
            row = self.by_model.setdefault(model or "không rõ model", {"calls": 0, "input": 0, "output": 0})
            row["calls"] += 1
            row["input"] += found_in
            row["output"] += found_out

    def totals(self) -> dict[str, int]:
        with self._lock:
            rows = list(self.by_model.values())
        return {key: sum(r[key] for r in rows) for key in ("calls", "input", "output")}

    def cost(self, prices: dict[str, tuple[float, float]] | None = None) -> float | None:
        """USD with ``prices`` = {model: (USD / 1M input tokens, USD / 1M output tokens)};
        a key "*" prices every model not listed. None when a model has no price."""

        prices = prices or {}
        total = 0.0
        with self._lock:
            items = list(self.by_model.items())
        for model, row in items:
            price = prices.get(model) or prices.get("*")
            if price is None:
                return None
            total += row["input"] / 1e6 * price[0] + row["output"] / 1e6 * price[1]
        return total

    def report(self, prices: dict[str, tuple[float, float]] | None = None, usd_to_vnd: float | None = None) -> str:
        lines = ["Model | Số lần gọi | Token vào | Token ra | Tổng token"]
        with self._lock:
            items = sorted(self.by_model.items())
        for model, r in items:
            lines.append(f"{model} | {r['calls']:,} | {r['input']:,} | {r['output']:,} | {r['input'] + r['output']:,}")
        t = self.totals()
        lines.append(f"TỔNG | {t['calls']:,} | {t['input']:,} | {t['output']:,} | {t['input'] + t['output']:,}")
        usd = self.cost(prices)
        if usd is None:
            lines.append("Chi phí: chưa có đơn giá cho mọi model (điền PRICES_USD_PER_1M)")
        else:
            lines.append(f"Chi phí ước tính: {usd:,.4f} USD"
                         + (f" ≈ {usd * usd_to_vnd:,.0f} VND" if usd_to_vnd else ""))
        return "\n".join(lines)


TOKEN_USAGE = TokenUsage()
