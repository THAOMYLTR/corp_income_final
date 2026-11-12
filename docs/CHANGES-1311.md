# Thay đổi 13/11/2026 — lỗi bảng 1b và bảng 4a khi chạy nhiều case

## 1. Bảng 4a — tên ngân hàng không viết tắt (VPBank)

| Nguyên nhân | Sửa | File |
|---|---|---|
| Bảng viết tắt ghi "Ngân hàng TMCP **Thịnh Vượng Việt Nam**", CIC ghi "Ngân hàng TMCP **Việt Nam Thịnh Vượng**" — khác thứ tự từ nên không khớp. Lỗi theo hồ sơ (chỉ case nào có VPBank), không phải do LLM. | Dòng VPBank đổi thành tên đúng + `(tên khác: TMCP Thịnh Vượng Việt Nam)`; code nhận thêm `(tên khác: …)` như `(tên cũ: …)`. | `src/templates/bang-viet-tat-ngan-hang.txt`, `src/agents/calculator/banks.py` (`_full_variants`) |

## 2. Bảng 1b — tỷ lệ góp vốn = 0 dù OCR đọc được

| Nguyên nhân | Sửa | File |
|---|---|---|
| `_primary_member_record` luôn chọn ĐKKD trước điều lệ. Công ty cổ phần: ĐKKD không in danh sách cổ đông, LLM đưa người đại diện vào `members` không có tỷ lệ → văn bản này thắng, 7 cổ đông và tỷ lệ của điều lệ bị bỏ. | Văn bản có tỷ lệ / vốn góp cho ≥ 50% thành viên đứng trước, rồi mới xét thứ tự loại văn bản. | `legal_checks._primary_member_record` |
| `_num` bỏ mọi giá trị dạng chữ ("30%", "7,5") → None. | `parse_pct` nhận cả số và chữ, dấu phẩy thập phân. | `legal_checks.parse_pct`, `check_shareholders` |
| Thành viên thiếu tỷ lệ ở văn bản chính không được bù từ văn bản khác. | `_pct_elsewhere`: lấy tỷ lệ của cùng người ở văn bản khác. | `legal_checks.check_shareholders` |
| `person_row` hiển thị None là "0" → không phân biệt "không góp vốn" và "chưa rõ". | Thành viên góp vốn chưa rõ tỷ lệ → "—"; người ngoài danh sách thành viên (đại diện PL, ban lãnh đạo) vẫn "0". | `appendix_context.build_appendix_context` (1b) |
| Prompt | `ownership_pct` phải là số (7,5% → 7.5); `members` chỉ gồm người trong danh sách góp vốn, ĐKKD công ty cổ phần → `[]`. | `config/prompts/shareholders_extraction.md` |

## 3. Bảng 1b — "Giám đốc" thành tên người; một người hiện nhiều dòng

| Nguyên nhân | Sửa | File |
|---|---|---|
| Báo cáo thực địa chỉ ghi chức danh → LLM điền "Giám đốc" vào `name`; khớp theo tên chính xác nên thành dòng riêng. | `is_title_not_name`: bỏ phần tử có "tên" chỉ là chức danh (người đại diện, `people`, `members`). Prompt: không có họ tên thì không tạo phần tử. | `legal_checks`, `appendix_context._field_people`, `config/prompts/legal_rep_extraction.md`, `shareholders_extraction.md` |
| OCR đọc sai họ: "PHAN QUANG ĐIỀN" / "PHẠM QUANG ĐIỀN" / "Phan Quang Điện" → 3 dòng. | `same_person`: bỏ dấu; tên đệm + tên phải giống hệt, họ lệch tối đa 1 chữ cái. KHÔNG dùng khớp gần đúng chung (vd "Nguyễn Thị Pha" ≠ "Nguyễn Thị Hà" dù giống 96%). Dùng khi gộp người đại diện, ban lãnh đạo, dòng 1b, đánh dấu (*). | `legal_checks.same_person`, `check_legal_rep`, `appendix_context` |

Chưa xử lý: tên OCR sai cả tên đệm / tên (vd "Quang Quên") — không gộp tự động được vì dễ gộp nhầm hai người khác nhau; cần OCR tốt hơn ở trang đó hoặc kiểm tra tay.

Test: `testing/test_display_1311.py` (Update1311Test).
