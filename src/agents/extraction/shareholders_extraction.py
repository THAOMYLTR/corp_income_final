"""LLM extraction for BRD mục 2 — cổ đông, thành viên góp vốn.

Members with their stake, capital and acquisition date and method, transfers,
relationships between owners, and — from the site visit / RBO — notes on who the
real owner is. Ownership percentages are read as printed, never derived by the
model; legal_checks.py derives them from capital ÷ charter only when absent.

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


REQUIRED_TOP_LEVEL_KEYS = {"members"}

_AMOUNT_FIELDS: dict[str | None, tuple[str, ...]] = {None: ("charter_capital",), "members": ("capital_amount",), "transfers": ("capital_amount",)}


def normalize_amounts(result: dict[str, Any]) -> dict[str, Any]:
    """Convert every amount to đồng using the result's source_unit, in place."""

    scale_listed_amounts(result, _AMOUNT_FIELDS)
    return result


def build_shareholders_extraction_chain(llm: Any):
    """Build the JSON-output extraction chain for BRD mục 2 — cổ đông, thành viên góp vốn."""

    return build_extraction_chain(system_prompt("shareholders_extraction"), llm)


def extract_shareholders_structured_data(
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
        "No shareholders_extraction_llm configured.",
        normalize_amounts,
    )
