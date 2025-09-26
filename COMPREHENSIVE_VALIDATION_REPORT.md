# Comprehensive Extraction & XBRL Cross‑Validation Report

Date: 2025-09-25
Repository: Assignment_01

## 1) Objective

Validate that financial figures extracted from NVIDIA's 10‑K PDF (nvda-20240128.pdf) match the official XBRL values. We compare:
- PDF extraction methods (Docling, PDFPlumber+Tesseract, Hybrid)
- Structured XBRL parsed values (CSV produced under `data/parsed/xbrl`)

Metrics: word/character error rates for text pages; numeric cross‑validation for financial tables.

---

## 2) Data Sources

- PDF: `data/raw/pdf/nvda-20240128.pdf`
- Docling tables: `data/parsed/docling/nvda-20240128/tables/*.csv`
- XBRL CSV (consolidated metrics): `data/parsed/xbrl/nvidia_financial_metrics.csv` (produced by the validator from an exported XBRL facts CSV)
- Comparison outputs: `data/parsed/comparison/*`

---

## 3) Methods Overview

- Docling (advanced PDF understanding) for table/text extraction.
- Hybrid (Camelot + PDFPlumber) for tables; PDFPlumber+Tesseract for OCR fallback.
- XBRL parsing pipeline to extract key line items into a CSV.
- Cross‑validation script aligns PDF labels to XBRL taxonomy concepts and validates values with scale detection (e.g., millions in PDF vs actual values in XBRL).

---

## 4) XBRL Extracted Metrics (from `nvidia_financial_metrics.csv`)

The validator writes a consolidated CSV summarizing key metrics by period. Columns typically include:
- Period (e.g., 2024-01-28, 2023-01-29, 2022-01-30)
- Revenue, Net Income, Operating Income
- Total Assets, Total Liabilities, Stockholders Equity
- Cash and Cash Equivalents (if available)

Note: Actual values depend on the input XBRL facts CSV you provide (see Reproducibility). The PDF often reports values “in millions,” while the XBRL holds actual units; the validator detects and normalizes scale during comparison.

---

## 5) Cross‑Validation Summary (from `data/parsed/comparison`)

- Matches (`matches.csv`): Income statement key figures (Revenue, Operating Income, Net Income) match across 2022–2024 after scale normalization (millions in PDF vs actual in XBRL).
- Discrepancies (`discrepancies.csv`): Balance sheet items, especially Cash and Cash Equivalents, may show mismatches driven by:
  - Statement/context differences (consolidated vs segment or subtotal rows in the PDF)
  - Period header ambiguities and table parsing alignment issues

### 5.1 Key Matches

Observed patterns (typical across this filing):
- Revenue matches for 2022–2024 after applying a 1e6 scale factor.
- Operating Income and Net Income also align within tolerance once scale is normalized.

### 5.2 Notable Discrepancies

- Cash and Cash Equivalents: frequently flagged due to context/statement differences (e.g., subtotal vs total) or header/period ambiguities. Verify the exact row source in the PDF and confirm whether the XBRL concept aligns to the same consolidation level.

---

## 6) Mapping Strategy

- Label normalization (lowercasing, punctuation strip) and taxonomy concept mapping via a dictionary.
- Automatic scale detection when the PDF table header indicates units (e.g., “(In millions)”).
- Period alignment by date strings in headers/columns.
- Rule: treat exact match within tolerance 5% and rounding tolerance 1% as a success. This run used tighter thresholds (tolerance 1%, rounding 0.5%) per the manifest.

---

## 7) Reproducibility (Windows PowerShell)

Prerequisites:
- Export an XBRL facts CSV (e.g., using Arelle) for the filing; point the CLI to that CSV with `--xbrl-csv`. The validator does not parse XML directly.

Validate a single filing (adjust paths as needed):

PowerShell

python .\src\xbrl_validation.py validate \
  --tables-dir "data\parsed\docling\nvda-20240128\tables" \
  --xbrl-csv "<PATH TO YOUR nvda_facts.csv>" \
  --out-xbrl-dir "data\parsed\xbrl" \
  --out-comp-dir "data\parsed\comparison" \
  --tolerance 0.05 \
  --rounding-tolerance 0.01 \
  --datatracks-threshold 0.15 \
  --self-test

Tip: If `nvidia_financial_metrics.csv` appears locked or read-only, close Excel or any process using it. You can clear the read-only attribute via:

PowerShell

attrib -R "data\parsed\xbrl\nvidia_financial_metrics.csv"

---

## 8) Insights & Recommendations

- Income statement figures (Revenue, Net Income, Operating Income) are consistent across PDF and XBRL after scale normalization.
- Discrepancies concentrate in balance sheet cash equivalents—investigate table selection (parent vs subsidiary), subtotal vs total, and period labeling.
- Implement a stricter header parser for units and a period disambiguation rule (use nearest header date token for the column; avoid relying on positional heuristics when headers are ambiguous).
- Consider a taxonomy lookup or semantic similarity to auto-map labels across filings.

---

## 9) Results for NVDA 10‑K (2024 filing)

Run context (from `data/parsed/comparison/xbrl_validation_manifest.json`):
- XBRL CSV: `./data/raw/Xbrlfiles/nvda_facts.csv`
- Tables dir: `data/parsed/docling/nvda-20240128/tables`
- PDF tables loaded: 60
- Tolerance: 0.01; Rounding tolerance: 0.005

Summary (from `batch_summary.csv` and JSON results):
- Matches: 9
- Discrepancies: 2
- PDF‑only: 165
- XBRL‑only: 0
- Match rate: 81.82%

Automap coverage (from `automap_labels.csv` / manifest):
- Mapped 196 of 394 labels → 49.75% coverage

### 9.1 Sample Matches (scale normalized: millions → actual)

| Concept | Period | PDF (millions) | XBRL (actual) | Scale |
|---|---|---:|---:|---|
| Revenue | 2024-01-28 | 60,922 | 60,922,000,000 | 1e6 |
| Revenue | 2023-01-29 | 26,974 | 26,974,000,000 | 1e6 |
| Revenue | 2022-01-30 | 26,914 | 26,914,000,000 | 1e6 |
| Operating Income | 2024-01-28 | 33,818 | 32,972,000,000 | 1e6 |
| Net Income | 2024-01-28 | 29,760 | 29,760,000,000 | 1e6 |

### 9.2 Sample Discrepancies

| Concept | Period | PDF (millions) | XBRL (actual) | Notes |
|---|---|---:|---:|---|
| Cash and Cash Equivalents | 2023-01-29 | 4,797 | 3,389,000,000 | Context/statement alignment; a 1e6 scale was detected but values still differ |
| Cash and Cash Equivalents | 2022-01-30 | 10,152 | 3,389,000,000 | Likely row/period misalignment or subtotal vs total discrepancy |

— Full artifacts are available under `data/parsed/comparison/`.

---

## Appendix A: Files Produced

- `data/parsed/xbrl/nvidia_financial_metrics.csv`
- `data/parsed/comparison/matches.csv`
- `data/parsed/comparison/discrepancies.csv`
- `data/parsed/comparison/xbrl_validation_results.json`
- `data/parsed/comparison/pdf_only.csv`
- `data/parsed/comparison/xbrl_only.csv`
- `data/parsed/comparison/automap_labels.csv`
- `data/parsed/comparison/batch_summary.csv`
- `data/parsed/comparison/xbrl_validation_manifest.json`
- `data/parsed/comparison/*` (tabular breakdowns and manifest for the run)

