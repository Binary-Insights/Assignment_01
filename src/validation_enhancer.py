"""Enhanced validation module for XBRL-PDF comparison."""

import logging
from typing import Dict, List, Any, Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class ValidationEnhancer:
    def __init__(self, tolerance: float = 0.01):
        """Initialize with configurable tolerance."""
        self.tolerance = tolerance
    
    def validate_values(self, xbrl_val: float, pdf_val: float, 
                       context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a pair of values with detailed analysis."""
        if xbrl_val is None or pdf_val is None:
            return {
                'match': False,
                'severity': 'error',
                'reason': 'Missing value',
                'details': {
                    'xbrl_value': xbrl_val,
                    'pdf_value': pdf_val
                }
            }
        
        diff = abs(xbrl_val - pdf_val)
        rel_diff = diff / abs(xbrl_val) if xbrl_val != 0 else float('inf')
        
        result = {
            'match': rel_diff <= self.tolerance,
            'absolute_difference': diff,
            'relative_difference': rel_diff,
            'details': {
                'xbrl_value': xbrl_val,
                'pdf_value': pdf_val,
                'context': context
            }
        }
        
        if not result['match']:
            # Analyze potential causes
            if abs(xbrl_val + pdf_val) <= self.tolerance:
                result['reason'] = 'Sign mismatch'
                result['severity'] = 'error'
            elif abs(xbrl_val) > 1000 * abs(pdf_val):
                result['reason'] = 'Scale mismatch (thousands)'
                result['severity'] = 'warning'
            elif abs(xbrl_val) > 1000000 * abs(pdf_val):
                result['reason'] = 'Scale mismatch (millions)'
                result['severity'] = 'warning'
            elif rel_diff > 0.5:
                result['reason'] = 'Large discrepancy'
                result['severity'] = 'error'
            else:
                result['reason'] = 'Small discrepancy'
                result['severity'] = 'warning'
        
        return result
    
    def analyze_patterns(self, values: List[float], 
                        context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze numerical patterns in a set of values."""
        patterns = []
        
        # Check for basic arithmetic relationships
        if len(values) >= 3:
            for i in range(len(values)-2):
                for j in range(i+1, len(values)-1):
                    for k in range(j+1, len(values)):
                        # Check if a + b = c
                        if abs(values[i] + values[j] - values[k]) <= self.tolerance:
                            patterns.append({
                                'type': 'sum',
                                'description': f'Value[{i}] + Value[{j}] = Value[{k}]',
                                'values': {
                                    'a': values[i],
                                    'b': values[j],
                                    'sum': values[k]
                                },
                                'context': context
                            })
                        # Check if a - b = c
                        if abs(values[i] - values[j] - values[k]) <= self.tolerance:
                            patterns.append({
                                'type': 'difference',
                                'description': f'Value[{i}] - Value[{j}] = Value[{k}]',
                                'values': {
                                    'a': values[i],
                                    'b': values[j],
                                    'difference': values[k]
                                },
                                'context': context
                            })
        
        # Check for percentage relationships
        for i in range(len(values)):
            for j in range(len(values)):
                if i != j and values[i] != 0:
                    ratio = values[j] / values[i]
                    if 0 < abs(ratio) <= 1:
                        patterns.append({
                            'type': 'percentage',
                            'description': f'Value[{j}] is {ratio:.1%} of Value[{i}]',
                            'values': {
                                'base': values[i],
                                'derived': values[j],
                                'percentage': ratio
                            },
                            'context': context
                        })
        
        return patterns
    
    def analyze_year_over_year(self, current_values: List[float], 
                             previous_values: List[float],
                             context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze year-over-year changes."""
        changes = []
        
        for i, (curr, prev) in enumerate(zip(current_values, previous_values)):
            if prev != 0:
                change = (curr - prev) / abs(prev)
                
                analysis = {
                    'type': 'yoy_change',
                    'index': i,
                    'current_value': curr,
                    'previous_value': prev,
                    'change': change,
                    'context': context
                }
                
                # Classify the change
                if abs(change) > 0.5:
                    analysis['significance'] = 'major'
                    if abs(change) > 1:
                        analysis['flag'] = 'investigate'
                elif abs(change) > 0.1:
                    analysis['significance'] = 'moderate'
                else:
                    analysis['significance'] = 'minor'
                
                changes.append(analysis)
        
        return changes
    
    def generate_summary(self, validations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of validation results."""
        total = len(validations)
        matches = sum(1 for v in validations if v.get('match', False))
        
        return {
            'total_validations': total,
            'successful_matches': matches,
            'match_rate': matches / total if total > 0 else 0,
            'issues': [
                v for v in validations 
                if not v.get('match', False) and 'reason' in v
            ],
            'patterns_found': sum(
                1 for v in validations 
                if 'patterns' in v and v['patterns']
            )
        }