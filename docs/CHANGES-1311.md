# Thay đổi 13/11/2026 — lỗi bảng 1b và bảng 4a khi chạy nhiều case

Mọi chỗ sửa trong code có comment `[13/11]` hoặc `[Sửa 13/11]`. Không có giá trị nào gắn cứng cho một hồ
sơ: các thay đổi là luật chung, trừ dòng VPBank là sửa dữ liệu trong bảng viết tắt.

## 1. Bảng 4a — tên ngân hàng không viết tắt (VPBank)

| Nguyên nhân | Sửa | Đổi logic cũ? |
|---|---|---|
| Bảng viết tắt ghi "Ngân hàng TMCP **Thịnh Vượng Việt Nam**", CIC ghi "**Việt Nam Thịnh Vượng**" → khác thứ tự từ, không khớp. Lỗi theo hồ sơ (case nào có VPBank), không do LLM. | Sửa dòng VPBank (tên đúng + `(tên khác: …)`); code nhận `(tên khác: …)` như `(tên cũ: …)`. | Không. Cách khớp giữ nguyên. |

## 2. Bảng 1b — tỷ lệ góp vốn = 0 dù OCR đọc được

| Nguyên nhân | Sửa | Đổi logic cũ? |
|---|---|---|
| Tỷ lệ dạng chữ ("30%", "7,5") bị bỏ → None → hiện "0". | `parse_pct` đọc cả số và chữ, dấu phẩy thập phân. | Không. Giá trị dạng số xử lý như cũ. |
| ĐKKD luôn thắng điều lệ. Công ty cổ phần: ĐKKD không in cổ đông, LLM đưa người đại diện vào `members` (không tỷ lệ) → mất 7 cổ đông và tỷ lệ của điều lệ. | **Luật 1 (đã siết):** chỉ xếp sau khi văn bản **không có tỷ lệ / vốn góp của BẤT KỲ ai**. Có của 1 người là giữ thứ tự cũ. TNHH MTV / DNTN luôn giữ thứ tự cũ (ĐKKD, 100%). Văn bản được dùng cũ hơn / không rõ ngày so với văn bản bị bỏ → cảnh báo `members_from_older_doc` ("kiểm tra chuyển nhượng sau ngày văn bản"), hiện ở Cảnh báo pháp lý. | **Có**, chỉ trong trường hợp văn bản ưu tiên không có tỷ lệ nào. |
| Thành viên thiếu tỷ lệ không được bù. | `_pct_elsewhere`: lấy tỷ lệ của cùng người ở văn bản khác — tên khớp chính xác (bỏ dấu), **không lấy từ văn bản cũ hơn** văn bản chính. | Thêm mới (trước đây để trống). |
| None hiển thị "0" → không phân biệt "không góp vốn" / "chưa rõ". | Thành viên chưa rõ tỷ lệ → "—"; người ngoài danh sách thành viên (đại diện PL, ban lãnh đạo) vẫn "0". | Có — chỉ cách hiển thị. |
| Prompt | **Luật 3 (đã siết):** `ownership_pct` là số (7,5% → 7.5). `members` chỉ gồm người văn bản IN TRONG DANH SÁCH cổ đông / cổ đông sáng lập / thành viên / chủ sở hữu; không có danh sách thì `[]` (bỏ câu "ĐKKD công ty cổ phần thường không in…" để không làm mất cổ đông sáng lập trên ĐKKD đời cũ). | Thêm ràng buộc cho LLM. |

## 3. Bảng 1b — "Giám đốc" thành tên người; một người hiện nhiều dòng

| Nguyên nhân | Sửa | Đổi logic cũ? |
|---|---|---|
| Báo cáo thực địa chỉ ghi chức danh → LLM điền "Giám đốc" vào `name`. | `is_title_not_name`: bỏ phần tử mà CẢ ô tên đúng bằng một chức danh (danh sách `_TITLE_ONLY_NAMES`). Prompt: không có họ tên thì không tạo phần tử. | Không (không ai tên "Giám đốc"). |
| OCR sai họ: "PHAN QUANG ĐIỀN" / "PHẠM QUANG ĐIỀN" → 2 dòng. | `same_person`: bỏ dấu; tên đệm + tên giống hệt, họ lệch tối đa 1 chữ. **Luật 2 (đã siết):** chỉ gộp khi hai tên ở **hai văn bản khác nhau**; cùng một văn bản → hai người. Đánh dấu (*): khớp chính xác người vay trước, chỉ xét lệch họ khi không ai khớp chính xác. | Có — trước đây chỉ khớp chính xác. |

Không gộp được: tên OCR sai cả tên đệm / tên (vd "Quang Quên") — cố ý, vì dễ gộp nhầm hai người; cần kiểm tra tay.

## Lưu ý theo file (để chép sang Databricks)

| File | Thay đổi | Lưu ý |
|---|---|---|
| `src/agents/calculator/legal_checks.py` | Hàm mới: `is_title_not_name`, `same_person`, `parse_pct`, `_has_stake`, `_any_stake`, `_doc_date`, `_skipped_member_records`, `_pct_elsewhere`. Sửa: `_primary_member_record` (thêm `keep_priority`), `check_shareholders` (chọn văn bản, bù tỷ lệ, cảnh báo `members_from_older_doc`), `check_legal_rep` (bỏ chức danh, gộp lệch họ khác văn bản). | File lớn nhất; chép cả các hàm mới (đặt ngay trên `norm_tax_code` và trên `SINGLE_OWNER_FORMS`). |
| `src/utils/report/appendix_context.py` | Import thêm `_cite as cite_record`, `is_title_not_name`, `same_person`. `_field_people` (bỏ chức danh, lưu `_doc`). Khối 1b: `match` / `is_seen` theo văn bản, `person_row` có thêm tham số `doc`, "—" cho thành viên chưa rõ tỷ lệ, đánh dấu (*) chính xác trước. Thêm `members_from_older_doc` vào 2 danh sách mã cảnh báo. | `person_row` đổi chữ ký hàm — sửa cả 3 chỗ gọi. |
| `src/agents/calculator/banks.py` | `_full_variants`: regex `tên (?:cũ|khác):`. | 1 dòng. |
| `src/templates/bang-viet-tat-ngan-hang.txt` | Dòng VPBank + chú thích đầu file. | Thêm ngân hàng mới: tên đầy đủ phải đúng thứ tự từ như CIC ghi. |
| `config/prompts/shareholders_extraction.md` | Luật `ownership_pct` là số; luật `members`; luật `name` không là chức danh. | Đổi prompt → kết quả LLM có thể khác lần chạy trước; chạy lại vài case cũ để so. |
| `config/prompts/legal_rep_extraction.md` | Luật `name` không là chức danh. | |
| `testing/test_display_1311.py` (mới) | 16 test: 2 hồ sơ lỗi + các trường hợp rủi ro (ĐKKD có tỷ lệ giữ thứ tự cũ, ĐKKD mới hơn điều lệ → cảnh báo, không bù tỷ lệ từ văn bản cũ, TNHH MTV, Phan/Phạm cùng văn bản là hai người, (*) đúng người). | Không cần chép nếu Databricks không chạy test. |
