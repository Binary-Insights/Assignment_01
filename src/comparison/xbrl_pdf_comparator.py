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
        if pd.isna(value) or value == '':
            return None
            
        try:
            if isinstance(value, (int, float)):
                return float(value)
                
            if isinstance(value, str):
                # Remove currency symbols, commas, and whitespace
                value = value.replace('$', '').replace(',', '').strip()
                
                # Handle parentheses for negative numbers
                if value.startswith('(') and value.endswith(')'):
                    value = '-' + value[1:-1]
                
                # Handle different formats of negative numbers
                if value.startswith('−'):  # Unicode minus
                    value = '-' + value[1:]
                
                # Handle percentage values
                if value.endswith('%'):
                    value = float(value.rstrip('%'))
                    if value_type == 'percentage':
                        return value / 100
                    return value
                    
                # Handle text representations
                if value.lower() == 'none' or value.lower() == 'nil':
                    return 0.0
                    
                # Handle special notations
                if '*' in value:  # Footnote indicator
                    value = value.replace('*', '').strip()
                    
                # Remove any remaining non-numeric characters except . and -
                value = ''.join(c for c in value if c.isdigit() or c in '.-')
                
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
        """Match a table to its type based on content and structure."""
        content = json.dumps(table_data).lower()
        
        # Check for date patterns first
        if any(month.lower() in content for month in [
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december'
        ]):
            # This might be a periodic report
            if any(word in content for word in ['quarter', 'qtd', 'q1', 'q2', 'q3', 'q4']):
                return 'quarterly_summary'
            if any(word in content for word in ['ytd', 'year to date', 'fiscal year']):
                return 'annual_summary'
        
        # Financial statement indicators
        balance_sheet_keywords = [
            'assets', 'liabilities', 'equity', 'intangible', 'patent', 'license',
            'goodwill', 'inventory', 'receivables', 'payables', 'debt', 
            'current assets', 'current liabilities', 'net book value',
            'accumulated depreciation', 'carrying amount'
        ]
        
        income_statement_keywords = [
            'revenue', 'income', 'expense', 'profit', 'loss', 'earnings',
            'cost of goods', 'operating expenses', 'tax', 'net income',
            'gross margin', 'ebitda', 'depreciation', 'amortization'
        ]
        
        cash_flow_keywords = [
            'cash flow', 'operating activities', 'investing activities',
            'financing activities', 'capital expenditures', 'dividends paid',
            'proceeds from', 'payments for', 'net cash'
        ]
        
        stockholders_equity_keywords = [
            'stock', 'share', 'repurchase', 'dividend', 'retained earnings',
            'additional paid-in capital', 'treasury stock', 'common stock'
        ]
        
        # Count matches for each type
        matches = {
            'balance_sheet': sum(1 for kw in balance_sheet_keywords if kw in content),
            'income_statement': sum(1 for kw in income_statement_keywords if kw in content),
            'cash_flow': sum(1 for kw in cash_flow_keywords if kw in content),
            'stockholders_equity': sum(1 for kw in stockholders_equity_keywords if kw in content)
        }
        
        # Additional context checks
        if 'data' in table_data:
            table_items = [str(item).lower() for item in table_data['data']]
            
            # Look for common patterns
            has_parentheses = any('(' in str(item) and ')' in str(item) for item in table_items)
            has_percentages = any('%' in str(item) for item in table_items)
            has_subtotals = any('total' in str(item).lower() for item in table_items)
            has_dates = any('20' in str(item) and any(m in str(item).lower() for m in [
                'jan', 'feb', 'mar', 'apr', 'may', 'jun',
                'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
            ]) for item in table_items)
            
            # Check for numeric patterns
            numeric_items = []
            for item in table_items:
                try:
                    if isinstance(item, (int, float)):
                        numeric_items.append(float(item))
                    elif isinstance(item, str) and any(c.isdigit() for c in item):
                        cleaned = ''.join(c for c in item if c.isdigit() or c in '.-')
                        if cleaned:
                            numeric_items.append(float(cleaned))
                except ValueError:
                    continue
            
            has_increasing_sequence = False
            has_paired_values = False
            if len(numeric_items) >= 3:
                # Check for increasing/decreasing sequences
                differences = [numeric_items[i+1] - numeric_items[i] for i in range(len(numeric_items)-1)]
                has_increasing_sequence = all(d >= 0 for d in differences) or all(d <= 0 for d in differences)
                
                # Check for paired values (common in financial statements)
                if len(numeric_items) % 2 == 0:
                    pairs = list(zip(numeric_items[::2], numeric_items[1::2]))
                    has_paired_values = any(abs(p[0] - p[1]) > 0 for p in pairs)
            
            # Adjust scores based on patterns
            if has_parentheses and has_subtotals:
                matches['balance_sheet'] += 1
                matches['income_statement'] += 1
                
            if has_dates and has_increasing_sequence:
                matches['income_statement'] += 2  # Time series data is common in income statements
                
            if has_paired_values:
                matches['balance_sheet'] += 1  # Paired values (e.g., cost/accumulated) are common in balance sheets
            
            if has_percentages:
                matches['income_statement'] += 2  # More common in income statements
            
            # Check for year-over-year comparisons
            if any('20' in str(item) for item in table_items):  # Year indicators
                matches['income_statement'] += 1
                matches['balance_sheet'] += 1
        
        # Return the type with the most matches
        if max(matches.values()) > 0:
            return max(matches.items(), key=lambda x: x[1])[0]
        
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
    config_path = os.path.join(project_root, 'config', 'xbrl_mappings.json')
    results_path = os.path.join(project_root, 'data', 'parsed', 'nvda-20240128',
                             'comparison', 'table_extraction_results.json')
    xbrl_path = os.path.join(project_root, 'data', 'parsed', 'nvda-20240128',
                          'xbrl_data.json')
    
    # Load data
    logger.info("Loading extraction results...")
    with open(results_path, 'r') as f:
        extraction_data = json.load(f)
        
    logger.info("Loading XBRL data...")
    with open(xbrl_path, 'r') as f:
        xbrl_data = json.load(f)
        
    # Extract tables from the extraction results
    tables = []
    if 'tables' in extraction_data:
        tables = extraction_data['tables']
    else:
        logger.warning("No tables found in extraction results")
                
    logger.info(f"Found {len(tables)} tables in DocLing results")
    
    # Initialize comparator and process
    comparator = XBRLPDFComparator(config_path)
    
    all_results = []
    for table in tables:
        # Process each table
        table_data = {
            'original_file': extraction_data.get('pdf_name', 'unknown'),
            'data': table.get('data', []),
            'metadata': table.get('metadata', {})
        }
        
        # Compare with XBRL data
        comparison = comparator.process_comparison(table_data, xbrl_data)
        if comparison['status'] != 'skipped':
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