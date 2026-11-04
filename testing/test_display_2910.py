"""[Sửa 29/10] Fine-tune of the final output: 1a, 1b, 2b, 3a, 3b, 4a."""

import unittest

from src.agents.calculator import cic_metrics, legal_checks
from src.agents.calculator import financial_metrics as fm
from src.utils.report.appendix_context import debt_table, drop_repeated_warnings
from testing.test_brd_2710 import AS_OF, M, Y2024, Y2025, fin


def legal(*rows):
    return [{"pass": "legal_basic", "source": "customer", "document": f"doc{i}.pdf", "document_type": "gcn_dkdn",
             "data": data} for i, data in enumerate(rows)]


def codes(records):
    return {f["code"] for f in legal_checks.run_all_checks(records, AS_OF)[1]["findings"]}


class LegalTest(unittest.TestCase):
    def test_company_abbreviations_are_not_a_mismatch(self):
        for a, b in (("Công ty TNHH Đức Phúc", "CT TNHH Đức Phúc"),
                     ("Công ty Cổ phần Đức Phúc", "CTCP Đức Phúc"),
                     ("CÔNG TY CP ĐỨC PHÚC", "Cty CP Đức Phúc")):
            self.assertNotIn("name_mismatch", codes(legal({"company_name": a}, {"company_name": b})), (a, b))
        self.assertIn("name_mismatch", codes(legal({"company_name": "CTCP Đức Phúc"},
                                                   {"company_name": "CTCP Việt Phúc"})))

    def test_year_only_matches_a_full_date_of_that_year(self):
        found = lambda a, b: "establishment_mismatch" in codes(
            legal({"establishment_date": a}, {"establishment_date": b}))
        self.assertFalse(found("2025", "06/02/2025"))
        self.assertTrue(found("2024", "06/02/2025"))
        self.assertTrue(found("05/02/2025", "06/02/2025"))       # both full dates → compared in full
        self.assertFalse(found("06/02/2025", "2025-02-06"))


class RepeatTest(unittest.TestCase):
    def test_2b_drops_mismatches_already_in_1b(self):
        legal_text = ("**Cảnh báo pháp lý:**\n\n- Địa chỉ trụ sở chính ghi khác nhau giữa các nguồn: A (ĐKKD) ≠ B")
        hdkd = "- Địa chỉ báo cáo thực địa ≠ ĐKKD<br>- Ảnh thực địa không có biển hiệu"
        self.assertEqual(drop_repeated_warnings(hdkd, legal_text), "- Ảnh thực địa không có biển hiệu")
        self.assertEqual(drop_repeated_warnings("- Địa chỉ báo cáo thực địa ≠ ĐKKD", legal_text), "—")
        self.assertEqual(drop_repeated_warnings(hdkd, ""), hdkd)


class FinanceTest(unittest.TestCase):
    def test_ros_positive_means_efficient(self):
        f = fm.compute([fin([Y2025, Y2024])], AS_OF)
        self.assertTrue(any("> 0 — KH là doanh nghiệp có hoạt động kinh doanh hiệu quả" in r
                            for r in f["status_remarks"]))


class CicTest(unittest.TestCase):
    def cic(self, **data):
        base = {"report_type": "S10A", "query_date": "20/10/2026",
                "lenders": [{"name": "Vietcombank", "short_term": 20 * M}], "collaterals": [{"name": "Nhà"}],
                "monthly_balances_12m": []}
        return {"pass": "cic", "document": "CIC.pdf", "data": {**base, **data}}

    def test_one_validity_line(self):
        old = [self.cic(query_date="01/08/2026"), self.cic(query_date="01/08/2026")]   # two prints
        table = debt_table(cic_metrics.compute(old, AS_OF, revenue_prev_year=900 * M))
        self.assertEqual(table.count("CIC chưa hợp lệ"), 1)
        self.assertEqual(table.count("quá 1 tháng"), 1)
        self.assertNotIn("Bản tin: ", table)
        ok = debt_table(cic_metrics.compute([self.cic()], AS_OF, revenue_prev_year=900 * M))
        self.assertIn("Bản tin CIC hợp lệ (S10A: 20/10/2026) — tra cứu trong vòng 1 tháng", ok)

    def test_no_debt_is_good_bureau(self):
        for lenders in ([], [{"name": "Vietcombank", "short_term": 0}]):
            r = cic_metrics.compute([self.cic(lenders=lenders)], AS_OF, revenue_prev_year=None)
            self.assertEqual(r["group"], "Good bureau", lenders)
            self.assertEqual(r["avg_balance_12m"], 0)
        with_debt = cic_metrics.compute([self.cic()], AS_OF, revenue_prev_year=900 * M)
        self.assertEqual(with_debt["group"], "Normal bureau")              # no monthly balances → unchanged

    def test_bad_debt_still_wins(self):
        r = cic_metrics.compute([self.cic(lenders=[], bad_debt_5y=[{"date": "01/2026", "lender": "X"}])], AS_OF, None)
        self.assertEqual(r["group"], "Bad bureau")


class Guidance0511Test(unittest.TestCase):
    def test_excluded_auditor_is_bad_finance(self):
        record = fin([Y2025, Y2024])
        record["data"]["audited"], record["data"]["auditor_name"] = True, "Công ty TNHH Kiểm toán và Tư vấn Bình An"
        f = fm.compute([record], AS_OF)
        self.assertEqual(f["group"], "Bad finance")
        self.assertTrue(any("Bình An" in w for w in f["material_warnings"]))

    def test_msme_uses_sme_industry_rows(self):
        from src.agents.calculator import industry
        row = industry.lookup("Dịch vụ Y tế và hoạt động hỗ trợ y tế", "MSME")
        self.assertEqual(row["segment"], "SME")


class Data0511Test(unittest.TestCase):
    def test_bank_short_names(self):
        from src.agents.calculator.banks import short_name
        cases = {"NGÂN HÀNG TMCP NGOẠI THƯƠNG VIỆT NAM - CN HÀ NỘI": "Vietcombank",
                 "Ngân hàng Thương mại cổ phần Sài Gòn Thương Tín": "Sacombank",
                 "Ngân hàng TMCP Sài Gòn": "SCB", "Ngân hàng TMCP Sài Gòn - Hà Nội": "SHB",
                 "NH TMCP Kỹ thương VN": "Techcombank", "MB CN Ba Đình": "MB",
                 "Ngân hàng Viet Capital Bank": "BVBank", "Quỹ tín dụng ABC": "Quỹ tín dụng ABC"}
        for name, short in cases.items():
            self.assertEqual(short_name(name), short, name)

    def test_branches_of_one_bank_are_one_column(self):
        data = {"report_type": "S10A", "query_date": "20/10/2026", "monthly_balances_12m": [], "lenders": [
            {"name": "Ngân hàng TMCP Ngoại thương Việt Nam - CN Hà Nội", "short_term": 10 * M},
            {"name": "Vietcombank CN Thăng Long", "short_term": 5 * M}]}
        r = cic_metrics.compute([{"pass": "cic", "document": "CIC.pdf", "data": data}], AS_OF, 900 * M)
        self.assertEqual([(l["name"], l["short_term"]) for l in r["lenders"]], [("Vietcombank", 15 * M)])

    def test_allocation_table(self):
        from src.agents.calculator import industry
        row = industry.allocation("Thủy sản xuất khẩu (Tôm, Cá)")      # spaces differ from the table
        self.assertEqual(row["ranges"]["inventory"], (0.25, 0.55))
        self.assertEqual(len(industry.allocations()), 17)


class Template0511Test(unittest.TestCase):
    def fin(self, **fields):
        f = fm.compute([fin([Y2025, Y2024])], AS_OF)
        f["years"][f["latest_year"]].update(fields)
        return f

    def test_current_ratio_bands(self):
        f = fm.compute([fin([Y2025, Y2024])], AS_OF)
        for ratio, text in ((0.8, "rủi ro mất khả năng thanh toán"), (2.0, "mức an toàn"), (3.5, "chưa hiệu quả")):
            f["ratios"][f["latest_year"]]["current_ratio"] = ratio
            self.assertIn(text, fm.current_ratio_remark(f))

    def test_industry_fit_two_of_four(self):
        from src.agents.calculator import industry
        trade = industry.allocation("Bán lẻ & Thương mại")    # Tiền 15–25, ĐTTC 5–15, Phải thu 5–10, HTK 35–50
        fit = self.fin(current_assets=100, cash=20, short_term_investments=10, receivables=30, inventory=40)
        self.assertIn("phù hợp với ngành nghề (Bán lẻ & Thương mại): 3/4", fm.industry_fit_remark(fit, trade))
        off = self.fin(current_assets=100, cash=60, short_term_investments=0, receivables=30, inventory=10)
        self.assertIn("chưa phù hợp", fm.industry_fit_remark(off, trade))
        self.assertEqual(fm.industry_fit_remark(fit, None), "")

    def test_earnings_quality_and_ros_vs_industry(self):
        good = self.fin(gross_profit=90, profit_before_tax=100)
        self.assertIn("tốt đến từ hoạt động kinh doanh cốt lõi", fm.earnings_quality_remark(good))
        mid = self.fin(gross_profit=60, profit_before_tax=100)
        self.assertIn("trung bình", fm.earnings_quality_remark(mid))
        poor = self.fin(gross_profit=40, profit_before_tax=100)
        self.assertIn("kém", fm.earnings_quality_remark(poor))
        f = fm.compute([fin([Y2025, Y2024])], AS_OF)
        ros = f["ratios"][f["latest_year"]]["ros"]
        self.assertIn(" phù hợp", fm.ros_vs_industry_remark(f, ros - 0.01))
        self.assertIn("chưa phù hợp", fm.ros_vs_industry_remark(f, ros + 0.01))


class Fix0511Test(unittest.TestCase):
    def test_founding_counts_from_the_first_registration(self):
        from src.utils.report.appendix_context import first_registration
        records = [{"pass": "legal_basic", "document_type": "dieu_le", "data": {"establishment_date": "26/12/2025"}},
                   {"pass": "legal_basic", "document_type": "gcn_dkdn", "data": {"establishment_date": "26/12/2022"}}]
        self.assertEqual(f"{first_registration(records):%d/%m/%Y}", "26/12/2022")

    def test_chart_labels_every_month_in_million_without_paint_order(self):
        import base64, re
        from src.utils.report.visualization.debt_chart import debt_chart
        img = debt_chart([("09/2026", 105_300e6), ("10/2026", 96_215e6)], 64_273e6)
        svg = base64.b64decode(re.search(r"base64,([A-Za-z0-9+/=]+)", img).group(1)).decode("utf-8")
        self.assertIn(">105.300</text>", svg)
        self.assertIn(">96.215</text>", svg)
        self.assertIn("triệu đồng", svg)
        self.assertNotIn("paint-order", svg)          # WeasyPrint ignores it → white text over the digits


class TemplateTest(unittest.TestCase):
    def test_no_t24_row(self):
        with open("src/templates/corp-income-structure.md", encoding="utf-8") as handle:
            text = handle.read()
        self.assertNotIn("T24", text)


if __name__ == "__main__":
    unittest.main()
