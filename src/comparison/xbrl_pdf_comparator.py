"""XBRL to PDF comparison module."""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import sys

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from comparison.validation_enhancer import ValidationEnhancer
from comparison.text_matcher import find_best_match

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class XBRLPDFComparator:
    def __init__(self, config_path: str):
        """Initialize the comparator with configuration."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.mappings = self.config['concept_mappings']
        self.transformations = self.config['common_transformations']
        self.validation_rules = self.config['validation_rules']
        
        # Initialize validation enhancer
        tolerance = self.validation_rules['tolerance']['absolute_values']
        self.validator = ValidationEnhancer(tolerance=tolerance)
    
    def normalize_value(self, value: Any, value_type: str = 'monetary') -> Optional[float]:
        """Normalize a value based on its type and transformations."""
        if pd.isna(value):
            return None
            
        try:
            if isinstance(value, str):
                # Remove currency symbols and commas
                value = value.replace('$', '').replace(',', '').strip()
                
                # Handle parentheses for negative numbers
                if value.startswith('(') and value.endswith(')'):
                    value = '-' + value[1:-1]
                
                # Handle percentage values
                if value.endswith('%'):
                    value = float(value.rstrip('%'))
                    if value_type == 'percentage':
                        return value / 100
                    return value
                
                # Handle scale indicators
                if value[-1].upper() in {'K', 'M', 'B'}:
                    multiplier = {
                        'K': 1000,
                        'M': 1000000,
                        'B': 1000000000
                    }[value[-1].upper()]
                    return float(value[:-1]) * multiplier
            
            return float(value)
            
        except (ValueError, TypeError, IndexError):
            return None
    
    def match_table_type(self, table_data: Dict[str, Any]) -> str:
        """Match a table to its type based on content."""
        content = json.dumps(table_data).lower()
        
        # Check for keywords indicating table type
        if any(keyword in content for keyword in ['stock', 'share', 'repurchase']):
            return 'stock_transactions'
        elif any(keyword in content for keyword in ['intangible', 'patent', 'license']):
            return 'balance_sheet'
        elif any(keyword in content for keyword in ['revenue', 'income', 'expense']):
            return 'income_statement'
        elif any(keyword in content for keyword in ['cash', 'flow']):
            return 'cash_flow'
        
        return 'unknown'
    
    def get_xbrl_concepts(self, table_type: str, line_item: str) -> List[str]:
        """Get relevant XBRL concepts for a line item using fuzzy matching."""
        if table_type not in self.mappings:
            return []
        
        matches = []
        for concept, details in self.mappings[table_type].items():
            concept_clean = concept.replace('_', ' ')
            match, score = find_best_match(line_item, [concept_clean])
            
            if match and score > 0.7:  # Configurable threshold
                matches.append({
                    'concept': concept,
                    'xbrl_concepts': details['xbrl_concepts'],
                    'match_score': score,
                    'value_type': details.get('value_type', 'monetary')
                })
        
        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return [concept for match in matches for concept in match['xbrl_concepts']]
    
    def process_comparison(self, table_data: Dict[str, Any], 
                         xbrl_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process comparison between PDF table and XBRL data."""
        table_type = self.match_table_type(table_data)
        result = {
            'table_type': table_type,
            'file_name': table_data.get('original_file', 'unknown'),
            'comparisons': [],
            'status': 'analyzed',
            'timestamp': datetime.now().isoformat()
        }
        
        if table_type == 'unknown':
            result['status'] = 'skipped'
            result['reason'] = 'Unable to determine table type'
            return result
        
        validations = []
        
        # Process each line item
        for item in table_data['data']:
            line_item = item['line_item']
            xbrl_concepts = self.get_xbrl_concepts(table_type, line_item)
            
            # Group PDF values by fiscal year
            pdf_values = {}
            values = item['values']
            if len(values) == 6:  # [gross, amortization, net] * 2 years
                pdf_values['FY2024'] = values[0:3]  # Current year
                pdf_values['FY2023'] = values[3:6]  # Previous year
            
            comparison = {
                'line_item': line_item,
                'pdf_values': values,
                'value_pairs': pdf_values,
                'xbrl_concepts': xbrl_concepts,
                'matches': []
            }
            
            # Try to match values with XBRL concepts
            for concept in xbrl_concepts:
                if concept in xbrl_data:
                    for xbrl_fact in xbrl_data[concept]:
                        period = xbrl_fact['context']['id']
                        if period in pdf_values:
                            group = pdf_values[period]
                            xbrl_val = self.normalize_value(xbrl_fact['value'])
                            
                            # Compare with each value in the group
                            for i, pdf_val in enumerate(group):
                                context = {
                                    'fiscal_year': period,
                                    'value_index': i,
                                    'concept': concept
                                }
                                
                                validation = self.validator.validate_values(
                                    xbrl_val,
                                    self.normalize_value(pdf_val),
                                    context
                                )
                                
                                if validation['match']:
                                    value_type = ['gross', 'amortization', 'net'][i]
                                    comparison['matches'].append({
                                        'xbrl_concept': concept,
                                        'fiscal_year': period,
                                        'value_type': value_type,
                                        'xbrl_value': xbrl_fact,
                                        'pdf_value': pdf_val,
                                        'validation': validation
                                    })
                                
                                validations.append(validation)
            
            # Analyze patterns
            if len(values) == 6:
                for year in ['FY2024', 'FY2023']:
                    current = pdf_values[year]
                    context = {'fiscal_year': year}
                    
                    # Get value patterns
                    patterns = self.validator.analyze_patterns(current, context)
                    if patterns:
                        comparison.setdefault('patterns', []).extend(patterns)
                    
                    # Get year-over-year changes for FY2024
                    if year == 'FY2024':
                        previous = pdf_values['FY2023']
                        yoy = self.validator.analyze_year_over_year(
                            current, previous, context
                        )
                        if yoy:
                            comparison.setdefault('year_over_year', []).extend(yoy)
            
            # Add validation summary for this line item
            validation_summary = self.validator.generate_summary(validations)
            comparison['validation'] = validation_summary
            result['comparisons'].append(comparison)
        
        # Add overall analysis
        result['analysis'] = {
            'total_line_items': len(result['comparisons']),
            'matched_items': sum(1 for c in result['comparisons'] 
                               if c['validation']['successful_matches'] > 0),
            'pattern_matches': sum(len(c.get('patterns', [])) 
                                 for c in result['comparisons']),
            'year_over_year_changes': sum(len(c.get('year_over_year', [])) 
                                        for c in result['comparisons']),
            'issues': [
                {
                    'line_item': c['line_item'],
                    'issues': c['validation']['issues']
                }
                for c in result['comparisons']
                if c['validation']['issues']
            ]
        }
        
        return result

def main():
    # File paths
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(project_root, 'config', 'config.json')
    docling_path = os.path.join(project_root, 'data', 'parsed', 'docling', 'nvda-20240128',
                            'docling_extraction_results.json')
    layout_path = os.path.join(project_root, 'data', 'parsed', 'layout_parser', 'nvda-20240128',
                               'layout_parser_extraction_results.json')
    
    # Load data
    logger.info("Loading DocLing extraction results...")
    with open(docling_path, 'r') as f:
        docling_data = json.load(f)
        
    logger.info("Loading LayoutParser extraction results...")
    with open(layout_path, 'r') as f:
        layout_data = json.load(f)
        
    # Extract tables from docling data
    tables = []
    for page in docling_data['document_analysis']['content_elements']:
        for element in page.get('elements', []):
            if element.get('type') == 'table':
                tables.append(element)
                
    logger.info(f"Found {len(tables)} tables in DocLing results")
    
    # Initialize comparator and process
    comparator = XBRLPDFComparator(config_path)
    
    all_results = []
    for table in tables:
        # Compare DocLing and LayoutParser results
        docling_table = {
            'original_file': docling_data['pdf_name'],
            'data': table.get('data', []),
            'metadata': table.get('metadata', {})
        }
        
        # Find matching table in LayoutParser results
        layout_table = None
        for lt in layout_data.get('tables', []):
            if lt.get('page_number') == table.get('page_number'):
                layout_table = lt
                break
                
        if layout_table:
            comparison = comparator.process_comparison(docling_table, layout_table)
            all_results.append(comparison)
    
    # Save results
    output_path = os.path.join(project_root, 'data', 'parsed', 'comparison',
                              'docling_layout_comparison.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_tables': len(all_results),
            'results': all_results
        }, f, indent=2)
    
    logger.info(f"Comparison analysis saved to: {output_path}")

if __name__ == "__main__":
    main()