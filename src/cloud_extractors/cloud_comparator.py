"""
Cloud vs Open Source Extraction Comparator

This module compares the quality, performance, and cost of cloud-based
document extraction services (AWS Textract, Google Document AI, Azure AI)
against open-source alternatives (Docling, LayoutParser).

Features:
- Side-by-side quality metrics comparison
- Cost-benefit analysis
- Performance benchmarking
- Table structure comparison
- OCR accuracy evaluation
- Recommendation engine for service selection
"""

import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import difflib
import re
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns


@dataclass
class ExtractionMetrics:
    """Standardized metrics for extraction comparison"""
    method: str
    document_id: str
    processing_time: float
    confidence_avg: float
    confidence_min: float
    text_length: int
    word_count: int
    table_count: int
    block_count: int
    cost_per_page: float
    error_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QualityComparison:
    """Quality comparison between two extraction methods"""
    document_id: str
    method_a: str
    method_b: str
    text_similarity: float
    table_structure_similarity: float
    content_completeness_ratio: float
    confidence_difference: float
    processing_time_ratio: float
    cost_ratio: float
    overall_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CloudExtractionComparator:
    """
    Comprehensive comparator for cloud vs open-source document extraction.
    
    Analyzes quality, cost, and performance metrics to provide insights
    on when to use cloud services vs open-source alternatives.
    """
    
    def __init__(self, 
                 cloud_results_dir: str = "data/parsed/aws_textract",
                 opensource_results_dir: str = "data/parsed",
                 comparison_output_dir: str = "data/analysis/cloud_comparison"):
        """
        Initialize the comparator.
        
        Args:
            cloud_results_dir: Directory containing cloud extraction results
            opensource_results_dir: Directory containing open-source results
            comparison_output_dir: Directory for comparison outputs
        """
        self.cloud_results_dir = Path(cloud_results_dir)
        self.opensource_results_dir = Path(opensource_results_dir)
        self.comparison_output_dir = Path(comparison_output_dir)
        
        # Create output directory
        self.comparison_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Storage for comparison results
        self.extraction_metrics = []
        self.quality_comparisons = []
        self.cost_analysis = {}
        self.performance_analysis = {}
        
        # Method configurations
        self.methods = {
            'aws_textract': {
                'type': 'cloud',
                'cost_model': 'per_page',
                'results_dir': self.cloud_results_dir
            },
            'docling': {
                'type': 'opensource',
                'cost_model': 'infrastructure',
                'results_dir': self.opensource_results_dir / 'docling'
            },
            'layout_parser': {
                'type': 'opensource',
                'cost_model': 'infrastructure',
                'results_dir': self.opensource_results_dir / 'layout_parser'
            }
        }
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logger = logging.getLogger('CloudComparator')
        logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = self.comparison_output_dir / 'comparison.log'
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        if not logger.handlers:
            logger.addHandler(handler)
        
        return logger
    
    def compare_all_extractions(self, document_ids: List[str] = None) -> Dict[str, Any]:
        """
        Compare all extraction methods for specified documents.
        
        Args:
            document_ids: List of document IDs to compare. If None, compare all available.
            
        Returns:
            dict: Comprehensive comparison results
        """
        self.logger.info("Starting comprehensive extraction comparison")
        
        if document_ids is None:
            document_ids = self._discover_common_documents()
        
        if not document_ids:
            self.logger.warning("No common documents found for comparison")
            return {'status': 'error', 'message': 'No documents to compare'}
        
        comparison_results = {
            'comparison_timestamp': datetime.now().isoformat(),
            'documents_compared': len(document_ids),
            'methods_analyzed': list(self.methods.keys()),
            'document_results': {},
            'aggregate_metrics': {},
            'recommendations': {}
        }
        
        # Compare each document across all methods
        for doc_id in document_ids:
            self.logger.info(f"Comparing extractions for document: {doc_id}")
            doc_comparison = self._compare_document_extractions(doc_id)
            comparison_results['document_results'][doc_id] = doc_comparison
        
        # Calculate aggregate metrics
        comparison_results['aggregate_metrics'] = self._calculate_aggregate_metrics()
        
        # Generate recommendations
        comparison_results['recommendations'] = self._generate_recommendations()
        
        # Save comprehensive results
        self._save_comparison_results(comparison_results)
        
        # Generate visualizations
        self._generate_comparison_visualizations(comparison_results)
        
        self.logger.info("Extraction comparison completed")
        return comparison_results
    
    def _discover_common_documents(self) -> List[str]:
        """Discover documents that have been processed by multiple methods."""
        common_docs = set()
        
        # Find documents in each method directory
        method_docs = {}
        for method_name, method_config in self.methods.items():
            results_dir = method_config['results_dir']
            if results_dir.exists():
                docs = [d.name for d in results_dir.iterdir() if d.is_dir()]
                method_docs[method_name] = set(docs)
                
                if not common_docs:
                    common_docs = set(docs)
                else:
                    common_docs = common_docs.intersection(set(docs))
        
        self.logger.info(f"Found {len(common_docs)} common documents across methods")
        return list(common_docs)
    
    def _compare_document_extractions(self, doc_id: str) -> Dict[str, Any]:
        """Compare all extraction methods for a single document."""
        doc_results = {
            'document_id': doc_id,
            'methods_found': [],
            'extraction_metrics': {},
            'quality_comparisons': {},
            'best_method': None,
            'cost_analysis': {}
        }
        
        # Load extraction results for each method
        method_results = {}
        for method_name, method_config in self.methods.items():
            results = self._load_method_results(doc_id, method_name, method_config)
            if results:
                method_results[method_name] = results
                doc_results['methods_found'].append(method_name)
                
                # Calculate standardized metrics
                metrics = self._calculate_extraction_metrics(results, method_name, doc_id)
                doc_results['extraction_metrics'][method_name] = metrics.to_dict()
                self.extraction_metrics.append(metrics)
        
        # Perform pairwise quality comparisons
        methods = list(method_results.keys())
        for i, method_a in enumerate(methods):
            for method_b in methods[i+1:]:
                comparison = self._compare_method_pair(
                    doc_id, method_a, method_results[method_a], 
                    method_b, method_results[method_b]
                )
                comparison_key = f"{method_a}_vs_{method_b}"
                doc_results['quality_comparisons'][comparison_key] = comparison.to_dict()
                self.quality_comparisons.append(comparison)
        
        # Determine best method for this document
        doc_results['best_method'] = self._determine_best_method(doc_results['extraction_metrics'])
        
        # Calculate cost analysis
        doc_results['cost_analysis'] = self._calculate_document_costs(method_results)
        
        return doc_results
    
    def _load_method_results(self, doc_id: str, method_name: str, method_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Load extraction results for a specific method and document."""
        results_dir = method_config['results_dir'] / doc_id
        
        if not results_dir.exists():
            self.logger.warning(f"No {method_name} results found for {doc_id}")
            return None
        
        try:
            if method_name == 'aws_textract':
                results_file = results_dir / 'textract_extraction_results.json'
            elif method_name == 'docling':
                results_file = results_dir / 'docling_extraction_results.json'
            elif method_name == 'layout_parser':
                results_file = results_dir / 'layout_parser_extraction_results.json'
            else:
                # Try to find any JSON results file
                json_files = list(results_dir.glob('*.json'))
                if not json_files:
                    return None
                results_file = json_files[0]
            
            if results_file.exists():
                with open(results_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
        except Exception as e:
            self.logger.error(f"Error loading {method_name} results for {doc_id}: {e}")
        
        return None
    
    def _calculate_extraction_metrics(self, results: Dict[str, Any], method: str, doc_id: str) -> ExtractionMetrics:
        """Calculate standardized metrics from extraction results."""
        # Default values
        processing_time = results.get('processing_time', 0.0)
        
        # Extract quality metrics based on method
        if method == 'aws_textract':
            quality = results.get('quality_metrics', {})
            confidence_stats = quality.get('confidence_stats', {})
            content_stats = quality.get('content_stats', {})
            
            return ExtractionMetrics(
                method=method,
                document_id=doc_id,
                processing_time=processing_time,
                confidence_avg=confidence_stats.get('average', 0.0),
                confidence_min=confidence_stats.get('minimum', 0.0),
                text_length=content_stats.get('total_text_length', 0),
                word_count=content_stats.get('word_count', 0),
                table_count=content_stats.get('tables_found', 0),
                block_count=quality.get('total_blocks', 0),
                cost_per_page=results.get('costs', {}).get('cost_per_page', 0.0),
                error_rate=0.0  # Will be calculated from success rate
            )
        
        else:  # Open-source methods
            # Adapt metrics from open-source results
            content_structure = results.get('content_structure', {})
            
            # Calculate text stats
            text_length = 0
            word_count = 0
            if 'text' in content_structure:
                text_content = content_structure['text'].get('content', '')
                text_length = len(text_content)
                word_count = len(text_content.split())
            
            # Count tables
            table_count = len(content_structure.get('tables', {}).get('tables', []))
            
            return ExtractionMetrics(
                method=method,
                document_id=doc_id,
                processing_time=processing_time,
                confidence_avg=0.8,  # Default confidence for open-source
                confidence_min=0.5,
                text_length=text_length,
                word_count=word_count,
                table_count=table_count,
                block_count=results.get('total_blocks', 0),
                cost_per_page=0.0,  # No direct cost for open-source
                error_rate=0.0
            )
    
    def _compare_method_pair(self, doc_id: str, method_a: str, results_a: Dict[str, Any],
                           method_b: str, results_b: Dict[str, Any]) -> QualityComparison:
        """Compare two extraction methods for quality metrics."""
        
        # Extract text content for comparison
        text_a = self._extract_text_content(results_a, method_a)
        text_b = self._extract_text_content(results_b, method_b)
        
        # Calculate text similarity
        text_similarity = self._calculate_text_similarity(text_a, text_b)
        
        # Compare table structures
        table_similarity = self._compare_table_structures(results_a, results_b, method_a, method_b)
        
        # Calculate content completeness ratio
        completeness_ratio = len(text_b) / max(len(text_a), 1) if text_a else 1.0
        
        # Get metrics for both methods
        metrics_a = self._calculate_extraction_metrics(results_a, method_a, doc_id)
        metrics_b = self._calculate_extraction_metrics(results_b, method_b, doc_id)
        
        # Calculate differences
        confidence_diff = abs(metrics_a.confidence_avg - metrics_b.confidence_avg)
        time_ratio = metrics_b.processing_time / max(metrics_a.processing_time, 0.001)
        cost_ratio = metrics_b.cost_per_page / max(metrics_a.cost_per_page, 0.001)
        
        # Calculate overall score (weighted combination)
        overall_score = (
            text_similarity * 0.4 +
            table_similarity * 0.3 +
            min(completeness_ratio, 1.0) * 0.2 +
            (1 - confidence_diff) * 0.1
        )
        
        return QualityComparison(
            document_id=doc_id,
            method_a=method_a,
            method_b=method_b,
            text_similarity=text_similarity,
            table_structure_similarity=table_similarity,
            content_completeness_ratio=completeness_ratio,
            confidence_difference=confidence_diff,
            processing_time_ratio=time_ratio,
            cost_ratio=cost_ratio,
            overall_score=overall_score
        )
    
    def _extract_text_content(self, results: Dict[str, Any], method: str) -> str:
        """Extract text content from extraction results."""
        if method == 'aws_textract':
            text_blocks = results.get('structured_content', {}).get('text_blocks', [])
            return '\n'.join(block.get('text', '') for block in text_blocks)
        
        else:  # Open-source methods
            content_structure = results.get('content_structure', {})
            return content_structure.get('text', {}).get('content', '')
    
    def _calculate_text_similarity(self, text_a: str, text_b: str) -> float:
        """Calculate similarity between two text extractions."""
        if not text_a or not text_b:
            return 0.0
        
        # Normalize texts
        text_a_normalized = re.sub(r'\s+', ' ', text_a.lower().strip())
        text_b_normalized = re.sub(r'\s+', ' ', text_b.lower().strip())
        
        # Calculate sequence similarity
        similarity = difflib.SequenceMatcher(None, text_a_normalized, text_b_normalized).ratio()
        
        return similarity
    
    def _compare_table_structures(self, results_a: Dict[str, Any], results_b: Dict[str, Any],
                                method_a: str, method_b: str) -> float:
        """Compare table structures between two extraction methods."""
        
        # Extract table information
        if method_a == 'aws_textract':
            tables_a = results_a.get('structured_content', {}).get('tables', [])
        else:
            tables_a = results_a.get('content_structure', {}).get('tables', {}).get('tables', [])
        
        if method_b == 'aws_textract':
            tables_b = results_b.get('structured_content', {}).get('tables', [])
        else:
            tables_b = results_b.get('content_structure', {}).get('tables', {}).get('tables', [])
        
        # Compare table counts
        table_count_similarity = 1.0 - abs(len(tables_a) - len(tables_b)) / max(len(tables_a) + len(tables_b), 1)
        
        # If both have tables, compare structure details
        if tables_a and tables_b:
            # Compare first table structure (simplified)
            table_a = tables_a[0] if tables_a else {}
            table_b = tables_b[0] if tables_b else {}
            
            # Compare cell counts or structure
            cells_a = len(table_a.get('cells', []))
            cells_b = len(table_b.get('cells', []))
            
            cell_similarity = 1.0 - abs(cells_a - cells_b) / max(cells_a + cells_b, 1)
            
            return (table_count_similarity + cell_similarity) / 2
        
        return table_count_similarity
    
    def _determine_best_method(self, metrics: Dict[str, Dict[str, Any]]) -> str:
        """Determine the best extraction method for a document based on metrics."""
        if not metrics:
            return "none"
        
        # Calculate scores for each method
        method_scores = {}
        
        for method, metric_data in metrics.items():
            score = 0.0
            
            # Quality score (40% weight)
            confidence_score = metric_data.get('confidence_avg', 0.0)
            score += confidence_score * 0.4
            
            # Content completeness (30% weight)
            text_length = metric_data.get('text_length', 0)
            word_count = metric_data.get('word_count', 0)
            content_score = min(1.0, (text_length + word_count) / 1000)  # Normalize
            score += content_score * 0.3
            
            # Table extraction (20% weight)
            table_score = min(1.0, metric_data.get('table_count', 0) / 5)  # Normalize
            score += table_score * 0.2
            
            # Speed score (10% weight)
            processing_time = metric_data.get('processing_time', float('inf'))
            speed_score = 1.0 / (1.0 + processing_time)  # Inverse time
            score += speed_score * 0.1
            
            method_scores[method] = score
        
        # Return method with highest score
        return max(method_scores.items(), key=lambda x: x[1])[0]
    
    def _calculate_document_costs(self, method_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate cost analysis for all methods on a document."""
        cost_analysis = {
            'per_page_costs': {},
            'total_costs': {},
            'cost_ratios': {}
        }
        
        for method, results in method_results.items():
            if method == 'aws_textract':
                costs = results.get('costs', {})
                cost_analysis['per_page_costs'][method] = costs.get('cost_per_page', 0.0)
                cost_analysis['total_costs'][method] = costs.get('total_cost', 0.0)
            else:
                # Open-source methods - calculate infrastructure costs
                processing_time = results.get('processing_time', 0.0)
                # Estimate cost based on compute time (rough estimate)
                estimated_cost = processing_time * 0.001  # $0.001 per second of compute
                cost_analysis['per_page_costs'][method] = estimated_cost
                cost_analysis['total_costs'][method] = estimated_cost
        
        # Calculate cost ratios
        costs = list(cost_analysis['per_page_costs'].values())
        if costs:
            min_cost = min(costs)
            for method in cost_analysis['per_page_costs']:
                ratio = cost_analysis['per_page_costs'][method] / max(min_cost, 0.001)
                cost_analysis['cost_ratios'][method] = ratio
        
        return cost_analysis
    
    def _calculate_aggregate_metrics(self) -> Dict[str, Any]:
        """Calculate aggregate metrics across all comparisons."""
        if not self.extraction_metrics:
            return {}
        
        # Group metrics by method
        method_metrics = defaultdict(list)
        for metric in self.extraction_metrics:
            method_metrics[metric.method].append(metric)
        
        aggregate = {}
        for method, metrics in method_metrics.items():
            aggregate[method] = {
                'avg_confidence': np.mean([m.confidence_avg for m in metrics]),
                'avg_processing_time': np.mean([m.processing_time for m in metrics]),
                'avg_cost_per_page': np.mean([m.cost_per_page for m in metrics]),
                'avg_word_count': np.mean([m.word_count for m in metrics]),
                'avg_table_count': np.mean([m.table_count for m in metrics]),
                'total_documents': len(metrics)
            }
        
        return aggregate
    
    def _generate_recommendations(self) -> Dict[str, Any]:
        """Generate recommendations based on comparison results."""
        recommendations = {
            'best_overall': None,
            'best_for_cost': None,
            'best_for_quality': None,
            'best_for_speed': None,
            'use_cases': {},
            'integration_strategy': ""
        }
        
        if not self.extraction_metrics:
            return recommendations
        
        # Analyze by method
        method_stats = defaultdict(lambda: {'quality': [], 'cost': [], 'speed': []})
        
        for metric in self.extraction_metrics:
            method_stats[metric.method]['quality'].append(metric.confidence_avg)
            method_stats[metric.method]['cost'].append(metric.cost_per_page)
            method_stats[metric.method]['speed'].append(1.0 / max(metric.processing_time, 0.001))
        
        # Calculate averages and determine best methods
        method_averages = {}
        for method, stats in method_stats.items():
            method_averages[method] = {
                'quality': np.mean(stats['quality']),
                'cost': np.mean(stats['cost']),
                'speed': np.mean(stats['speed'])
            }
        
        # Find best methods for each criterion
        if method_averages:
            recommendations['best_for_quality'] = max(method_averages.items(), key=lambda x: x[1]['quality'])[0]
            recommendations['best_for_cost'] = min(method_averages.items(), key=lambda x: x[1]['cost'])[0]
            recommendations['best_for_speed'] = max(method_averages.items(), key=lambda x: x[1]['speed'])[0]
            
            # Calculate overall score (weighted)
            overall_scores = {}
            for method, avgs in method_averages.items():
                score = avgs['quality'] * 0.5 + (1.0 / max(avgs['cost'], 0.001)) * 0.3 + avgs['speed'] * 0.2
                overall_scores[method] = score
            
            recommendations['best_overall'] = max(overall_scores.items(), key=lambda x: x[1])[0]
        
        # Generate use case recommendations
        recommendations['use_cases'] = {
            'high_accuracy_required': recommendations['best_for_quality'],
            'cost_sensitive': recommendations['best_for_cost'],
            'high_volume_processing': recommendations['best_for_speed'],
            'complex_tables': 'aws_textract',  # Generally better for complex tables
            'simple_documents': recommendations['best_for_cost']
        }
        
        # Integration strategy
        recommendations['integration_strategy'] = self._generate_integration_strategy(method_averages)
        
        return recommendations
    
    def _generate_integration_strategy(self, method_averages: Dict[str, Dict[str, float]]) -> str:
        """Generate integration strategy recommendations."""
        strategy = "Recommended integration strategy:\n\n"
        
        # Find cloud and open-source methods
        cloud_methods = [m for m in method_averages.keys() if 'aws' in m or 'google' in m or 'azure' in m]
        opensource_methods = [m for m in method_averages.keys() if m not in cloud_methods]
        
        if cloud_methods and opensource_methods:
            best_cloud = max(cloud_methods, key=lambda x: method_averages[x]['quality'])
            best_opensource = max(opensource_methods, key=lambda x: method_averages[x]['quality'])
            
            strategy += f"1. Use {best_opensource} as primary extraction method for cost efficiency\n"
            strategy += f"2. Use {best_cloud} as fallback for:\n"
            strategy += "   - Documents with poor open-source extraction quality\n"
            strategy += "   - Complex tables requiring high accuracy\n"
            strategy += "   - Scanned documents with poor OCR results\n"
            strategy += "3. Implement quality thresholds to trigger cloud fallback\n"
            strategy += "4. Monitor costs and adjust thresholds based on budget constraints"
        
        return strategy
    
    def _save_comparison_results(self, results: Dict[str, Any]):
        """Save comprehensive comparison results."""
        # Save complete results
        results_file = self.comparison_output_dir / 'cloud_vs_opensource_comparison.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save metrics as CSV for analysis
        if self.extraction_metrics:
            metrics_df = pd.DataFrame([m.to_dict() for m in self.extraction_metrics])
            metrics_df.to_csv(self.comparison_output_dir / 'extraction_metrics.csv', index=False)
        
        if self.quality_comparisons:
            comparisons_df = pd.DataFrame([c.to_dict() for c in self.quality_comparisons])
            comparisons_df.to_csv(self.comparison_output_dir / 'quality_comparisons.csv', index=False)
        
        self.logger.info(f"Saved comparison results to {self.comparison_output_dir}")
    
    def _generate_comparison_visualizations(self, results: Dict[str, Any]):
        """Generate visualization charts for the comparison."""
        try:
            if not self.extraction_metrics:
                return
            
            # Create metrics DataFrame
            metrics_df = pd.DataFrame([m.to_dict() for m in self.extraction_metrics])
            
            # Set up the plotting style
            plt.style.use('default')
            sns.set_palette("husl")
            
            # Create subplot grid
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Cloud vs Open Source Extraction Comparison', fontsize=16, fontweight='bold')
            
            # 1. Confidence comparison
            sns.boxplot(data=metrics_df, x='method', y='confidence_avg', ax=axes[0,0])
            axes[0,0].set_title('Extraction Confidence by Method')
            axes[0,0].set_ylabel('Average Confidence')
            axes[0,0].tick_params(axis='x', rotation=45)
            
            # 2. Processing time comparison
            sns.boxplot(data=metrics_df, x='method', y='processing_time', ax=axes[0,1])
            axes[0,1].set_title('Processing Time by Method')
            axes[0,1].set_ylabel('Processing Time (seconds)')
            axes[0,1].tick_params(axis='x', rotation=45)
            
            # 3. Cost comparison
            sns.boxplot(data=metrics_df, x='method', y='cost_per_page', ax=axes[1,0])
            axes[1,0].set_title('Cost per Page by Method')
            axes[1,0].set_ylabel('Cost per Page ($)')
            axes[1,0].tick_params(axis='x', rotation=45)
            
            # 4. Content quality (word count)
            sns.boxplot(data=metrics_df, x='method', y='word_count', ax=axes[1,1])
            axes[1,1].set_title('Content Extraction (Word Count)')
            axes[1,1].set_ylabel('Words Extracted')
            axes[1,1].tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            plt.savefig(self.comparison_output_dir / 'comparison_metrics.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            # Create cost-quality scatter plot
            plt.figure(figsize=(10, 8))
            for method in metrics_df['method'].unique():
                method_data = metrics_df[metrics_df['method'] == method]
                plt.scatter(method_data['cost_per_page'], method_data['confidence_avg'], 
                           label=method, s=100, alpha=0.7)
            
            plt.xlabel('Cost per Page ($)')
            plt.ylabel('Average Confidence')
            plt.title('Cost vs Quality Trade-off Analysis')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.savefig(self.comparison_output_dir / 'cost_quality_tradeoff.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info("Generated comparison visualizations")
            
        except Exception as e:
            self.logger.error(f"Error generating visualizations: {e}")
    
    def generate_comparison_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive markdown report."""
        report_lines = []
        
        # Header
        report_lines.extend([
            "# Cloud vs Open Source Document Extraction Comparison",
            "",
            f"**Analysis Date:** {results.get('comparison_timestamp', 'Unknown')}",
            f"**Documents Analyzed:** {results.get('documents_compared', 0)}",
            f"**Methods Compared:** {', '.join(results.get('methods_analyzed', []))}",
            "",
            "---",
            ""
        ])
        
        # Executive Summary
        recommendations = results.get('recommendations', {})
        report_lines.extend([
            "## Executive Summary",
            "",
            f"**Best Overall Method:** {recommendations.get('best_overall', 'N/A')}",
            f"**Most Cost-Effective:** {recommendations.get('best_for_cost', 'N/A')}",
            f"**Highest Quality:** {recommendations.get('best_for_quality', 'N/A')}",
            f"**Fastest Processing:** {recommendations.get('best_for_speed', 'N/A')}",
            "",
            "### Key Findings",
            ""
        ])
        
        # Add aggregate metrics summary
        aggregate = results.get('aggregate_metrics', {})
        if aggregate:
            for method, metrics in aggregate.items():
                report_lines.extend([
                    f"**{method.title()}:**",
                    f"- Average Confidence: {metrics.get('avg_confidence', 0):.2f}",
                    f"- Average Processing Time: {metrics.get('avg_processing_time', 0):.2f}s",
                    f"- Average Cost per Page: ${metrics.get('avg_cost_per_page', 0):.4f}",
                    f"- Documents Processed: {metrics.get('total_documents', 0)}",
                    ""
                ])
        
        # Integration Strategy
        strategy = recommendations.get('integration_strategy', '')
        if strategy:
            report_lines.extend([
                "## Integration Strategy",
                "",
                strategy,
                "",
                "---",
                ""
            ])
        
        # Detailed Analysis
        report_lines.extend([
            "## Detailed Analysis",
            "",
            "### Method Comparison",
            ""
        ])
        
        # Document-level results
        doc_results = results.get('document_results', {})
        if doc_results:
            report_lines.append("### Document-Level Results")
            report_lines.append("")
            
            for doc_id, doc_data in doc_results.items():
                report_lines.extend([
                    f"#### Document: {doc_id}",
                    "",
                    f"**Best Method:** {doc_data.get('best_method', 'N/A')}",
                    f"**Methods Available:** {', '.join(doc_data.get('methods_found', []))}",
                    ""
                ])
                
                # Add metrics table
                metrics = doc_data.get('extraction_metrics', {})
                if metrics:
                    report_lines.extend([
                        "| Method | Confidence | Processing Time | Cost/Page | Word Count |",
                        "|--------|------------|----------------|-----------|------------|"
                    ])
                    
                    for method, metric_data in metrics.items():
                        conf = metric_data.get('confidence_avg', 0)
                        time_val = metric_data.get('processing_time', 0)
                        cost = metric_data.get('cost_per_page', 0)
                        words = metric_data.get('word_count', 0)
                        
                        report_lines.append(f"| {method} | {conf:.2f} | {time_val:.2f}s | ${cost:.4f} | {words} |")
                    
                    report_lines.append("")
        
        # Use Case Recommendations
        use_cases = recommendations.get('use_cases', {})
        if use_cases:
            report_lines.extend([
                "## Use Case Recommendations",
                ""
            ])
            
            for use_case, recommended_method in use_cases.items():
                report_lines.append(f"- **{use_case.replace('_', ' ').title()}:** {recommended_method}")
            
            report_lines.append("")
        
        # Cost Analysis
        report_lines.extend([
            "## Cost Analysis",
            "",
            "### Pricing Models",
            "",
            "**AWS Textract:**",
            "- Text Detection: $0.0015 per page",
            "- Table Detection: $0.015 per page", 
            "- Form Detection: $0.05 per page",
            "",
            "**Open Source Methods:**",
            "- Infrastructure costs only",
            "- Estimated compute cost: ~$0.001 per processing second",
            "",
            "### Cost Comparison",
            ""
        ])
        
        # Add cost comparison if available
        if aggregate:
            cloud_cost = 0
            opensource_cost = 0
            
            for method, metrics in aggregate.items():
                if 'aws' in method or 'google' in method or 'azure' in method:
                    cloud_cost = metrics.get('avg_cost_per_page', 0)
                else:
                    opensource_cost = max(opensource_cost, metrics.get('avg_cost_per_page', 0))
            
            if cloud_cost > 0:
                cost_ratio = cloud_cost / max(opensource_cost, 0.001)
                report_lines.extend([
                    f"- Cloud services are approximately **{cost_ratio:.1f}x** more expensive per page",
                    f"- Break-even point: ~{1/cost_ratio:.0f} pages for cloud service cost efficiency",
                    ""
                ])
        
        # Quality Analysis
        report_lines.extend([
            "## Quality Analysis",
            "",
            "### Confidence Scores",
            "Higher confidence scores indicate better extraction quality and OCR accuracy.",
            ""
        ])
        
        # Conclusions
        report_lines.extend([
            "## Conclusions and Recommendations",
            "",
            "### When to Use Cloud Services",
            "- Complex table structures requiring high accuracy",
            "- Scanned documents with poor image quality",
            "- Documents where extraction quality is critical",
            "- Low-volume processing where cost is not a primary concern",
            "",
            "### When to Use Open Source",
            "- High-volume document processing",
            "- Cost-sensitive applications",
            "- Documents with standard layouts",
            "- When data privacy is a concern",
            "",
            "### Recommended Hybrid Approach",
            "1. Use open-source methods as primary extraction",
            "2. Implement quality thresholds to detect poor extractions",
            "3. Use cloud services as fallback for low-quality results",
            "4. Monitor costs and adjust thresholds accordingly",
            "",
            "---",
            "",
            f"*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        ])
        
        return "\n".join(report_lines)
