"""LLM extraction for Phụ lục 01 mục 3 — số liệu báo cáo tài chính.

Runs on BCTC năm / giữa niên độ / thuyết minh. One JSON per document with one
entry per printed column (năm nay, năm trước, kỳ giữa niên độ). Ratios are NOT
asked of the LLM: src/agents/calculator/financial_metrics.py computes them.
"""

from typing import Any

from src.agents.extraction.structured_extraction import (
    build_extraction_chain,
    resolve_money_multiplier,
    run_extraction,
    scale_amount,
)
from src.prompts import system_prompt

REQUIRED_TOP_LEVEL_KEYS = {"periods"}

AMOUNT_FIELDS = (
    "total_assets", "current_assets", "non_current_assets", "total_liabilities",
    "current_liabilities", "long_term_liabilities", "equity", "total_capital",
    "net_revenue", "cogs", "gross_profit", "financial_income", "financial_expenses",
    "selling_expenses", "admin_expenses", "operating_profit", "other_profit",
    "profit_before_tax", "profit_after_tax", "depreciation",
    # [BRD 16/10] TT133 components, retained earnings, other income, interest expense
    "cash", "short_term_investments", "receivables", "inventory", "other_assets",
    "retained_earnings", "other_income", "interest_expense",
)


def normalize_amounts(result: dict[str, Any]) -> dict[str, Any]:
    """Convert every period's amounts to đồng with the document's source_unit."""

    multiplier = resolve_money_multiplier(result.get("source_unit"))
    periods = [p for p in result.get("periods") or [] if isinstance(p, dict)]
    for period in periods:
        for field in AMOUNT_FIELDS:
            period[field] = scale_amount(period.get(field), multiplier)
    result["periods"] = periods
    result["source_unit"] = "dong"
    return result


def build_financial_extraction_chain(llm: Any):
    """Build the JSON-output extraction chain for the financial statements."""

    return build_extraction_chain(system_prompt("financial_extraction"), llm)


def extract_financial_structured_data(
    chain: Any,
    filename: str,
    content: str,
    path: str = "",
) -> tuple[dict[str, Any] | None, str]:
    """Run the extraction chain and validate its shape. Never raises."""

    return run_extraction(
        chain,
        filename,
        content,
        REQUIRED_TOP_LEVEL_KEYS,
        "No financial_extraction_llm configured.",
        normalize_amounts,
    )
