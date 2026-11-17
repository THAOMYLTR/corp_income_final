# Thay đổi 17/11/2026 — tiêu chí phân nhóm Bad / Good corp

| Mục | Trước (13/11) | Nay (17/11) |
|---|---|---|
| Bad corp (≥ 1 tiêu chí) | DN không hoạt động (tra cứu thuế / thẩm định thực tế); **lệch bất kỳ thông tin pháp lý** (MST, tên, TSC, NĐDPL, ngày thành lập); thành lập < 12 tháng; ngành nghề thực tế không phù hợp chứng từ (chỉ trong prompt); Bad finance; Bad bureau | DN không hoạt động theo tra cứu thuế **hoặc** theo thẩm định thực tế; **mã số thuế không đồng nhất giữa các chứng từ**; thành lập < 12 tháng; Bad finance **hoặc** Bad bureau |
| Lệch tên, TSC, NĐDPL, ngày thành lập | Bad corp | Chỉ **cảnh báo ở 1b** (như trước 13/11) |
| Ngành nghề thực tế ≠ chứng từ | Tiêu chí Bad corp trong prompt / guidance | Bỏ khỏi tiêu chí Bad corp (vẫn cảnh báo ở 2b) |
| Good corp | Good finance VÀ Good bureau | Good finance VÀ Good bureau **VÀ không phải Bad corp** (code vốn đã kiểm tra Bad trước) |
| Normal corp | còn lại | còn lại |
| Đề xuất | Bad → Không sử dụng; Normal → tối đa có điều kiện; Good → Sử dụng | Không đổi |

| File | Thay đổi |
|---|---|
| `src/utils/report/appendix_context.py` | Thêm `BAD_CORP_MISMATCH_CODES = ("tax_code_mismatch",)`; `corp_group` dùng hằng này. `LEGAL_MISMATCH_CODES` giữ cho cảnh báo 1b. Bỏ bản khai báo trùng `LEGAL_MISMATCH_CODES` trước `corp_group`. |
| `src/templates/corp-income-guidance.md` | Mục 5 (Bad Corp) và mục 6: tiêu chí mới như trên. |
| `config/prompts/credit_assessment.md`, `src/templates/corp-income-cell-specs.md` | Danh sách tiêu chí Bad corp mới. |
| `testing/test_display_1311.py` | `CorpGroup1711Test`. |
