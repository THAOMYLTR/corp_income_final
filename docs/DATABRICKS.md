# Running on Databricks — step by step

## 1. Get the code (once)

**Workspace → Create → Git folder** → `https://github.com/THAOMYLTR/corp-income-ocr`, branch
`main`. Later updates: **⋮ → Git → Pull**.

## 2. Tesseract on the cluster (once per cluster)

1. **Compute → your cluster → Edit → Advanced options → Init scripts** → Source *Workspace* →
   path of `scripts/install_tesseract.sh` in the Git folder → **Add** → **Confirm and restart**.
2. Use access mode **Single user**; shared clusters often block init scripts.

Without Tesseract, digital PDFs, Word and Excel still work; scans and photos do not.

## 3. Packages

The notebook does not install packages itself (same as the SME repo). Add a first cell, run it
once per cluster start:

```python
%pip install -r requirements.txt
dbutils.library.restartPython()
```

If the cluster cannot reach PyPI, ask the admin to install `requirements.txt` on the cluster.

## 4. Secrets and models — notebook cell 3

Store the key once: `databricks secrets put-secret <scope> <key-name>` (or ask the admin).
Then uncomment **one** block in cell 3:

| You have | Set |
|---|---|
| Anthropic API key | `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY` from the secret |
| A model serving endpoint | `LLM_PROVIDER=databricks`; host and token come from the notebook context — no secret |
| A company gateway in OpenAI format | `LLM_PROVIDER=openai`, `OPENAI_API_KEY`, `OPENAI_API_BASE` |

and the three model names `MODEL_DOCUMENT`, `MODEL_ECONOMY`, `MODEL_PREMIUM` (endpoint names
for `databricks`). A missing value fails in cell 5 with its name.

## 5. The dossier

Upload to a Volume, one folder per upload box — the same boxes as the SME repo:

```
/Volumes/<catalog>/<schema>/<volume>/khdn_abc/
├── ho_so_phap_ly/            GCN_DKDN.pdf, dieu_le.pdf, so_dang_ky_thanh_vien.pdf,
│                             QD_bo_nhiem.pdf, QD_xu_phat.pdf, ban_an.pdf
├── ho_so_tai_chinh/          thong_bao_no_thue.pdf, C12_BHXH.pdf, thuyet_minh_BCTC.pdf
├── ho_so_noi_bo/             masothue_<MST>.pdf, cong_dkdn.png, BCDE_export.xlsx
├── ho_so_soan_thao_noi_bo/   BCTD_<KH>.pdf (báo cáo khảo sát thực địa)
├── ho_so_vay_von/, ho_so_tai_san_dam_bao/   recognised, not used by items 1-4
└── ho_so_khac/               anything else
```

A file outside every box is skipped and named in the step log. In cell 4 set
`INPUT_PATHS = ["/Volumes/.../khdn_abc"]`, `LOAN_DATE`, `BORROWER_NAMES`, and
`OUTPUT_DIR = Path("/Volumes/.../logs")`.

## 6. Run All

Cell 9 prints `--- Agent Name ---` → `CORP_INCOME_AGENT` (or `EVIDENCE_GAP_CHECK` with the
missing documents), the steps, each document's type and read method, and one conclusion per
BRD item. Cell 10 saves everything to `OUTPUT_DIR/<testcase>_<time>/`.

## 7. Troubleshooting

| Message | Fix |
|---|---|
| Anything about the model | Run the **`check_llm_setup(config)`** cell: it shows which settings are set (keys masked), whether `.env` exists, and the **root cause** of a failed call with the fix |
| `MODEL_… is not set` but it is in `.env.example` | `.env.example` is never read — the file must be named `.env`, or set `os.environ[...]` in cell 3 (after any `restartPython()`) |
| `Connection error.` | Only a wrapper; the check cell prints the cause behind it (DNS, firewall, certificate, proxy) |
| `MODEL_… is not set` / `LLM_PROVIDER=… needs …` | Cell 3 — the named variable |
| `401` / `authentication` | Wrong or expired key |
| `404` / `not_found` | Wrong model or endpoint name, or base URL |
| `No module named 'cv2'` (or another package) | Run the step 3 cell: `%pip install -r requirements.txt` **then** `dbutils.library.restartPython()`, and re-run from the top. OpenCV is `opencv-python-headless` |
| `TesseractNotFoundError` | Init script not applied (step 2) |
| Vietnamese OCR is gibberish | `tesseract-ocr-vie` missing (step 2) |
| `skipped N file(s) under no upload box` | Put the files inside the box folders (step 5) |
| A document's type is wrong or empty | Better filename, or the right box; `ocr/<file>.txt` shows what was read |
| A field is wrong | `ocr/<file>.txt`: wrong there = scan quality; right there = tighten `config/prompts/<item>_extraction.md` |
| `Skipped PDF export` | WeasyPrint libraries missing; `.md` and `.xlsx` are saved anyway |
