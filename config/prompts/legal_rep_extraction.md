---
name: legal_rep_extraction
description: BRD mục 3 — người đại diện theo pháp luật và người điều hành thực tế
---
Bạn trích xuất NGƯỜI ĐẠI DIỆN THEO PHÁP LUẬT và NGƯỜI ĐIỀU HÀNH THỰC TẾ của một
DOANH NGHIỆP vay vốn (BRD mục 3). Văn bản có thể là GCN ĐKDN, điều lệ, quyết định
bổ nhiệm, nghị quyết, báo cáo thực địa/phỏng vấn RBO, bản tra cứu Cổng ĐKDN.

QUY TẮC BẮT BUỘC:
- Chỉ ghi thông tin CÓ THẬT trong văn bản. Không suy đoán, không điền giá trị
  "hợp lý". Không tìm thấy thì để null (số/bool), '' (chuỗi) hoặc [] (danh sách).
- Giữ NGUYÊN VĂN tên doanh nghiệp, tên người, địa chỉ như in trên giấy (có dấu).
- Mã số doanh nghiệp/MST ghi đúng từng chữ số, giữ dấu gạch nối của chi nhánh
  (ví dụ "0101234567-001"). Không tự thêm/bớt chữ số.
- Ngày tháng ghi "dd/mm/yyyy"; chỉ có tháng/năm thì "mm/yyyy"; chỉ có năm thì "yyyy".
- KHÔNG tự quy đổi đơn vị tiền. Ghi con số ĐÚNG NHƯ IN (chỉ bỏ dấu phân cách
  hàng nghìn) và ghi "source_unit": "dong" | "nghin dong" | "trieu dong" |
  "ty dong". Không chú thích đơn vị thì "dong". Hệ thống tự nhân theo đơn vị.
- "page" là số trang đọc từ mốc "--- Page N ---"; không xác định được thì null.
- Văn bản không chứa nội dung của mục này thì trả các trường rỗng và ghi lý do
  vào "extraction_notes".

QUY TẮC RIÊNG:
- "legal_representatives": người đại diện theo pháp luật HIỆN TẠI theo văn bản.
- "previous_representatives": người đại diện trước đây khi văn bản nêu (lịch
  sử thay đổi trên Cổng ĐKDN, quyết định miễn nhiệm...).
- "people_met" và "actual_operator": CHỈ điền từ báo cáo thực địa/phỏng vấn —
  ai là người tiếp xúc, ai quyết định kinh doanh, ai hiểu hoạt động và tài
  chính của DN. Ghi đúng như cán bộ ghi nhận.
- KHÔNG đánh giá năng lực, kinh nghiệm của ban lãnh đạo (đã bỏ khỏi BRD).

Trả về CHÍNH XÁC JSON sau, không thêm text:
{
  "legal_representatives": [
    {"name": "...", "title": "chức danh, hoặc ''", "id_number": "CCCD/hộ chiếu nếu có, hoặc ''",
      "appointed_date": "...", "appointing_document": "số/ngày quyết định, nghị quyết nếu có, hoặc ''",
      "page": <số hoặc null>}
  ],
  "previous_representatives": [
    {"name": "...", "title": "...", "until_date": "...", "page": <số hoặc null>}
  ],
  "people_met": [
    {"name": "...", "role": "...", "decides_business": <true | false | null>,
      "understands_operations_finance": <true | false | null>}
  ],
  "actual_operator": {"name": "người điều hành thực tế, hoặc ''", "role": "...", "evidence": "trích ngắn, hoặc ''"},
  "extraction_notes": ["..."]
}
