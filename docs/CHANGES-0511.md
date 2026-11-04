# Thay đổi 05/11/2026 — guidance v1, output template 05/11, bảng ngành / phân bổ ngành / viết tắt ngân hàng

| Mục | Thay đổi | File |
|---|---|---|
| Guidance | Thay bằng corp_income_guidance_v1. Bad corp không còn tiêu chí "thông tin pháp lý không phù hợp giữa các chứng từ" (chỉ cảnh báo ở 1b). Phân khúc: SME ≥ 80 tỷ, MSME < 80 tỷ. Bad finance chỉ a–d (DTT lệch VAT → cảnh báo). Danh sách kiểm toán loại trừ: Bình An. | `src/templates/corp-income-guidance.md`, `src/templates/danh-sach-kiem-toan-loai-tru.txt`, `appendix_context.corp_group`, `financial_metrics` |
| Bảng ngành TCB | 470 dòng (thêm MSME × 30), cột mới "Loại hình doanh nghiệp". Ngành chưa có ở MSME → dùng dòng SME. | `src/templates/bang-nganh-tcb.csv`, `calculator/industry.py` |
| Bảng phân bổ ngành nghề | 17 loại hình, khoảng tỷ trọng Tiền / ĐTTC NH / Phải thu NH / HTK trên TSNH. | `src/templates/bang-phan-bo-nganh.csv`, `industry.allocation` |
| Viết tắt ngân hàng | Tên CIC → tên ngắn ở cột bảng 4a; các chi nhánh một ngân hàng gộp một cột. | `src/templates/bang-viet-tat-ngan-hang.txt`, `calculator/banks.py`, `cic_metrics` |
| 3a | Nhãn "Tổng tài sản". Nhận xét: (1) phù hợp ngành — ≥ 2/4 khoản mục TSNH trong khoảng của bảng phân bổ; (2) HSTT: < 1 rủi ro mất khả năng thanh toán / 1–3 an toàn / > 3 vốn ngắn hạn chưa hiệu quả; (3) cảnh báo BCTC. | `financial_metrics.industry_fit_remark`, `current_ratio_remark`, `appendix_context` |
| 3b | Cột "Tăng/giảm"; dòng DTT, LNST, LN sau thuế/DTT. Nhận xét: VAT đến tháng, phân khúc TCB, chất lượng lợi nhuận (LN gộp / LNTT: > 85% tốt, 50–85% trung bình, < 50% kém), ROS so với ROS ngành; cảnh báo DTT ≠ VAT, lãi vay ≠ dư nợ CIC × 6–14%, thuế ≠ 20%; lãi vay / LN gộp > 50%. | `financial_metrics.earnings_quality_remark`, `ros_vs_industry_remark`, `appendix_context` |
| 4a | Không có cam kết ngoại bảng → ẩn dòng; không có CIC → "Không có thông tin CIC". | `appendix_context.debt_table` |
| 5a | Bảng 2 thêm cột "Lệch" (dự phóng − ngành). Cơ sở dự phóng: tỷ lệ thực hiện DT theo tờ khai thuế năm kế hoạch / kế hoạch. | `corp-income-structure.md`, `appendix_context.plan_cells` |

Test: `testing/test_display_2910.py` (Guidance0511Test, Data0511Test, Template0511Test).
