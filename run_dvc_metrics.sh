#!/bin/bash
# DVC Metrics Validation Pipeline Runner
# Shell Script for automated metrics testing
# Date: September 25, 2025

set -e  # Exit on any error

echo "======================================"
echo "DVC METRICS VALIDATION PIPELINE"
echo "======================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python not found in PATH"
        exit 1
    fi
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

# Check if we're in the right directory
if [ ! -f "scripts/dvc_metrics_pipeline.py" ]; then
    echo "ERROR: dvc_metrics_pipeline.py not found. Make sure you're in the project root directory."
    exit 1
fi

# Show help function
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  --commit              Commit current metrics as new baseline"
    echo "  --quiet               Reduce output verbosity"
    echo "  --thresholds-only     Run only threshold validation tests"
    echo "  --regression-only     Run only regression detection tests"
    echo "  --help                Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                        # Run full pipeline"
    echo "  $0 --thresholds-only     # Only validate thresholds"
    echo "  $0 --commit              # Run pipeline and commit baseline"
    exit 0
}

# Parse command line arguments
ARGS=""
for arg in "$@"; do
    case $arg in
        --help)
            show_help
            ;;
        --commit|--quiet|--thresholds-only|--regression-only)
            ARGS="$ARGS $arg"
            ;;
        *)
            echo "Unknown argument: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "Running DVC Metrics Pipeline..."
echo ""

# Run the pipeline
if $PYTHON_CMD scripts/dvc_metrics_pipeline.py $ARGS; then
    echo ""
    echo "======================================"
    echo "PIPELINE COMPLETED SUCCESSFULLY"
    echo "======================================"
    exit 0
else
    echo ""
    echo "======================================"
    echo "PIPELINE FAILED"
    echo "======================================"
    exit 1
fi