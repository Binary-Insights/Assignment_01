# DVC Pipeline Documentation

## Overview

This document processing pipeline uses **Data Version Control (DVC)** to create a reproducible, scalable workflow for analyzing financial documents. DVC manages large data files, tracks dependencies, and ensures reproducibility across different environments.

## Pipeline Architecture

### Stage Flow
```
┌─────────────┐
│  download   │ ← Download SEC filings, PDFs
└─────┬───────┘
      │
      ▼
┌─────────────┐
│    parse    │ ← Extract text content
└─────┬───────┘
      │
      ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   tables    │    │   layout    │    │   docling   │ ← Parallel processing
└─────┬───────┘    └─────┬───────┘    └─────┬───────┘
      │                  │                  │
      └──────────┬───────┴──────────────────┘
                 │              │
                 ▼              ▼
           ┌─────────────┐ ┌─────────────┐
           │ benchmark   │ │   export    │ ← Generate reports
           └─────────────┘ └─────────────┘
```

## Stage Details

### 1. Download Stage
**Purpose**: Acquire raw data files
**Script**: `scripts/download_data.py`
**Dependencies**: 
- `config/config.json`
**Outputs**:
- `data/raw/pdf/nvda-20240128.pdf`
- `data/raw/nvda-20240128.zip`

**What it does**:
- Validates data file availability
- Creates directory structure
- Provides fallback data handling

### 2. Parse Stage
**Purpose**: Extract text content from PDFs
**Script**: `scripts/parse_documents.py`
**Dependencies**:
- `data/raw/pdf/nvda-20240128.pdf`
- `src/text_extractor.py`
**Outputs**:
- `data/parsed/nvda-20240128/text/`
- `data/parsed/nvda-20240128/extraction_summary.json`

**What it does**:
- Extracts text using TextExtractor or pypdf fallback
- Creates per-page text files
- Generates extraction summary with metrics

### 3. Tables Stage
**Purpose**: Extract and analyze table data
**Script**: `scripts/extract_tables.py`
**Dependencies**:
- `data/raw/pdf/nvda-20240128.pdf`
- `src/pdfplumber_tess_extractor.py`
- `src/table_normalizer.py`
**Outputs**:
- `data/parsed/nvda-20240128/tables/`
- `data/parsed/nvda-20240128/table_extraction_summary.json`

**What it does**:
- Extracts tables using pdfplumber
- Normalizes table data
- Creates enhanced table versions

### 4. Layout Stage
**Purpose**: Analyze document layout structure
**Script**: `scripts/layout_analysis.py`
**Dependencies**:
- `data/raw/pdf/nvda-20240128.pdf`
- `src/layout_parser_extractor.py`
**Outputs**:
- `data/parsed/layout_parser/`
- `data/parsed/comparison/layout_analysis.json`

**What it does**:
- Detects layout elements using LayoutParser
- Analyzes document structure
- Creates layout comparison data

### 5. Docling Stage
**Purpose**: Extract content using Docling framework
**Script**: `scripts/docling_extraction.py`
**Dependencies**:
- `data/raw/pdf/nvda-20240128.pdf`
- `src/docling_extractor.py`
**Outputs**:
- `data/parsed/docling/`
- `data/parsed/comparison/docling_layout_comparison.json`

**What it does**:
- Processes documents with Docling
- Extracts tables and text
- Generates comparison metrics

### 6. Benchmark Stage
**Purpose**: Performance testing and metrics
**Script**: `scripts/benchmark_pipeline.py`
**Dependencies**:
- `data/raw/pdf/nvda-20240128.pdf`
- `src/pdfplumber_tess_extractor.py`
- `src/docling_extractor.py`
**Outputs**:
- `data/parsed/benchmarks/benchmark_results.csv`
- `data/parsed/benchmarks/cost_analysis.json`

**What it does**:
- Runs performance benchmarks
- Measures runtime, memory usage
- Generates cost analysis

### 7. Export Stage
**Purpose**: Generate final reports and analysis
**Script**: `scripts/export_results.py`
**Dependencies**:
- All previous stage outputs
- `src/validation_report_generator.py`
**Outputs**:
- `data/parsed/benchmarks/benchmark_results.json`
- `data/parsed/analysis/final_report.md`
- `data/parsed/comparison/method_comparison.json`

**What it does**:
- Collects results from all stages
- Generates comprehensive reports
- Creates method comparisons

## Common DVC Commands

### Pipeline Execution
```bash
# Run entire pipeline
uv run dvc repro

# Run specific stage
uv run dvc repro download

# Run multiple stages
uv run dvc repro parse tables

# Force re-run (ignore cache)
uv run dvc repro --force download

# Dry run (show what would execute)
uv run dvc repro --dry
```

### Pipeline Inspection
```bash
# Show pipeline structure
uv run dvc dag

# Check pipeline status
uv run dvc status

# Show stage details
uv run dvc dag --full

# List all stages
uv run dvc stage list
```

### Cache Management
```bash
# Commit changes to cache
uv run dvc commit

# Clean unused cache
uv run dvc gc

# Show cache statistics
uv run dvc cache dir
```

## File Management

### What's Tracked by Git
- `dvc.yaml` - Pipeline configuration
- `dvc.lock` - Pipeline lock file with checksums
- `*.dvc` - Data file metadata
- All source code in `src/` and `scripts/`
- Configuration files

### What's Tracked by DVC
- Raw data files (`data/raw/`)
- Processed outputs (`data/parsed/`)
- Model files (`models/`)
- Large result files

### .gitignore Configuration
The `.gitignore` is configured to:
- Exclude all large data files
- Include DVC metadata files (`.dvc`, `dvc.lock`)
- Exclude DVC cache directory (`.dvc/cache/`)

## Reproducibility Features

### Dependency Tracking
DVC automatically tracks:
- Input files and their checksums
- Source code dependencies
- Configuration files
- Output files and their checksums

### Caching
- DVC caches all outputs by content hash
- Skips stages when inputs haven't changed
- Enables fast re-runs and experimentation

### Version Control Integration
- Git tracks code and DVC configuration
- DVC tracks data and model versions
- Combined system provides full reproducibility

## Troubleshooting

### Common Issues

#### Pipeline Fails on Missing Files
```bash
# Check what files are missing
uv run dvc status

# Force re-run problematic stage
uv run dvc repro --force stage_name
```

#### Cache Issues
```bash
# Clean and rebuild cache
uv run dvc gc
uv run dvc repro --force
```

#### Import Errors
```bash
# Check Python path and dependencies
uv run python -c "import sys; print(sys.path)"
uv install
```

#### Git Tracking Conflicts
```bash
# Remove files from git tracking
git rm --cached file_name
git commit -m "Remove file from git tracking"
```

### Performance Optimization

#### Parallel Execution
The pipeline is designed with parallel stages:
- `tables`, `layout`, and `docling` can run in parallel
- Use `dvc repro -j 3` for parallel execution

#### Memory Management
- Large files are processed in chunks
- Intermediate results are cached to disk
- Memory usage is tracked in benchmarks

## CI/CD Integration

### GitHub Actions
The repository includes a GitHub Actions workflow (`.github/workflows/dvc-smoke-test.yml`) that:
- Validates pipeline configuration
- Tests all stage scripts
- Runs syntax checks
- Performs dry-run validation

### Workflow Triggers
- Pull requests to main branches
- Changes to pipeline files
- Manual workflow dispatch

## Best Practices

### Development Workflow
1. **Make changes**: Modify scripts or configuration
2. **Test locally**: Run `uv run dvc repro --dry` to validate
3. **Execute pipeline**: Run `uv run dvc repro`
4. **Commit changes**: Git commit code changes
5. **Track outputs**: DVC automatically tracks data changes

### Data Management
- Keep raw data immutable
- Use descriptive output names
- Document data transformations
- Version control configuration changes

### Performance
- Profile scripts using the benchmark stage
- Monitor memory usage
- Use appropriate data formats (JSON for metadata, CSV for tables)
- Cache intermediate results

## Extension Points

### Adding New Stages
1. Create script in `scripts/` directory
2. Add stage to `dvc.yaml`
3. Define dependencies and outputs
4. Test with `dvc repro --dry`

### Adding New Extractors
1. Implement in `src/` directory
2. Add to relevant stage script
3. Update dependencies in `dvc.yaml`
4. Add to benchmark comparison

### Custom Analysis
1. Extend `export_results.py` 
2. Add outputs to export stage
3. Create visualization scripts
4. Update documentation

---

This DVC pipeline provides a robust foundation for document processing research, enabling reproducible experiments and scalable analysis workflows.