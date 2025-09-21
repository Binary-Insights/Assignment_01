# Document Processing Pipeline

**Big Data Case Study Assignment - Document Extraction & Analysis**

A comprehensive document processing pipeline with **DVC (Data Version Control)** for reproducible workflows, comparing cloud services (AWS Textract, Google Document AI, Azure Form Recognizer) with open-source solutions (pdfplumber, Docling, LayoutParser) for financial document analysis.

## 🚀 Quick Start

### DVC Pipeline (Recommended)
```bash
# Install dependencies
uv install

# Run complete pipeline
uv run dvc repro

# Run specific stage
uv run dvc repro download
uv run dvc repro parse

# View pipeline structure
uv run dvc dag

# Check pipeline status
uv run dvc status
```

### Manual Execution
```bash
# Run performance benchmarks
python scripts/benchmark_pipeline.py --methods pdfplumber,docling

# Generate cost analysis
python scripts/cost_analyzer.py

# Validate costs with real data
python scripts/validate_costs.py

# View results
cat data/parsed/benchmarks/benchmark_results.json
cat docs/benchmarks.md
```

## 📊 Project Overview

This project evaluates document processing methods for extracting tables, text, and metadata from financial documents (SEC filings). We analyze:

- **Performance**: Runtime, memory usage, success rates
- **Cost**: Cloud service pricing vs. on-premise infrastructure  
- **Accuracy**: Table extraction quality and text recognition
- **Scalability**: Recommendations for different volume scenarios

## 🏗️ Directory Structure

```
📁 Assignment_01/
├── 📁 src/                          # Source code modules
├── 📁 data/
│   ├── 📁 raw/                      # Original PDF files & cloud results
│   └── 📁 parsed/                   # Processing results
│       ├── 📁 benchmarks/           # Performance & cost data
│       ├── 📁 aws_results/          # AWS Textract analysis
│       ├── 📁 docling/              # Docling extraction results
│       └── 📁 comparison/           # Method comparisons
├── 📁 scripts/                      # Utility scripts
│   ├── benchmark_pipeline.py        # Performance benchmarking
│   ├── cost_analyzer.py            # Cost analysis framework
│   └── cleanup_workspace.py        # Workspace maintenance
├── 📁 docs/                         # Documentation & analysis
│   ├── benchmarks.md                # Performance analysis report
│   ├── CLOUD_VS_OPENSOURCE_ANALYSIS.md # Method comparison
│   └── DIRECTORY_STRUCTURE.md      # Directory organization guide
├── 📁 config/                       # Configuration files
├── 📁 tests/                        # Test suites
└── main.py                         # Main pipeline entry point
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.11+
- UV package manager (recommended) or pip
- DVC for pipeline management

### Install Dependencies
```bash
# Using UV (recommended)
uv install

# Or using pip
pip install -r requirements.txt

# Install DVC with S3 support (optional)
uv add dvc[s3]
```

### Configure Environment
```bash
# Copy and edit configuration
cp config/config.json.example config/config.json

# Initialize DVC (if not already done)
uv run dvc init

# Set up cloud credentials (if using cloud services)
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
```

## 📋 DVC Pipeline Stages

The project uses DVC to manage a reproducible pipeline with the following stages:

### Pipeline Overview
```
download → parse → tables ↘
                          ↘
layout ↗                   export
      ↗                   ↗
docling → benchmark ↗
```

### Stage Descriptions

| Stage | Description | Inputs | Outputs |
|-------|-------------|--------|---------|
| **download** | Download SEC filings and documents | config.json | PDF files, ZIP archives |
| **parse** | Extract text content from PDFs | PDF files | Text files, extraction summary |
| **tables** | Extract and normalize tables | PDF files | Table data, analysis |
| **layout** | Layout analysis using LayoutParser | PDF files | Layout elements, analysis |
| **docling** | Content extraction using Docling | PDF files | Docling results, comparisons |
| **benchmark** | Performance benchmarks | PDF files | Benchmark data, metrics |
| **export** | Generate final reports | All stage outputs | Final analysis, reports |

### Running the Pipeline

```bash
# Run complete pipeline
uv run dvc repro

# Run specific stages
uv run dvc repro download
uv run dvc repro parse tables

# Force re-run a stage
uv run dvc repro --force download

# Show pipeline status
uv run dvc status

# Visualize pipeline
uv run dvc dag
```

## 📈 Key Results

### Performance Benchmarks
- **pdfplumber**: 2.14 sec/page, 14.9MB RAM/page, 88.1% table detection (104/118 pages)
- **Docling**: 2.86 sec/page, 12.3MB RAM/page, 51.7% table detection (61/118 pages)
- **AWS Textract**: ~0.5 sec/page, ~80.5% table detection (cloud processed)
- **Processing Volume**: 118-page NVIDIA 10-K filing

### Cost Analysis
| Scale | Best Solution | Cost/Month |
|-------|---------------|------------|
| <1K pages | Cloud (free tier) | $0 |
| 1K-10K pages | Cloud services | $13-135 |
| >50K pages | Open-source | $77 (on-premise) |

**Break-even points**: 3,100-29,100 pages depending on service type.

### ROI Projections
- **80-99% cost reduction** for high-volume processing (open-source)
- **1-2 month payback** period for infrastructure setup
- **$8K-15K annual savings** for organizations processing 50K+ pages
- **pdfplumber advantage**: 34.7x better table detection than Docling at same cost tier

## 🛠️ Usage Examples

### DVC Pipeline Commands
```bash
# Run complete pipeline
uv run dvc repro

# Run specific stages
uv run dvc repro download parse
uv run dvc repro tables --force

# Check what will be executed
uv run dvc repro --dry

# View pipeline dependency graph
uv run dvc dag

# Check pipeline status
uv run dvc status
```

### Manual Script Execution
```bash
# Benchmark all available methods
python scripts/benchmark_pipeline.py

# Benchmark specific method
python scripts/benchmark_pipeline.py --methods docling

# Custom output directory  
python scripts/benchmark_pipeline.py --output-dir custom/path
```

### Cost Analysis
```bash
# Generate cost projections
python scripts/cost_analyzer.py

# Validate with real data
python scripts/validate_costs.py

# View detailed results
cat data/parsed/benchmarks/cost_analysis.json
```

### Process Documents
```bash
# Extract from PDF using Docling
python main.py --method docling --input data/raw/pdf/document.pdf

# Compare multiple methods
python main.py --compare --input data/raw/pdf/document.pdf
```

## 📋 Available Methods

### Open-Source
- **Docling**: IBM's document layout analysis
- **LayoutParser**: Deep learning-based layout detection  
- **pdfplumber**: Python PDF text extraction
- **Camelot**: Table extraction specialist

### Cloud Services
- **AWS Textract**: Table and form detection
- **Google Document AI**: Form and document parsing
- **Azure Form Recognizer**: Structured data extraction

## 📊 Analysis & Reports

### Generated Documentation
- **`docs/benchmarks.md`**: Comprehensive performance analysis
- **`docs/CLOUD_VS_OPENSOURCE_ANALYSIS.md`**: Method comparison
- **`data/parsed/benchmarks/`**: Raw performance data

### Key Insights
1. **Small Scale**: Use cloud free tiers
2. **Medium Scale**: Cloud services cost-effective
3. **Large Scale**: On-premise open-source solutions offer 80-99% savings
4. **Table Detection**: pdfplumber excels at financial document tables (88.1% vs 51.7% for Docling)
5. **Quality**: All methods achieve >95% accuracy for structured documents

## 🔧 Maintenance

### DVC Operations
```bash
# Update pipeline cache
uv run dvc commit

# Clean pipeline cache
uv run dvc gc

# Show data lineage
uv run dvc dag --tree

# Validate pipeline
uv run dvc repro --dry
```

### Cleanup Workspace
```bash
python scripts/cleanup_workspace.py
```

### Update Dependencies
```bash
uv update  # or pip install -U -r requirements.txt
```

### Run Tests
```bash
python -m pytest tests/
```

## 📊 Data Version Control (DVC)

This project uses DVC for:
- **Pipeline Management**: Reproducible data processing workflows
- **Data Versioning**: Track large files without storing them in Git
- **Experiment Tracking**: Compare different processing methods
- **Dependency Management**: Automatic dependency tracking between stages

### Key DVC Files
- `dvc.yaml`: Pipeline configuration with stages and dependencies
- `dvc.lock`: Lock file with exact stage outputs and checksums
- `.dvc/`: DVC configuration and cache directory
- `*.dvc`: Individual file tracking metadata

### DVC Workflow
1. **Modify code or data**: Update scripts, configuration, or input data
2. **Run pipeline**: `uv run dvc repro` automatically runs changed stages
3. **Commit changes**: Git tracks code changes, DVC tracks data changes
4. **Share results**: `dvc push` (if remote storage configured)

## 📚 Documentation

- **[Benchmarks Report](docs/benchmarks.md)**: Detailed performance analysis
- **[Method Comparison](docs/CLOUD_VS_OPENSOURCE_ANALYSIS.md)**: Cloud vs open-source
- **[Directory Guide](docs/DIRECTORY_STRUCTURE.md)**: File organization
- **[Setup Instructions](docs/InitialSetupSteps.txt)**: Initial configuration

### DVC Documentation
- **Pipeline Configuration**: See `dvc.yaml` for stage definitions
- **Stage Scripts**: Individual processing scripts in `scripts/` directory
- **Data Tracking**: `.dvc` files track large data artifacts
- **Pipeline Visualization**: Run `uv run dvc dag` to see workflow graph

## 🎯 Use Cases

### Small Teams (< 1,000 pages/month)
- **Recommended**: Cloud services (free tier)
- **Best Option**: AWS Textract or Azure Form Recognizer
- **Cost**: $0 (within free limits)

### Medium Organizations (1,000-50,000 pages/month)  
- **Recommended**: Cloud services or hybrid approach
- **Best Option**: Azure Form Recognizer ($0.01/page)
- **Cost**: $10-500/month

### Large Enterprises (> 50,000 pages/month)
- **Recommended**: On-premise open-source solutions (pdfplumber + Docling)
- **Best Option**: pdfplumber for table-heavy documents, Docling for general analysis
- **Cost**: $77/month (80-99% savings vs cloud)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-method`)
3. Run tests (`python -m pytest`)
4. Submit pull request

## 📄 License

This project is part of a Big Data course assignment. See course guidelines for usage terms.

## 📞 Support

For questions about this implementation:
- Check documentation in `docs/`
- Review benchmark results in `data/parsed/benchmarks/`
- Run cleanup if experiencing issues: `python scripts/cleanup_workspace.py`

---

**Last Updated**: December 19, 2024  
**Dataset**: NVIDIA 10-K Filing (118 pages)  
**Test Environment**: 12-core CPU, 15.7GB RAM, Windows 11  
**Latest Benchmarks**: pdfplumber (104 tables), Docling (61 tables), AWS Textract (443 expense entries)
