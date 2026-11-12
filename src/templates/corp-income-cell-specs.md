<!--
Khung viết cho từng ô do LLM viết (report writer). Sửa file này để đổi cách viết,
không cần sửa code.

Cách dùng: mỗi ô là một mục "## TenO" (đúng tên biến trong template, không có {{ }}).
Nội dung bên dưới là khung LLM PHẢI theo — thứ tự các phần, số câu, cách mở đầu.
Ô không có mục ở đây thì LLM viết theo quy tắc chung (config/prompts/report_writer.md).
Ghi chú trong khối này không gửi cho LLM.

[12/11] Khớp với corp-income-guidance.md (Instruction final) và corp-income-structure.md:
6 ô LLM viết = SanPhamDichVu (2a), TruSoChinh / NhaXuong / KhoHang / NhanXetHDKD (2b),
KetLuanNguonThuDoanhNghiep (5b). Mọi ô khác do code điền.
-->

## SanPhamDichVu
Đúng 3 dòng ngắn nối bằng "<br>", KHÔNG ghi nguồn / tên file:
Loại hình: <sản xuất / thương mại / dịch vụ>
Tên ngành: <tên theo "nganh_tcb">
Diễn giải chi tiết: <sản phẩm / dịch vụ chính, quy mô — dưới 25 từ>
- Loại hình: ưu tiên báo cáo khảo sát thực địa (ĐVKD phỏng vấn KH), rồi "loai_hinh_kinh_doanh". Đa loại hình: ghi loại
  hình có tỷ trọng lớn nhất kèm tỷ trọng / giá trị. Không có thông tin: ghi "Đề nghị người dùng đánh giá bổ sung".
- Tên ngành: dùng đúng tên trong "nganh_tcb". Chưa có "nganh_tcb": ghi tên ngành như hồ sơ + "(chưa đối chiếu bảng ngành TCB)".
- Diễn giải chi tiết: có "san_pham_dich_vu_bao_cao_thuc_dia" thì bắt đầu ĐÚNG bằng câu đó (báo cáo thực địa được ưu tiên);
  báo cáo thực địa không có thông tin thì ghi "—".

## TruSoChinh
Địa chỉ trụ sở chính + "(đi thuê / thuộc sở hữu của thành viên góp vốn / thuộc sở hữu của doanh nghiệp / chưa xác định)".
- Ưu tiên địa chỉ trong báo cáo khảo sát thực địa; không có thì dùng "dia_chi_tsc_tren_dkkd".
- Đi thuê hay sở hữu: đọc hợp đồng thuê, GCN QSDĐ nếu có; không có tài liệu thì ghi "chưa xác định".
- Không ghi cảnh báo trong ô này (cảnh báo địa chỉ thuộc ô NhanXetHDKD). Không có địa chỉ nào: "Chưa có thông tin trong hồ sơ".

## NhaXuong
Địa chỉ nhà xưởng + "(đi thuê / thuộc sở hữu của thành viên góp vốn / thuộc sở hữu của doanh nghiệp / chưa xác định)",
ưu tiên báo cáo khảo sát thực địa. Hồ sơ không có nhà xưởng thì ghi đúng "—" (hệ thống tự ẩn dòng).

## KhoHang
Địa chỉ kho hàng + "(đi thuê / thuộc sở hữu của thành viên góp vốn / thuộc sở hữu của doanh nghiệp / chưa xác định)",
ưu tiên báo cáo khảo sát thực địa. Hồ sơ không có kho hàng thì ghi đúng "—" (hệ thống tự ẩn dòng).

## NhanXetHDKD
Dòng "Cảnh báo HĐKD" dưới bảng mục 2 — CHỈ liệt kê cảnh báo, mỗi cảnh báo một gạch đầu dòng ngắn (dưới 25 từ),
không ghi tên file / thư mục / nguồn; chỗ không tương đồng ghi "<A> ≠ <B>" và kết thúc bằng "— đề nghị người dùng đánh giá lại":
- báo cáo thực địa thiếu loại hình hoặc ngành nghề;
- không có địa chỉ nào trong 3 địa chỉ (TSC, nhà xưởng, kho hàng);
- địa chỉ TSC trên ĐKKD ("dia_chi_tsc_tren_dkkd") ≠ địa chỉ đọc được trên ảnh thực địa;
- ảnh thực địa: thiếu biển hiệu hoặc biển hiệu không có tên DN; không có người làm việc; số người làm việc / máy móc không
  phù hợp ngành nghề và loại hình; chữ đọc được trên ảnh (biển hiệu, nhãn hàng) ≠ sản phẩm / dịch vụ trong báo cáo thực địa
  (ảnh chỉ có văn phòng / địa điểm, không có sản phẩm → bỏ qua đối chiếu này);
- sản phẩm / dịch vụ đầu ra trên hợp đồng kinh tế, hóa đơn đầu ra ≠ báo cáo thực địa (hợp đồng nguyên tắc không xác định
  sản phẩm → bỏ qua);
- ngành nghề theo dữ liệu thẩm định KHDN nội bộ TCB ≠ báo cáo thực địa → ghi thêm "reflag rủi ro cao";
- đối tác trong "mo_hinh_hdkd" không khớp báo cáo thực địa; đối tác chính cùng NĐDPL hoặc cùng địa chỉ TSC với DN →
  "cảnh báo mua đi bán lại, đề nghị người dùng đánh giá".
KHÔNG lặp lại cảnh báo đã có trong ô CanhBaoPhapLy (mục 1b, xem "gia_tri_da_dien"), nhất là các chỗ không khớp giữa
nguồn (tên, MST, ngày thành lập, người đại diện…). Không có cảnh báo nào thì ghi đúng "—" (hệ thống tự ẩn dòng).

## KetLuanNguonThuDoanhNghiep
NGẮN GỌN — tối đa ~90 từ, KHÔNG ghi nguồn / tên file. Dùng đúng "quyet_dinh" của "danh_gia_tin_dung" và nhóm trong
"phan_nhom_doanh_nghiep" (KHÔNG tự phân nhóm lại): Bad corp → Không sử dụng (không dự phóng); Normal corp → tối đa
Sử dụng có điều kiện; Good corp và không còn rủi ro trung bình trở lên → Sử dụng. Viết đúng khung, bỏ phần không có nội dung:
**Đề xuất: <Sử dụng / Sử dụng có điều kiện / Không sử dụng> nguồn thu doanh nghiệp để đánh giá năng lực trả nợ lần này.**
**Lý do:** tối đa 3 gạch đầu dòng, mỗi dòng dưới 20 từ, có số liệu — nêu cơ sở pháp lý, tài chính, tín dụng (và PAKD có
cơ sở hay không, nếu có PAKD). Bad corp: nêu đúng tiêu chí trong "phan_nhom_doanh_nghiep" (DN không hoạt động theo tra cứu
thuế; thành lập < 12 tháng tính từ ngày đăng ký lần đầu; ngành nghề thực tế không phù hợp chứng từ; DN không hoạt động theo
thẩm định thực tế; Bad finance; Bad bureau).
**Điều kiện:** (chỉ khi "Sử dụng có điều kiện") tối đa 2 gạch đầu dòng — việc phải hoàn tất trước giải ngân.
**Hồ sơ cần bổ sung:** (chỉ khi thiếu tài liệu quan trọng) tối đa 2 gạch đầu dòng, cụ thể, làm được ngay.
Không nhắc lại công thức / giá trị thu nhập — hệ thống in ngay bên dưới.
