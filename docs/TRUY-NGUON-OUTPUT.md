# Truy nguồn output — mỗi ô của Phụ lục 01 lấy từ đâu, ai điền, theo luật gì

Cập nhật 18/11/2026 (theo code tại commit có file này). Dùng để kiểm định từng case: với mỗi ô trong
`final_response_<case>.pdf`, bảng dưới cho biết **hồ sơ nguồn**, **ai điền** (CODE / LLM) và **luật**, và
**file nào trong thư mục kết quả** để đối chiếu.

---

## 0. Luồng xử lý chung

| Bước | Ai làm | Làm gì | Kiểm định ở |
|---|---|---|---|
| 1. Đọc file | code (OCR Tesseract cho PDF scan / ảnh; đọc trực tiếp DOCX, XLSX, CSV, TXT, XML) | Lấy toàn bộ chữ của từng file. Ảnh thực địa chỉ có phần **chữ** đọc được (biển hiệu, nhãn), không có "nhìn ảnh". | `ocr/<tên file>.txt` |
| 2. Phân loại hồ sơ | code chấm điểm từ khóa (tên file ×3 + nội dung) theo `document_matrix.yaml`, trong đúng ô upload (thư mục); LLM chỉ chọn khi hai loại sát điểm | Gán mỗi file một **loại hồ sơ** (bảng mục 0.1) | `result.json` → `document_classifications` (loại, độ tin cậy) |
| 3. Trích xuất | **LLM** — mỗi loại hồ sơ chạy các "lượt" (pass) cố định, mỗi lượt một prompt trong `config/prompts/<pass>_extraction.md` | Chỉ **chép** thông tin có trong văn bản ra JSON (không tính, không suy đoán; thiếu → để trống) | `<pass>_extraction.json` (mỗi file một mục) |
| 4. Tính toán, đối chiếu, phân nhóm | **CODE** (`src/agents/calculator/*`, `src/utils/report/appendix_context.py`) | Mọi số liệu, tỷ lệ, so khớp giữa nguồn, cảnh báo, phân nhóm Bad/Normal/Good, giá trị nguồn thu | `corp_income.json`, `corp_income.xlsx` |
| 5. Nhận định tín dụng | **LLM** (`config/prompts/credit_assessment.md`) | Một lần gọi: quyết định Sử dụng / có điều kiện / Không sử dụng + rủi ro. **Code ép theo nhóm**: Bad corp → "Không sử dụng"; Normal corp không được "Sử dụng" hẳn | `corp_income.json` → `credit_assessment` (`quyet_dinh`, `quyet_dinh_llm` nếu bị ép, `rui_ro`) |
| 6. Viết ô chữ | **LLM** (`config/prompts/report_writer.md` + khung từng ô `src/templates/corp-income-cell-specs.md` + guidance) | Chỉ 6 ô: `SanPhamDichVu`, `TruSoChinh`, `NhaXuong`, `KhoHang`, `NhanXetHDKD`, `KetLuanNguonThuDoanhNghiep` | `corp_income.json` → `meta.llm_placeholders`, `meta.writer_error` |

**LLM viết ô chữ dựa trên gì:** chỉ gói dữ liệu code gửi kèm — các ô code đã điền (`gia_tri_da_dien`), kết quả kiểm
tra pháp lý, số liệu và cảnh báo tài chính, CIC, nhóm DN, ngành TCB, đối tác đầu vào/ra, địa chỉ TSC trên ĐKKD, và
**trích đoạn** hồ sơ (tối đa 6.000 ký tự/file cho báo cáo thực địa, ảnh thực địa, hợp đồng, sao kê, ĐKKD, CIC, VAT,
PAKD…; 2.500 ký tự/file khác; tổng 80.000). **Thông tin nằm sau phần trích đoạn của một file dài thì LLM không thấy.**

### 0.1. Loại hồ sơ → lượt trích xuất (LLM)

Lượt: **LB** legal_basic · **SH** shareholders · **LR** legal_rep · **LI** liabilities · **FI** financial ·
**VAT** vat · **CIC** cic · **PL** plan · **BM** business_model. Nguồn: KH = KH cung cấp · TĐ = thực địa ·
NGOÀI = tra cứu bên ngoài · NB = nội bộ.

| Ô upload | Loại hồ sơ | Nguồn | Lượt |
|---|---|---|---|
| ho_so_phap_ly | ĐKKD / GCN ĐKDN | KH | LB, SH, LR |
| | Điều lệ | KH | LB, SH, LR |
| | Sổ cổ đông / sổ đăng ký thành viên | KH | LB, SH |
| | HĐ chuyển nhượng vốn | KH | SH |
| | QĐ bổ nhiệm / nghị quyết | KH | SH, LR |
| | Báo cáo khảo sát thực địa (đặt ở pháp lý) | TĐ | LB, SH, LR, LI, BM |
| | QĐ xử phạt, biên bản kiểm tra, hồ sơ tranh chấp | KH | LI |
| | Giấy phép ngành nghề, quyền sử dụng nhà xưởng | KH | — (chỉ vào trích đoạn cho LLM) |
| ho_so_tai_chinh | BCTC, thuyết minh BCTC | KH | FI, LI |
| | Tờ khai thuế GTGT | KH | VAT |
| | Sao kê tài khoản, sổ chi tiết công nợ | KH | BM |
| | Thông báo nợ thuế, xác nhận BHXH | KH | LI |
| ho_so_vay_von | PAKD / đề nghị cấp tín dụng | KH | PL |
| | Hợp đồng / hóa đơn đầu vào, đầu ra | KH | BM |
| ho_so_noi_bo | CIC KHDN (S10A, R20) | NGOÀI | CIC |
| | Tra cứu ĐKDN / thuế | NGOÀI | LB, SH, LR |
| | Tra cứu nợ thuế / BHXH | NGOÀI | LI |
| | Dữ liệu nội bộ (BCDE / BEP / DBX) | NB | LB, SH, LR, BM |
| ho_so_soan_thao_noi_bo | Báo cáo khảo sát và đề xuất tín dụng (thực địa) | TĐ | LB, SH, LR, LI, BM |
| | Hình ảnh khảo sát thực địa | TĐ | — (OCR chữ → trích đoạn cho LLM) |
| ho_so_tai_san_dam_bao | TSBĐ, chứng thư định giá | KH | — (không dùng cho Corp Income) |

---

## 1. Pháp lý doanh nghiệp

| Ô | Ai | Hồ sơ nguồn | Luật | Đối chiếu |
|---|---|---|---|---|
| Tên doanh nghiệp, Mã số thuế, Người đại diện theo PL | CODE | Lượt LB | Lấy giá trị đầu tiên có theo thứ tự **ĐKKD → Điều lệ → Sổ cổ đông → Báo cáo thực địa**, rồi hồ sơ khác. Ô chỉ ghi giá trị; chỗ các nguồn không khớp nằm ở "Cảnh báo pháp lý" (1b) | `legal_basic_extraction.json` |
| Năm thành lập | CODE | Lượt LB (`establishment_date`, `registration_change_number`, `latest_change_date`) | Năm = **ngày đăng ký lần đầu = ngày sớm nhất** mà các hồ sơ ghi (Điều lệ / hồ sơ thay đổi có thể ghi ngày sửa đổi). Ghi kèm "Đăng ký lần đầu …; thay đổi lần thứ … ngày …" | như trên |
| Tình trạng hoạt động | CODE | Lượt LB của **tra cứu ĐKDN / thuế** (GCN không ghi tình trạng) | Ưu tiên nguồn: tra cứu → KH → thực địa → nội bộ. Khác "đang hoạt động" → in **đỏ đậm** và là tiêu chí Bad corp. Không có tra cứu → "Chưa có kết quả tra cứu" | `legal_basic_extraction.json` (`operating_status`) |
| 1b — Tên thành viên góp vốn / ban lãnh đạo | CODE | Lượt SH (thành viên), LR (NĐDPL), SH-`people` (ban lãnh đạo trong báo cáo thực địa) | Thứ tự dòng: thành viên góp vốn (tỷ lệ giảm dần) → NĐDPL không góp vốn → người chỉ có trong báo cáo thực địa. Người đứng ra vay có **(\*)** | `shareholders_extraction.json`, `legal_rep_extraction.json` |
| 1b — Tỷ lệ vốn góp (%) | CODE | Lượt SH | Văn bản ưu tiên: **Sổ cổ đông → ĐKKD → Tra cứu ĐKDN → Điều lệ → QĐ bổ nhiệm → HĐ chuyển nhượng**; văn bản mới hơn có tỷ lệ thì thay. TNHH MTV / DNTN có một chủ sở hữu → 100%. Thành viên chưa rõ tỷ lệ → "—"; người không góp vốn → "0". LLM không được tự chia vốn góp / vốn điều lệ | `shareholders_extraction.json` (`members`) |
| 1b — Chức vụ, Mối quan hệ, Mức độ ảnh hưởng, Đánh giá năng lực | CODE (chép) | **Báo cáo khảo sát thực địa** (lượt SH, mục `people`) | Chép đúng ý báo cáo; quan hệ đổi sang "… KH vay" (báo cáo không ghi → code suy từ quan hệ giữa các thành viên trong hồ sơ). Không có → "—". Chức vụ: báo cáo thực địa → chức danh NĐDPL (lượt LR, thêm "kiêm người đại diện theo pháp luật") → "Thành viên góp vốn" | `shareholders_extraction.json` (`people`) |
| Người đứng ra vay (\*) | CODE | `BORROWER_NAMES` (notebook) → nếu trống: "Đại diện KH" trong báo cáo thực địa → tên trong hồ sơ vay vốn / tờ trình | `src/agents/calculator/borrowers.py` | `corp_income.json` → `meta.borrower_names` |
| Cảnh báo pháp lý | CODE | Lượt LB, SH, LR, LI | Chỉ hiện khi có: chưa xác định KH vay; **không khớp giữa các nguồn** (MST, tên, địa chỉ TSC, NĐDPL, ngày thành lập — kèm văn bản khác nhau); tình trạng không hoạt động / chưa tra cứu; tỷ lệ góp vốn ≠ 100% / thiếu / tổng vốn lệch; mọi cảnh báo mức "alert" khác của mục 1–3 (nợ thuế, BHXH, tranh chấp, thay đổi 12 tháng…) | `corp_income.json` → `items.1/2/3.findings` |

---

## 2. Hoạt động kinh doanh

| Ô | Ai | Hồ sơ nguồn | Luật (khung trong `corp-income-cell-specs.md`) | Đối chiếu |
|---|---|---|---|---|
| Sản phẩm / dịch vụ | **LLM** | Báo cáo thực địa (ưu tiên) → loại hình trong lượt LB; tên ngành do **LLM chọn trong danh sách ngành TCB** ở lượt BM, code tra bảng `bang-nganh-tcb.csv` | 3 dòng: **Loại hình** (đa loại hình → loại có tỷ trọng lớn nhất; không có → "Đề nghị người dùng đánh giá bổ sung") · **Tên ngành** (đúng tên ngành TCB; chưa có → tên như hồ sơ + "(chưa đối chiếu bảng ngành TCB)") · **Diễn giải chi tiết** (bắt đầu đúng bằng câu "sản phẩm/dịch vụ" của báo cáo thực địa) | `business_model_extraction.json`, `corp_income.json` → `business_model.industry` |
| Địa chỉ — TSC | **LLM** | Báo cáo thực địa (ưu tiên) → địa chỉ TSC trên ĐKKD (code gửi kèm); đi thuê / sở hữu từ hợp đồng thuê, GCN QSDĐ (chỉ qua trích đoạn) | Địa chỉ + "(đi thuê / thuộc sở hữu của thành viên góp vốn / thuộc sở hữu của DN / chưa xác định)". Không ghi cảnh báo ở ô này | `ocr/` của báo cáo thực địa, hợp đồng thuê |
| Địa chỉ — Nhà xưởng, Kho hàng | **LLM** | Như TSC | Hồ sơ không có → LLM ghi "—" và code **ẩn dòng** | như trên |
| Mô hình hoạt động kinh doanh (sơ đồ) | CODE (vẽ) | Lượt BM | Nguồn ưu tiên: **báo cáo thực địa → hợp đồng / hóa đơn đầu vào, đầu ra → sổ chi tiết TK 131/331 → sao kê → dữ liệu nội bộ**. Tối đa 5 đối tác mỗi bên, xếp theo giá trị; tỷ trọng = giá trị đối tác / tổng các đối tác nhận diện được; nhà cung cấp bên trái, khách hàng bên phải; không bịa đối tác | `business_model_extraction.json`, `corp_income.json` → `business_model.suppliers/customers` |
| Cảnh báo HĐKD | **LLM** | Báo cáo thực địa, OCR ảnh thực địa, hợp đồng / hóa đơn đầu ra, dữ liệu thẩm định nội bộ, đối tác của sơ đồ, địa chỉ TSC trên ĐKKD | Chỉ liệt kê cảnh báo (mỗi dòng < 25 từ, "A ≠ B — đề nghị người dùng đánh giá lại"): báo cáo thực địa thiếu loại hình / ngành; không có địa chỉ nào; TSC trên ĐKKD ≠ ảnh; ảnh thiếu biển hiệu / không người làm / không phù hợp ngành; sản phẩm trên hợp đồng, hóa đơn đầu ra ≠ báo cáo thực địa; ngành theo thẩm định nội bộ ≠ báo cáo thực địa → "reflag rủi ro cao"; đối tác cùng NĐDPL / cùng địa chỉ TSC → "cảnh báo mua đi bán lại". **Không lặp** cảnh báo đã có ở 1b. Không có → code ẩn dòng | `ocr/`, trích đoạn hồ sơ |

---

## 3. Tài chính (đơn vị trên báo cáo: triệu đồng)

| Ô | Ai | Hồ sơ nguồn | Luật | Đối chiếu |
|---|---|---|---|---|
| Nguồn | CODE | Lượt FI | "BCTC kiểm toán năm …" / "BCTC thuế năm …" (không ghi tên file) | `financial_extraction.json` (`audited`, `periods`) |
| Số liệu từng năm (mọi bảng 3a, 3b, 5a) | CODE | Lượt FI (LLM chép số **đúng như in** + đơn vị; code quy đổi) | Năm N-1 = năm gần nhất có BCTC đủ năm; N-2 = năm trước đó. Cùng một năm có nhiều BCTC: **kiểm toán thắng thuế**; cùng hạng → file đầu tiên in số đó. TT133 → code tự suy TSNH / TSDH / nợ NH (Nguyên tắc 1) | `financial_extraction.json`, `corp_income.json` → `financials.years` (`_source` = file của từng số) |
| 3a — Các dòng tài sản, % Tỷ trọng | CODE | Lượt FI (bảng CĐKT) | Tổng tài sản + các khoản mục **≥ 20% tổng TS** ở một trong hai năm; mỗi năm một cột % = khoản mục / tổng TS; dòng cuối Hệ số TT hiện hành = TSNH / Nợ NH | như trên |
| 3a — Nhận xét | CODE | Lượt FI | (1) HSTT năm N-1: < 1 rủi ro mất khả năng thanh toán; 1–3 an toàn; > 3 vốn NH chưa hiệu quả. (2) ⚠ dấu hiệu bất thường của CĐKT: kiểm toán thuộc danh sách loại trừ (`danh-sach-kiem-toan-loai-tru.txt`), Tổng TS ≠ Tổng NV, cuối kỳ năm trước ≠ đầu kỳ năm sau, LNST chưa phân phối tăng > LNST trong kỳ | `corp_income.json` → `financials.bs_warnings` |
| 3b — DTT, LNST, ROS, Tăng/giảm | CODE | Lượt FI | Tăng/giảm = năm sau / năm trước − 1 (không so năm đủ 12 tháng với năm đầu thành lập); ROS = LNST / DTT | `financials.ratios` |
| 3b — Nhận xét | CODE | Lượt FI, **VAT**, CIC, bảng ngành TCB | Theo thứ tự: doanh thu theo tờ khai VAT các tháng năm N (so BQ tháng năm N-1); phân khúc theo DTT (MSME < 80 tỷ, SME < 200, USME < 600, MM < 2.000, LC); **chất lượng lợi nhuận = (LN khác + DT tài chính) / LNTT** (< 25% tốt; 25–< 50% trung bình; ≥ 50% kém; < 0 không nhận xét); ROS so với ROS ngành TCB; ⚠ DTT lệch VAT cùng kỳ > 20%, thuế TNDN / LNTT ≠ 20% (±2 điểm), DTT − giá vốn ≠ LN gộp (nghi đọc sai); ⚠ chi phí lãi vay / dư nợ BQ 12 tháng CIC ngoài 6–14%/năm; chi phí lãi vay / LN gộp > 50% | `financials.vat`, `financials.pl_warnings`, `financials.status_remarks` |
| Nhóm tài chính (không in, dùng phân nhóm) | CODE | Lượt FI, VAT | **Bad finance**: có dấu hiệu bất thường trọng yếu (4 dấu hiệu ở 3a). **Good finance**: năm N-1 biến động DT > 0%, ROS > 0, HSTT ≥ 1. Còn lại Normal | `corp_income.json` → `financials.group`, `group_reason` |

---

## 4. Dư nợ tại TCTD

| Ô | Ai | Hồ sơ nguồn | Luật | Đối chiếu |
|---|---|---|---|---|
| Bảng dư nợ theo TCTD | CODE | Lượt CIC: **S10A** (dư nợ từng dòng), **R20** (TSBĐ) | Chỉ nhận bản tin tra cứu trong **31 ngày** đến ngày phân tích (cũ hơn → cảnh báo lấy lại). Cộng theo TCTD: ngắn hạn, dài hạn, cho thuê TC, tổng, %, BQ 12 tháng, cam kết ngoại bảng, TSBĐ. Tên ngân hàng rút gọn theo `bang-viet-tat-ngan-hang.txt` (tên lạ → giữ như CIC ghi) | `cic_extraction.json`, `corp_income.json` → `cic.lenders` |
| Biểu đồ dư nợ | CODE | S10A — diễn biến dư nợ 12 tháng | Đường dư nợ theo tháng + đường BQ 12 tháng | `cic.monthly`, `cic.avg_balance_12m` |
| Nợ cần chú ý / Nợ xấu | CODE | S10A phần 2.9 (12 tháng) / 2.7 (5 năm) | Liệt kê khoản, TCTD, ngày; không có → ghi không có | `cic.special_mention`, `cic.bad_debt` |
| Nhóm bureau (không in, dùng phân nhóm) | CODE | CIC + DTT năm N-1 + loại hình | **Bad bureau**: nợ xấu trong 24 tháng hoặc nợ cần chú ý trong 12 tháng. **Good bureau**: không nợ xấu 5 năm, không chậm thanh toán thẻ 3 năm, dư nợ BQ 12 tháng / DT BQ tháng ≤ 6 (thương mại, dịch vụ khác, chưa rõ) hoặc ≤ 9 (sản xuất, xây lắp). Còn lại Normal | `cic.group`, `cic.group_reason` |

---

## 5. Kết luận nguồn thu doanh nghiệp

| Ô | Ai | Hồ sơ nguồn | Luật | Đối chiếu |
|---|---|---|---|---|
| 5a — Dự phóng (chỉ khi có PAKD) | CODE | Lượt PL (PAKD), FI, bảng ngành TCB | TH = BCTC N-1; KH = PAKD; Tăng/giảm = KH / TH − 1. ROS / tăng trưởng "theo am hiểu ngành TCB" = bảng ngành theo phân khúc; "theo dự phóng" = LNST KH / DTT KH và DTT KH / DTT TH − 1; Lệch = theo dự phóng − theo ngành. Không có PAKD → câu "KH không cung cấp phương án kinh doanh" | `plan_extraction.json`, `corp_income.json` → `income_estimate.projection` |
| Phân nhóm DN (không in thành bảng; quyết định 5b) | CODE | Kết quả mục 1, 2, 3, 4 | [17/11] **Bad corp** (≥ 1): DN không hoạt động theo tra cứu thuế hoặc thẩm định thực tế; **MST không đồng nhất giữa các chứng từ**; thành lập < 12 tháng (từ ngày đăng ký lần đầu); Bad finance; Bad bureau. **Good corp**: Good finance + Good bureau + không Bad. Còn lại Normal | `corp_income.json` → `corp_group` (`group`, `bad_reasons`, `finance`, `bureau`) |
| 5b — Đề xuất (KetLuanNguonThuDoanhNghiep) | **LLM** (quyết định bị code ép theo nhóm) | Toàn bộ gói dữ liệu, `credit_assessment` | Khung: **Đề xuất** (Bad → Không sử dụng; Normal → tối đa Sử dụng có điều kiện; Good và không còn rủi ro trung bình trở lên → Sử dụng) · **Lý do** ≤ 3 dòng có số (pháp lý, tài chính, tín dụng, PAKD) · **Điều kiện** (khi có điều kiện) · **Hồ sơ cần bổ sung**. Không nhắc lại công thức | `credit_assessment.quyet_dinh`, `rui_ro`; `meta.writer_error` ghi khi code ép quyết định |
| 5b — Giá trị nguồn thu (KetLuan) | CODE | FI, PL, ngành TCB, tỷ lệ góp vốn của KH vay (1b), `ANNUAL_LT_PRINCIPAL` (notebook) | Bad corp → không sử dụng + lý do. Không PAKD: **LNST hợp lý = LNST N-1 − DT tài chính − Thu nhập khác**. Có PAKD (và có ngành TCB, không Bad): DT khả thi = min[DT PAKD; max[DT thực tế năm kế hoạch theo VAT; DT N × (1 + tăng trưởng ngành × 1,5 nếu Good corp, × 1 nếu không)]]; ROS khả thi = min{ROS PAKD; max[ROS N; ROS ngành]}; LNST = ROS × DT. **LNST trả nợ TDH** = gốc TDH hằng năm − khấu hao (= 0 nếu thiếu một trong hai). **Giá trị** = (LNST hợp lý − LNST trả nợ TDH) × tỷ lệ góp vốn của KH vay | `corp_income.json` → `income_estimate` (`missing` = thành phần thiếu) |

---

## 6. Các file trong thư mục kết quả của một case

| File | Nội dung |
|---|---|
| `final_response_<case>.pdf / .md` | Báo cáo |
| `ocr/<file>.txt` | Chữ đọc được của từng hồ sơ (kiểm tra OCR đọc đúng chưa) |
| `<pass>_extraction.json` | Thông tin LLM chép ra từ từng hồ sơ, theo lượt |
| `corp_income.json` | Mọi kết quả code: `items` (kiểm tra pháp lý + căn cứ), `financials`, `cic`, `corp_group`, `income_estimate`, `credit_assessment`, `business_model`, `meta` |
| `corp_income.xlsx` | Như trên dạng bảng, **có cột "Nguồn" (file) cho từng giá trị**: Tóm tắt, 1. Pháp lý cơ bản, 2. Cổ đông, 3. Người đại diện, 4. Nợ thuế - tranh chấp, 5. Tài chính, Mô hình HĐKD, Kiểm tra (mọi cảnh báo + căn cứ), Hồ sơ (mỗi file: loại, thư mục, đọc bằng gì) |
| `result.json` | Phân loại hồ sơ, lỗi đọc file / lỗi trích xuất từng lượt |

**Cách kiểm định nhanh một số trên báo cáo:** số trong báo cáo → `corp_income.json` (`financials.years.<năm>._source`
cho biết file) → `financial_extraction.json` của file đó (số LLM chép) → `ocr/<file>.txt` (số in trên hồ sơ).
Sai ở bước OCR → chất lượng scan; sai ở bước chép → prompt trích xuất; sai ở bước tính → code (`calculator/`).
