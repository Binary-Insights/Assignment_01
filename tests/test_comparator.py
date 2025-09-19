import os
import json
import sys
import unittest
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.xbrl_pdf_comparator import XBRLPDFComparator

class TestXBRLPDFComparator(unittest.TestCase):
    def setUp(self):
        # Create test config
        self.config = {
            "concept_mappings": {
                "stock_transactions": {
                    "shares_repurchased": {
                        "xbrl_concepts": ["SharesRepurchased", "SharesRepurchasedInPeriod"],
                        "value_type": "numeric"
                    }
                }
            },
            "common_transformations": {
                "monetary_to_millions": "value / 1000000",
                "percentage_to_decimal": "value / 100"
            },
            "validation_rules": {
                "tolerance": {
                    "percentages": 0.001,  # 0.1%
                    "absolute_values": 0.01  # 1%
                }
            }
        }
        
        # Write test config
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
        os.makedirs(config_dir, exist_ok=True)
        self.config_path = os.path.join(config_dir, 'test_config.json')
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f)
        
        self.comparator = XBRLPDFComparator(self.config_path)
    
    def test_normalize_value(self):
        test_cases = [
            ('$1,234.56', 1234.56),
            ('(123.45)', -123.45),
            ('50%', 50.0),
            ('1.5M', 1500000.0),
            ('2.5B', 2500000000.0),
            ('Invalid', None)
        ]
        
        for input_val, expected in test_cases:
            with self.subTest(input=input_val):
                result = self.comparator.normalize_value(input_val)
                self.assertEqual(result, expected)
    
    def test_compare_values(self):
        # Test exact match
        result = self.comparator.compare_values(100.0, 100.0)
        self.assertTrue(result['match'])
        self.assertEqual(result['difference'], 0.0)
        
        # Test within tolerance
        result = self.comparator.compare_values(100.0, 100.5)
        self.assertTrue(result['match'])
        
        # Test outside tolerance
        result = self.comparator.compare_values(100.0, 150.0)
        self.assertFalse(result['match'])
    
    def test_match_table_type(self):
        test_cases = [
            ({
                'data': [{'line_item': 'Stock Repurchases'}]
            }, 'stock_transactions'),
            ({
                'data': [{'line_item': 'Intangible Assets'}]
            }, 'balance_sheet'),
            ({
                'data': [{'line_item': 'Unknown Content'}]
            }, 'unknown')
        ]
        
        for table_data, expected_type in test_cases:
            with self.subTest(table_data=table_data):
                result = self.comparator.match_table_type(table_data)
                self.assertEqual(result, expected_type)
    
    def test_process_comparison(self):
        table_data = {
            'original_file': 'test.pdf',
            'data': [{
                'line_item': 'Shares Repurchased',
                'values': ['1.5M']
            }]
        }
        
        xbrl_data = {
            'SharesRepurchased': [{
                'value': '1500000',
                'context': 'FY2024',
                'unit': 'shares'
            }]
        }
        
        result = self.comparator.process_comparison(table_data, xbrl_data)
        self.assertEqual(result['table_type'], 'stock_transactions')
        self.assertTrue(len(result['comparisons']) > 0)

if __name__ == '__main__':
    unittest.main()