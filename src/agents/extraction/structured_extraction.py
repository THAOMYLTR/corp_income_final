"""Shared plumbing for the LLM passes that turn a scanned document into JSON."""

from typing import Any

from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.llm_errors import explain_llm_error
from src.prompts import system_prompt as prompt_file
from src.utils.common import normalize_text


TRIEU_VND = 10 ** 6


def resolve_money_multiplier(source_unit: Any) -> int:
    """Turn a unit a form printed into the multiplier that takes it to đồng."""

    tokens = normalize_text(str(source_unit or "")).split()
    if "ty" in tokens:
        return 10 ** 9
    if "trieu" in tokens:
        return 10 ** 6
    if "nghin" in tokens:
        return 10 ** 3
    return 1


def to_number(value: Any) -> Any:
    """[BRD 16/10] A figure the LLM returned as text ("1.234.567", "(1.234)", "12,5") → number.

    Vietnamese print: "." groups thousands, "," is the decimal mark; brackets mean
    negative. Anything that is not a number is returned unchanged.
    """

    if not isinstance(value, str):
        return value
    text = value.strip().replace(" ", "").replace("đ", "").replace("VND", "")
    negative = text.startswith("(") and text.endswith(")") or text.startswith("-")
    text = text.strip("()-")
    if not text or not all(ch.isdigit() or ch in ".," for ch in text):
        return value
    if "." in text and "," in text:                      # both: the last one is decimal
        dec = "," if text.rfind(",") > text.rfind(".") else "."
        text = text.replace("." if dec == "," else ",", "").replace(dec, ".")
    elif text.count(".") > 1 or (text.count(".") == 1 and len(text.split(".")[1]) == 3):
        text = text.replace(".", "")                     # 1.234.567 / 1.234 → thousands
    elif text.count(",") > 1 or (text.count(",") == 1 and len(text.split(",")[1]) == 3):
        text = text.replace(",", "")
    else:
        text = text.replace(",", ".")                    # 12,5 → 12.5
    try:
        number = float(text)
    except ValueError:
        return value
    number = -number if negative else number
    return int(number) if number.is_integer() else number


def scale_amount(value: Any, multiplier: int) -> Any:
    """Multiply a printed figure into đồng, leaving anything else untouched."""

    value = to_number(value)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return value
    return round(value * multiplier, 2)


def scale_declared_blocks(
    result: dict[str, Any],
    amount_fields: dict[str, tuple[str, ...]],
) -> dict[str, int]:
    """Scale each block's flat money fields by that block's own source_unit."""

    multipliers: dict[str, int] = {}
    for block_name, fields in amount_fields.items():
        block = result.get(block_name)
        if not isinstance(block, dict):
            continue
        multiplier = resolve_money_multiplier(block.get("source_unit"))
        multipliers[block_name] = multiplier
        for field in fields:
            block[field] = scale_amount(block.get(field), multiplier)
    return multipliers


def build_extraction_chain(system_prompt: str, llm: Any):
    """Wire a system prompt to the LLM with a JSON-parsing tail."""

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_prompt),
            ("human", prompt_file("extraction_user")),
        ]
    )
    return prompt | llm | JsonOutputParser()


def _explain(exc: Exception) -> str:
    """The failure as a sentence somebody can act on."""

    text = str(exc)
    if "max_tokens" in text and "at most" in text:
        return (
            "max_tokens exceeds the model's ceiling — the request was refused "
            "before the model ran. Lower LLM_MAX_TOKENS (or the pass's own "
            "max_tokens_env, e.g. LLM_LEDGER_MAX_TOKENS) in .env; run "
            "testing/probe_max_tokens.py to read the model's real ceiling. "
            f"API said: {text}"
        )[:500]
    return explain_llm_error(exc)


def run_extraction(
    chain: Any,
    filename: str,
    content: str,
    required_keys: set[str],
    missing_llm_message: str,
    normalize: Any = None,
) -> tuple[dict[str, Any] | None, str]:
    """Invoke an extraction chain, validate its shape, and normalise the result."""

    if chain is None:
        return None, missing_llm_message
    try:
        result = chain.invoke({"filename": filename, "content": content})
    except Exception as exc:
        return None, _explain(exc)

    if not isinstance(result, dict):
        return None, f"Extraction returned non-dict result: {type(result).__name__}"
    missing = required_keys - result.keys()
    if missing:
        return None, f"Extraction result missing keys: {sorted(missing)}"
    return (normalize(result) if normalize else result), ""


def scale_listed_amounts(
    result: dict[str, Any],
    amount_fields: dict[str | None, tuple[str, ...]],
) -> int:
    """Scale money fields by the result's single top-level ``source_unit``.

    The corporate passes print one unit per document, and their figures sit
    either at the top level (``None`` key, e.g. charter_capital) or in lists of
    rows (tax_debts, members…). Converted here and only here, then the unit is
    reset to "dong" so a second pass over the same result cannot scale twice.
    """

    multiplier = resolve_money_multiplier(result.get("source_unit"))
    for list_key, fields in amount_fields.items():
        rows = [result] if list_key is None else result.get(list_key) or []
        for row in rows:
            if isinstance(row, dict):
                for field in fields:
                    row[field] = scale_amount(row.get(field), multiplier)
    if "source_unit" in result:
        result["source_unit"] = "dong"
    return multiplier
