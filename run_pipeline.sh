#!/bin/bash
# DVC Pipeline Execution Script

set -e  # Exit on any error

echo "🚀 Starting PDF Extraction Pipeline"
echo "=================================="

# Check if DVC is installed
if ! command -v dvc &> /dev/null; then
    echo "❌ DVC is not installed. Please install with: pip install dvc dvc-s3"
    exit 1
fi

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not detected. Activating..."
    source .venv/bin/activate
fi

# Validate configuration
echo "📋 Validating configuration..."
python -c "
import yaml
try:
    with open('config/extraction_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    print('✅ Configuration file is valid')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    exit(1)
"

# Check for input data
if [ ! -d "data/raw/pdf" ] || [ -z "$(ls -A data/raw/pdf 2>/dev/null)" ]; then
    echo "⚠️  No PDF files found in data/raw/pdf/"
    echo "   Run the download stage first or add PDF files manually"
    echo "   To run download: dvc repro download"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Show pipeline structure
echo "📊 Pipeline Structure:"
dvc dag

# Check pipeline status
echo "🔍 Checking pipeline status..."
dvc status

echo ""
while true; do
    echo ""
    echo "Choose execution mode:"
    echo "1) Run full pipeline (dvc repro)"
    echo "2) Run specific stage"
    echo "3) Force rebuild all stages"
    echo "4) Show pipeline metrics"
    echo "5) Launch Streamlit exports viewer"
    echo "6) Exit"
    read -p "Enter choice (1-6): " choice

    case $choice in
        1)
            echo "🔄 Running full pipeline..."
            dvc repro
            echo "✅ Pipeline completed successfully!"
            ;;
        2)
            echo "Available stages:"
            echo "- pdfplumber" 
            echo "- hybrid"
            echo "- layout-parser"
            echo "- docling"
            echo "- metadata"
            echo "- compare"
            echo "- export"
            read -p "Enter stage name: " stage
            echo "🔄 Running stage: $stage"
            dvc repro $stage
            ;;
        3)
            echo "🔄 Force rebuilding all stages..."
            dvc repro --force
            echo "✅ Pipeline rebuilt successfully!"
            ;;
        4)
            echo "📈 Pipeline Metrics:"
            if [ -f "data/analysis/extraction_metrics.json" ]; then
                dvc metrics show
                dvc plots show
            else
                echo "No metrics available yet. Run the pipeline first."
            fi
            ;;
        5)
            echo "🖥️ Launching Streamlit exports viewer..."
            streamlit run src/exports_viewer.py
            ;;
        6)
            echo "👋 Goodbye!"
            break
            ;;
        *)
            echo "❌ Invalid choice"
            ;;
    esac
done

# Show final status
echo ""
echo "📊 Final Pipeline Status:"
dvc status

# Show output summary
echo ""
echo "📁 Generated Outputs:"
find data/parsed -name "*.csv" -o -name "*.json" -o -name "*.txt" | head -10
if [ $(find data/parsed -name "*.csv" -o -name "*.json" -o -name "*.txt" | wc -l) -gt 10 ]; then
    echo "... and more files"
fi

echo ""
echo "🎉 Pipeline execution completed!"
echo "Check data/parsed/ for extraction results"
echo "Check reports/ for final documentation"