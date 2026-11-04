"""Turn an LLM call failure into one line that says what to fix.

LangChain and the OpenAI SDK wrap every network problem as
``APIConnectionError: Connection error.`` — the real cause (DNS, firewall,
certificate, proxy) sits in ``__cause__``. This walks that chain, keeps the
deepest message, and adds a hint in Vietnamese.
"""

from __future__ import annotations

_HINTS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("missing credentials", "api_key client option must be set", "no api key"),
     "Chưa có API key: đặt OPENAI_API_KEY (hoặc key của LLM_PROVIDER) trong .env / cell 3."),
    (("401", "invalid_api_key", "incorrect api key", "authentication", "unauthorized"),
     "Key sai hoặc hết hạn; hoặc đang gửi token Databricks cho OpenAI (kiểm tra api_key=...)."),
    (("403", "permission_denied", "forbidden"),
     "Không có quyền gọi model/endpoint này (Databricks: quyền Can Query)."),
    (("404", "not_found", "does not exist", "model_not_found"),
     "Sai tên model/endpoint hoặc sai base URL (OPENAI_API_BASE / ANTHROPIC_API_BASE)."),
    (("429", "insufficient_quota", "rate limit", "rate_limit"),
     "Hết quota/credit hoặc gọi quá nhanh: nạp tiền, hoặc đặt LLM_REQUESTS_PER_MINUTE."),
    (("certificate_verify_failed", "certificate verify failed", "ssl"),
     "Proxy ngân hàng chặn SSL: cần file CA của ngân hàng → SSL_CERT_FILE."),
    (("proxyerror", "407", "proxy"),
     "Phải đi qua proxy công ty: đặt HTTPS_PROXY theo hướng dẫn team platform."),
    (("name or service not known", "nodename nor servname", "getaddrinfo", "name resolution"),
     "Không phân giải được tên miền: base URL sai, hoặc cluster không ra được internet."),
    (("timed out", "timeout", "connecttimeout"),
     "Firewall chặn hoặc mạng chậm: cluster có thể không ra được internet → dùng Databricks Serving."),
    (("connection refused",),
     "Có địa chỉ nhưng không có dịch vụ: sai cổng hoặc sai URL."),
    (("unsupported protocol", "request url is missing", "invalid url"),
     "Base URL rỗng hoặc thiếu https:// (kiểm tra OPENAI_API_BASE / ANTHROPIC_API_BASE)."),
)


def error_chain(exc: BaseException) -> list[BaseException]:
    """``exc`` and every exception it was raised from, outermost first."""

    chain: list[BaseException] = []
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        chain.append(current)
        seen.add(id(current))
        current = current.__cause__ or current.__context__
    return chain


def hint_for(text: str) -> str:
    lowered = text.lower()
    for needles, hint in _HINTS:
        if any(needle in lowered for needle in needles):
            return hint
    return ""


def explain_llm_error(exc: BaseException, limit: int = 500) -> str:
    """``Type: message`` of the outermost error, the root cause if different, and a hint."""

    chain = error_chain(exc)
    outer, root = chain[0], chain[-1]
    text = f"{type(outer).__name__}: {outer}"
    if root is not outer:
        text += f" | nguyên nhân gốc: {type(root).__name__}: {root}"
    hint = hint_for(" ".join(f"{type(e).__name__} {e}" for e in chain))
    if hint:
        text += f" → {hint}"
    return text[:limit]
