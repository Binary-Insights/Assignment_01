import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from .validation_enhancer import ValidationEnhancer

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
    
    def validate_units(self, xbrl_unit: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize unit information."""
        if not xbrl_unit or 'measure' not in xbrl_unit:
            return {'valid': False, 'reason': 'Missing unit information'}
            
        measure = xbrl_unit['measure'].lower()
        
        # Handle common currency units
        if 'iso4217:' in measure:
            currency = measure.split(':')[1]
            return {
                'valid': True,
                'type': 'currency',
                'currency': currency,
                'scale': 1  # Could be adjusted based on decimals attribute
            }
            
        # Handle pure numbers (like shares)
        if 'xbrli:pure' in measure:
            return {
                'valid': True,
                'type': 'pure',
                'scale': 1
            }
            
        # Handle percentages
        if 'xbrli:percent' in measure:
            return {
                'valid': True,
                'type': 'percentage',
                'scale': 0.01  # Convert to decimal
            }
            
        return {
            'valid': False,
            'reason': f'Unsupported unit type: {measure}'
        }

    def compare_values(self, xbrl_value: float, pdf_value: float, 
                      xbrl_unit: Dict[str, Any] = None,
                      value_type: str = 'monetary') -> Dict[str, Any]:
        """Compare two values using configured tolerance rules."""
        if pd.isna(xbrl_value) or pd.isna(pdf_value):
            return {
                'match': False,
                'difference': None,
                'reason': 'One or both values are missing',
                'severity': 'error'
            }
        
        try:
            # Validate and apply unit scaling
            unit_info = {'valid': True, 'type': 'monetary', 'scale': 1}
            if xbrl_unit:
                unit_info = self.validate_units(xbrl_unit)
                if not unit_info['valid']:
                    return {
                        'match': False,
                        'difference': None,
                        'reason': f'Unit validation failed: {unit_info["reason"]}',
                        'severity': 'error'
                    }
                
                # Apply unit scaling
                xbrl_value *= unit_info['scale']
            
            # Calculate difference
            difference = abs(xbrl_value - pdf_value)
            relative_diff = difference / abs(xbrl_value) if xbrl_value != 0 else difference
            
            # Use appropriate tolerance based on value type
            tolerance = (self.validation_rules['tolerance']['percentages'] 
                       if unit_info['type'] == 'percentage'
                       else self.validation_rules['tolerance']['absolute_values'])
            
            is_match = relative_diff <= tolerance
            
            # Generate detailed analysis
            result = {
                'match': is_match,
                'difference': float(difference),
                'relative_difference': float(relative_diff),
                'unit_info': unit_info,
                'severity': 'none' if is_match else 'warning'
            }
            
            # Add detailed reason for mismatch
            if not is_match:
                reasons = []
                if relative_diff > tolerance * 10:
                    reasons.append('Large discrepancy detected')
                    result['severity'] = 'error'
                elif relative_diff > tolerance * 2:
                    reasons.append('Moderate discrepancy')
                else:
                    reasons.append('Small discrepancy')
                    
                if abs(xbrl_value) >= 1000000 and abs(pdf_value) < 1000:
                    reasons.append('Possible scale mismatch (millions vs thousands)')
                elif abs(xbrl_value) >= 1000 and abs(pdf_value) < 10:
                    reasons.append('Possible scale mismatch (thousands vs units)')
                    
                if abs(xbrl_value + pdf_value) < tolerance:
                    reasons.append('Possible sign mismatch (+/-)')
                
                result['reason'] = '; '.join(reasons)
            else:
                result['reason'] = 'Values match within tolerance'
            
            return result
            
        except Exception as e:
            return {
                'match': False,
                'difference': None,
                'reason': f'Comparison error: {str(e)}',
                'severity': 'error'
            }
    
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
        
    def analyze_value_patterns(self, year: str, values: List[float]) -> List[Dict[str, Any]]:
        """Analyze numerical patterns in values."""
        patterns = []
        tolerance = self.validation_rules['tolerance']['absolute_values']
        
        # Pattern 1: Gross + Amortization = Net
        if len(values) == 3 and abs(values[0] + values[1] - values[2]) <= tolerance:
            patterns.append({
                'fiscal_year': year,
                'type': 'balance',
                'description': 'Gross + Amortization = Net',
                'values': {
                    'gross': values[0],
                    'amortization': values[1],
                    'net': values[2]
                }
            })
        
        # Pattern 2: Check for percentage relationships
        for i in range(len(values)):
            for j in range(i + 1, len(values)):
                if values[i] != 0:
                    ratio = values[j] / values[i]
                    if 0 < abs(ratio) <= 1:
                        patterns.append({
                            'fiscal_year': year,
                            'type': 'ratio',
                            'description': f'Value ratio: {ratio:.2%}',
                            'values': {
                                'base': values[i],
                                'derived': values[j],
                                'ratio': ratio
                            }
                        })
        
        return patterns

    def analyze_yoy_changes(self, year: str, current: List[float], 
                           previous: List[float]) -> List[Dict[str, Any]]:
        """Analyze year-over-year changes."""
        patterns = []
        
        for i, (curr, prev) in enumerate(zip(current, previous)):
            if prev != 0:
                change = (curr - prev) / abs(prev)
                
                pattern = {
                    'fiscal_year': year,
                    'type': 'yoy_change',
                    'value_index': i,
                    'description': f'Year-over-year change: {change:.2%}',
                    'values': {
                        'current': curr,
                        'previous': prev,
                        'change': change
                    }
                }
                
                # Add change classification
                if abs(change) > 0.5:
                    pattern['significance'] = 'major'
                elif abs(change) > 0.1:
                    pattern['significance'] = 'moderate'
                else:
                    pattern['significance'] = 'minor'
                
                patterns.append(pattern)
        
        return patterns
    
    def get_xbrl_concepts(self, table_type: str, line_item: str) -> List[Dict[str, Any]]:
        """Get relevant XBRL concepts for a line item using fuzzy matching."""
        from .text_matcher import find_best_match
        
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
        
        return [m['xbrl_concepts'] for m in matches] if matches else []
    
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
        
        # Process each line item
        for item in table_data['data']:
            line_item = item['line_item']
            xbrl_concepts = self.get_xbrl_concepts(table_type, line_item)
            
            # Group PDF values by fiscal year based on their position
            pdf_values = {}
            values = item['values']
            if len(values) == 6:  # Assuming pattern: [gross, amortization, net] * 2 years
                pdf_values['FY2024'] = values[0:3]  # Current year
                pdf_values['FY2023'] = values[3:6]  # Previous year
            
            comparison = {
                'line_item': line_item,
                'pdf_values': item['values'],
                'value_pairs': pdf_values,
                'xbrl_concepts': xbrl_concepts,
                'matches': []
            }
            
            # Try to match values with XBRL concepts
            for concept in xbrl_concepts:
                if concept in xbrl_data:
                    xbrl_values = xbrl_data[concept]
                    for xbrl_value in xbrl_values:
                        period = xbrl_value['context']['id']
                        if period in pdf_values:
                            # Compare values for matching fiscal year
                            pdf_group = pdf_values[period]
                            xbrl_val = self.normalize_value(xbrl_value['value'])
                            
                            # Try to match with gross, amortization, or net values
                            for i, pdf_val in enumerate(pdf_group):
                                match_result = self.compare_values(
                                    xbrl_val,
                                    self.normalize_value(pdf_val)
                                )
                                if match_result['match']:
                                    value_type = ['gross', 'amortization', 'net'][i]
                                    comparison['matches'].append({
                                        'xbrl_concept': concept,
                                        'fiscal_year': period,
                                        'value_type': value_type,
                                        'xbrl_value': xbrl_value,
                                        'pdf_value': pdf_val,
                                        'comparison': match_result
                                    })
            
            # Add value pattern analysis
            if len(item['values']) == 6:
                patterns = []
                for year in ['FY2024', 'FY2023']:
                    group = pdf_values[year]
                    
                    # Check standard patterns
                    patterns.extend(self.analyze_value_patterns(year, group))
                    
                    # Check year-over-year changes
                    if year == 'FY2024':
                        prev_group = pdf_values['FY2023']
                        yoy_patterns = self.analyze_yoy_changes(year, group, prev_group)
                        patterns.extend(yoy_patterns)
                
                if patterns:
                    comparison['patterns'] = patterns
            
            # Add validation summary
            validation = {
                'total_checks': len(comparison['matches']) + len(comparison.get('patterns', [])),
                'matched_values': len([m for m in comparison['matches'] if m['comparison']['match']]),
                'pattern_validations': len(comparison.get('patterns', [])),
                'issues': []
            }
            
            # Check for common issues
            if not comparison['matches']:
                validation['issues'].append({
                    'severity': 'warning',
                    'type': 'no_matches',
                    'message': 'No matching XBRL concepts found'
                })
            
            if any(not m['comparison']['match'] for m in comparison['matches']):
                mismatches = [m for m in comparison['matches'] if not m['comparison']['match']]
                validation['issues'].append({
                    'severity': 'error',
                    'type': 'value_mismatch',
                    'message': f'Found {len(mismatches)} value mismatches',
                    'details': [m['comparison']['reason'] for m in mismatches]
                })
            
            comparison['validation'] = validation
            results['comparisons'].append(comparison)
            
    # Add overall analysis
    results['analysis'] = {
        'total_line_items': len(results['comparisons']),
        'matched_items': sum(1 for c in results['comparisons'] if c.get('matches')),
        'pattern_matches': sum(len(c.get('patterns', [])) for c in results['comparisons']),
        'validation_issues': [
            {
                'line_item': c['line_item'],
                'issues': c['validation']['issues']
            }
            for c in results['comparisons']
            if c.get('validation', {}).get('issues')
        ]
    }
    
    return results

def analyze_value_patterns(self, year: str, values: List[float]) -> List[Dict[str, Any]]:
    """Analyze numerical patterns in values."""
    patterns = []
    tolerance = self.validation_rules['tolerance']['absolute_values']
    
    # Pattern 1: Gross + Amortization = Net
    if len(values) == 3 and abs(values[0] + values[1] - values[2]) <= tolerance:
        patterns.append({
            'fiscal_year': year,
            'type': 'balance',
            'description': 'Gross + Amortization = Net',
            'values': {
                'gross': values[0],
                'amortization': values[1],
                'net': values[2]
            }
        })
    
    # Pattern 2: Check for percentage relationships
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            ratio = values[j] / values[i] if values[i] != 0 else 0
            if 0 < abs(ratio) <= 1:
                patterns.append({
                    'fiscal_year': year,
                    'type': 'ratio',
                    'description': f'Value ratio: {ratio:.2%}',
                    'values': {
                        'base': values[i],
                        'derived': values[j],
                        'ratio': ratio
                    }
                })
    
    return patterns

def analyze_yoy_changes(self, year: str, current: List[float], 
                       previous: List[float]) -> List[Dict[str, Any]]:
    """Analyze year-over-year changes."""
    patterns = []
    
    for i, (curr, prev) in enumerate(zip(current, previous)):
        if prev != 0:
            change = (curr - prev) / abs(prev)
            
            pattern = {
                'fiscal_year': year,
                'type': 'yoy_change',
                'value_index': i,
                'description': f'Year-over-year change: {change:.2%}',
                'values': {
                    'current': curr,
                    'previous': prev,
                    'change': change
                }
            }
            
            # Add change classification
            if abs(change) > 0.5:
                pattern['significance'] = 'major'
            elif abs(change) > 0.1:
                pattern['significance'] = 'moderate'
            else:
                pattern['significance'] = 'minor'
            
            patterns.append(pattern)
    
    return patterns
        
        # Add summary statistics
        total_items = len(results['comparisons'])
        matched_items = sum(1 for comp in results['comparisons'] if comp['matches'])
        
        results['summary'] = {
            'total_items': total_items,
            'matched_items': matched_items,
            'match_rate': (matched_items / total_items) if total_items > 0 else 0
        }
        
        return results

def main():
    # File paths
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, 'config', 'xbrl_mappings.json')
    results_path = os.path.join(project_root, 'data', 'parsed', 'nvda-20240128', 
                               'comparison', 'table_extraction_results.json')
    xbrl_path = os.path.join(project_root, 'data', 'parsed', 'nvda-20240128',
                            'xbrl_data.json')
    
    # Load extracted table results
    with open(results_path, 'r') as f:
        table_results = json.load(f)
    
    # Load XBRL data
    with open(xbrl_path, 'r') as f:
        xbrl_data = json.load(f)['facts']
    
    # Initialize comparator
    comparator = XBRLPDFComparator(config_path)
    
    # Process each table
    comparisons = []
    for table in table_results['tables']:
        comparison = comparator.process_comparison(table, xbrl_data)
        comparisons.append(comparison)
    
    # Save comparison results
    output_path = os.path.join(os.path.dirname(results_path), 'comparison_analysis.json')
    with open(output_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_tables': len(comparisons),
            'comparisons': comparisons,
            'summary': {
                'total_tables': len(comparisons),
                'matched_tables': sum(1 for c in comparisons 
                                    if c.get('table_type') != 'unknown'),
                'total_line_items': sum(len(c.get('comparisons', []))
                                      for c in comparisons),
                'matched_items': sum(len([i for i in c.get('comparisons', [])
                                       if i.get('matches')])
                                  for c in comparisons)
            }
        }, f, indent=2)
    
    logger.info(f"Comparison analysis saved to: {output_path}")

if __name__ == "__main__":
    main()