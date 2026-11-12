"""[05/11/2026] Tên viết tắt ngân hàng (sheet bank_abbr) cho bảng dư nợ tại TCTD (mục 4a).

CIC writes the full name, often with the branch: "NGÂN HÀNG TMCP NGOẠI THƯƠNG VIỆT NAM - CN HÀ NỘI".
``short_name`` turns it into "Vietcombank", so all branches of one bank are one column.
The table is src/templates/bang-viet-tat-ngan-hang.txt — add a line there for a new bank.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from src.utils.common import normalize_text
from src.utils.paths import PROJECT_ROOT

BANK_FILE = PROJECT_ROOT / "src" / "templates" / "bang-viet-tat-ngan-hang.txt"
GENERIC = {"ngan hang", "ngan hang tmcp", "ngan hang thuong mai co phan", "ngan hang thuong mai tnhh mtv",
           "ngan hang tnhh mtv"}


def _full_variants(full: str) -> list[str]:
    """'Ngân hàng TMCP Bản Việt (tên cũ: Viet Capital Bank)' → both names, normalized; TMCP spelled
    out too ("Ngân hàng Thương mại cổ phần …" is common on CIC)."""

    names = [re.sub(r"\(.*?\)", "", full)]
    # [13/11] "(tên khác: …)" — cùng ngân hàng, thứ tự từ khác (VPBank: "Việt Nam Thịnh Vượng" / "Thịnh Vượng Việt Nam")
    names += [f"Ngân hàng {m.strip()}" for m in re.findall(r"tên (?:cũ|khác):\s*([^)]+)", full)]
    out = []
    for name in names:
        key = normalize_text(name)
        out += [key, key.replace(" tmcp ", " thuong mai co phan ")]
    return [k for k in out if k and k not in GENERIC]


@lru_cache(maxsize=1)
def banks() -> tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...]:
    """(display name, full-name keys, short-name keys) per bank."""

    rows = []
    if not BANK_FILE.is_file():
        return ()
    for line in BANK_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#") or ":" not in line:
            continue
        short, full = line.split(":", 1)
        display = short.split("(")[0].split("/")[0].strip()          # "MB/MBBank(MBB)" → "MB"
        shorts = [s for s in re.split(r"[()/]", short) if s.strip()]
        rows.append((display, tuple(_full_variants(full)), tuple(normalize_text(s) for s in shorts)))
    return tuple(rows)


def short_name(name: Any) -> str:
    """The bank's short name, or the name as written when it is not in the table."""

    text = str(name or "").strip()
    key = f" {normalize_text(text)} "
    for short, full in ((" nh ", " ngan hang "), (" vn ", " viet nam "), (" tm cp ", " tmcp ")):
        key = key.replace(short, full)                  # "NH TMCP Kỹ thương VN"
    if not key.strip():
        return text
    # 1) full name inside the CIC text — longest first ("TMCP Sài Gòn" ⊂ "TMCP Sài Gòn Thương Tín")
    best = max(((len(full), display) for display, fulls, _ in banks() for full in fulls if f" {full} " in key),
               default=None)
    if best:
        return best[1]
    # 2) a short name or code written as a word ("Vietcombank - CN Hà Nội", "VCB")
    for display, _, shorts in banks():
        if any(f" {s} " in key for s in shorts):
            return display
    return text
