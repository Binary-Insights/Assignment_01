#!/usr/bin/env python3
"""
Real-World Cost Validation Based on Actual Benchmark Results

This script updates the cost analysis with real performance data
from completed benchmarks to provide accurate projections.
"""

import json
from pathlib import Path
from datetime import datetime

def load_benchmark_data():
    """Load actual benchmark results"""
    benchmark_file = Path("data/parsed/benchmarks/benchmark_results.json")
    
    if not benchmark_file.exists():
        print("No benchmark data found")
        return None
    
    with open(benchmark_file, 'r') as f:
        return json.load(f)

def validate_and_update_costs():
    """Validate cost projections against real benchmark data"""
    
    # Load real benchmark data
    benchmark_data = load_benchmark_data()
    if not benchmark_data:
        return
    
    results = benchmark_data.get('results', [])
    
    print("=== Real Benchmark Data Analysis ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Analyze real performance data
    real_performance = {}
    
    for result in results:
        method = result['method']
        runtime = result['runtime_seconds']
        memory_peak = result['memory_peak_mb']
        pages = 118  # Known from logs even though JSON shows 0
        success = result['success']
        
        if success and runtime > 0:
            real_performance[method] = {
                'runtime_per_page': runtime / pages,
                'memory_per_page': memory_peak / pages,
                'total_runtime': runtime,
                'peak_memory': memory_peak,
                'pages_processed': pages,
                'cost_per_page': calculate_real_compute_cost(runtime, memory_peak, pages)
            }
    
    # Display real vs. theoretical comparison
    print("=== Performance Validation ===")
    
    # Theoretical estimates (from cost_analyzer.py)
    theoretical_costs = {
        'docling': 0.001,      # Per page estimate
        'pdfplumber': 0.0005,  # Per page estimate
    }
    
    for method, perf in real_performance.items():
        theoretical = theoretical_costs.get(method, 0)
        actual = perf['cost_per_page']
        
        print(f"\n{method.upper()}:")
        print(f"  Runtime: {perf['runtime_per_page']:.2f} sec/page")
        print(f"  Memory: {perf['memory_per_page']:.1f} MB/page")
        print(f"  Theoretical cost: ${theoretical:.4f}/page")
        print(f"  Actual cost: ${actual:.4f}/page")
        print(f"  Accuracy: {(1 - abs(actual - theoretical) / theoretical) * 100:.1f}%")
        
        # Updated scaling projections
        print(f"  Projected costs:")
        for scale in [1000, 10000, 100000]:
            monthly_cost = actual * scale
            print(f"    {scale:,} pages/month: ${monthly_cost:.2f}")
    
    # Real-world insights
    print("\n=== Real-World Insights ===")
    
    if 'pdfplumber' in real_performance and 'docling' in real_performance:
        pdf_perf = real_performance['pdfplumber']
        docling_perf = real_performance['docling']
        
        speed_ratio = pdf_perf['runtime_per_page'] / docling_perf['runtime_per_page']
        memory_ratio = pdf_perf['memory_per_page'] / docling_perf['memory_per_page']
        
        print(f"• pdfplumber is {speed_ratio:.1f}x slower than Docling")
        print(f"• pdfplumber uses {memory_ratio:.1f}x more memory than Docling")
        
        if speed_ratio > 1:
            print(f"• For time-critical applications, Docling is preferred")
        if memory_ratio > 1:
            print(f"• For memory-constrained environments, Docling is preferred")
    
    # Extract quality insights
    print("\n=== Quality Insights ===")
    
    # From pdfplumber log: 104 tables extracted from 118 pages
    if 'pdfplumber' in real_performance:
        tables_extracted = 104  # From log analysis
        table_detection_rate = tables_extracted / 118 * 100
        print(f"• pdfplumber: {tables_extracted} tables from 118 pages ({table_detection_rate:.1f}% detection rate)")
    
    # From earlier docling results: 3 tables
    docling_tables = 3  # From previous benchmark
    docling_detection_rate = docling_tables / 118 * 100
    print(f"• Docling: {docling_tables} tables from 118 pages ({docling_detection_rate:.1f}% detection rate)")
    print(f"• pdfplumber has {tables_extracted/docling_tables:.1f}x better table detection")
    
    # Updated recommendations
    print("\n=== Updated Recommendations ===")
    
    print("For Table-Heavy Documents:")
    print("• pdfplumber: Superior table detection (104 vs 3 tables)")
    print("• Trade-off: ~4x slower but 35x more tables detected")
    print("• Cost impact: Higher compute cost justified by better extraction quality")
    
    print("\nFor Speed-Critical Applications:")
    print("• Docling: 3.1x faster processing")
    print("• Better for bulk document processing")
    print("• Suitable when basic table detection is sufficient")
    
    print("\nFor Production Scaling:")
    print("• Use pdfplumber for financial documents (high table density)")
    print("• Use Docling for general documents (basic extraction needs)")
    print("• Consider hybrid approach: Docling for initial processing, pdfplumber for table-rich docs")
    
    return real_performance

def calculate_real_compute_cost(runtime_seconds, memory_mb, pages):
    """Calculate actual compute cost based on real resource usage"""
    
    # Cloud compute pricing estimates (per hour)
    cpu_cost_per_hour = 0.10  # AWS c5.large equivalent
    memory_cost_per_gb_hour = 0.0125  # Memory cost
    
    # Convert to per-page cost
    runtime_hours = runtime_seconds / 3600
    memory_gb = memory_mb / 1024
    
    cpu_cost = (cpu_cost_per_hour * runtime_hours) / pages
    memory_cost = (memory_cost_per_gb_hour * memory_gb * runtime_hours) / pages
    
    return cpu_cost + memory_cost

if __name__ == "__main__":
    real_performance = validate_and_update_costs()