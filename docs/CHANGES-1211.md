# Thay đổi 12/11/2026

## 1. Guidance và template

| Mục | Thay đổi | File |
|---|---|---|
| Guidance | Thay bằng "Instruction final". Mới: công ty TNHH một thành viên / doanh nghiệp tư nhân — chủ sở hữu / chủ DN trên ĐKKD sở hữu 100%. | `src/templates/corp-income-guidance.md` |
| Tỷ lệ góp vốn TNHH MTV / DNTN | Prompt: ghi chủ sở hữu là thành viên duy nhất, 100%. Code: tên DN có "TNHH MỘT THÀNH VIÊN / TNHH MTV / DOANH NGHIỆP TƯ NHÂN / DNTN", đúng 1 thành viên và ĐKKD không in tỷ lệ → 100%. | `config/prompts/shareholders_extraction.md`, `legal_checks.check_shareholders` |
| 1b | Tên người đứng ra vay có "(*)", chú thích "(*) Người đứng ra vay." dưới bảng. | `appendix_context.py` |
| 5b — Doanh thu dự phóng khả thi | = min[DT PAKD; max[DT thực tế năm kế hoạch theo tờ khai VAT; DT năm N × (1 + tăng trưởng ngành × 1,5 nếu Good corp)]]. | `financial_metrics.income_estimate`, `appendix_context.income_block` |

## 2. Hướng dẫn cho LLM khớp với guidance và template

| File | Thay đổi |
|---|---|
| `src/templates/corp-income-cell-specs.md` | SanPhamDichVu: nhãn "Diễn giải chi tiết", quy tắc đa loại hình và thiếu thông tin. TruSoChinh: khung mới (địa chỉ + đi thuê / sở hữu). NhanXetHDKD: đủ cảnh báo theo guidance (thiếu cả 3 địa chỉ, TSC ≠ ảnh, đối tác không khớp thực địa, mua đi bán lại, reflag rủi ro cao). KetLuanNguonThuDoanhNghiep: Đề xuất · Lý do (pháp lý, tài chính, tín dụng) · Điều kiện · Hồ sơ cần bổ sung. |
| `config/prompts/report_writer.md` | Bỏ quy tắc cũ về ghi tên file và ví dụ có tên file; ô Đề xuất chỉ một khung; ô có khung riêng không thêm dòng "Ảnh hưởng tới quyết định". |
| `config/prompts/credit_assessment.md` | Căn cứ không ghi tên file; tiêu chí Bad corp theo mục 5 guidance. |

## 3. Chạy nhiều case

| Mục | Thay đổi | File |
|---|---|---|
| `run_cases` | Chạy lần lượt các case trong `TESTCASE_IDS`, lưu mỗi case như cell lưu kết quả; case lỗi không dừng cả lô. Bảng tổng hợp: status (OK / THIẾU TRÍCH XUẤT / LỖI), số file, số lượt trích xuất thất bại + chi tiết, nhóm DN, thư mục, số phút; lưu `logs/batch_<giờ>.json`. | `src/utils/batch.py` (mới) |
| Tên file báo cáo | `final_response_<case_id>.pdf / .md`. | `src/utils/batch.py` |
| Notebook — chỉ còn chạy nhiều case | Cell 3: `CASES_DIR` (thư mục chứa các case), `TESTCASE_IDS`, `PER_CASE`; bỏ `TESTCASE_ID`, `INPUT_PATHS`. Bỏ cell Run 1 case và cell lưu kết quả 1 case (việc lưu nằm trong `batch.save_run`). Cell "Run" gọi `run_cases`, hiện bảng tổng hợp. Cell cuối (tuỳ chọn): xem báo cáo, lượt trích xuất thất bại, kết luận từng mục của một case. | `local_underwriting_agents.ipynb` |

Cách chạy: cell 1 → 8 (thông số, config, kiểm tra model, import) → cell Run → (tuỳ chọn) cell xem một case.

## Giữ nguyên theo các quyết định trước (Template final ghi khác — chờ xác nhận)
- Chất lượng lợi nhuận = (LN khác + DT TC) / LNTT, ngưỡng 25% / 50% (10/11).
- Lệch thông tin pháp lý không làm Bad corp (05/11).
- Bảng 3a một cột % Tỷ trọng (05/11); vẫn có nhận xét phù hợp ngành ở 3a.

Test: `testing/test_display_2910.py` (Update1211Test).
