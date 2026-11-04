"""[BRD 16/10] LLM extraction of VAT returns (tờ khai thuế GTGT) — Nguyên tắc 2.

One row per tax period (month / quarter): revenue [34] and output VAT [35].
src/agents/calculator/financial_metrics.py sums year N for the "Cập nhật các
tháng năm N" column and compares year N-1 with the BCTC revenue.
"""

from typing import Any

from src.agents.extraction.structured_extraction import (
    build_extraction_chain,
    resolve_money_multiplier,
    run_extraction,
    scale_amount,
)
from src.prompts import system_prompt

REQUIRED_TOP_LEVEL_KEYS = {"returns"}


def normalize_amounts(result: dict[str, Any]) -> dict[str, Any]:
    multiplier = resolve_money_multiplier(result.get("source_unit"))
    rows = [r for r in result.get("returns") or [] if isinstance(r, dict)]
    for row in rows:
        for field in ("revenue", "output_vat"):
            row[field] = scale_amount(row.get(field), multiplier)
    result["returns"] = rows
    result["source_unit"] = "dong"
    return result


def build_vat_extraction_chain(llm: Any):
    return build_extraction_chain(system_prompt("vat_extraction"), llm)


def extract_vat_structured_data(chain: Any, filename: str, content: str, path: str = ""):
    return run_extraction(chain, filename, content, REQUIRED_TOP_LEVEL_KEYS,
                          "No vat_extraction_llm configured.", normalize_amounts)
