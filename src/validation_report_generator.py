import os
import json
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime

class ValidationReportGenerator:
    def __init__(self, comparison_data: Dict[str, Any]):
        """Initialize the report generator with comparison data."""
        self.data = comparison_data
        self.summary = comparison_data['summary']
        self.matches = comparison_data['matches']
        self.mismatches = comparison_data['mismatches']
        self.unmatched_pdf = comparison_data['unmatched_pdf']
        self.unmatched_xbrl = comparison_data['unmatched_xbrl']
    
    def generate_detailed_report(self) -> Dict[str, Any]:
        """Generate a detailed validation report with analytics."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': self._generate_summary(),
            'mismatch_analysis': self._analyze_mismatches(),
            'table_coverage': self._analyze_table_coverage(),
            'recommendations': self._generate_recommendations()
        }
        return report
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate a comprehensive summary of the comparison results."""
        total = self.summary['total_comparisons']
        match_rate = (self.summary['matches'] / total) * 100 if total > 0 else 0
        
        return {
            'comparison_stats': {
                'total_comparisons': total,
                'total_matches': self.summary['matches'],
                'total_mismatches': self.summary['mismatches'],
                'match_rate': round(match_rate, 2),
                'unmatched_items': {
                    'pdf': self.summary['unmatched_pdf'],
                    'xbrl': self.summary['unmatched_xbrl']
                }
            },
            'quality_assessment': self._assess_data_quality()
        }
    
    def _analyze_mismatches(self) -> Dict[str, Any]:
        """Analyze patterns in mismatched data."""
        if not self.mismatches:
            return {'status': 'No mismatches found'}
        
        # Convert mismatches to DataFrame for analysis
        df = pd.DataFrame(self.mismatches)
        
        # Analyze differences
        diff_stats = {
            'max_difference': df['difference'].max(),
            'min_difference': df['difference'].min(),
            'avg_difference': df['difference'].mean(),
            'median_difference': df['difference'].median()
        }
        
        # Group mismatches by concept
        concept_groups = df.groupby('concept').size().to_dict()
        
        # Group by table
        table_groups = df.groupby('table_id').size().to_dict()
        
        return {
            'difference_statistics': diff_stats,
            'concept_distribution': concept_groups,
            'table_distribution': table_groups,
            'systematic_issues': self._identify_systematic_issues(df)
        }
    
    def _analyze_table_coverage(self) -> Dict[str, Any]:
        """Analyze the coverage of tables and concepts."""
        # Get unique tables
        tables = set(match['table_id'] for match in self.matches + self.mismatches)
        
        # Calculate coverage per table
        table_coverage = {}
        for table in tables:
            table_matches = sum(1 for m in self.matches if m['table_id'] == table)
            table_mismatches = sum(1 for m in self.mismatches if m['table_id'] == table)
            total = table_matches + table_mismatches
            
            if total > 0:
                coverage_rate = (table_matches / total) * 100
                table_coverage[table] = {
                    'total_values': total,
                    'matched': table_matches,
                    'mismatched': table_mismatches,
                    'coverage_rate': round(coverage_rate, 2)
                }
        
        return {
            'tables_analyzed': len(tables),
            'table_coverage': table_coverage
        }
    
    def _identify_systematic_issues(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify potential systematic issues in the mismatches."""
        issues = []
        
        # Check for rounding issues
        rounding_threshold = 0.01
        potential_rounding = df[df['difference'] <= rounding_threshold]
        if len(potential_rounding) > 0:
            issues.append({
                'type': 'rounding',
                'description': 'Potential rounding differences detected',
                'affected_count': len(potential_rounding),
                'affected_concepts': potential_rounding['concept'].unique().tolist()
            })
        
        # Check for scaling issues (e.g., thousands vs millions)
        scaling_factors = [1000, 1000000]
        for factor in scaling_factors:
            scaled_diff = df['difference'] / factor
            potential_scaling = df[abs(scaled_diff - scaled_diff.round()) < 0.1]
            if len(potential_scaling) > 0:
                issues.append({
                    'type': 'scaling',
                    'description': f'Potential scaling issue (factor: {factor})',
                    'affected_count': len(potential_scaling),
                    'affected_concepts': potential_scaling['concept'].unique().tolist()
                })
        
        # Check for sign issues
        potential_sign_issues = df[abs(df['difference']) * 2 == abs(df['xbrl_value']) + abs(df['pdf_value'])]
        if len(potential_sign_issues) > 0:
            issues.append({
                'type': 'sign',
                'description': 'Potential sign mismatches (positive vs negative)',
                'affected_count': len(potential_sign_issues),
                'affected_concepts': potential_sign_issues['concept'].unique().tolist()
            })
        
        return issues
    
    def _assess_data_quality(self) -> Dict[str, Any]:
        """Assess the overall quality of the data comparison."""
        total = self.summary['total_comparisons']
        match_rate = (self.summary['matches'] / total) * 100 if total > 0 else 0
        
        quality_level = 'high'
        if match_rate < 95:
            quality_level = 'medium'
        if match_rate < 80:
            quality_level = 'low'
        
        issues = []
        if self.summary['unmatched_pdf'] > 0:
            issues.append('Unmatched PDF values found')
        if self.summary['unmatched_xbrl'] > 0:
            issues.append('Unmatched XBRL facts found')
        if match_rate < 90:
            issues.append('Match rate below 90%')
        
        return {
            'quality_level': quality_level,
            'confidence_score': round(match_rate, 2),
            'identified_issues': issues
        }
    
    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """Generate recommendations based on the analysis."""
        recommendations = []
        
        # Based on match rate
        match_rate = (self.summary['matches'] / self.summary['total_comparisons'] * 100 
                     if self.summary['total_comparisons'] > 0 else 0)
        
        if match_rate < 95:
            recommendations.append({
                'priority': 'high',
                'area': 'Data Quality',
                'recommendation': 'Investigate tables with low match rates for potential extraction or alignment issues'
            })
        
        # Based on unmatched items
        if self.summary['unmatched_pdf'] > 0:
            recommendations.append({
                'priority': 'medium',
                'area': 'PDF Processing',
                'recommendation': 'Review PDF table extraction process for potential improvements in data capture'
            })
        
        if self.summary['unmatched_xbrl'] > 0:
            recommendations.append({
                'priority': 'medium',
                'area': 'XBRL Processing',
                'recommendation': 'Review XBRL fact mapping and consider additional context matching rules'
            })
        
        # Based on systematic issues
        df = pd.DataFrame(self.mismatches)
        if not df.empty:
            if (df['difference'].abs() < 0.01).any():
                recommendations.append({
                    'priority': 'low',
                    'area': 'Data Processing',
                    'recommendation': 'Consider adjusting rounding precision in comparison logic'
                })
        
        return recommendations
    
    def save_report(self, output_path: str) -> None:
        """Generate and save the validation report."""
        report = self.generate_detailed_report()
        
        # Save main report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save CSV summaries
        base_path = os.path.splitext(output_path)[0]
        
        # Save mismatches summary
        if self.mismatches:
            pd.DataFrame(self.mismatches).to_csv(f"{base_path}_mismatches.csv", index=False)
        
        # Save unmatched items summary
        unmatched_summary = {
            'pdf_unmatched': self.unmatched_pdf,
            'xbrl_unmatched': self.unmatched_xbrl
        }
        with open(f"{base_path}_unmatched.json", 'w') as f:
            json.dump(unmatched_summary, f, indent=2)

def main():
    # Example usage
    comparison_file = "path/to/comparison_results.json"
    output_dir = "path/to/output"
    
    # Load comparison results
    with open(comparison_file) as f:
        comparison_data = json.load(f)
    
    # Generate report
    generator = ValidationReportGenerator(comparison_data)
    output_path = os.path.join(output_dir, 'validation_report.json')
    generator.save_report(output_path)

if __name__ == "__main__":
    main()