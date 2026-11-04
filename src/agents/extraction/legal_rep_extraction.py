"""LLM extraction for BRD mục 3 — người đại diện pháp luật.

Current and previous legal representatives with appointment dates, and from the
site visit / RBO interview the people met and the actual operator. Leadership
capability is deliberately not assessed (removed per the BRD dependency note).

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


REQUIRED_TOP_LEVEL_KEYS = {"legal_representatives"}

_AMOUNT_FIELDS: dict[str | None, tuple[str, ...]] = {}


def normalize_amounts(result: dict[str, Any]) -> dict[str, Any]:
    """Convert every amount to đồng using the result's source_unit, in place."""

    scale_listed_amounts(result, _AMOUNT_FIELDS)
    return result


def build_legal_rep_extraction_chain(llm: Any):
    """Build the JSON-output extraction chain for BRD mục 3 — người đại diện pháp luật."""

    return build_extraction_chain(system_prompt("legal_rep_extraction"), llm)


def extract_legal_rep_structured_data(
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
        "No legal_rep_extraction_llm configured.",
        normalize_amounts,
    )
