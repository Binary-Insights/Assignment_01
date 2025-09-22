# NVIDIA XBRL Metrics Summary

This report summarizes key financial metrics extracted from the XBRL facts CSV (`nvda_facts.csv`) and saved to `data/parsed/xbrl/nvidia_financial_metrics.csv`.

Source file: `data/raw/Xbrlfiles/nvda_facts.csv`
Extracted CSV: `data/parsed/xbrl/nvidia_financial_metrics.csv`

## Metrics
Metrics included per period (where available):
- Revenue
- Net Income
- Operating Income
- Total Assets
- Cash and Cash Equivalents
- Total Liabilities
- Stockholders Equity

## Extracted Values

| Period     | Revenue       | Net Income    | Operating Income | Total Assets | Cash & Equivalents | Total Liabilities | Stockholders Equity |
|------------|---------------:|--------------:|-----------------:|-------------:|-------------------:|------------------:|--------------------:|
| 2022-01-30 | 26914000000.0 | 9752000000.0 | 10041000000.0   |              |                    |                   |                    |
| 2023-01-29 | 26974000000.0 | 4368000000.0 | 4224000000.0    |              | 3389000000.0       |                   |                    |
| 2024-01-28 | 60922000000.0 | 29760000000.0| 32972000000.0   |              | 7280000000.0       |                   |                    |

Notes:
- Empty cells indicate the metric was not located for that period in the CSV input.
- Values are raw numbers (e.g., dollars) after removing common formatting.

## Coverage
- Periods extracted: 3
- Metrics found per period vary based on presence in `nvda_facts.csv` and parsing rules.

## Next Steps
- If you want scaled or human-readable formatting (e.g., billions), we can add a presentation layer.
- To include additional metrics (e.g., Gross Profit, Operating Expenses, EPS), extend `extract_nvidia_financials()` in `src/xbrl_validation.py`.

## Cross-Verification
For mismatches and consistency checks between the PDF tables and XBRL values, see the cross-verification report:
`data/parsed/comparison/CROSS_VERIFICATION_REPORT.md`
