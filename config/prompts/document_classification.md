---
name: document_classification
description: Classify an uploaded document against the document-type catalogue
---
You classify extracted text from a CORPORATE (KHDN) loan dossier: legal papers,
tax and social-insurance notices, penalty and court papers, the bank's own
lookups and site-visit reports.

Pick the ONE document type from the catalogue below that best describes this
document. Answer with its exact id string (the value in quotes).

Document type catalogue:
{{document_type_catalogue}}

Rules:
- Judge what the document *is*, not what it mentions. A charter (điều lệ) that
  lists the members is still a charter, not a shareholder register.
- Use the group headings as context: they say what kind of file each type is.
- If the document genuinely matches none of the types, return "" for
  document_type. Do not force a bad match — an unmatched document is kept as
  general context, whereas a wrong type runs the wrong extraction on it.
- Do not invent ids. Only ids listed above are valid.

"description" names this document for a reader of the finished credit memo, who
sees the filename and nothing else:
- Vietnamese, ONE line, AT MOST 20 WORDS. A longer one is dropped and replaced
  by the document type's own name, so the words have to earn their place.
- Say what the document IS, then whichever of these the text actually shows:
  number, counterparty, signing date, period covered.
- Never guess. A detail that is not on the page is left out, not inferred from
  the filename or the type.

- Good: "GCN ĐKDN Công ty TNHH ABC, MST 0101234567, đăng ký thay đổi lần 6 ngày 20/03/2026"
- Good: "Thông báo tiền thuế nợ của Chi cục Thuế Đống Đa, tại ngày 30/09/2026"
- Too long: "Giấy chứng nhận đăng ký doanh nghiệp công ty trách nhiệm hữu hạn hai thành
  viên trở lên do Sở Kế hoạch và Đầu tư Hà Nội cấp lần đầu ngày 12/05/2015 và
  thay đổi lần thứ sáu"

Return JSON only with:
{
  "document_type": "...",
  "reasoning": "short reason",
  "description": "...",
  "confidence": 0.0
}
