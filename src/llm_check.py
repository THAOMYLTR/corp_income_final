"""One cell that says whether the models can be called, before the real run.

    from src.llm_check import check_llm_setup
    check_llm_setup(config)        # raises if a model cannot be reached

Prints where the settings come from (masked), then makes one tiny call per
distinct model. A failure stops "Run all" here with the root cause and a hint,
instead of 8 identical "Connection error." lines after a few minutes of OCR.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from src.config import llm_provider
from src.llm_errors import explain_llm_error

_SHOWN = (
    "LLM_PROVIDER", "MODEL_DOCUMENT", "MODEL_ECONOMY", "MODEL_PREMIUM",
    "OPENAI_API_KEY", "OPENAI_API_BASE", "ANTHROPIC_API_KEY", "ANTHROPIC_API_BASE",
    "ANTHROPIC_BASE_URL", "DATABRICKS_HOST", "DATABRICKS_TOKEN",
    "HTTPS_PROXY", "SSL_CERT_FILE", "OCR_LANG",
)
_LLM_FIELDS = (
    "document_llm", "legal_basic_extraction_llm", "shareholders_extraction_llm",
    "legal_rep_extraction_llm", "liabilities_extraction_llm",
)


def _mask(name: str, value: str | None) -> str:
    if not value:
        return "(trống)"
    if "KEY" in name or "TOKEN" in name:
        return f"{value[:5]}…{value[-3:]} ({len(value)} ký tự)"
    return value


def describe_env(folder: str | Path | None = None) -> None:
    """Which .env file exists next to the notebook, and what os.environ holds."""

    folder = Path(folder or Path().resolve())
    env_file, example = folder / ".env", folder / ".env.example"
    print(f"Thư mục notebook: {folder}")
    print(f"  .env         : {'CÓ' if env_file.is_file() else 'KHÔNG CÓ'}")
    if not env_file.is_file() and example.is_file():
        print("  → Chỉ có .env.example. Notebook KHÔNG đọc file này: tạo bản sao tên '.env',"
              " hoặc đặt os.environ[...] ngay trong notebook.")
    try:
        print(f"Provider đang dùng: {llm_provider()}")
    except ValueError as exc:
        print(f"Provider: LỖI — {exc}")
    for name in _SHOWN:
        print(f"  {name:<20} = {_mask(name, os.getenv(name))}")


def check_llm_setup(config: Any = None, raise_on_failure: bool = True) -> bool:
    """Call each distinct model of ``config`` once; True when all answer."""

    describe_env()
    if config is None:
        print("\n(Không có config — chỉ in biến môi trường.)")
        return True

    clients: dict[str, tuple[str, Any]] = {}
    for field in _LLM_FIELDS:
        llm = getattr(config, field, None)
        if llm is None:
            print(f"\n{field}: chưa cấu hình (bước dùng model này sẽ bị bỏ qua)")
            continue
        model = getattr(llm, "model_name", None) or getattr(llm, "model", None) or "?"
        base = getattr(llm, "openai_api_base", None) or getattr(llm, "anthropic_api_url", None) or ""
        clients.setdefault(f"{model}|{base}", (field, llm))

    ok = True
    print()
    for key, (field, llm) in clients.items():
        model, base = key.split("|", 1)
        where = base or "mặc định của provider"
        try:
            answer = llm.invoke("Trả lời đúng 1 chữ: OK")
            text = getattr(answer, "content", answer)
            print(f"✅ {model} ({where}) trả lời: {str(text)[:40]!r}")
        except Exception as exc:  # noqa: BLE001 — every failure is reported
            ok = False
            print(f"❌ {model} ({where}) — dùng cho {field}")
            print(f"   {explain_llm_error(exc, limit=800)}")

    if not ok and raise_on_failure:
        raise RuntimeError(
            "Chưa gọi được model — sửa theo dòng ❌ ở trên rồi chạy lại cell này. "
            "Không chạy tiếp để khỏi OCR cả bộ hồ sơ rồi mới thất bại."
        )
    return ok
