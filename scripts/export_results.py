#!/usr/bin/env python3
"""
Export results stage for DVC pipeline
Generate final analysis and comparison reports
"""

import os
import json
import argparse
from pathlib import Path
import sys
from datetime import datetime

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

try:
    from validation_report_generator import ValidationReportGenerator
except ImportError:
    print("⚠️  ValidationReportGenerator not available")
    ValidationReportGenerator = None

def ensure_directories():
    """Create necessary directories"""
    dirs = [
        "data/parsed/benchmarks",
        "data/parsed/analysis",
        "data/parsed/comparison"
    ]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def collect_results():
    """Collect results from all previous stages"""
    results = {
        "text_extraction": {},
        "table_extraction": {},
        "layout_analysis": {},
        "docling_extraction": {},
        "timestamp": datetime.now().isoformat()
    }
    
    # Load text extraction results
    text_summary_path = Path("data/parsed/nvda-20240128/extraction_summary.json")
    if text_summary_path.exists():
        with open(text_summary_path) as f:
            results["text_extraction"] = json.load(f)
    
    # Load table extraction results
    table_summary_path = Path("data/parsed/nvda-20240128/table_extraction_summary.json")
    if table_summary_path.exists():
        with open(table_summary_path) as f:
            results["table_extraction"] = json.load(f)
    
    # Load layout analysis results
    layout_analysis_path = Path("data/parsed/comparison/layout_analysis.json")
    if layout_analysis_path.exists():
        with open(layout_analysis_path) as f:
            results["layout_analysis"] = json.load(f)
    
    # Load Docling results
    docling_comparison_path = Path("data/parsed/comparison/docling_layout_comparison.json")
    if docling_comparison_path.exists():
        with open(docling_comparison_path) as f:
            results["docling_extraction"] = json.load(f)
    
    return results

def generate_benchmark_results(results):
    """Generate benchmark results from collected data"""
    benchmark_results = {
        "pipeline_version": "1.0.0",
        "execution_date": datetime.now().isoformat(),
        "document": "nvda-20240128.pdf",
        "stages": {
            "text_extraction": {
                "status": results["text_extraction"].get("status", "unknown"),
                "pages_processed": results["text_extraction"].get("pages_processed", 0),
                "files_created": results["text_extraction"].get("text_files_created", 0)
            },
            "table_extraction": {
                "status": results["table_extraction"].get("status", "unknown"),
                "tables_extracted": results["table_extraction"].get("tables_extracted", 0),
                "pages_processed": results["table_extraction"].get("pages_processed", 0)
            },
            "layout_analysis": {
                "status": results["layout_analysis"].get("status", "unknown"),
                "layout_elements": results["layout_analysis"].get("layout_elements", 0),
                "pages_processed": results["layout_analysis"].get("pages_processed", 0)
            },
            "docling_extraction": {
                "status": results["docling_extraction"].get("status", "unknown"),
                "tables_detected": results["docling_extraction"].get("tables_detected", 0),
                "pages_processed": results["docling_extraction"].get("pages_processed", 0)
            }
        },
        "summary": {
            "total_stages": 4,
            "successful_stages": sum(1 for stage in results.values() 
                                   if isinstance(stage, dict) and stage.get("status") == "success"),
            "overall_success": all(isinstance(stage, dict) and stage.get("status") == "success" 
                                 for stage in results.values() if isinstance(stage, dict))
        }
    }
    
    return benchmark_results

def generate_final_report(results):
    """Generate final markdown report"""
    report_content = f"""# DVC Pipeline Execution Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Document:** nvda-20240128.pdf  

## Pipeline Summary

| Stage | Status | Pages Processed | Output |
|-------|--------|----------------|--------|
| Text Extraction | {results['text_extraction'].get('status', 'N/A')} | {results['text_extraction'].get('pages_processed', 0)} | {results['text_extraction'].get('text_files_created', 0)} files |
| Table Extraction | {results['table_extraction'].get('status', 'N/A')} | {results['table_extraction'].get('pages_processed', 0)} | {results['table_extraction'].get('tables_extracted', 0)} tables |
| Layout Analysis | {results['layout_analysis'].get('status', 'N/A')} | {results['layout_analysis'].get('pages_processed', 0)} | {results['layout_analysis'].get('layout_elements', 0)} elements |
| Docling Extraction | {results['docling_extraction'].get('status', 'N/A')} | {results['docling_extraction'].get('pages_processed', 0)} | {results['docling_extraction'].get('tables_detected', 0)} tables |

## Performance Metrics

### Text Extraction
- **Method:** {results['text_extraction'].get('extraction_method', 'N/A')}
- **Success Rate:** {'100%' if results['text_extraction'].get('status') == 'success' else '0%'}

### Table Extraction  
- **Method:** {results['table_extraction'].get('extraction_method', 'N/A')}
- **Tables Per Page:** {results['table_extraction'].get('tables_extracted', 0) / max(results['table_extraction'].get('pages_processed', 1), 1):.2f}

### Layout Analysis
- **Method:** {results['layout_analysis'].get('analysis_method', 'N/A')}
- **Elements Per Page:** {results['layout_analysis'].get('layout_elements', 0) / max(results['layout_analysis'].get('pages_processed', 1), 1):.2f}

### Docling Extraction
- **Method:** {results['docling_extraction'].get('extraction_method', 'N/A')}
- **Confidence:** {results['docling_extraction'].get('confidence_score', 0):.2f}

## Quality Assessment

### Overall Pipeline Success
- **Stages Completed:** {sum(1 for stage in results.values() if isinstance(stage, dict) and stage.get('status') == 'success')}/4
- **Data Quality:** {'High' if all(isinstance(stage, dict) and stage.get('status') == 'success' for stage in results.values() if isinstance(stage, dict)) else 'Mixed'}

### Recommendations
1. **Text Extraction:** {'✅ Working well' if results['text_extraction'].get('status') == 'success' else '⚠️ Needs attention'}
2. **Table Extraction:** {'✅ Working well' if results['table_extraction'].get('status') == 'success' else '⚠️ Needs attention'}
3. **Layout Analysis:** {'✅ Working well' if results['layout_analysis'].get('status') == 'success' else '⚠️ Needs attention'}
4. **Docling Extraction:** {'✅ Working well' if results['docling_extraction'].get('status') == 'success' else '⚠️ Needs attention'}

---
*Report generated by DVC pipeline automation*
"""
    
    return report_content

def generate_method_comparison(results):
    """Generate method comparison data"""
    comparison = {
        "comparison_date": datetime.now().isoformat(),
        "document": "nvda-20240128.pdf",
        "methods": {
            "text_extraction": {
                "method": results['text_extraction'].get('extraction_method', 'unknown'),
                "success": results['text_extraction'].get('status') == 'success',
                "pages_processed": results['text_extraction'].get('pages_processed', 0),
                "output_quality": "high" if results['text_extraction'].get('status') == 'success' else "low"
            },
            "table_extraction": {
                "method": results['table_extraction'].get('extraction_method', 'unknown'),
                "success": results['table_extraction'].get('status') == 'success',
                "tables_found": results['table_extraction'].get('tables_extracted', 0),
                "detection_rate": results['table_extraction'].get('tables_extracted', 0) / max(results['table_extraction'].get('pages_processed', 1), 1)
            },
            "layout_analysis": {
                "method": results['layout_analysis'].get('analysis_method', 'unknown'),
                "success": results['layout_analysis'].get('status') == 'success',
                "elements_detected": results['layout_analysis'].get('layout_elements', 0)
            },
            "docling_extraction": {
                "method": results['docling_extraction'].get('extraction_method', 'unknown'),
                "success": results['docling_extraction'].get('status') == 'success',
                "tables_detected": results['docling_extraction'].get('tables_detected', 0),
                "confidence": results['docling_extraction'].get('confidence_score', 0.0)
            }
        },
        "overall_assessment": {
            "best_text_method": results['text_extraction'].get('extraction_method', 'unknown'),
            "best_table_method": results['table_extraction'].get('extraction_method', 'unknown'),
            "pipeline_success": all(isinstance(stage, dict) and stage.get('status') == 'success' 
                                  for stage in results.values() if isinstance(stage, dict))
        }
    }
    
    return comparison

def export_results():
    """
    Export final results and generate reports
    """
    print("📊 Starting export results stage...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Collect results from all stages
    results = collect_results()
    
    # Generate benchmark results
    benchmark_results = generate_benchmark_results(results)
    benchmark_path = Path("data/parsed/benchmarks/benchmark_results.json")
    with open(benchmark_path, 'w') as f:
        json.dump(benchmark_results, f, indent=2)
    print(f"✅ Generated benchmark results: {benchmark_path}")
    
    # Generate final report
    final_report = generate_final_report(results)
    report_path = Path("data/parsed/analysis/final_report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(final_report)
    print(f"✅ Generated final report: {report_path}")
    
    # Generate method comparison
    method_comparison = generate_method_comparison(results)
    comparison_path = Path("data/parsed/comparison/method_comparison.json")
    with open(comparison_path, 'w') as f:
        json.dump(method_comparison, f, indent=2)
    print(f"✅ Generated method comparison: {comparison_path}")
    
    # Try to use ValidationReportGenerator if available
    if ValidationReportGenerator:
        try:
            generator = ValidationReportGenerator()
            validation_report = generator.generate_report(results)
            validation_path = Path("data/parsed/analysis/validation_report.json")
            with open(validation_path, 'w') as f:
                json.dump(validation_report, f, indent=2)
            print(f"✅ Generated validation report: {validation_path}")
        except Exception as e:
            print(f"⚠️  ValidationReportGenerator failed: {e}")
    
    print("📊 Export results stage completed")

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Export results for DVC pipeline")
    parser.add_argument("--force", action="store_true", help="Force re-processing")
    args = parser.parse_args()
    
    export_results()

if __name__ == "__main__":
    main()