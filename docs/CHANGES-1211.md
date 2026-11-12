# Thay đổi 12/11/2026 — Instruction final, Template final, chạy nhiều case

| Mục | Thay đổi | File |
|---|---|---|
| Guidance | Thay bằng "Instruction final". Mới: công ty TNHH một thành viên / doanh nghiệp tư nhân — chủ sở hữu / chủ DN trên ĐKKD sở hữu 100%. | `src/templates/corp-income-guidance.md` |
| Tỷ lệ góp vốn TNHH MTV / DNTN | Prompt: ghi chủ sở hữu là thành viên duy nhất, 100%. Code: tên DN có "TNHH MỘT THÀNH VIÊN / TNHH MTV / DOANH NGHIỆP TƯ NHÂN / DNTN", có đúng 1 thành viên và ĐKKD không in tỷ lệ → 100%. | `config/prompts/shareholders_extraction.md`, `legal_checks.check_shareholders` |
| 1b | Tên người đứng ra vay có "(*)", chú thích "(*) Người đứng ra vay." dưới bảng. | `appendix_context.py` |
| 5b — Doanh thu dự phóng khả thi | = min[DT PAKD; max[DT thực tế năm kế hoạch theo tờ khai VAT; DT năm N × (1 + tăng trưởng ngành × 1,5 nếu Good corp)]]. | `financial_metrics.income_estimate`, `appendix_context.income_block` |
| Chạy nhiều case | `run_cases(...)` chạy lần lượt các case trong `TESTCASE_IDS`, lưu mỗi case như cell lưu kết quả, in bảng tổng hợp; case lỗi không dừng cả lô. Cell mới cuối notebook. | `src/utils/batch.py` (mới), `local_underwriting_agents.ipynb` |

Giữ nguyên theo các quyết định trước (Template final ghi khác — chờ xác nhận): chất lượng lợi nhuận = (LN khác + DT TC) / LNTT (10/11); lệch thông tin pháp lý không làm Bad corp (05/11); bảng 3a một cột % Tỷ trọng (05/11); nhận xét phù hợp ngành ở 3a.

Test: `testing/test_display_2910.py` (Update1211Test).
