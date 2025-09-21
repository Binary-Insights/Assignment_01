#!/usr/bin/env python3
"""
Cost Analysis Framework for Document Processing Pipeline

This script provides detailed cost projections and scaling analysis
for cloud vs open-source document extraction solutions.

Features:
- Real-world pricing models
- Hardware cost calculations
- Scaling projections
- ROI analysis
- Break-even calculations
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class CostModel:
    """Cost model for a document processing method"""
    method: str
    cost_per_page: float
    setup_cost: float
    monthly_minimum: float
    free_tier_pages: int
    currency: str = "USD"


@dataclass
class HardwareCost:
    """Hardware cost modeling"""
    cpu_cores: int
    memory_gb: int
    storage_gb: int
    gpu_enabled: bool
    monthly_cost: float
    provider: str


class CostAnalyzer:
    """
    Comprehensive cost analysis for document processing pipelines
    """
    
    def __init__(self):
        """Initialize cost models based on real-world pricing"""
        
        # Cloud service pricing (as of 2024)
        self.cloud_costs = {
            'aws_textract': CostModel(
                method='aws_textract',
                cost_per_page=0.015,  # Table detection
                setup_cost=0,
                monthly_minimum=0,
                free_tier_pages=1000
            ),
            'aws_textract_text': CostModel(
                method='aws_textract_text', 
                cost_per_page=0.0015,  # Text only
                setup_cost=0,
                monthly_minimum=0,
                free_tier_pages=1000
            ),
            'google_document_ai': CostModel(
                method='google_document_ai',
                cost_per_page=0.015,  # Form parser
                setup_cost=0,
                monthly_minimum=0,
                free_tier_pages=1000
            ),
            'azure_form_recognizer': CostModel(
                method='azure_form_recognizer',
                cost_per_page=0.01,   # Layout analysis
                setup_cost=0,
                monthly_minimum=0,
                free_tier_pages=5000
            )
        }
        
        # Hardware configurations for open-source solutions
        self.hardware_configs = {
            'basic_cpu': HardwareCost(
                cpu_cores=4,
                memory_gb=16,
                storage_gb=100,
                gpu_enabled=False,
                monthly_cost=50,  # Cloud VM estimate
                provider='AWS EC2 t3.xlarge'
            ),
            'high_performance_cpu': HardwareCost(
                cpu_cores=16,
                memory_gb=64,
                storage_gb=500,
                gpu_enabled=False,
                monthly_cost=200,  # Cloud VM estimate  
                provider='AWS EC2 m5.4xlarge'
            ),
            'gpu_accelerated': HardwareCost(
                cpu_cores=8,
                memory_gb=32,
                storage_gb=200,
                gpu_enabled=True,
                monthly_cost=300,  # Cloud GPU instance
                provider='AWS EC2 p3.2xlarge'
            ),
            'on_premise_basic': HardwareCost(
                cpu_cores=8,
                memory_gb=32,
                storage_gb=1000,
                gpu_enabled=False,
                monthly_cost=25,   # Amortized hardware cost
                provider='On-premise server'
            )
        }
        
        # Open-source compute costs (estimated)
        self.compute_costs = {
            'docling': 0.001,        # Per page compute cost
            'layoutparser': 0.001,   # Per page compute cost
            'pdfplumber': 0.0005,    # Per page compute cost
            'camelot': 0.0005       # Per page compute cost
        }
    
    def calculate_cloud_cost(self, method: str, pages: int, months: int = 1) -> Dict[str, float]:
        """Calculate total cost for cloud service"""
        if method not in self.cloud_costs:
            return {'error': f'Unknown method: {method}'}
        
        model = self.cloud_costs[method]
        
        # Apply free tier
        billable_pages = max(0, pages - (model.free_tier_pages * months))
        
        costs = {
            'base_cost': billable_pages * model.cost_per_page,
            'setup_cost': model.setup_cost,
            'monthly_minimum': model.monthly_minimum * months,
            'free_tier_savings': min(pages, model.free_tier_pages * months) * model.cost_per_page
        }
        
        costs['total_cost'] = max(
            costs['base_cost'] + costs['setup_cost'],
            costs['monthly_minimum']
        )
        
        costs['effective_cost_per_page'] = costs['total_cost'] / pages if pages > 0 else 0
        
        return costs
    
    def calculate_opensource_cost(self, method: str, pages: int, hardware_config: str, months: int = 1) -> Dict[str, float]:
        """Calculate total cost for open-source solution"""
        if method not in self.compute_costs:
            return {'error': f'Unknown method: {method}'}
        
        if hardware_config not in self.hardware_configs:
            return {'error': f'Unknown hardware config: {hardware_config}'}
        
        compute_cost_per_page = self.compute_costs[method]
        hardware = self.hardware_configs[hardware_config]
        
        costs = {
            'compute_cost': pages * compute_cost_per_page,
            'hardware_cost': hardware.monthly_cost * months,
            'setup_cost': 0,  # Assuming software is free
            'maintenance_cost': hardware.monthly_cost * 0.1 * months  # 10% of hardware cost
        }
        
        costs['total_cost'] = sum(costs.values())
        costs['effective_cost_per_page'] = costs['total_cost'] / pages if pages > 0 else 0
        
        return costs
    
    def compare_scaling_scenarios(self, scenarios: List[int]) -> pd.DataFrame:
        """Compare costs across different scaling scenarios"""
        results = []
        
        for pages in scenarios:
            # Cloud costs
            for method in self.cloud_costs.keys():
                cloud_cost = self.calculate_cloud_cost(method, pages)
                results.append({
                    'pages': pages,
                    'method': method,
                    'type': 'cloud',
                    'total_cost': cloud_cost['total_cost'],
                    'cost_per_page': cloud_cost['effective_cost_per_page'],
                    'configuration': 'managed_service'
                })
            
            # Open-source costs
            for os_method in self.compute_costs.keys():
                for hw_config in self.hardware_configs.keys():
                    os_cost = self.calculate_opensource_cost(os_method, pages, hw_config)
                    results.append({
                        'pages': pages,
                        'method': os_method,
                        'type': 'open_source',
                        'total_cost': os_cost['total_cost'],
                        'cost_per_page': os_cost['effective_cost_per_page'],
                        'configuration': hw_config
                    })
        
        return pd.DataFrame(results)
    
    def find_break_even_points(self) -> Dict[str, Dict[str, int]]:
        """Find break-even points where open-source becomes cheaper"""
        break_even_points = {}
        
        # Test range of page volumes
        test_volumes = range(100, 100000, 1000)
        
        for cloud_method in self.cloud_costs.keys():
            break_even_points[cloud_method] = {}
            
            for os_method in self.compute_costs.keys():
                for hw_config in self.hardware_configs.keys():
                    
                    for pages in test_volumes:
                        cloud_cost = self.calculate_cloud_cost(cloud_method, pages)['total_cost']
                        os_cost = self.calculate_opensource_cost(os_method, pages, hw_config)['total_cost']
                        
                        if os_cost < cloud_cost:
                            config_key = f"{os_method}_{hw_config}"
                            break_even_points[cloud_method][config_key] = pages
                            break
        
        return break_even_points
    
    def generate_cost_report(self, benchmark_file: str = None) -> Dict[str, Any]:
        """Generate comprehensive cost analysis report"""
        
        # Load benchmark data if available
        performance_data = {}
        if benchmark_file and Path(benchmark_file).exists():
            with open(benchmark_file, 'r') as f:
                benchmark_data = json.load(f)
                performance_data = benchmark_data.get('results', [])
        
        # Generate scaling scenarios
        scenarios = [100, 1000, 5000, 10000, 50000, 100000]
        comparison_df = self.compare_scaling_scenarios(scenarios)
        
        # Find break-even points
        break_even = self.find_break_even_points()
        
        # Calculate ROI projections
        roi_analysis = self._calculate_roi_projections(comparison_df)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'cost_comparison': comparison_df.to_dict('records'),
            'break_even_analysis': break_even,
            'roi_projections': roi_analysis,
            'recommendations': self._generate_recommendations(comparison_df, break_even),
            'performance_integration': performance_data
        }
        
        return report
    
    def _calculate_roi_projections(self, comparison_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate ROI for different approaches"""
        
        # Base case: AWS Textract
        base_costs = comparison_df[
            (comparison_df['method'] == 'aws_textract') & 
            (comparison_df['type'] == 'cloud')
        ].copy()
        
        roi_data = []
        
        for pages in comparison_df['pages'].unique():
            base_cost = base_costs[base_costs['pages'] == pages]['total_cost'].iloc[0]
            
            alternatives = comparison_df[
                (comparison_df['pages'] == pages) & 
                (comparison_df['method'] != 'aws_textract')
            ]
            
            for _, alt in alternatives.iterrows():
                savings = base_cost - alt['total_cost']
                roi_percent = (savings / base_cost * 100) if base_cost > 0 else 0
                
                roi_data.append({
                    'pages': pages,
                    'alternative': f"{alt['method']}_{alt['configuration']}",
                    'cost_savings': savings,
                    'roi_percent': roi_percent,
                    'payback_months': 1 if savings > 0 else float('inf')
                })
        
        return roi_data
    
    def _generate_recommendations(self, comparison_df: pd.DataFrame, break_even: Dict) -> List[str]:
        """Generate strategic recommendations"""
        recommendations = []
        
        # Find most cost-effective solutions
        for pages in [1000, 10000, 100000]:
            subset = comparison_df[comparison_df['pages'] == pages]
            cheapest = subset.loc[subset['total_cost'].idxmin()]
            
            recommendations.append(
                f"For {pages:,} pages: {cheapest['method']} with {cheapest['configuration']} "
                f"(${cheapest['total_cost']:.2f}, ${cheapest['cost_per_page']:.4f}/page)"
            )
        
        # Break-even insights
        if break_even:
            for cloud_method, alternatives in break_even.items():
                if alternatives:
                    min_break_even = min(alternatives.values())
                    recommendations.append(
                        f"Open-source becomes cheaper than {cloud_method} at {min_break_even:,} pages"
                    )
        
        return recommendations
    
    def save_analysis(self, output_dir: str = "data/parsed/benchmarks"):
        """Save comprehensive cost analysis"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate full report
        report = self.generate_cost_report(str(output_path / "benchmark_results.json"))
        
        # Save report
        with open(output_path / "cost_analysis.json", 'w') as f:
            # Convert numpy types to Python natives for JSON serialization
            def convert_types(obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return obj
            
            # Recursively convert numpy types
            def clean_for_json(data):
                if isinstance(data, dict):
                    return {k: clean_for_json(v) for k, v in data.items()}
                elif isinstance(data, list):
                    return [clean_for_json(item) for item in data]
                else:
                    return convert_types(data)
            
            clean_report = clean_for_json(report)
            json.dump(clean_report, f, indent=2)
        
        # Save comparison table
        comparison_df = pd.DataFrame(report['cost_comparison'])
        comparison_df.to_csv(output_path / "cost_comparison.csv", index=False)
        
        print(f"Cost analysis saved to {output_path}")
        
        return report


def main():
    """Main cost analysis script"""
    analyzer = CostAnalyzer()
    
    print("Generating comprehensive cost analysis...")
    
    # Run analysis
    report = analyzer.save_analysis("data/parsed/benchmarks")
    
    # Print key insights
    print("\n=== Key Cost Insights ===")
    for rec in report['recommendations']:
        print(f"• {rec}")
    
    print(f"\nDetailed analysis saved to: data/parsed/benchmarks/cost_analysis.json")


if __name__ == "__main__":
    main()