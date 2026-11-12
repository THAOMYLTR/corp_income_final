"""[13/11] Bảng 1b (thành viên góp vốn) và tên viết tắt ngân hàng — lỗi gặp khi chạy nhiều case."""

import unittest

from src.agents.calculator import legal_checks
from src.agents.calculator import financial_metrics as fm
from src.agents.calculator.banks import short_name
from src.agents.calculator.legal_checks import is_title_not_name, parse_pct, same_person
from testing.test_brd_2710 import AS_OF, Y2025, fin

DIEU_LE_MEMBERS = [  # điều lệ 2016 — tỷ lệ in như văn bản, một số dạng chữ ("30%", "7,5%")
    ("Nguyễn Sỹ Quảng", "30%"), ("Sái Xuân Sinh", "7,5%"), ("Nguyễn Thị Tuyết Vân", 7.5),
    ("Phan Quang Điện", "1%"), ("Nguyễn Thị Pha", "22,5"), ("Nguyễn Thị Mỹ Bình", 25),
    ("Nguyễn Thị Thanh Hà", "6,5%"),
]


def records():
    def rec(pass_name, source, doc_type, data):
        return {"pass": pass_name, "source": source, "document": f"{doc_type}.pdf",
                "document_type": doc_type, "data": data}
    return [
        rec("legal_basic", "customer", "gcn_dkdn", {
            "company_name": "CÔNG TY CỔ PHẦN ABC",
            "legal_representatives": [{"name": "PHAN QUANG ĐIỀN", "title": "Giám đốc"}]}),
        # ĐKKD công ty cổ phần: LLM đưa người đại diện vào "members", không có tỷ lệ
        rec("shareholders", "customer", "gcn_dkdn", {"members": [
            {"name": "PHAN QUANG ĐIỀN", "ownership_pct": None},
            {"name": "Nguyễn Sỹ Quảng", "ownership_pct": None}]}),
        rec("shareholders", "customer", "dieu_le", {"members": [
            {"name": n, "member_type": "ca_nhan", "ownership_pct": p} for n, p in DIEU_LE_MEMBERS]}),
        # báo cáo thực địa: chức danh điền vào ô tên, họ đọc sai (PHẠM)
        rec("legal_rep", "field", "bao_cao_thuc_dia", {"legal_representatives": [
            {"name": "PHẠM QUANG ĐIỀN", "title": "Người đại diện theo pháp luật"},
            {"name": "Giám đốc", "title": "Giám đốc kiêm người đại diện theo pháp luật"}]}),
        rec("shareholders", "field", "bao_cao_thuc_dia", {"members": [], "people": [
            {"name": "Giám đốc", "position": "Giám đốc kiêm người đại diện theo pháp luật"},
            {"name": "Nguyễn Thị Pha", "position": "Thành viên góp vốn", "relation_to_borrower": "Vợ KH vay"}]}),
    ]


class Update1311Test(unittest.TestCase):
    def test_helpers(self):
        self.assertEqual(parse_pct("7,5%"), 7.5)
        self.assertEqual(parse_pct("30 %"), 30.0)
        self.assertEqual(parse_pct(25), 25.0)
        self.assertIsNone(parse_pct("chưa rõ"))
        self.assertTrue(is_title_not_name("Giám đốc"))
        self.assertTrue(is_title_not_name("Ông Giám Đốc"))
        self.assertFalse(is_title_not_name("Nguyễn Văn A"))
        self.assertTrue(same_person("PHAN QUANG ĐIỀN", "Phạm Quang Điện"))
        self.assertTrue(same_person("Ông Nguyễn Văn A", "NGUYỄN VĂN A"))
        self.assertFalse(same_person("Nguyễn Thị Pha", "Nguyễn Thị Hà"))      # một chữ, hai người
        self.assertFalse(same_person("Trần Văn Bình", "Trần Văn Minh"))

    def test_members_come_from_the_document_with_ratios(self):
        members = legal_checks.run_all_checks(records(), AS_OF)[2]["summary"]["members"]
        got = {m["name"]: m["ownership_pct"] for m in members}
        self.assertEqual(got, {"Nguyễn Sỹ Quảng": 30.0, "Sái Xuân Sinh": 7.5, "Nguyễn Thị Tuyết Vân": 7.5,
                               "Phan Quang Điện": 1.0, "Nguyễn Thị Pha": 22.5, "Nguyễn Thị Mỹ Bình": 25.0,
                               "Nguyễn Thị Thanh Hà": 6.5})

    def test_ratio_filled_from_another_document(self):
        recs = records()
        # ĐKKD có vốn góp cho 2/3 người → vẫn là văn bản chính; tỷ lệ còn thiếu lấy từ điều lệ
        recs[1]["data"]["members"][1]["capital_amount"] = 5
        recs[1]["data"]["members"].append({"name": "Nguyễn Văn X", "capital_amount": 5})
        recs[2]["data"]["members"] = [{"name": "Phan Quang Điện", "ownership_pct": "1%"}]
        members = legal_checks.run_all_checks(recs, AS_OF)[2]["summary"]["members"]
        self.assertEqual({m["name"]: m["ownership_pct"] for m in members}["PHAN QUANG ĐIỀN"], 1.0)

    def test_legal_reps_drop_titles_and_ocr_duplicates(self):
        reps = legal_checks.run_all_checks(records(), AS_OF)[3]["summary"]["legal_representatives"]
        self.assertEqual([r["name"] for r in reps], ["PHAN QUANG ĐIỀN"])

    def test_table_1b_rows(self):
        from src.utils.report.appendix_context import build_appendix_context
        recs = records()
        items = legal_checks.run_all_checks(recs, AS_OF)
        result = {"items": items, "meta": {"borrower_names": []}}
        ctx = build_appendix_context(result, recs, fm.compute([fin([Y2025])], AS_OF), AS_OF)
        rows = [r for r in ctx["RowsThanhVien"].splitlines() if r.startswith("|")]
        names = [r.split("|")[1].strip() for r in rows]
        self.assertEqual(len(rows), 7, ctx["RowsThanhVien"])                 # không có "Giám đốc", không trùng PHẠM
        self.assertNotIn("Giám đốc", names)
        pct = {r.split("|")[1].strip(): r.split("|")[2].strip() for r in rows}
        self.assertEqual(pct["Nguyễn Sỹ Quảng"], "30")
        self.assertEqual(pct["Sái Xuân Sinh"], "7,5")
        self.assertEqual(pct["Phan Quang Điện"], "1")
        self.assertIn("đại diện", rows[names.index("Phan Quang Điện")])      # khớp với người đại diện PL

    def test_unknown_member_ratio_is_a_dash_not_zero(self):
        from src.utils.report.appendix_context import build_appendix_context
        recs = records()[:2]                                                 # chỉ ĐKKD, không có tỷ lệ
        items = legal_checks.run_all_checks(recs, AS_OF)
        ctx = build_appendix_context({"items": items, "meta": {"borrower_names": []}}, recs,
                                     fm.compute([fin([Y2025])], AS_OF), AS_OF)
        row = next(r for r in ctx["RowsThanhVien"].splitlines() if "Nguyễn Sỹ Quảng" in r)
        self.assertEqual(row.split("|")[2].strip(), "—")

    def test_vpbank_word_order(self):
        self.assertEqual(short_name("Ngân hàng TMCP Việt Nam Thịnh Vượng - Chi nhánh Thăng Long"), "VPBank")
        self.assertEqual(short_name("NGÂN HÀNG TMCP THỊNH VƯỢNG VIỆT NAM"), "VPBank")
        self.assertEqual(short_name("Ngân hàng TMCP Thịnh vượng và Phát triển"), "PG Bank")


if __name__ == "__main__":
    unittest.main()
