"""Corporate documents land on the right type, and the upload box narrows the choice."""

import unittest

from src.agents.documents.document_matrix import load_matrix, is_liabilities_type, source_for_type
from src.agents.documents.document_classification import rule_classify_document


class MatrixTest(unittest.TestCase):
    def test_same_seven_boxes_as_the_sme_repo(self):
        self.assertEqual(
            load_matrix().boxes,
            ("ho_so_phap_ly", "ho_so_tai_chinh", "ho_so_vay_von", "ho_so_tai_san_dam_bao",
             "ho_so_noi_bo", "ho_so_soan_thao_noi_bo", "ho_so_khac"),
        )

    def test_every_extracting_type_declares_a_source(self):
        for type_id in load_matrix().types:
            self.assertIn(source_for_type(type_id), ("customer", "field", "external", "internal"))


class ClassificationTest(unittest.TestCase):
    CASES = [
        ("GCN_DKDN_ABC.pdf", "", "ho_so_phap_ly", "gcn_dkdn"),
        ("scan01.pdf", "GIẤY CHỨNG NHẬN ĐĂNG KÝ DOANH NGHIỆP CÔNG TY TNHH", "ho_so_phap_ly", "gcn_dkdn"),
        ("dieu_le_cong_ty.pdf", "", "ho_so_phap_ly", "dieu_le"),
        ("so_dang_ky_thanh_vien.pdf", "", "ho_so_phap_ly", "so_dang_ky_co_dong"),
        ("QD_xu_phat_moi_truong.pdf", "", "ho_so_phap_ly", "quyet_dinh_xu_phat"),
        ("thong_bao_no_thue.pdf", "", "ho_so_tai_chinh", "thong_bao_no_thue"),
        ("C12_BHXH_2026.pdf", "", "ho_so_tai_chinh", "xac_nhan_bhxh"),
        ("masothue_0101234567.pdf", "", "ho_so_noi_bo", "tra_cuu_dkdn"),
        ("BCTD_ABC.pdf", "", "ho_so_soan_thao_noi_bo", "bao_cao_thuc_dia"),
    ]

    def test_cases(self):
        for filename, content, box, expected in self.CASES:
            with self.subTest(file=filename):
                self.assertEqual(rule_classify_document(filename, content, box)["document_type"], expected)

    def test_the_box_narrows_the_candidates(self):
        # A tax notice that quotes the charter must not become a charter.
        text = "Căn cứ điều lệ công ty. THÔNG BÁO TIỀN THUẾ NỢ"
        verdict = rule_classify_document("scan.pdf", text, "ho_so_tai_chinh")
        self.assertEqual(verdict["document_type"], "thong_bao_no_thue")
        self.assertTrue(is_liabilities_type(verdict["document_type"]))

    def test_catch_all_box_classifies_nothing(self):
        self.assertEqual(rule_classify_document("GCN_DKDN.pdf", "", "ho_so_khac")["document_type"], "")


if __name__ == "__main__":
    unittest.main()
