"""Fill the template placeholders that code cannot: one LLM call per report.

Code fills every fact and figure first (appendix_context). The placeholders
still empty — "Nhận xét…", business activity, CIC, the conclusion — are sent
to the LLM together with the guidance (src/templates/corp-income-guidance.md),
the writer rules (config/prompts/report_writer.md), the values code already
filled, the BRD checks, the financial ratios and excerpts of the documents.
The LLM answers ``{placeholder: text}``; code puts the text in place, so the
template layout and every code-filled number stay exactly as they are.

Never raises: without an LLM, or when the call fails, the cells read
"Chưa có thông tin" and the reason is returned for the run log.
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.llm_errors import explain_llm_error
from src.prompts import system_prompt
from src.utils.paths import PROJECT_ROOT

NO_INFO = "Chưa có thông tin trong hồ sơ"
MAX_EVIDENCE_CHARS = 120_000


GUIDANCE_PATH = PROJECT_ROOT / "src" / "templates" / "corp-income-guidance.md"
# [BRD 16/10] Per-cell writing frame ("## TenO" sections), editable next to the template.
CELL_SPECS_PATH = PROJECT_ROOT / "src" / "templates" / "corp-income-cell-specs.md"
_NUMBER = re.compile(r"-?\d[\d.,]*%?")


def load_cell_specs() -> dict[str, str]:
    """{cell name: frame} from corp-income-cell-specs.md; {} when the file is absent."""

    if not CELL_SPECS_PATH.is_file():
        return {}
    text = re.sub(r"<!--.*?-->", "", CELL_SPECS_PATH.read_text(encoding="utf-8"), flags=re.S)
    specs: dict[str, str] = {}
    for block in re.split(r"^## ", text, flags=re.M)[1:]:
        name, _, body = block.partition("\n")
        specs[name.strip()] = body.strip()
    return specs


def keeps_every_number(draft: str, rewritten: str) -> list[str]:
    """[BRD 16/10] Numbers of the code draft missing from the LLM rewrite ([] = safe)."""

    def numbers(text: str) -> list[str]:
        return [n.rstrip(".,") for n in _NUMBER.findall(text)]   # "0,94." → "0,94"

    have = set(numbers(rewritten))
    return [n for n in dict.fromkeys(numbers(draft)) if n not in have]


def load_guidance() -> str:
    """The business guidance, edited by the user next to the report template."""

    if not GUIDANCE_PATH.is_file():
        raise FileNotFoundError(f"guidance not found: {GUIDANCE_PATH}")
    return GUIDANCE_PATH.read_text(encoding="utf-8").strip()


def build_writer_chain(llm: Any):
    system = "GUIDANCE:\n" + load_guidance() + "\n\n" + system_prompt("report_writer")
    prompt = ChatPromptTemplate.from_messages(
        [SystemMessage(content=system), ("human", system_prompt("report_writer_user"))]
    )
    return prompt | llm | JsonOutputParser()


def fit_payload(evidence: dict[str, Any], limit: int = MAX_EVIDENCE_CHARS) -> str:
    """JSON of the evidence within ``limit`` characters.

    [BRD 16/10] Shrinks the document excerpts first (halving each round) instead of cutting
    the JSON at the end, so the field report and contracts are never dropped whole.
    """

    payload = json.dumps(evidence, ensure_ascii=False, default=str)
    excerpts = evidence.get("trich_doan_ho_so") or []
    size = max((len(e.get("noi_dung", "")) for e in excerpts), default=0)
    while len(payload) > limit and size > 300:
        size //= 2
        evidence = {**evidence, "trich_doan_ho_so": [{**e, "noi_dung": e.get("noi_dung", "")[:size]}
                                                     for e in excerpts]}
        payload = json.dumps(evidence, ensure_ascii=False, default=str)
    return payload if len(payload) <= limit else payload[:limit] + "…(cắt bớt)"


# --------------------------------------------------------------------------- #
# [BRD 16/10] Step 1 — the credit approver's overall view
# --------------------------------------------------------------------------- #
DECISIONS = ("Sử dụng", "Sử dụng có điều kiện", "Không sử dụng")


def build_assessment_chain(llm: Any):
    system = "GUIDANCE:\n" + load_guidance() + "\n\n" + system_prompt("credit_assessment")
    prompt = ChatPromptTemplate.from_messages(
        [SystemMessage(content=system), ("human", system_prompt("credit_assessment_user"))]
    )
    return prompt | llm | JsonOutputParser()


def assess_credit(llm: Any, evidence: dict[str, Any], corp_group: str) -> tuple[dict[str, Any], str]:
    """One call that decides the "so what" before any cell is written.

    The decision cannot contradict the code's corp group: Bad corp is always
    "Không sử dụng", Normal corp is never plain "Sử dụng" (at most "có điều kiện").
    """

    if llm is None:
        return {}, ""
    try:
        answer = build_assessment_chain(llm).invoke({"evidence": fit_payload(evidence)})
    except Exception as exc:  # noqa: BLE001
        return {}, f"Credit assessment failed: {explain_llm_error(exc)}"
    if not isinstance(answer, dict) or not answer:
        return {}, "Credit assessment returned no JSON."
    decision = answer.get("quyet_dinh")
    forced = ""
    if corp_group == "Bad corp" and decision != "Không sử dụng":
        forced = "Không sử dụng"
    elif corp_group == "Normal corp" and decision == "Sử dụng":
        forced = "Sử dụng có điều kiện"
    elif decision not in DECISIONS:
        forced = "Sử dụng có điều kiện" if corp_group != "Bad corp" else "Không sử dụng"
    if forced:
        answer["quyet_dinh_llm"] = decision
        answer["quyet_dinh"] = forced
        return answer, f"Credit decision set to '{forced}' by the corp group ({corp_group}); LLM said '{decision}'."
    return answer, ""


def describe_fields(template: str, names: list[str]) -> str:
    """Each name with the template line it sits on, so the LLM knows its meaning,
    and [BRD 16/10] its writing frame from corp-income-cell-specs.md ("cau_truc")."""

    specs = load_cell_specs()
    lines = template.splitlines()
    out = []
    for name in names:
        where = next((line.strip() for line in lines if "{{" + name + "}}" in line), "")
        in_table = where.startswith("|") or "<td>" in where
        if len(where) > 240:
            start = max(0, where.find("{{" + name + "}}") - 120)
            where = "…" + where[start:start + 240] + "…"
        # Nearest heading above, for context.
        heading = ""
        for line in lines[: next((i for i, l in enumerate(lines) if "{{" + name + "}}" in l), 0)]:
            if line.startswith("#"):
                heading = line.strip("# ").strip()
        field = {"o": name, "phan": heading, "dong_mau": where, "trong_bang": in_table}
        if name in specs:
            field["cau_truc"] = specs[name]
        out.append(json.dumps(field, ensure_ascii=False))
    return "\n".join(out)


def write_placeholders(
    llm: Any,
    template: str,
    names: list[str],
    evidence: dict[str, Any],
) -> tuple[dict[str, str], str]:
    """``({name: text}, error)``. Missing names come back as NO_INFO."""

    if not names:
        return {}, ""
    fallback = {name: NO_INFO for name in names}
    if llm is None:
        return fallback, "No report_writer_llm configured — narrative cells left as 'Chưa có thông tin'."
    payload = fit_payload(evidence)
    try:
        answer = build_writer_chain(llm).invoke(
            {"fields": describe_fields(template, names), "evidence": payload}
        )
    except Exception as exc:  # noqa: BLE001 — reported, never raised
        return fallback, f"Report writer failed: {explain_llm_error(exc)}"
    if not isinstance(answer, dict):
        return fallback, f"Report writer returned {type(answer).__name__}, not a JSON object."
    filled = {}
    for name in names:
        value = answer.get(name)
        filled[name] = str(value).strip() if value not in (None, "") else NO_INFO
    missing = [n for n in names if answer.get(n) in (None, "")]
    return filled, (f"Report writer left {len(missing)} cell(s) empty: {', '.join(missing)}" if missing else "")
