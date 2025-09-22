"""
Extraction Methods Comparison Tool

This script compares results from different PDF extraction approaches:
1. Traditional pipeline (pdfplumber + OCR)
2. LayoutParser (deep learning layout analysis)  
3. Docling (advanced PDF understanding)

Provides comprehensive analysis of extraction quality, performance,
and capabilities of each method.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging


class ExtractionComparator:
    """
    Compare results from different PDF extraction methods.
    
    Analyzes extraction quality, performance, and capabilities
    across traditional, LayoutParser, and Docling approaches.
    """
    
    def __init__(self, output_dir="data/parsed/comparison"):
        """Initialize the extraction comparator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Extraction method directories
        self.method_dirs = {
            'traditional': Path("data/parsed"),
            'layout_parser': Path("data/parsed/layout_parser"),
            'docling': Path("data/parsed/docling")
        }
        
        # Comparison metrics
        self.comparison_results = {}
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logger = logging.getLogger('ExtractionComparator')
        logger.setLevel(logging.INFO)
        
        log_file = self.output_dir / 'comparison_log.txt'
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        if not logger.handlers:
            logger.addHandler(handler)
        
        return logger
    
    def compare_all_methods(self, pdf_name: str) -> Dict[str, Any]:
        """
        Compare extraction results from all available methods for a specific PDF.
        
        Args:
            pdf_name (str): Name of the PDF file (without extension)
            
        Returns:
            dict: Comprehensive comparison results
        """
        self.logger.info(f"Starting comparison for PDF: {pdf_name}")
        
        comparison = {
            'pdf_name': pdf_name,
            'comparison_timestamp': datetime.now().isoformat(),
            'methods_analyzed': [],
            'extraction_metrics': {},
            'content_quality': {},
            'performance_metrics': {},
            'capability_comparison': {},
            'recommendations': {}
        }
        
        # Analyze each method
        for method_name, base_dir in self.method_dirs.items():
            pdf_dir = base_dir / pdf_name
            
            if pdf_dir.exists():
                self.logger.info(f"Analyzing {method_name} results...")
                method_analysis = self._analyze_method_results(method_name, pdf_dir)
                comparison['methods_analyzed'].append(method_name)
                comparison['extraction_metrics'][method_name] = method_analysis
            else:
                self.logger.warning(f"No results found for {method_name} method")
        
        # Perform comparative analysis
        if len(comparison['methods_analyzed']) > 1:
            comparison['content_quality'] = self._compare_content_quality(comparison['extraction_metrics'])
            comparison['performance_metrics'] = self._compare_performance(comparison['extraction_metrics'])
            comparison['capability_comparison'] = self._compare_capabilities(comparison['extraction_metrics'])
            comparison['recommendations'] = self._generate_recommendations(comparison)
        
        # Save comparison results
        self._save_comparison_results(comparison, pdf_name)
        
        return comparison
    
    def _analyze_method_results(self, method_name: str, pdf_dir: Path) -> Dict[str, Any]:
        """Analyze results from a specific extraction method."""
        analysis = {
            'method': method_name,
            'results_found': True,
            'text_extraction': {},
            'table_extraction': {},
            'structure_analysis': {},
            'performance': {},
            'unique_features': {}
        }
        
        try:
            # Analyze text extraction
            analysis['text_extraction'] = self._analyze_text_extraction(method_name, pdf_dir)
            
            # Analyze table extraction
            analysis['table_extraction'] = self._analyze_table_extraction(method_name, pdf_dir)
            
            # Analyze document structure
            analysis['structure_analysis'] = self._analyze_structure_preservation(method_name, pdf_dir)
            
            # Analyze performance
            analysis['performance'] = self._analyze_performance_metrics(method_name, pdf_dir)
            
            # Analyze unique features
            analysis['unique_features'] = self._analyze_unique_features(method_name, pdf_dir)
            
        except Exception as e:
            self.logger.error(f"Error analyzing {method_name} results: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    def _analyze_text_extraction(self, method_name: str, pdf_dir: Path) -> Dict[str, Any]:
        """Analyze text extraction quality and completeness."""
        text_analysis = {
            'total_text_files': 0,
            'total_characters': 0,
            'average_file_size': 0,
            'text_organization': 'unknown',
            'reading_order_preserved': False
        }
        
        try:
            # Count text files
            text_dirs = ['text', 'titles', 'reading_order']
            total_files = 0
            total_chars = 0
            
            for text_dir in text_dirs:
                dir_path = pdf_dir / text_dir
                if dir_path.exists():
                    text_files = list(dir_path.glob('*.txt'))
                    total_files += len(text_files)
                    
                    for text_file in text_files:
                        try:
                            content = text_file.read_text(encoding='utf-8')
                            total_chars += len(content)
                        except:
                            continue
            
            text_analysis['total_text_files'] = total_files
            text_analysis['total_characters'] = total_chars
            text_analysis['average_file_size'] = total_chars / max(total_files, 1)
            
            # Method-specific analysis
            if method_name == 'traditional':
                text_analysis['text_organization'] = 'page_based'
                text_analysis['ocr_fallback'] = self._check_ocr_usage(pdf_dir)
            elif method_name == 'layout_parser':
                text_analysis['text_organization'] = 'block_based'
                text_analysis['layout_aware'] = True
            elif method_name == 'docling':
                text_analysis['text_organization'] = 'semantic_structure'
                text_analysis['reading_order_preserved'] = True
                text_analysis['hierarchical_structure'] = True
            
        except Exception as e:
            text_analysis['error'] = str(e)
        
        return text_analysis
    
    def _analyze_table_extraction(self, method_name: str, pdf_dir: Path) -> Dict[str, Any]:
        """Analyze table extraction capabilities."""
        table_analysis = {
            'tables_found': 0,
            'table_files': [],
            'extraction_method': 'unknown',
            'structure_preservation': False,
            'format_support': []
        }
        
        try:
            tables_dir = pdf_dir / 'tables'
            if tables_dir.exists():
                csv_files = list(tables_dir.glob('*.csv'))
                json_files = list(tables_dir.glob('*.json'))
                
                table_analysis['tables_found'] = len(csv_files)
                table_analysis['table_files'] = [f.name for f in csv_files]
                
                if csv_files:
                    table_analysis['format_support'].append('csv')
                if json_files:
                    table_analysis['format_support'].append('json')
                
                # Method-specific table analysis
                if method_name == 'traditional':
                    table_analysis['extraction_method'] = 'pdfplumber'
                    table_analysis['structure_preservation'] = True
                elif method_name == 'layout_parser':
                    table_analysis['extraction_method'] = 'layout_aware'
                    table_analysis['structure_preservation'] = True
                    table_analysis['bounding_box_detection'] = True
                elif method_name == 'docling':
                    table_analysis['extraction_method'] = 'advanced_understanding'
                    table_analysis['structure_preservation'] = True
                    table_analysis['semantic_analysis'] = True
        
        except Exception as e:
            table_analysis['error'] = str(e)
        
        return table_analysis
    
    def _analyze_structure_preservation(self, method_name: str, pdf_dir: Path) -> Dict[str, Any]:
        """Analyze how well document structure is preserved."""
        structure_analysis = {
            'layout_information': False,
            'bounding_boxes': False,
            'hierarchical_structure': False,
            'reading_order': False,
            'cross_page_continuity': False
        }
        
        try:
            # Check for bounding box information
            bbox_dir = pdf_dir / 'bounding_boxes'
            if bbox_dir.exists():
                structure_analysis['bounding_boxes'] = True
                structure_analysis['layout_information'] = True
            
            # Check for layout visualizations
            layout_dir = pdf_dir / 'layout_images'
            if layout_dir.exists():
                structure_analysis['layout_information'] = True
            
            # Method-specific structure analysis
            if method_name == 'docling':
                structure_analysis['hierarchical_structure'] = True
                structure_analysis['reading_order'] = True
                structure_analysis['cross_page_continuity'] = True
            elif method_name == 'layout_parser':
                structure_analysis['layout_information'] = True
                structure_analysis['bounding_boxes'] = True
            
        except Exception as e:
            structure_analysis['error'] = str(e)
        
        return structure_analysis
    
    def _analyze_performance_metrics(self, method_name: str, pdf_dir: Path) -> Dict[str, Any]:
        """Analyze performance metrics for each method."""
        performance = {
            'processing_time': 0,
            'pages_processed': 0,
            'success_rate': 0,
            'memory_efficiency': 'unknown'
        }
        
        try:
            # Look for results files with timing information
            result_files = [
                'extraction_summary.json',
                'layout_parser_extraction_results.json',
                'docling_extraction_results.json'
            ]
            
            for result_file in result_files:
                file_path = pdf_dir / result_file
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Extract performance metrics
                    if 'processing_time_seconds' in data:
                        performance['processing_time'] = data['processing_time_seconds']
                    elif 'extraction_summary' in data:
                        summary = data['extraction_summary']
                        performance['processing_time'] = summary.get('processing_time_seconds', 0)
                    
                    # Extract other metrics
                    if 'total_pages' in data:
                        performance['pages_processed'] = data['total_pages']
                    elif 'document_analysis' in data:
                        performance['pages_processed'] = data['document_analysis'].get('total_pages', 0)
                    
                    break
        
        except Exception as e:
            performance['error'] = str(e)
        
        return performance
    
    def _analyze_unique_features(self, method_name: str, pdf_dir: Path) -> Dict[str, Any]:
        """Analyze unique features of each extraction method."""
        features = {
            'special_capabilities': [],
            'output_formats': [],
            'advanced_features': {}
        }
        
        try:
            if method_name == 'traditional':
                features['special_capabilities'] = [
                    'OCR fallback for scanned pages',
                    'Word-level bounding boxes',
                    'Configurable layout parameters'
                ]
                features['output_formats'] = ['txt', 'json']
                
            elif method_name == 'layout_parser':
                features['special_capabilities'] = [
                    'Deep learning-based block detection',
                    'Multiple block types (text, title, table, figure, list)',
                    'Layout visualization',
                    'Confidence scores for detections'
                ]
                features['output_formats'] = ['txt', 'csv', 'png', 'json']
                features['advanced_features'] = {
                    'block_classification': True,
                    'layout_visualization': True,
                    'confidence_scoring': True
                }
                
            elif method_name == 'docling':
                features['special_capabilities'] = [
                    'Reading order preservation',
                    'Mathematical formula detection',
                    'Advanced table understanding',
                    'Unified document model',
                    'Multiple export formats'
                ]
                features['output_formats'] = ['txt', 'csv', 'json', 'markdown']
                features['advanced_features'] = {
                    'reading_order': True,
                    'formula_detection': True,
                    'semantic_understanding': True,
                    'markdown_export': True,
                    'hierarchical_structure': True
                }
                
                # Check for specific Docling features
                if (pdf_dir / 'formulas').exists():
                    features['formula_detection'] = True
                if (pdf_dir / 'markdown').exists():
                    features['markdown_export'] = True
        
        except Exception as e:
            features['error'] = str(e)
        
        return features
    
    def _check_ocr_usage(self, pdf_dir: Path) -> Dict[str, Any]:
        """Check OCR usage in traditional extraction."""
        ocr_info = {
            'ocr_pages': 0,
            'total_pages': 0,
            'ocr_percentage': 0
        }
        
        try:
            summary_file = pdf_dir / 'extraction_summary.json'
            if summary_file.exists():
                with open(summary_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if 'extraction_stats' in data:
                    stats = data['extraction_stats']
                    ocr_info['ocr_pages'] = stats.get('pages_with_ocr', 0)
                    ocr_info['total_pages'] = data['pdf_info'].get('total_pages', 0)
                    
                    if ocr_info['total_pages'] > 0:
                        ocr_info['ocr_percentage'] = (ocr_info['ocr_pages'] / ocr_info['total_pages']) * 100
        
        except Exception as e:
            ocr_info['error'] = str(e)
        
        return ocr_info
    
    def _compare_content_quality(self, extraction_metrics: Dict) -> Dict[str, Any]:
        """Compare content quality across methods."""
        quality_comparison = {
            'text_completeness': {},
            'table_extraction': {},
            'structure_preservation': {},
            'overall_ranking': []
        }
        
        try:
            # Compare text extraction
            for method, metrics in extraction_metrics.items():
                text_metrics = metrics.get('text_extraction', {})
                quality_comparison['text_completeness'][method] = {
                    'total_characters': text_metrics.get('total_characters', 0),
                    'organization': text_metrics.get('text_organization', 'unknown'),
                    'reading_order': text_metrics.get('reading_order_preserved', False)
                }
            
            # Compare table extraction
            for method, metrics in extraction_metrics.items():
                table_metrics = metrics.get('table_extraction', {})
                quality_comparison['table_extraction'][method] = {
                    'tables_found': table_metrics.get('tables_found', 0),
                    'extraction_quality': table_metrics.get('structure_preservation', False),
                    'format_support': table_metrics.get('format_support', [])
                }
            
            # Overall ranking based on capabilities
            rankings = []
            for method, metrics in extraction_metrics.items():
                score = self._calculate_quality_score(metrics)
                rankings.append((method, score))
            
            rankings.sort(key=lambda x: x[1], reverse=True)
            quality_comparison['overall_ranking'] = rankings
        
        except Exception as e:
            quality_comparison['error'] = str(e)
        
        return quality_comparison
    
    def _calculate_quality_score(self, metrics: Dict) -> float:
        """Calculate overall quality score for a method."""
        score = 0
        
        # Text extraction quality (0-30 points)
        text_metrics = metrics.get('text_extraction', {})
        if text_metrics.get('total_characters', 0) > 0:
            score += 10
        if text_metrics.get('reading_order_preserved', False):
            score += 10
        if text_metrics.get('text_organization') in ['semantic_structure', 'block_based']:
            score += 10
        
        # Table extraction quality (0-25 points)
        table_metrics = metrics.get('table_extraction', {})
        score += min(table_metrics.get('tables_found', 0) * 5, 15)
        if table_metrics.get('structure_preservation', False):
            score += 10
        
        # Structure preservation (0-25 points)
        structure_metrics = metrics.get('structure_analysis', {})
        if structure_metrics.get('bounding_boxes', False):
            score += 5
        if structure_metrics.get('hierarchical_structure', False):
            score += 10
        if structure_metrics.get('reading_order', False):
            score += 10
        
        # Unique features (0-20 points)
        features = metrics.get('unique_features', {})
        score += len(features.get('special_capabilities', [])) * 2
        score += len(features.get('output_formats', [])) * 2
        
        return min(score, 100)  # Cap at 100
    
    def _compare_performance(self, extraction_metrics: Dict) -> Dict[str, Any]:
        """Compare performance metrics across methods."""
        performance_comparison = {
            'processing_speed': {},
            'efficiency_ranking': [],
            'scalability': {}
        }
        
        try:
            # Compare processing times
            for method, metrics in extraction_metrics.items():
                perf_metrics = metrics.get('performance', {})
                processing_time = perf_metrics.get('processing_time', 0)
                pages_processed = perf_metrics.get('pages_processed', 1)
                
                performance_comparison['processing_speed'][method] = {
                    'total_time': processing_time,
                    'time_per_page': processing_time / max(pages_processed, 1),
                    'pages_processed': pages_processed
                }
            
            # Rank by efficiency (time per page)
            efficiency_rankings = []
            for method, speed_data in performance_comparison['processing_speed'].items():
                time_per_page = speed_data['time_per_page']
                if time_per_page > 0:
                    efficiency_rankings.append((method, time_per_page))
            
            efficiency_rankings.sort(key=lambda x: x[1])  # Lower time is better
            performance_comparison['efficiency_ranking'] = efficiency_rankings
        
        except Exception as e:
            performance_comparison['error'] = str(e)
        
        return performance_comparison
    
    def _compare_capabilities(self, extraction_metrics: Dict) -> Dict[str, Any]:
        """Compare unique capabilities of each method."""
        capability_comparison = {
            'feature_matrix': {},
            'strengths': {},
            'limitations': {}
        }
        
        # Define capability categories
        capabilities = [
            'ocr_support', 'layout_detection', 'table_extraction', 
            'figure_extraction', 'formula_detection', 'reading_order',
            'bounding_boxes', 'multiple_formats', 'visualization'
        ]
        
        try:
            # Build feature matrix
            for capability in capabilities:
                capability_comparison['feature_matrix'][capability] = {}
                
                for method, metrics in extraction_metrics.items():
                    has_capability = self._check_capability(method, capability, metrics)
                    capability_comparison['feature_matrix'][capability][method] = has_capability
            
            # Identify strengths and limitations
            for method, metrics in extraction_metrics.items():
                strengths = []
                limitations = []
                
                if method == 'traditional':
                    strengths = ['Fast processing', 'OCR fallback', 'Reliable text extraction']
                    limitations = ['Limited layout understanding', 'No semantic analysis']
                elif method == 'layout_parser':
                    strengths = ['Deep learning accuracy', 'Layout visualization', 'Block classification']
                    limitations = ['Requires GPU for best performance', 'Complex setup']
                elif method == 'docling':
                    strengths = ['Advanced understanding', 'Reading order', 'Multiple formats', 'Formula detection']
                    limitations = ['Newer library', 'Higher resource requirements']
                
                capability_comparison['strengths'][method] = strengths
                capability_comparison['limitations'][method] = limitations
        
        except Exception as e:
            capability_comparison['error'] = str(e)
        
        return capability_comparison
    
    def _check_capability(self, method: str, capability: str, metrics: Dict) -> bool:
        """Check if a method has a specific capability."""
        capability_map = {
            'traditional': {
                'ocr_support': True,
                'layout_detection': False,
                'table_extraction': True,
                'figure_extraction': False,
                'formula_detection': False,
                'reading_order': False,
                'bounding_boxes': True,
                'multiple_formats': False,
                'visualization': False
            },
            'layout_parser': {
                'ocr_support': True,
                'layout_detection': True,
                'table_extraction': True,
                'figure_extraction': True,
                'formula_detection': False,
                'reading_order': False,
                'bounding_boxes': True,
                'multiple_formats': True,
                'visualization': True
            },
            'docling': {
                'ocr_support': True,
                'layout_detection': True,
                'table_extraction': True,
                'figure_extraction': True,
                'formula_detection': True,
                'reading_order': True,
                'bounding_boxes': True,
                'multiple_formats': True,
                'visualization': False
            }
        }
        
        return capability_map.get(method, {}).get(capability, False)
    
    def _generate_recommendations(self, comparison: Dict) -> Dict[str, Any]:
        """Generate recommendations based on comparison results."""
        recommendations = {
            'best_for_speed': None,
            'best_for_accuracy': None,
            'best_for_complex_documents': None,
            'best_for_tables': None,
            'overall_recommendation': None,
            'use_case_recommendations': {}
        }
        
        try:
            methods = comparison.get('methods_analyzed', [])
            
            # Performance-based recommendations
            perf_ranking = comparison.get('performance_metrics', {}).get('efficiency_ranking', [])
            if perf_ranking:
                recommendations['best_for_speed'] = perf_ranking[0][0]
            
            # Quality-based recommendations
            quality_ranking = comparison.get('content_quality', {}).get('overall_ranking', [])
            if quality_ranking:
                recommendations['best_for_accuracy'] = quality_ranking[0][0]
            
            # Specific use case recommendations
            use_cases = {
                'simple_text_extraction': 'traditional',
                'financial_reports_with_tables': 'docling',
                'academic_papers_with_formulas': 'docling',
                'layout_analysis': 'layout_parser',
                'high_volume_processing': 'traditional',
                'complex_document_understanding': 'docling'
            }
            
            # Filter recommendations based on available methods
            available_recommendations = {}
            for use_case, recommended_method in use_cases.items():
                if recommended_method in methods:
                    available_recommendations[use_case] = recommended_method
            
            recommendations['use_case_recommendations'] = available_recommendations
            
            # Overall recommendation
            if 'docling' in methods:
                recommendations['overall_recommendation'] = 'docling'
            elif 'layout_parser' in methods:
                recommendations['overall_recommendation'] = 'layout_parser'
            else:
                recommendations['overall_recommendation'] = 'traditional'
        
        except Exception as e:
            recommendations['error'] = str(e)
        
        return recommendations
    
    def _save_comparison_results(self, comparison: Dict, pdf_name: str):
        """Save comprehensive comparison results."""
        # Save detailed comparison
        detailed_file = self.output_dir / f'{pdf_name}_detailed_comparison.json'
        with open(detailed_file, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2, ensure_ascii=False, default=str)
        
        # Save summary report
        summary = self._create_summary_report(comparison)
        summary_file = self.output_dir / f'{pdf_name}_comparison_summary.txt'
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        # Save as CSV for easy analysis
        self._save_comparison_csv(comparison, pdf_name)
        
        self.logger.info(f"Comparison results saved:")
        self.logger.info(f"  Detailed: {detailed_file}")
        self.logger.info(f"  Summary: {summary_file}")
    
    def _create_summary_report(self, comparison: Dict) -> str:
        """Create a human-readable summary report."""
        report = []
        report.append(f"PDF Extraction Methods Comparison Report")
        report.append(f"PDF: {comparison['pdf_name']}")
        report.append(f"Analysis Date: {comparison['comparison_timestamp']}")
        report.append("=" * 60)
        
        # Methods analyzed
        methods = comparison.get('methods_analyzed', [])
        report.append(f"Methods Analyzed: {', '.join(methods)}")
        report.append("")
        
        # Quality ranking
        quality_ranking = comparison.get('content_quality', {}).get('overall_ranking', [])
        if quality_ranking:
            report.append("Quality Ranking:")
            for i, (method, score) in enumerate(quality_ranking, 1):
                report.append(f"  {i}. {method}: {score:.1f}/100")
            report.append("")
        
        # Performance comparison
        perf_ranking = comparison.get('performance_metrics', {}).get('efficiency_ranking', [])
        if perf_ranking:
            report.append("Speed Ranking (faster is better):")
            for i, (method, time_per_page) in enumerate(perf_ranking, 1):
                report.append(f"  {i}. {method}: {time_per_page:.2f}s per page")
            report.append("")
        
        # Recommendations
        recommendations = comparison.get('recommendations', {})
        if recommendations:
            report.append("Recommendations:")
            if recommendations.get('overall_recommendation'):
                report.append(f"  Overall Best: {recommendations['overall_recommendation']}")
            if recommendations.get('best_for_speed'):
                report.append(f"  Fastest: {recommendations['best_for_speed']}")
            if recommendations.get('best_for_accuracy'):
                report.append(f"  Most Accurate: {recommendations['best_for_accuracy']}")
        
        return "\n".join(report)
    
    def _save_comparison_csv(self, comparison: Dict, pdf_name: str):
        """Save comparison data as CSV for analysis."""
        try:
            data = []
            
            for method in comparison.get('methods_analyzed', []):
                metrics = comparison['extraction_metrics'].get(method, {})
                
                row = {
                    'method': method,
                    'pdf_name': pdf_name,
                    'text_files': metrics.get('text_extraction', {}).get('total_text_files', 0),
                    'total_characters': metrics.get('text_extraction', {}).get('total_characters', 0),
                    'tables_found': metrics.get('table_extraction', {}).get('tables_found', 0),
                    'processing_time': metrics.get('performance', {}).get('processing_time', 0),
                    'pages_processed': metrics.get('performance', {}).get('pages_processed', 0),
                    'has_bounding_boxes': metrics.get('structure_analysis', {}).get('bounding_boxes', False),
                    'has_reading_order': metrics.get('structure_analysis', {}).get('reading_order', False),
                    'output_formats': len(metrics.get('unique_features', {}).get('output_formats', []))
                }
                
                data.append(row)
            
            if data:
                df = pd.DataFrame(data)
                csv_file = self.output_dir / f'{pdf_name}_comparison_data.csv'
                df.to_csv(csv_file, index=False)
        
        except Exception as e:
            self.logger.error(f"Error saving CSV: {e}")


def main():
    """Main function to run extraction comparison."""
    print("=== PDF Extraction Methods Comparison ===")
    print("Comparing: Traditional, LayoutParser, and Docling approaches")
    print()
    
    comparator = ExtractionComparator()
    
    # Find processed PDFs
    processed_pdfs = set()
    
    for method_dir in comparator.method_dirs.values():
        if method_dir.exists():
            for pdf_dir in method_dir.iterdir():
                if pdf_dir.is_dir() and pdf_dir.name not in ['comparison', 'layout_parser', 'docling']:
                    processed_pdfs.add(pdf_dir.name)
    
    if not processed_pdfs:
        print("No processed PDFs found for comparison")
        print("Please run extraction methods first:")
        print("  python src/pdf_text_extractor.py")
        print("  python src/layout_parser_extractor.py")  
        print("  python src/docling_extractor.py")
        return
    
    # Compare each PDF
    for pdf_name in processed_pdfs:
        print(f"\nComparing extraction results for: {pdf_name}")
        comparison = comparator.compare_all_methods(pdf_name)
        
        if comparison['methods_analyzed']:
            print(f"✓ Comparison completed for {pdf_name}")
            print(f"  Methods analyzed: {', '.join(comparison['methods_analyzed'])}")
            
            # Show quick summary
            if 'recommendations' in comparison:
                overall = comparison['recommendations'].get('overall_recommendation')
                if overall:
                    print(f"  Overall recommendation: {overall}")
        else:
            print(f"✗ No extraction results found for {pdf_name}")
    
    print(f"\nComparison results saved to: {comparator.output_dir}")


if __name__ == "__main__":
    main()