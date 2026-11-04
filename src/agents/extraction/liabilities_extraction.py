"""LLM extraction for BRD mục 4 — nợ thuế, BHXH, phạt hành chính, tranh chấp.

Tax and social-insurance debts, clearance confirmations, administrative
penalties, enforcement, inspections, disputes and their remediation status, plus
environment / fire-safety risks seen on site.

Amounts are read exactly as printed plus ``source_unit`` and scaled to đồng in
``normalize_amounts`` — the only place a figure is converted.
"""

from typing import Any

from src.agents.extraction.structured_extraction import (
    build_extraction_chain,
    run_extraction,
    scale_listed_amounts,
)
from src.prompts import system_prompt


REQUIRED_TOP_LEVEL_KEYS = {"tax_debts", "social_insurance_debts", "administrative_penalties", "disputes"}

_AMOUNT_FIELDS: dict[str | None, tuple[str, ...]] = {
    "tax_debts": ("amount",),
    "social_insurance_debts": ("amount",),
    "administrative_penalties": ("amount",),
    "enforcement_actions": ("amount",),
    "disputes": ("claim_amount",),
}


def normalize_amounts(result: dict[str, Any]) -> dict[str, Any]:
    """Convert every amount to đồng using the result's source_unit, in place."""

    scale_listed_amounts(result, _AMOUNT_FIELDS)
    return result


def build_liabilities_extraction_chain(llm: Any):
    """Build the JSON-output extraction chain for BRD mục 4 — nợ thuế, BHXH, phạt hành chính, tranh chấp."""

    return build_extraction_chain(system_prompt("liabilities_extraction"), llm)


def extract_liabilities_structured_data(
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
        "No liabilities_extraction_llm configured.",
        normalize_amounts,
    )
