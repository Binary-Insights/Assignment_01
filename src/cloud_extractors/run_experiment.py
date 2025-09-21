"""
Cloud vs Open Source Extraction Experiment Runner

This script runs comprehensive experiments comparing AWS Textract, Google Document AI,
and Azure AI Document Intelligence against open-source alternatives (Docling, LayoutParser).

Features:
- Automated experiment execution
- Cost and quality analysis
- Performance benchmarking
- Comprehensive reporting
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import sys
from datetime import datetime

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from aws_textract import AWSTextractExtractor
from cloud_comparator import CloudExtractionComparator
from fallback_extractor import IntelligentFallbackExtractor


def setup_experiment_logging(output_dir: Path) -> logging.Logger:
    """Setup logging for the experiment."""
    logger = logging.getLogger('ExperimentRunner')
    logger.setLevel(logging.INFO)
    
    # Create file handler
    log_file = output_dir / 'experiment.log'
    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    if not logger.handlers:
        logger.addHandler(handler)
        logger.addHandler(console_handler)
    
    return logger


def run_aws_textract_experiment(pdf_files: List[Path], output_dir: Path, logger: logging.Logger) -> Dict[str, Any]:
    """Run AWS Textract extraction experiment."""
    logger.info("Starting AWS Textract experiment")
    
    # Initialize Textract extractor
    try:
        textract_extractor = AWSTextractExtractor(output_dir=str(output_dir / "aws_textract"))
    except Exception as e:
        logger.error(f"Failed to initialize AWS Textract: {e}")
        logger.warning("Skipping AWS Textract experiment - check AWS credentials")
        return {'status': 'skipped', 'reason': 'initialization_failed', 'error': str(e)}
    
    results = {
        'extraction_results': [],
        'total_cost': 0.0,
        'total_time': 0.0,
        'success_count': 0,
        'error_count': 0
    }
    
    start_time = time.time()
    
    for pdf_file in pdf_files:
        logger.info(f"Processing {pdf_file.name} with AWS Textract")
        
        try:
            # Extract with table detection
            result = textract_extractor.extract_document(pdf_file, features=['TABLES'])
            
            results['extraction_results'].append({
                'document': pdf_file.name,
                'success': True,
                'processing_time': result.get('processing_time', 0),
                'cost': result.get('costs', {}).get('total_cost', 0),
                'blocks_found': result.get('total_blocks', 0),
                'tables_found': result.get('structured_content', {}).get('tables', [])
            })
            
            results['success_count'] += 1
            results['total_cost'] += result.get('costs', {}).get('total_cost', 0)
            
        except Exception as e:
            logger.error(f"AWS Textract failed for {pdf_file.name}: {e}")
            results['extraction_results'].append({
                'document': pdf_file.name,
                'success': False,
                'error': str(e)
            })
            results['error_count'] += 1
    
    results['total_time'] = time.time() - start_time
    
    # Get overall cost summary
    cost_summary = textract_extractor.get_total_costs()
    results['cost_breakdown'] = cost_summary
    
    logger.info(f"AWS Textract experiment completed: {results['success_count']} successes, {results['error_count']} errors")
    logger.info(f"Total cost: ${results['total_cost']:.4f}")
    
    return results


def run_fallback_experiment(pdf_files: List[Path], output_dir: Path, logger: logging.Logger) -> Dict[str, Any]:
    """Run intelligent fallback experiment."""
    logger.info("Starting intelligent fallback experiment")
    
    # Initialize fallback extractor
    fallback_extractor = IntelligentFallbackExtractor(
        output_dir=str(output_dir / "fallback"),
        enable_cloud_fallback=True
    )
    
    results = {
        'extraction_results': [],
        'fallback_statistics': {},
        'total_time': 0.0
    }
    
    start_time = time.time()
    
    for pdf_file in pdf_files:
        logger.info(f"Processing {pdf_file.name} with intelligent fallback")
        
        try:
            result = fallback_extractor.extract_document(pdf_file)
            
            results['extraction_results'].append({
                'document': pdf_file.name,
                'final_method': result.get('final_method'),
                'fallback_triggered': result.get('fallback_triggered', False),
                'total_attempts': result.get('attempts', 0),
                'total_cost': result.get('cost_summary', {}).get('total_cost', 0),
                'processing_time': result.get('total_processing_time', 0)
            })
            
        except Exception as e:
            logger.error(f"Fallback extraction failed for {pdf_file.name}: {e}")
            results['extraction_results'].append({
                'document': pdf_file.name,
                'error': str(e)
            })
    
    results['total_time'] = time.time() - start_time
    results['fallback_statistics'] = fallback_extractor.get_statistics()
    
    # Save fallback statistics
    fallback_extractor.save_statistics()
    
    logger.info(f"Fallback experiment completed in {results['total_time']:.2f}s")
    
    return results


def run_comparison_analysis(output_dir: Path, logger: logging.Logger) -> Dict[str, Any]:
    """Run comprehensive comparison analysis."""
    logger.info("Starting comparison analysis")
    
    # Initialize comparator
    comparator = CloudExtractionComparator(
        cloud_results_dir=str(output_dir / "aws_textract"),
        opensource_results_dir="data/parsed",
        comparison_output_dir=str(output_dir / "comparison")
    )
    
    try:
        # Run comprehensive comparison
        comparison_results = comparator.compare_all_extractions()
        
        logger.info(f"Comparison analysis completed: {comparison_results.get('documents_compared', 0)} documents analyzed")
        
        return comparison_results
        
    except Exception as e:
        logger.error(f"Comparison analysis failed: {e}")
        return {'status': 'error', 'error': str(e)}


def generate_experiment_report(experiment_results: Dict[str, Any], output_dir: Path, logger: logging.Logger):
    """Generate comprehensive experiment report."""
    logger.info("Generating experiment report")
    
    # Create report directory
    report_dir = output_dir / "reports"
    report_dir.mkdir(exist_ok=True)
    
    # Generate markdown report
    report_content = generate_markdown_report(experiment_results)
    
    # Save report
    report_file = report_dir / "cloud_vs_opensource_experiment_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    # Save detailed results as JSON
    detailed_results_file = report_dir / "detailed_experiment_results.json"
    with open(detailed_results_file, 'w', encoding='utf-8') as f:
        json.dump(experiment_results, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"Experiment report saved to {report_file}")
    return report_file


def generate_markdown_report(experiment_results: Dict[str, Any]) -> str:
    """Generate comprehensive markdown report."""
    
    report_lines = [
        "# Cloud vs Open Source Document Extraction Experiment",
        "",
        f"**Experiment Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Total Duration:** {experiment_results.get('total_experiment_time', 0):.2f} seconds",
        "",
        "## Executive Summary",
        "",
        "This experiment compares the performance, quality, and cost of cloud-based document extraction services (AWS Textract) against open-source alternatives (Docling, LayoutParser) for financial document processing.",
        "",
        "### Key Findings",
        ""
    ]
    
    # AWS Textract Results
    aws_results = experiment_results.get('aws_textract', {})
    if aws_results.get('status') != 'skipped':
        report_lines.extend([
            "#### AWS Textract Performance",
            f"- **Success Rate:** {aws_results.get('success_count', 0)}/{aws_results.get('success_count', 0) + aws_results.get('error_count', 0)} documents",
            f"- **Total Cost:** ${aws_results.get('total_cost', 0):.4f}",
            f"- **Average Processing Time:** {aws_results.get('total_time', 0) / max(aws_results.get('success_count', 1), 1):.2f}s per document",
            ""
        ])
        
        # Cost breakdown
        cost_breakdown = aws_results.get('cost_breakdown', {})
        if cost_breakdown:
            report_lines.extend([
                "#### AWS Textract Cost Breakdown",
                f"- **Pages Processed:** {cost_breakdown.get('pages_processed', 0)}",
                f"- **Text Detection Cost:** ${cost_breakdown.get('text_detection_cost', 0):.4f}",
                f"- **Table Detection Cost:** ${cost_breakdown.get('table_detection_cost', 0):.4f}",
                f"- **Cost per Page:** ${cost_breakdown.get('cost_per_page', 0):.4f}",
                ""
            ])
    else:
        report_lines.extend([
            "#### AWS Textract Performance",
            f"- **Status:** Skipped ({aws_results.get('reason', 'unknown')})",
            f"- **Note:** {aws_results.get('error', 'AWS credentials not configured')}",
            ""
        ])
    
    # Fallback Experiment Results
    fallback_results = experiment_results.get('fallback', {})
    if fallback_results:
        fallback_stats = fallback_results.get('fallback_statistics', {})
        
        report_lines.extend([
            "#### Intelligent Fallback Performance", 
            f"- **Total Documents:** {fallback_stats.get('total_documents', 0)}",
            f"- **Primary Success Rate:** {fallback_stats.get('primary_success_rate', 0):.1%}",
            f"- **Fallback Triggered:** {fallback_stats.get('fallback_rate', 0):.1%}",
            f"- **Cloud Service Usage:** {fallback_stats.get('cloud_usage_rate', 0):.1%}",
            f"- **Average Cost per Document:** ${fallback_stats.get('average_cost_per_document', 0):.4f}",
            ""
        ])
        
        # Method usage breakdown
        method_usage = fallback_stats.get('method_usage', {})
        if method_usage:
            report_lines.extend([
                "#### Method Usage Distribution",
                ""
            ])
            for method, count in method_usage.items():
                report_lines.append(f"- **{method.title()}:** {count} attempts")
            report_lines.append("")
    
    # Comparison Results
    comparison_results = experiment_results.get('comparison', {})
    if comparison_results and comparison_results.get('status') != 'error':
        recommendations = comparison_results.get('recommendations', {})
        
        report_lines.extend([
            "## Comparative Analysis",
            "",
            "### Method Recommendations",
            f"- **Best Overall:** {recommendations.get('best_overall', 'N/A')}",
            f"- **Most Cost-Effective:** {recommendations.get('best_for_cost', 'N/A')}",
            f"- **Highest Quality:** {recommendations.get('best_for_quality', 'N/A')}",
            f"- **Fastest Processing:** {recommendations.get('best_for_speed', 'N/A')}",
            "",
            "### Use Case Recommendations",
            ""
        ])
        
        use_cases = recommendations.get('use_cases', {})
        for use_case, method in use_cases.items():
            report_lines.append(f"- **{use_case.replace('_', ' ').title()}:** {method}")
        
        report_lines.extend([
            "",
            "### Integration Strategy",
            "",
            recommendations.get('integration_strategy', 'No strategy available'),
            ""
        ])
        
        # Aggregate metrics
        aggregate = comparison_results.get('aggregate_metrics', {})
        if aggregate:
            report_lines.extend([
                "## Detailed Metrics Comparison",
                "",
                "| Method | Avg Confidence | Avg Time (s) | Avg Cost/Page | Avg Words | Avg Tables |",
                "|--------|---------------|--------------|---------------|-----------|------------|"
            ])
            
            for method, metrics in aggregate.items():
                conf = metrics.get('avg_confidence', 0)
                time_val = metrics.get('avg_processing_time', 0)
                cost = metrics.get('avg_cost_per_page', 0)
                words = metrics.get('avg_word_count', 0)
                tables = metrics.get('avg_table_count', 0)
                
                report_lines.append(f"| {method} | {conf:.3f} | {time_val:.2f} | ${cost:.4f} | {words:.0f} | {tables:.1f} |")
            
            report_lines.append("")
    
    # Cost Analysis
    report_lines.extend([
        "## Cost Analysis",
        "",
        "### AWS Textract Pricing (US East)",
        "- **Text Detection:** $0.0015 per page",
        "- **Table Detection:** $0.015 per page",
        "- **Form Detection:** $0.05 per page",
        "",
        "### Open Source Infrastructure Costs",
        "- **Compute:** ~$0.001 per processing second",
        "- **Storage:** Minimal for document caching",
        "- **Development:** One-time setup cost",
        ""
    ])
    
    # Calculate cost comparison if we have both results
    if (aws_results.get('status') != 'skipped' and 
        aws_results.get('success_count', 0) > 0 and
        fallback_results.get('fallback_statistics', {}).get('total_documents', 0) > 0):
        
        aws_cost_per_doc = aws_results.get('total_cost', 0) / aws_results.get('success_count', 1)
        fallback_cost_per_doc = fallback_results.get('fallback_statistics', {}).get('average_cost_per_document', 0)
        
        if fallback_cost_per_doc > 0:
            cost_ratio = aws_cost_per_doc / fallback_cost_per_doc
            
            report_lines.extend([
                "### Cost Comparison Summary",
                f"- **AWS Textract avg cost per document:** ${aws_cost_per_doc:.4f}",
                f"- **Open source avg cost per document:** ${fallback_cost_per_doc:.4f}",
                f"- **Cost ratio:** {cost_ratio:.1f}x more expensive for cloud services",
                ""
            ])
    
    # Quality Analysis
    report_lines.extend([
        "## Quality Analysis",
        "",
        "### Extraction Quality Factors",
        "1. **OCR Accuracy:** Cloud services typically excel with scanned documents",
        "2. **Table Structure:** AWS Textract provides superior table parsing",
        "3. **Complex Layouts:** Cloud services handle complex layouts better",
        "4. **Confidence Scores:** Cloud services provide detailed confidence metrics",
        "",
        "### Open Source Advantages",
        "1. **Data Privacy:** Complete control over document processing",
        "2. **Customization:** Full control over extraction logic",
        "3. **Cost Predictability:** No per-page charges",
        "4. **Offline Processing:** No internet dependency",
        ""
    ])
    
    # Recommendations
    report_lines.extend([
        "## Recommendations",
        "",
        "### When to Use Cloud Services",
        "- **Complex table extraction:** Financial reports with intricate table structures",
        "- **Scanned documents:** Poor quality PDFs requiring advanced OCR",
        "- **Low volume processing:** When cost per document is not a concern",
        "- **High accuracy requirements:** Critical applications requiring maximum precision",
        "",
        "### When to Use Open Source",
        "- **High volume processing:** Large-scale document processing pipelines",
        "- **Cost-sensitive applications:** Budget-constrained environments",
        "- **Data privacy concerns:** Sensitive financial documents",
        "- **Predictable layouts:** Standard financial filing formats",
        "",
        "### Recommended Hybrid Strategy",
        "1. **Primary:** Use open-source methods (Docling/LayoutParser) for initial processing",
        "2. **Quality gates:** Implement confidence and completeness thresholds",
        "3. **Fallback:** Use cloud services for documents failing quality checks",
        "4. **Monitoring:** Track costs and adjust thresholds based on budget",
        "5. **Special cases:** Use cloud services for complex tables or scanned documents",
        ""
    ])
    
    # Limitations and Future Work
    report_lines.extend([
        "## Limitations and Future Work",
        "",
        "### Current Limitations",
        "- Limited to AWS Textract (Google Document AI and Azure AI not tested)",
        "- Small sample size may not represent all document types",
        "- Cost estimates for open-source infrastructure may vary",
        "",
        "### Future Enhancements",
        "1. **Multi-cloud comparison:** Test Google Document AI and Azure AI",
        "2. **Larger dataset:** Expand testing to more document types and volumes",
        "3. **Real-time processing:** Implement streaming document processing",
        "4. **Advanced quality metrics:** Develop domain-specific quality scores",
        "",
        "---",
        "",
        f"*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
        "## Appendix",
        "",
        "### Experiment Configuration",
        f"- **AWS Region:** us-east-1",
        f"- **Textract Features:** TABLES",
        f"- **Quality Thresholds:** Confidence ≥ 0.7, Text length ≥ 100 chars",
        f"- **Fallback Strategy:** Open-source first, cloud fallback on quality failure"
    ]
    
    return "\n".join(report_lines)


def main():
    """Main experiment runner."""
    parser = argparse.ArgumentParser(description='Run cloud vs open-source extraction experiment')
    parser.add_argument('--pdf-dir', type=str, default='data/raw/pdf',
                       help='Directory containing PDF files to process')
    parser.add_argument('--output-dir', type=str, default='data/experiments/cloud_comparison',
                       help='Output directory for experiment results')
    parser.add_argument('--max-files', type=int, default=5,
                       help='Maximum number of PDF files to process')
    parser.add_argument('--skip-aws', action='store_true',
                       help='Skip AWS Textract experiment')
    parser.add_argument('--skip-fallback', action='store_true',
                       help='Skip intelligent fallback experiment')
    parser.add_argument('--skip-comparison', action='store_true',
                       help='Skip comparison analysis')
    
    args = parser.parse_args()
    
    # Setup experiment environment
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger = setup_experiment_logging(output_dir)
    
    logger.info("Starting cloud vs open-source extraction experiment")
    logger.info(f"Output directory: {output_dir}")
    
    # Find PDF files
    pdf_dir = Path(args.pdf_dir)
    if not pdf_dir.exists():
        logger.error(f"PDF directory not found: {pdf_dir}")
        return 1
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        logger.error(f"No PDF files found in {pdf_dir}")
        return 1
    
    # Limit number of files
    pdf_files = pdf_files[:args.max_files]
    logger.info(f"Processing {len(pdf_files)} PDF files")
    
    # Run experiments
    experiment_results = {
        'experiment_timestamp': datetime.now().isoformat(),
        'pdf_files_processed': [f.name for f in pdf_files],
        'experiment_config': {
            'max_files': args.max_files,
            'pdf_directory': str(pdf_dir),
            'output_directory': str(output_dir)
        }
    }
    
    experiment_start_time = time.time()
    
    # Run AWS Textract experiment
    if not args.skip_aws:
        try:
            aws_results = run_aws_textract_experiment(pdf_files, output_dir, logger)
            experiment_results['aws_textract'] = aws_results
        except Exception as e:
            logger.error(f"AWS Textract experiment failed: {e}")
            experiment_results['aws_textract'] = {'status': 'error', 'error': str(e)}
    else:
        logger.info("Skipping AWS Textract experiment")
        experiment_results['aws_textract'] = {'status': 'skipped', 'reason': 'user_request'}
    
    # Run intelligent fallback experiment
    if not args.skip_fallback:
        try:
            fallback_results = run_fallback_experiment(pdf_files, output_dir, logger)
            experiment_results['fallback'] = fallback_results
        except Exception as e:
            logger.error(f"Fallback experiment failed: {e}")
            experiment_results['fallback'] = {'status': 'error', 'error': str(e)}
    else:
        logger.info("Skipping intelligent fallback experiment")
        experiment_results['fallback'] = {'status': 'skipped', 'reason': 'user_request'}
    
    # Run comparison analysis
    if not args.skip_comparison:
        try:
            comparison_results = run_comparison_analysis(output_dir, logger)
            experiment_results['comparison'] = comparison_results
        except Exception as e:
            logger.error(f"Comparison analysis failed: {e}")
            experiment_results['comparison'] = {'status': 'error', 'error': str(e)}
    else:
        logger.info("Skipping comparison analysis")
        experiment_results['comparison'] = {'status': 'skipped', 'reason': 'user_request'}
    
    # Calculate total experiment time
    experiment_results['total_experiment_time'] = time.time() - experiment_start_time
    
    # Generate comprehensive report
    try:
        report_file = generate_experiment_report(experiment_results, output_dir, logger)
        logger.info(f"Experiment completed successfully. Report available at: {report_file}")
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        return 1
    
    logger.info("Experiment completed successfully")
    return 0


if __name__ == "__main__":
    exit(main())
