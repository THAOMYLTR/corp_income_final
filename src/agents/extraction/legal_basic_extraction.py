"""LLM extraction for BRD mục 1 — thông tin cơ bản về pháp lý doanh nghiệp.

Runs on the GCN ĐKDN, the charter, the shareholder register, the national-register
lookup (Cổng ĐKDN / thuế), internal-system printouts and the site-visit report. Every
one of them states some of: name, MST, legal form, founding date, charter capital,
head office, legal representative, operating status, registration changes — and
the site-visit report whether the company really operates at the address. The
same JSON comes back from each, so src/agents/calculator/legal_checks.py can
compare the sources field by field (MST must match exactly).

Amounts are read exactly as printed plus ``source_unit`` and scaled to đồng in
``normalize_amounts`` — the only place a figure is converted.
"""

import re
from typing import Any

from src.agents.extraction.structured_extraction import (
    build_extraction_chain,
    run_extraction,
    scale_listed_amounts,
)
from src.prompts import system_prompt
from src.utils.common import normalize_text


REQUIRED_TOP_LEVEL_KEYS = {"company_name", "tax_code", "legal_representatives"}

_AMOUNT_FIELDS: dict[str | None, tuple[str, ...]] = {None: ("charter_capital",)}


def normalize_amounts(result: dict[str, Any]) -> dict[str, Any]:
    """Convert every amount to đồng using the result's source_unit, in place."""

    scale_listed_amounts(result, _AMOUNT_FIELDS)
    return result


# Deterministic back-up for the four GCN fields the checks lean on most. A
# scanned GCN often OCRs as "MA so doanh nghiép: 0108977425" or "ngay 07 thang
# 11 naém 2019" — readable to a regex on the accent-stripped text even when the
# LLM leaves the field empty. Only fills what the LLM left empty.
# [Sửa 20/10] nhận cả "ngày 12 tháng 05 năm 2015" lẫn "12/05/2015" (sau normalize "/" → " ").
_DATE = r"(?:ngay\s*)?(\d{1,2})\s*(?:thang\s*)?(\d{1,2})\s*(?:n\w{0,3}\s*)?((?:19|20)\d{2})"
_TAX_CODE = re.compile(r"ma\s*so\s*(?:doanh\s*nghiep|thue|dn)\s*(\d{10})(?:\s*(\d{3})\b)?")
_FIRST = re.compile(r"dang\s*ky\s*lan\s*dau\s*" + _DATE)
_CHANGE = re.compile(r"thay\s*\w{2,4}\s*lan\s*th\w{0,3}\s*(\d{1,2})\s*" + _DATE)


def _date(day: str, month: str, year: str) -> str:
    return f"{int(day):02d}/{int(month):02d}/{year}"


def fill_from_text(result: dict[str, Any], content: str) -> dict[str, Any]:
    """Fill empty tax_code / dates / change number from the OCR text itself."""

    text = normalize_text(content or "")
    filled = []
    if not result.get("tax_code"):
        match = _TAX_CODE.search(text)
        if match:
            result["tax_code"] = match.group(1) + (f"-{match.group(2)}" if match.group(2) else "")
            filled.append("tax_code")
    match = _FIRST.search(text)
    if match:
        printed = _date(*match.groups())
        current = str(result.get("establishment_date") or "")
        if not current:
            result["establishment_date"] = printed
            filled.append("establishment_date")
        elif printed[-4:] not in current:
            # [Sửa 20/10] LLM hay ghi nhầm ngày "thay đổi lần thứ N" vào ngày thành lập. Dòng
            # "Đăng ký lần đầu: ngày …" in trên giấy là căn cứ, nên số trên giấy thắng.
            result["establishment_date"] = printed
            filled.append(f"establishment_date (LLM ghi {current}, giấy ghi {printed})")
    change = _CHANGE.search(text)
    if change:
        if result.get("registration_change_number") in (None, ""):
            result["registration_change_number"] = int(change.group(1))
            filled.append("registration_change_number")
        if not result.get("latest_change_date"):
            result["latest_change_date"] = _date(*change.groups()[1:])
            filled.append("latest_change_date")
    if filled:
        notes = result.setdefault("extraction_notes", [])
        if isinstance(notes, list):
            notes.append("Điền từ văn bản OCR (quy tắc cố định): " + ", ".join(filled))
    return result


def build_legal_basic_extraction_chain(llm: Any):
    """Build the JSON-output extraction chain for BRD mục 1 — thông tin cơ bản về pháp lý doanh nghiệp."""

    return build_extraction_chain(system_prompt("legal_basic_extraction"), llm)


def extract_legal_basic_structured_data(
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
        "No legal_basic_extraction_llm configured.",
        lambda result: fill_from_text(normalize_amounts(result), content),
    )
