# How to Run the Cloud vs Open Source Experiment

This guide helps you execute Part 7 of the assignment - comparing cloud document extraction services with open-source alternatives.

## Prerequisites

### 1. Install Dependencies

```bash
# Install AWS dependencies
pip install boto3 botocore

# Install visualization dependencies  
pip install matplotlib seaborn

# Or install all at once from the updated pyproject.toml
pip install -e .
```

### 2. AWS Setup (Required for Textract)

```bash
# Option 1: Configure AWS CLI
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key  
# Enter region: us-east-1
# Enter output format: json

# Option 2: Set environment variables
export AWS_ACCESS_KEY_ID="your_access_key_here"
export AWS_SECRET_ACCESS_KEY="your_secret_key_here"
export AWS_DEFAULT_REGION="us-east-1"
```

### 3. Get AWS Free Tier (if needed)

- Sign up at https://aws.amazon.com/free/
- Free tier includes 1,000 pages/month of Textract
- Perfect for testing this assignment

## Running the Experiments

### Quick Start (Recommended)

```bash
# Navigate to cloud extractors directory
cd src/cloud_extractors

# Run the complete experiment (results saved to data/parsed)
python run_experiment.py --output-dir "../../data/parsed/aws_results" --max-files 3
```

This will:
1. Process 3 PDF files with AWS Textract
2. Run intelligent fallback experiments  
3. Generate comparison analysis
4. Create comprehensive reports in `data/parsed/aws_results/`

### Custom Experiments

```bash
# Process specific PDF directory (save to data/parsed)
python run_experiment.py --pdf-dir "path/to/your/pdfs" --output-dir "../../data/parsed/aws_results" --max-files 5

# Skip AWS if no credentials (open source only)
python run_experiment.py --skip-aws --output-dir "../../data/parsed/aws_results" --max-files 3

# Run only AWS Textract experiment
python run_experiment.py --skip-fallback --skip-comparison --output-dir "../../data/parsed/aws_results" --max-files 2

# Use default output directory (data/experiments/cloud_comparison)
python run_experiment.py --max-files 3
```

### Individual Component Testing

```bash
# Test AWS Textract only
python -c "
from aws_textract import AWSTextractExtractor
extractor = AWSTextractExtractor()
result = extractor.extract_document('path/to/document.pdf')
print(f'Cost: ${result[\"costs\"][\"total_cost\"]:.4f}')
"

# Test intelligent fallback
python -c "
from fallback_extractor import IntelligentFallbackExtractor  
extractor = IntelligentFallbackExtractor()
result = extractor.extract_document('path/to/document.pdf')
print(f'Method used: {result[\"final_method\"]}')
"
```

## Expected Outputs

### Directory Structure After Running
```
data/parsed/aws_results/
├── aws_textract/
│   └── [document_name]/
│       ├── textract_extraction_results.json
│       ├── text/
│       ├── tables/
│       └── quality_metrics.json
├── fallback/
│   └── [document_name]/
│       ├── fallback_extraction_results.json
│       └── extraction_metadata.json
├── comparison/
│   ├── cloud_vs_opensource_comparison.json
│   ├── extraction_metrics.csv
│   ├── comparison_metrics.png
│   └── cost_quality_tradeoff.png
├── reports/
│   ├── cloud_vs_opensource_experiment_report.md
│   └── detailed_experiment_results.json
├── cloud_vs_opensource_analysis.json
└── cloud_vs_opensource_report.md
```

### Key Files to Review

1. **Main Report**: `reports/cloud_vs_opensource_experiment_report.md`
2. **Final Analysis**: `cloud_vs_opensource_analysis.json` & `cloud_vs_opensource_report.md`
3. **Detailed Results**: `reports/detailed_experiment_results.json`  
4. **Cost Analysis**: `aws_textract/[doc]/extraction_costs.json`
5. **Visualizations**: `comparison/comparison_metrics.png`

## Troubleshooting

### Common Issues

#### AWS Credentials Error
```
Error: Failed to initialize AWS Textract client
```
**Solution**: Set up AWS credentials (see step 2 above)

#### Missing Dependencies  
```
ImportError: No module named 'boto3'
```
**Solution**: Install dependencies: `pip install boto3 matplotlib seaborn`

#### No PDF Files Found
```
No PDF files found in data/raw/pdf
```
**Solution**: 
- Check if PDFs exist in the directory
- Specify correct path with `--pdf-dir`
- Use sample PDFs from SEC EDGAR downloads

#### Import Errors
```
ModuleNotFoundError: No module named 'docling_extractor'
```
**Solution**: Run from correct directory or update Python path

### Skip Cloud Services (Testing Only)

If you don't have AWS credentials, you can still test the framework:

```bash
# Run without cloud services
python run_experiment.py --skip-aws --max-files 2
```

This will:
- Use only open-source methods
- Generate comparison framework
- Show cost analysis (theoretical)

## Cost Management

### Monitor AWS Costs
```bash
# Check AWS billing dashboard
aws ce get-cost-and-usage \
  --time-period Start=2024-12-01,End=2024-12-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE
```

### Free Tier Limits
- **AWS Textract**: 1,000 pages/month free
- **Typical assignment**: ~10-50 pages
- **Safe for testing**: Process 5-10 documents

### Cost Estimation
```python
# Quick cost calculator
pages = 10  # Your document pages
table_detection_cost = pages * 0.015  # $0.015 per page
print(f"Estimated cost: ${table_detection_cost:.4f}")
```

## Sample Commands for Assignment

### For 3-5 Documents (Recommended)
```bash
# Complete experiment with cost tracking
python run_experiment.py --max-files 3 --output-dir "assignment_results"
```

### For Cost Analysis Only  
```bash
# Generate report without actual cloud processing
python run_experiment.py --skip-aws --max-files 5 --output-dir "cost_analysis"
```

### For Demonstration
```bash
# Quick demo with 1 document
python run_experiment.py --max-files 1 --output-dir "demo"
```

## Assignment Deliverables

After running the experiments, you'll have:

1. ✅ **AWS Textract Integration** - Complete implementation
2. ✅ **Cost Analysis** - Per-page costs and projections  
3. ✅ **Quality Comparison** - Side-by-side extraction results
4. ✅ **Fallback System** - Intelligent cloud fallback mechanism
5. ✅ **Comprehensive Report** - Markdown analysis with recommendations

## Next Steps

1. **Run the experiment** with your PDF documents
2. **Review the generated report** in `reports/cloud_vs_opensource_experiment_report.md`
3. **Analyze costs** in the detailed JSON results
4. **Use the findings** to write your assignment conclusions
5. **Include the analysis** in your final project documentation

The comprehensive markdown report (`CLOUD_VS_OPENSOURCE_ANALYSIS.md`) already provides detailed analysis that you can reference for your assignment even without running live experiments.