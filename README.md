# Document Processing Pipeline

**Big Data Case Study Assignment - Document Extraction & Analysis**

A comprehensive document processing pipeline comparing cloud services (AWS Textract, Google Document AI, Azure Form Recognizer) with open-source solutions (Docling, LayoutParser, pdfplumber) for financial document analysis.

## 🚀 Quick Start

```bash
# Run performance benchmarks
python scripts/benchmark_pipeline.py --methods docling

# Generate cost analysis
python scripts/cost_analyzer.py

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

### Install Dependencies
```bash
# Using UV (recommended)
uv install

# Or using pip
pip install -r requirements.txt
```

### Configure Environment
```bash
# Copy and edit configuration
cp config/config.json.example config/config.json

# Set up cloud credentials (if using cloud services)
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
```

## 📈 Key Results

### Performance Benchmarks
- **Docling**: 3.13 sec/page, 12.3MB RAM/page, 100% success rate
- **AWS Textract**: ~0.5 sec/page, 99% success rate (cloud processed)
- **Processing Volume**: 118-page NVIDIA 10-K filing

### Cost Analysis
| Scale | Best Solution | Cost/Month |
|-------|---------------|------------|
| <1K pages | Cloud (free tier) | $0 |
| 1K-10K pages | Cloud services | $13-135 |
| >50K pages | Open-source | $77 (on-premise) |

**Break-even points**: 3,100-29,100 pages depending on service type.

### ROI Projections
- **60-70% cost reduction** for high-volume processing (open-source)
- **2-4 month payback** period for hardware investment
- **$8K-15K annual savings** for organizations processing 50K+ pages

## 🛠️ Usage Examples

### Run Benchmarks
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
3. **Large Scale**: On-premise open-source solutions offer 60-70% savings
4. **Quality**: All methods achieve >95% accuracy for structured documents

## 🔧 Maintenance

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

## 📚 Documentation

- **[Benchmarks Report](docs/benchmarks.md)**: Detailed performance analysis
- **[Method Comparison](docs/CLOUD_VS_OPENSOURCE_ANALYSIS.md)**: Cloud vs open-source
- **[Directory Guide](docs/DIRECTORY_STRUCTURE.md)**: File organization
- **[Setup Instructions](docs/InitialSetupSteps.txt)**: Initial configuration

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
- **Recommended**: On-premise open-source solutions
- **Best Option**: Docling + dedicated hardware
- **Cost**: $77/month (60-70% savings vs cloud)

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

**Last Updated**: September 21, 2025  
**Dataset**: NVIDIA 10-K Filing (118 pages)  
**Test Environment**: 12-core CPU, 15.7GB RAM, Windows 11
