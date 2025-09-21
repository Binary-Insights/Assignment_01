# Directory Structure Guide

## Document Processing Pipeline - Organized File Structure

This document describes the organized directory structure for the document processing pipeline project.

## 📁 Directory Structure

```
Assignment_01/
├── 📁 src/                          # Source code modules
│   ├── docling_extractor.py         # Docling document processor
│   ├── layout_parser_extractor.py   # LayoutParser processor  
│   ├── pdfplumber_tess_extractor.py # PDFPlumber processor
│   ├── financial_extractor.py       # Financial data extractor
│   ├── metadata_extractor.py        # Document metadata extractor
│   ├── table_normalizer.py          # Table standardization
│   ├── text_extractor.py           # Text extraction utilities
│   ├── validation_report_generator.py # Result validation
│   ├── xbrl_loader.py               # XBRL data loader
│   ├── extraction_comparator.py     # Method comparison
│   ├── method_specific_markdown_generator.py # Documentation generator
│   ├── 📁 cloud_extractors/         # Cloud service processors
│   │   ├── aws_textract.py          # AWS Textract integration
│   │   ├── cloud_comparator.py      # Cloud service comparison
│   │   ├── fallback_extractor.py    # Fallback processing
│   │   └── run_experiment.py        # Cloud experiments
│   └── 📁 comparison/               # Comparison utilities
│       ├── text_matcher.py          # Text matching algorithms
│       ├── validation_enhancer.py   # Result enhancement
│       └── xbrl_pdf_comparator.py   # XBRL vs PDF comparison
│
├── 📁 data/                         # Data storage (organized)
│   ├── 📁 raw/                      # Original data files
│   │   ├── 📁 pdf/                  # Source PDF documents
│   │   ├── 📁 extracted_zip/        # AWS Textract results
│   │   ├── nvda-20240128.zip        # Original AWS data
│   │   └── 📁 sec-edgar-filings/    # SEC filing data
│   └── 📁 parsed/                   # Processing results
│       ├── 📁 aws_results/          # AWS Textract analysis
│       ├── 📁 docling/              # Docling extraction results
│       ├── 📁 comparison/           # Method comparisons
│       ├── 📁 benchmarks/           # Performance benchmarks ⭐
│       │   ├── benchmark_results.json    # Performance data
│       │   ├── benchmark_results.csv     # Performance summary
│       │   ├── cost_analysis.json        # Cost projections
│       │   ├── cost_comparison.csv       # Cost comparisons
│       │   ├── benchmark_log.txt         # Execution logs
│       │   └── 📁 docling_bench/         # Detailed Docling results
│       ├── 📁 analysis/             # Analysis outputs
│       └── 📁 nvda-20240128/        # Document-specific results
│
├── 📁 scripts/                      # Utility scripts ⭐
│   ├── benchmark_pipeline.py        # Performance benchmarking
│   ├── cost_analyzer.py            # Cost analysis framework
│   └── cleanup_workspace.py        # Workspace maintenance
│
├── 📁 docs/                         # Documentation ⭐
│   ├── benchmarks.md                # Performance & cost analysis
│   ├── CLOUD_VS_OPENSOURCE_ANALYSIS.md # Comparison results
│   └── InitialSetupSteps.txt        # Setup instructions
│
├── 📁 config/                       # Configuration files
│   ├── config.json                 # Main configuration
│   └── xbrl_mappings.json          # XBRL field mappings
│
├── 📁 models/                       # Model configurations
│   └── 📁 layoutparser/            # LayoutParser models
│       └── config.yml              # Model configuration
│
├── 📁 pilots/                       # Experimental scripts
│   ├── docling-sample.py           # Docling experiments
│   ├── layout-parser-test.py       # LayoutParser tests
│   ├── sec_downloader.py           # SEC data downloader
│   └── [other pilot scripts]       # Various experiments
│
├── 📁 tests/                        # Test suites
│   └── test_comparator.py          # Comparison tests
│
├── main.py                         # Main pipeline entry point
├── README.md                       # Project overview
├── pyproject.toml                  # Python dependencies
└── uv.lock                        # Dependency lock file
```

## 🎯 Key Changes Made

### ⭐ New Organized Structure

1. **`data/parsed/benchmarks/`** - All performance and cost analysis results
   - Previously scattered in root `benchmarks/` directory
   - Now properly organized with parsed data

2. **`scripts/`** - Utility and analysis scripts  
   - `benchmark_pipeline.py` - Performance measurement
   - `cost_analyzer.py` - Cost analysis and projections
   - `cleanup_workspace.py` - Workspace maintenance

3. **`docs/`** - All documentation and analysis reports
   - `benchmarks.md` - Comprehensive performance analysis
   - `CLOUD_VS_OPENSOURCE_ANALYSIS.md` - Method comparison
   - `InitialSetupSteps.txt` - Setup documentation

### 📊 Data Organization

- **Raw data**: `data/raw/` (unchanged)
- **Processed results**: `data/parsed/` with clear categorization
- **Benchmarks**: `data/parsed/benchmarks/` for all performance data
- **Analysis**: `data/parsed/analysis/` for analytical outputs

## 🚀 Usage After Reorganization

### Running Benchmarks
```bash
# From project root
python scripts/benchmark_pipeline.py --methods docling
python scripts/cost_analyzer.py
```

### Accessing Results
```bash
# Performance data
cat data/parsed/benchmarks/benchmark_results.json

# Cost analysis  
cat data/parsed/benchmarks/cost_analysis.json

# Documentation
cat docs/benchmarks.md
```

### Cleaning Workspace
```bash
python scripts/cleanup_workspace.py
```

## 📈 Benefits of New Structure

1. **Clear Separation**: Scripts, data, and docs are properly separated
2. **Logical Grouping**: Related files are grouped together
3. **Scalability**: Easy to add new methods and results
4. **Maintainability**: Clear location for each type of file
5. **Professional Structure**: Follows standard project organization

## 🔍 Finding Specific Files

| What you need | Location |
|---------------|----------|
| Performance benchmarks | `data/parsed/benchmarks/` |
| Cost analysis | `data/parsed/benchmarks/cost_analysis.json` |
| Method comparisons | `data/parsed/comparison/` |
| Documentation | `docs/` |
| Analysis scripts | `scripts/` |
| Source code | `src/` |
| Configuration | `config/` |

This organization makes the project more professional, maintainable, and easier to navigate for both development and deployment purposes.