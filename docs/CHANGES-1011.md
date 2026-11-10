# Thay đổi 10/11/2026

| Mục | Thay đổi | File |
|---|---|---|
| Guidance — Bad finance (a) | Thêm Công ty TNHH Kiểm toán iGlobal (MST 0312075184) vào danh sách kiểm toán loại trừ. So khớp tên bỏ qua "Công ty / Cty / TNHH / CP…", và nhận cả MST (Bình An 0102662764, iGlobal 0312075184). | `corp-income-guidance.md`, `danh-sach-kiem-toan-loai-tru.txt`, `financial_metrics._is_excluded_auditor` |
| Guidance — Giá trị nguồn thu | Không xác định được nghĩa vụ trả gốc TDH hằng năm HOẶC khấu hao trong năm → LNST sử dụng để trả nghĩa vụ TDH = 0. | `corp-income-guidance.md`, `financial_metrics.income_estimate` |
| 3b — Chất lượng lợi nhuận | = (LN khác + DT hoạt động tài chính) / LNTT. < 25% tốt; 25% – < 50% trung bình; ≥ 50% kém; < 0 (hoặc LNTT = 0) → không nhận xét. Thay công thức LN gộp / LNTT. | `financial_metrics.earnings_quality_remark` |
| 429 QPM | Mọi lần gọi LLM (phân loại, trích xuất M1–M9, đánh giá, viết báo cáo) đi qua `call_llm`: giãn cách để không quá QPM trong 60 giây; bị 429 thì chờ (Retry-After, hoặc đến khi phút cũ giải phóng, 5–60 s), hạ QPM 20% và gọi lại (tối đa `LLM_RATE_LIMIT_RETRIES`, mặc định 8). QPM ban đầu: `LLM_REQUESTS_PER_MINUTE` (0 = tự học từ lần 429 đầu). | `src/utils/rate_limit.py` (mới), `structured_extraction.py`, `supervisor.py`, `report_writer.py`, `config.py`, `.env.example` |

Test: `testing/test_rate_limit.py` (mới), `testing/test_display_2910.py` (Guidance1011Test, earnings quality).
