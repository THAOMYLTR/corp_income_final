"""[12/11] Chạy nhiều case một lần, lần lượt từng case, mỗi case một thư mục kết quả.

Notebook (cell "Chạy nhiều case"):

    from src.utils.batch import run_cases
    summary = run_cases(supervisor, ["case_1", "case_2", "case_3"], samples_dir=PROJECT_ROOT / "samples",
                        output_dir=OUTPUT_DIR, agent=AGENT, loan_program=LOAN_PROGRAM)

- Cases run ONE AFTER ANOTHER (not at the same time): each case already reads its files and calls
  the LLM in parallel inside (FILE_WORKERS, LLM_WORKERS); several cases at once would multiply the
  memory and the LLM calls per minute (429). The QPM pacer (rate_limit.py) is shared by all cases.
- One case failing does not stop the others: the error is written to its row of the summary.
- ``per_case`` = {case_id: {...}} overrides the shared settings for one case, e.g.
  {"case_3": {"borrower_names": ["Nguyễn Văn A"], "annual_lt_principal": 5e9}}.
- ``save_run`` writes the same files as the single-case cell (final_response_<case_id>.md / .pdf,
  corp_income.json / .xlsx, *_extraction.json, ocr/, result.json).
"""

from __future__ import annotations

import json
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

# result key → file name, and the per-document extraction files (key in each classification).
OWN_FILES = ("document_classifications", "corp_income")
EXTRACTIONS = {
    "legal_basic_extraction": "is_legal_basic", "shareholders_extraction": "is_shareholders",
    "legal_rep_extraction": "is_legal_rep", "liabilities_extraction": "is_liabilities",
    "financial_extraction": "is_financial", "vat_extraction": "is_vat", "cic_extraction": "is_cic",
    "plan_extraction": "is_plan", "business_model_extraction": "is_business_model",
}


def _write_json(path: Path, content: Any) -> None:
    path.write_text(json.dumps(content, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def save_run(result: dict[str, Any], run_dir: Path, case_id: str = "") -> Path:
    """Write every output file of one case into ``run_dir``; returns ``run_dir``.

    [12/11] ``case_id`` goes into the report file names: final_response_<case_id>.pdf / .md.
    """

    from src.utils.report.excel_export import write_excel
    from src.utils.report.visualization.report_html import embed_diagrams

    run_dir.mkdir(parents=True, exist_ok=True)
    report = f"final_response_{case_id}" if case_id else "final_response"
    (run_dir / f"{report}.md").write_text(embed_diagrams(result.get("response") or ""), encoding="utf-8")
    docs = result.get("document_classifications") or []
    for key in OWN_FILES:
        _write_json(run_dir / f"{key}.json", result.get(key))
    for key, flag in EXTRACTIONS.items():
        _write_json(run_dir / f"{key}.json", {d["filename"]: d.get(key) for d in docs if d.get(flag)})
    (run_dir / "ocr").mkdir(exist_ok=True)
    for filename, text in (result.get("ocr_text") or {}).items():
        (run_dir / "ocr" / f"{filename}.txt").write_text(text, encoding="utf-8")
    if result.get("corp_income"):
        try:                               # a workbook problem must not lose the other files
            write_excel(result["corp_income"], run_dir / "corp_income.xlsx")
        except Exception as exc:  # noqa: BLE001
            print(f"  Bỏ qua corp_income.xlsx ({type(exc).__name__}: {exc})")
    slim = {k: v for k, v in result.items() if k not in (*OWN_FILES, "ocr_text")}
    slim["document_classifications"] = [{k: v for k, v in d.items() if k not in EXTRACTIONS} for d in docs]
    _write_json(run_dir / "result.json", slim)
    try:                                   # PDF needs WeasyPrint + Pango/Cairo; .md / .xlsx are saved anyway
        from weasyprint import HTML
        from src.utils.report.visualization.report_html import build_report_html

        HTML(string=build_report_html(result.get("response") or "")).write_pdf(str(run_dir / f"{report}.pdf"))
    except (ImportError, OSError) as exc:
        print(f"  Bỏ qua PDF ({type(exc).__name__}: {exc})")
    return run_dir


def failed_extractions(result: dict[str, Any]) -> list[str]:
    """[12/11] "file (lượt): lý do" for every extraction pass that should have run and gave nothing —
    same check as the WARNING of the single-case cell (a 429 that outlasted the retries lands here)."""

    from src.agents.supervisor import EXTRACTION_PASSES

    out = []
    for doc in result.get("document_classifications") or []:
        if doc.get("extraction_error"):
            out.append(f"{doc.get('filename')} (đọc file): {doc['extraction_error']}")
        for p in EXTRACTION_PASSES:
            if doc.get(p.flag_attr) and not doc.get(p.result_attr):
                out.append(f"{doc.get('filename')} ({p.label}): {doc.get(p.error_attr) or 'không rõ lý do'}")
    return out


def run_cases(supervisor: Any, case_ids: list[str], samples_dir: Path, output_dir: Path,
              per_case: dict[str, dict[str, Any]] | None = None, **shared: Any) -> list[dict[str, Any]]:
    """Run ``supervisor.process`` for each case folder ``samples_dir / case_id`` and save it.

    ``shared`` = the keyword arguments of ``supervisor.process`` common to every case (agent,
    loan_program, loan_date, borrower_names, internal_data, …). Returns one summary row per case.
    """

    summary = []
    for number, case_id in enumerate(case_ids, start=1):
        started = time.time()
        print(f"[{number}/{len(case_ids)}] {case_id} …")
        row: dict[str, Any] = {"case": case_id}
        try:
            settings = {**shared, **(per_case or {}).get(case_id, {})}
            inputs = settings.pop("input_paths", None) or [str(Path(samples_dir) / case_id)]
            result = supervisor.process(inputs, **settings)
            run_dir = save_run(result, Path(output_dir) / f"{case_id}_{datetime.now():%Y%m%d_%H%M%S}", case_id)
            group = ((result.get("corp_income") or {}).get("corp_group") or {}).get("group", "")
            failed = failed_extractions(result)
            row.update({"status": "OK" if not failed else "THIẾU TRÍCH XUẤT",
                        "files": len(result.get("document_classifications") or []),
                        "extraction_errors": len(failed), "failed": "; ".join(failed),
                        "corp_group": group, "output": str(run_dir)})
        except Exception as exc:  # noqa: BLE001 — one case must not stop the batch
            row.update({"status": "LỖI", "error": f"{type(exc).__name__}: {exc}"})
            traceback.print_exc()
        row["minutes"] = round((time.time() - started) / 60, 1)
        print(f"    → {row['status']} ({row['minutes']} phút)")
        summary.append(row)
    _write_json(Path(output_dir) / f"batch_{datetime.now():%Y%m%d_%H%M%S}.json", summary)
    return summary
