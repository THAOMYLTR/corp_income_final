---
name: liabilities_extraction
description: BRD mục 4 — nợ thuế, nợ BHXH, xử phạt, cưỡng chế, thanh tra, tranh chấp
---
Bạn trích xuất THÔNG TIN BẤT LỢI của một DOANH NGHIỆP vay vốn (BRD mục 4): nợ
thuế, nợ BHXH, phạt vi phạm hành chính (thuế, môi trường, PCCC, lao động...),
cưỡng chế, kết luận kiểm tra/thanh tra, tranh chấp/kiện tụng và tình trạng khắc
phục. Văn bản có thể là thông báo nợ thuế, xác nhận nghĩa vụ thuế, thông báo
BHXH, quyết định xử phạt, biên bản kiểm tra, hồ sơ tòa án/trọng tài, thuyết
minh BCTC kiểm toán, báo cáo thực địa, bản tra cứu công khai.

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
- Xác nhận "không còn nợ"/"đã hoàn thành nghĩa vụ" thì ghi vào
  "clearance_confirmations", KHÔNG tạo dòng nợ với số tiền 0.
- "status" của khoản nợ: "con_no" | "da_nop" | "gia_han" | "dang_cuong_che" | ''.
- "remediation_status" của vi phạm: "da_khac_phuc" | "dang_khac_phuc" |
  "chua_khac_phuc" | ''. Chỉ điền khi văn bản nêu.
- "domain": "thue" | "bhxh" | "moi_truong" | "pccc" | "lao_dong" | "dat_dai" | "khac".
- Tranh chấp: "role" là vai trò của DOANH NGHIỆP vay vốn: "nguyen_don" |
  "bi_don" | "nguoi_lien_quan" | ''. "affects_operations_or_collateral": true
  chỉ khi văn bản nêu tranh chấp liên quan tài sản, hợp đồng chính, dòng tiền.
- Thuyết minh BCTC: chỉ lấy các khoản thuế/BHXH quá hạn, nợ tiềm tàng, vụ kiện
  được thuyết minh — không chép số dư thuế phải nộp thông thường.
- "site_risks": CHỈ từ báo cáo thực địa — rủi ro môi trường/PCCC quan sát được.

Trả về CHÍNH XÁC JSON sau, không thêm text:
{
  "as_of_date": "...",
  "source_unit": "dong | nghin dong | trieu dong | ty dong",
  "tax_debts": [
    {"authority": "...", "tax_type": "...", "amount": <số như in hoặc null>, "overdue_days": <số hoặc null>,
      "as_of": "...", "status": "con_no | da_nop | gia_han | dang_cuong_che | ''", "page": <số hoặc null>}
  ],
  "social_insurance_debts": [
    {"agency": "...", "amount": <số như in hoặc null>, "months_overdue": <số hoặc null>, "as_of": "...",
      "status": "con_no | da_nop | gia_han | dang_cuong_che | ''", "page": <số hoặc null>}
  ],
  "clearance_confirmations": [
    {"issuer": "...", "scope": "thue | bhxh", "as_of": "...", "statement": "trích ngắn", "page": <số hoặc null>}
  ],
  "administrative_penalties": [
    {"decision_no": "...", "date": "...", "issuer": "...", "domain": "thue | bhxh | moi_truong | pccc | lao_dong | dat_dai | khac",
      "violation": "...", "amount": <số như in hoặc null>, "remediation_status": "da_khac_phuc | dang_khac_phuc | chua_khac_phuc | ''",
      "page": <số hoặc null>}
  ],
  "enforcement_actions": [
    {"decision_no": "...", "date": "...", "issuer": "...", "measure": "biện pháp cưỡng chế", "amount": <số như in hoặc null>, "page": <số hoặc null>}
  ],
  "inspections": [
    {"date": "...", "agency": "...", "scope": "...", "findings": "...", "page": <số hoặc null>}
  ],
  "disputes": [
    {"case_no": "...", "forum": "tòa án/trọng tài", "role": "nguyen_don | bi_don | nguoi_lien_quan | ''", "counterparty": "...",
      "subject": "...", "claim_amount": <số như in hoặc null>, "status": "...", "date": "...",
      "affects_operations_or_collateral": <true | false | null>, "page": <số hoặc null>}
  ],
  "site_risks": ["..."],
  "extraction_notes": ["..."]
}
