#!/usr/bin/env python3
"""
Document Processing Pipeline Benchmarking Tool

This script measures performance, memory consumption, and cost metrics
for all document extraction methods in our pipeline.

Benchmarks:
- Runtime per page
- Memory consumption 
- Success/failure rates
- Bottleneck identification
- Cost projections for different scales

Usage:
    python scripts/benchmark_pipeline.py --pages 50 --output-dir data/parsed/benchmarks/
"""

import time
import psutil
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import tracemalloc
import multiprocessing
import concurrent.futures
import argparse
import sys
import gc
import os

# Import our extraction modules
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import extractors individually to handle missing dependencies
DoclingExtractor = None
LayoutParserExtractor = None
PDFTableExtractor = None
AWSTextractExtractor = None

try:
    from src.docling_extractor import DoclingExtractor
except ImportError as e:
    print(f"Warning: Docling extractor not available: {e}")

try:
    from src.layout_parser_extractor import LayoutParserExtractor
except ImportError as e:
    print(f"Warning: LayoutParser extractor not available: {e}")

try:
    from src.pdfplumber_tess_extractor import PDFTableExtractor
except ImportError as e:
    print(f"Warning: PDFPlumber extractor not available: {e}")

try:
    from src.cloud_extractors.aws_textract import AWSTextractExtractor
except ImportError as e:
    print(f"Warning: AWS Textract extractor not available: {e}")

EXTRACTORS_AVAILABLE = any([DoclingExtractor, LayoutParserExtractor, PDFTableExtractor, AWSTextractExtractor])


@dataclass
class BenchmarkResult:
    """Performance metrics for a single extraction run"""
    method: str
    document: str
    pages: int
    runtime_seconds: float
    memory_peak_mb: float
    memory_avg_mb: float
    success: bool
    error_message: str
    tables_extracted: int
    text_length: int
    cost_estimate: float
    
    def runtime_per_page(self) -> float:
        return self.runtime_seconds / self.pages if self.pages > 0 else 0
    
    def memory_per_page(self) -> float:
        return self.memory_peak_mb / self.pages if self.pages > 0 else 0


class PerformanceBenchmarker:
    """
    Comprehensive benchmarking suite for document extraction pipelines
    """
    
    def __init__(self, output_dir: str = "data/parsed/benchmarks"):
        """Initialize the benchmarker with output directory"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Performance tracking
        self.results: List[BenchmarkResult] = []
        self.system_info = self._get_system_info()
        
        # Cost models (per page)
        self.cost_models = {
            'aws_textract_table': 0.015,  # Table detection
            'aws_textract_text': 0.0015,   # Text detection
            'google_document_ai': 0.015,   # Approximate
            'azure_form_recognizer': 0.01, # Approximate
            'docling': 0.001,             # Compute cost estimate
            'layoutparser': 0.001,        # Compute cost estimate
            'pdfplumber': 0.0005          # Minimal compute cost
        }
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('BenchmarkPipeline')
        logger.setLevel(logging.INFO)
        
        # File handler
        log_file = self.output_dir / 'benchmark_log.txt'
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        if not logger.handlers:
            logger.addHandler(handler)
        
        return logger
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Collect system information for benchmark context"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_count': multiprocessing.cpu_count(),
            'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'python_version': sys.version,
            'platform': sys.platform,
            'architecture': os.uname().machine if hasattr(os, 'uname') else 'unknown'
        }
    
    def measure_memory_usage(self, func, *args, **kwargs) -> Tuple[Any, float, float]:
        """Measure peak and average memory usage during function execution"""
        tracemalloc.start()
        process = psutil.Process()
        
        # Get initial memory
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
        memory_samples = [initial_memory]
        
        start_time = time.time()
        
        try:
            # Execute function
            result = func(*args, **kwargs)
            
            # Sample memory during execution
            current_memory = process.memory_info().rss / (1024 * 1024)
            memory_samples.append(current_memory)
            
        except Exception as e:
            result = None
            self.logger.error(f"Function execution failed: {e}")
        finally:
            # Final memory measurement
            final_memory = process.memory_info().rss / (1024 * 1024)
            memory_samples.append(final_memory)
            
            tracemalloc.stop()
        
        peak_memory = max(memory_samples)
        avg_memory = np.mean(memory_samples)
        
        return result, peak_memory, avg_memory
    
    def benchmark_docling(self, pdf_path: str) -> BenchmarkResult:
        """Benchmark Docling extraction"""
        self.logger.info(f"Benchmarking Docling on {pdf_path}")
        
        if DoclingExtractor is None:
            self.logger.error("DoclingExtractor not available")
            return BenchmarkResult(
                method='docling',
                document=Path(pdf_path).name,
                pages=0,
                runtime_seconds=0,
                memory_peak_mb=0,
                memory_avg_mb=0,
                success=False,
                error_message="DoclingExtractor not available",
                tables_extracted=0,
                text_length=0,
                cost_estimate=0
            )
        
        start_time = time.time()
        
        try:
            extractor = DoclingExtractor(output_dir=str(self.output_dir / "docling_bench"))
            
            # Measure memory during extraction
            result, peak_memory, avg_memory = self.measure_memory_usage(
                extractor.extract_from_pdf, pdf_path
            )
            
            runtime = time.time() - start_time
            
            # Extract metrics from result
            success = result is not None and result.get('processing_success', False)
            tables_count = len(result.get('content_structure', {}).get('tables', [])) if success else 0
            pages = result.get('document_analysis', {}).get('total_pages', 0) if success else 0
            
            return BenchmarkResult(
                method='docling',
                document=Path(pdf_path).name,
                pages=pages,
                runtime_seconds=runtime,
                memory_peak_mb=peak_memory,
                memory_avg_mb=avg_memory,
                success=success,
                error_message="",
                tables_extracted=tables_count,
                text_length=0,  # Could extract if needed
                cost_estimate=pages * self.cost_models['docling']
            )
            
        except Exception as e:
            runtime = time.time() - start_time
            self.logger.error(f"Docling benchmark failed: {e}")
            
            return BenchmarkResult(
                method='docling',
                document=Path(pdf_path).name,
                pages=0,
                runtime_seconds=runtime,
                memory_peak_mb=0,
                memory_avg_mb=0,
                success=False,
                error_message=str(e),
                tables_extracted=0,
                text_length=0,
                cost_estimate=0
            )
    
    def benchmark_layoutparser(self, pdf_path: str) -> BenchmarkResult:
        """Benchmark LayoutParser extraction"""
        self.logger.info(f"Benchmarking LayoutParser on {pdf_path}")
        
        if LayoutParserExtractor is None:
            self.logger.error("LayoutParserExtractor not available")
            return BenchmarkResult(
                method='layoutparser',
                document=Path(pdf_path).name,
                pages=0,
                runtime_seconds=0,
                memory_peak_mb=0,
                memory_avg_mb=0,
                success=False,
                error_message="LayoutParserExtractor not available",
                tables_extracted=0,
                text_length=0,
                cost_estimate=0
            )
        
        start_time = time.time()
        
        try:
            extractor = LayoutParserExtractor(output_dir=str(self.output_dir / "layoutparser_bench"))
            
            # Measure memory during extraction
            result, peak_memory, avg_memory = self.measure_memory_usage(
                extractor.extract_from_pdf, pdf_path
            )
            
            runtime = time.time() - start_time
            
            # Extract metrics from result
            success = result is not None and result.get('processing_success', False)
            tables_count = len(result.get('tables', [])) if success else 0
            pages = result.get('total_pages', 0) if success else 0
            
            return BenchmarkResult(
                method='layoutparser',
                document=Path(pdf_path).name,
                pages=pages,
                runtime_seconds=runtime,
                memory_peak_mb=peak_memory,
                memory_avg_mb=avg_memory,
                success=success,
                error_message="",
                tables_extracted=tables_count,
                text_length=0,
                cost_estimate=pages * self.cost_models['layoutparser']
            )
            
        except Exception as e:
            runtime = time.time() - start_time
            self.logger.error(f"LayoutParser benchmark failed: {e}")
            
            return BenchmarkResult(
                method='layoutparser',
                document=Path(pdf_path).name,
                pages=0,
                runtime_seconds=runtime,
                memory_peak_mb=0,
                memory_avg_mb=0,
                success=False,
                error_message=str(e),
                tables_extracted=0,
                text_length=0,
                cost_estimate=0
            )
    
    def benchmark_pdfplumber(self, pdf_path: str) -> BenchmarkResult:
        """Benchmark PDFPlumber extraction"""
        self.logger.info(f"Benchmarking PDFPlumber on {pdf_path}")
        
        if PDFTableExtractor is None:
            self.logger.error("PDFTableExtractor not available")
            return BenchmarkResult(
                method='pdfplumber',
                document=Path(pdf_path).name,
                pages=0,
                runtime_seconds=0,
                memory_peak_mb=0,
                memory_avg_mb=0,
                success=False,
                error_message="PDFTableExtractor not available",
                tables_extracted=0,
                text_length=0,
                cost_estimate=0
            )
        
        start_time = time.time()
        
        try:
            extractor = PDFTableExtractor(output_dir=str(self.output_dir / "pdfplumber_bench"))
            
            # Measure memory during extraction
            result, peak_memory, avg_memory = self.measure_memory_usage(
                extractor.extract_from_pdf, pdf_path
            )
            
            runtime = time.time() - start_time
            
            # Extract metrics from result
            success = result is not None and (
                'tables' in result or 
                'total_pages' in result or
                result.get('processing_time', 0) > 0
            )
            tables_count = len(result.get('tables', [])) if result and 'tables' in result else 0
            pages = result.get('total_pages', 0) if result else 0
            
            return BenchmarkResult(
                method='pdfplumber',
                document=Path(pdf_path).name,
                pages=pages,
                runtime_seconds=runtime,
                memory_peak_mb=peak_memory,
                memory_avg_mb=avg_memory,
                success=success,
                error_message="",
                tables_extracted=tables_count,
                text_length=0,
                cost_estimate=pages * self.cost_models['pdfplumber']
            )
            
        except Exception as e:
            runtime = time.time() - start_time
            self.logger.error(f"PDFPlumber benchmark failed: {e}")
            
            return BenchmarkResult(
                method='pdfplumber',
                document=Path(pdf_path).name,
                pages=0,
                runtime_seconds=runtime,
                memory_peak_mb=0,
                memory_avg_mb=0,
                success=False,
                error_message=str(e),
                tables_extracted=0,
                text_length=0,
                cost_estimate=0
            )
    
    def run_comprehensive_benchmark(self, pdf_path: str, methods: List[str] = None) -> List[BenchmarkResult]:
        """Run benchmarks for all specified methods"""
        if methods is None:
            methods = ['docling', 'layoutparser', 'pdfplumber']
        
        results = []
        
        for method in methods:
            self.logger.info(f"Starting {method} benchmark...")
            
            # Force garbage collection before each test
            gc.collect()
            
            if method == 'docling':
                result = self.benchmark_docling(pdf_path)
            elif method == 'layoutparser':
                result = self.benchmark_layoutparser(pdf_path)
            elif method == 'pdfplumber':
                result = self.benchmark_pdfplumber(pdf_path)
            else:
                self.logger.warning(f"Unknown method: {method}")
                continue
            
            results.append(result)
            self.results.append(result)
            
            # Log result
            self.logger.info(f"{method} completed: {result.runtime_seconds:.2f}s, "
                           f"{result.memory_peak_mb:.1f}MB peak, "
                           f"Success: {result.success}")
        
        return results
    
    def generate_scaling_analysis(self) -> Dict[str, Any]:
        """Generate cost and performance scaling analysis"""
        if not self.results:
            return {}
        
        # Convert results to DataFrame for analysis
        df = pd.DataFrame([asdict(r) for r in self.results])
        
        # Calculate scaling metrics
        scaling_analysis = {
            'performance_per_method': {},
            'cost_projections': {},
            'bottleneck_analysis': {},
            'recommendations': {}
        }
        
        # Performance analysis by method
        for method in df['method'].unique():
            method_data = df[df['method'] == method]
            
            if len(method_data) > 0:
                scaling_analysis['performance_per_method'][method] = {
                    'avg_runtime_per_page': method_data['runtime_seconds'].mean() / method_data['pages'].mean() if method_data['pages'].mean() > 0 else 0,
                    'avg_memory_per_page': method_data['memory_peak_mb'].mean() / method_data['pages'].mean() if method_data['pages'].mean() > 0 else 0,
                    'success_rate': method_data['success'].mean(),
                    'total_runtime': method_data['runtime_seconds'].sum(),
                    'peak_memory': method_data['memory_peak_mb'].max()
                }
        
        # Cost projections for different scales
        scales = [100, 1000, 10000, 100000]  # pages
        
        for scale in scales:
            scaling_analysis['cost_projections'][f'{scale}_pages'] = {}
            
            for method in df['method'].unique():
                method_data = df[df['method'] == method]
                
                if len(method_data) > 0 and method_data['pages'].sum() > 0:
                    avg_cost_per_page = method_data['cost_estimate'].sum() / method_data['pages'].sum()
                    total_cost = scale * avg_cost_per_page
                    
                    scaling_analysis['cost_projections'][f'{scale}_pages'][method] = {
                        'total_cost': total_cost,
                        'cost_per_page': avg_cost_per_page
                    }
        
        return scaling_analysis
    
    def save_results(self):
        """Save all benchmark results and analysis"""
        # Save raw results
        results_file = self.output_dir / 'benchmark_results.json'
        
        # Convert numpy types to Python natives for JSON serialization
        def convert_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj
        
        def clean_for_json(data):
            if isinstance(data, dict):
                return {k: clean_for_json(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [clean_for_json(item) for item in data]
            else:
                return convert_types(data)
        
        results_data = {
            'system_info': self.system_info,
            'results': [asdict(r) for r in self.results],
            'scaling_analysis': self.generate_scaling_analysis()
        }
        
        clean_data = clean_for_json(results_data)
        
        with open(results_file, 'w') as f:
            json.dump(clean_data, f, indent=2)
        
        # Save as CSV for analysis
        if self.results:
            df = pd.DataFrame([asdict(r) for r in self.results])
            df.to_csv(self.output_dir / 'benchmark_results.csv', index=False)
        
        self.logger.info(f"Results saved to {self.output_dir}")


def main():
    """Main benchmarking script"""
    parser = argparse.ArgumentParser(description='Benchmark document extraction pipeline')
    parser.add_argument('--pdf', type=str, 
                       default='data/raw/pdf/nvda-20240128.pdf',
                       help='PDF file to benchmark')
    parser.add_argument('--output-dir', type=str, 
                       default='data/parsed/benchmarks',
                       help='Output directory for results')
    parser.add_argument('--methods', nargs='+', 
                       default=['docling', 'layoutparser', 'pdfplumber'],
                       help='Methods to benchmark')
    
    args = parser.parse_args()
    
    # Initialize benchmarker
    benchmarker = PerformanceBenchmarker(args.output_dir)
    
    print(f"Starting benchmark on {args.pdf}")
    print(f"Methods: {args.methods}")
    print(f"System: {benchmarker.system_info['cpu_count']} CPU cores, "
          f"{benchmarker.system_info['memory_total_gb']:.1f}GB RAM")
    
    # Run benchmarks
    results = benchmarker.run_comprehensive_benchmark(args.pdf, args.methods)
    
    # Save results
    benchmarker.save_results()
    
    # Print summary
    print("\n=== Benchmark Summary ===")
    for result in results:
        print(f"{result.method:15s}: {result.runtime_seconds:6.2f}s, "
              f"{result.memory_peak_mb:6.1f}MB, "
              f"Success: {result.success}")
    
    print(f"\nDetailed results saved to: {args.output_dir}")


if __name__ == "__main__":
    main()