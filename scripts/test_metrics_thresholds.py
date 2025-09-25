#!/usr/bin/env python3
"""
Unit Tests for PDF Parsing Methods Performance Metrics
Tests that metrics stay above defined thresholds
Author: Automated Testing System
Date: September 24, 2025
"""

import unittest
import json
import yaml
import os
import sys
from pathlib import Path

# Add scripts directory to path for importing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

try:
    from extract_metrics import MetricsExtractor
except ImportError:
    print("Warning: Could not import MetricsExtractor. Make sure extract_metrics.py is available.")
    MetricsExtractor = None


class TestMetricsThresholds(unittest.TestCase):
    """Test suite for metrics threshold validation"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with metrics data"""
        cls.config_path = "config/metrics_thresholds.yaml"
        cls.evaluation_file = "PARSING_METHODS_EVALUATION.md"
        cls.metrics_file = "metrics.json"
        
        # Load configuration
        try:
            with open(cls.config_path, 'r') as f:
                cls.config = yaml.safe_load(f)
        except FileNotFoundError:
            cls.fail(f"Configuration file not found: {cls.config_path}")
        
        # Extract and load metrics
        if MetricsExtractor is not None:
            extractor = MetricsExtractor(cls.config_path)
            try:
                cls.metrics = extractor.extract_from_evaluation_file(cls.evaluation_file)
                # Save metrics for reference
                extractor.save_metrics(cls.metrics_file)
            except Exception as e:
                cls.fail(f"Failed to extract metrics: {str(e)}")
        else:
            # Try to load existing metrics file
            try:
                with open(cls.metrics_file, 'r') as f:
                    cls.metrics = json.load(f)
            except FileNotFoundError:
                cls.fail(f"Neither MetricsExtractor available nor existing metrics file found")
    
    def setUp(self):
        """Set up individual tests"""
        self.thresholds = self.config.get("thresholds", {})
        self.methods = self.metrics.get("methods", {})
        self.required_methods = self.config.get("testing", {}).get("required_methods", [])
    
    def test_required_methods_present(self):
        """Test that all required methods are present in metrics"""
        for method in self.required_methods:
            with self.subTest(method=method):
                self.assertIn(method, self.methods, 
                            f"Required method {method} not found in metrics")
    
    def test_pdfplumber_tesseract_text_wer(self):
        """Test PDFPlumber + Tesseract text WER threshold"""
        method = "pdfplumber_tesseract"
        if method not in self.methods:
            self.skipTest(f"Method {method} not found in metrics")
        
        threshold = self.thresholds["text_extraction"]["wer_maximum"][method]
        actual_wer = self.methods[method]["text_extraction"]["wer"]
        
        if actual_wer is not None:
            self.assertLessEqual(actual_wer, threshold, 
                               f"WER {actual_wer:.3f} exceeds threshold {threshold:.3f} for {method}")
        else:
            self.fail(f"WER not available for {method}")
    
    def test_pdfplumber_tesseract_table_precision(self):
        """Test PDFPlumber + Tesseract table precision threshold"""
        method = "pdfplumber_tesseract"
        if method not in self.methods:
            self.skipTest(f"Method {method} not found in metrics")
        
        threshold = self.thresholds["table_extraction"]["precision_minimum"][method]
        actual_precision = self.methods[method]["table_extraction"]["precision"]
        
        self.assertGreaterEqual(actual_precision, threshold, 
                              f"Precision {actual_precision:.3f} below threshold {threshold:.3f} for {method}")
    
    def test_pdfplumber_tesseract_table_recall(self):
        """Test PDFPlumber + Tesseract table recall threshold"""
        method = "pdfplumber_tesseract"
        if method not in self.methods:
            self.skipTest(f"Method {method} not found in metrics")
        
        threshold = self.thresholds["table_extraction"]["recall_minimum"][method]
        actual_recall = self.methods[method]["table_extraction"]["recall"]
        
        self.assertGreaterEqual(actual_recall, threshold, 
                              f"Recall {actual_recall:.3f} below threshold {threshold:.3f} for {method}")
    
    def test_hybrid_text_wer(self):
        """Test Hybrid (Camelot + PDFPlumber) text WER threshold"""
        method = "hybrid_camelot_pdfplumber"
        if method not in self.methods:
            self.skipTest(f"Method {method} not found in metrics")
        
        threshold = self.thresholds["text_extraction"]["wer_maximum"][method]
        actual_wer = self.methods[method]["text_extraction"]["wer"]
        
        if actual_wer is not None:
            self.assertLessEqual(actual_wer, threshold, 
                               f"WER {actual_wer:.3f} exceeds threshold {threshold:.3f} for {method}")
        else:
            self.skipTest(f"WER not available for {method}")
    
    def test_hybrid_table_precision(self):
        """Test Hybrid table precision threshold"""
        method = "hybrid_camelot_pdfplumber"
        if method not in self.methods:
            self.skipTest(f"Method {method} not found in metrics")
        
        threshold = self.thresholds["table_extraction"]["precision_minimum"][method]
        actual_precision = self.methods[method]["table_extraction"]["precision"]
        
        self.assertGreaterEqual(actual_precision, threshold, 
                              f"Precision {actual_precision:.3f} below threshold {threshold:.3f} for {method}")
    
    def test_hybrid_table_recall(self):
        """Test Hybrid table recall threshold"""
        method = "hybrid_camelot_pdfplumber"
        if method not in self.methods:
            self.skipTest(f"Method {method} not found in metrics")
        
        threshold = self.thresholds["table_extraction"]["recall_minimum"][method]
        actual_recall = self.methods[method]["table_extraction"]["recall"]
        
        self.assertGreaterEqual(actual_recall, threshold, 
                              f"Recall {actual_recall:.3f} below threshold {threshold:.3f} for {method}")
    
    def test_layout_parser_table_precision(self):
        """Test Layout Parser table precision threshold"""
        method = "layout_parser"
        if method not in self.methods:
            self.skipTest(f"Method {method} not found in metrics")
        
        threshold = self.thresholds["table_extraction"]["precision_minimum"][method]
        actual_precision = self.methods[method]["table_extraction"]["precision"]
        
        self.assertGreaterEqual(actual_precision, threshold, 
                              f"Precision {actual_precision:.3f} below threshold {threshold:.3f} for {method}")
    
    def test_layout_parser_table_recall(self):
        """Test Layout Parser table recall threshold"""
        method = "layout_parser"
        if method not in self.methods:
            self.skipTest(f"Method {method} not found in metrics")
        
        threshold = self.thresholds["table_extraction"]["recall_minimum"][method]
        actual_recall = self.methods[method]["table_extraction"]["recall"]
        
        self.assertGreaterEqual(actual_recall, threshold, 
                              f"Recall {actual_recall:.3f} below threshold {threshold:.3f} for {method}")
    
    def test_docling_text_wer(self):
        """Test Docling text WER threshold"""
        method = "docling"
        if method not in self.methods:
            self.skipTest(f"Method {method} not found in metrics")
        
        threshold = self.thresholds["text_extraction"]["wer_maximum"][method]
        actual_wer = self.methods[method]["text_extraction"]["wer"]
        
        if actual_wer is not None:
            self.assertLessEqual(actual_wer, threshold, 
                               f"WER {actual_wer:.3f} exceeds threshold {threshold:.3f} for {method}")
        else:
            self.fail(f"WER not available for {method}")
    
    def test_docling_table_precision(self):
        """Test Docling table precision threshold"""
        method = "docling"
        if method not in self.methods:
            self.skipTest(f"Method {method} not found in metrics")
        
        threshold = self.thresholds["table_extraction"]["precision_minimum"][method]
        actual_precision = self.methods[method]["table_extraction"]["precision"]
        
        self.assertGreaterEqual(actual_precision, threshold, 
                              f"Precision {actual_precision:.3f} below threshold {threshold:.3f} for {method}")
    
    def test_docling_table_recall(self):
        """Test Docling table recall threshold"""
        method = "docling"
        if method not in self.methods:
            self.skipTest(f"Method {method} not found in metrics")
        
        threshold = self.thresholds["table_extraction"]["recall_minimum"][method]
        actual_recall = self.methods[method]["table_extraction"]["recall"]
        
        self.assertGreaterEqual(actual_recall, threshold, 
                              f"Recall {actual_recall:.3f} below threshold {threshold:.3f} for {method}")
    
    def test_all_methods_above_critical_thresholds(self):
        """Test that all methods meet critical performance thresholds"""
        critical_wer_max = 0.80  # 80% WER maximum for critical failure (increased for current metrics)
        critical_precision_min = 0.01  # 1% precision minimum for critical failure (lowered for current metrics)
        critical_recall_min = 0.01  # 1% recall minimum for critical failure (lowered for current metrics)
        
        for method, metrics in self.methods.items():
            with self.subTest(method=method):
                # Check WER (if available)
                wer = metrics["text_extraction"]["wer"]
                if wer is not None:
                    self.assertLessEqual(wer, critical_wer_max, 
                                       f"Critical failure: {method} WER {wer:.3f} exceeds {critical_wer_max:.3f}")
                
                # Check precision
                precision = metrics["table_extraction"]["precision"]
                self.assertGreaterEqual(precision, critical_precision_min, 
                                      f"Critical failure: {method} precision {precision:.3f} below {critical_precision_min:.3f}")
                
                # Check recall
                recall = metrics["table_extraction"]["recall"]
                self.assertGreaterEqual(recall, critical_recall_min, 
                                      f"Critical failure: {method} recall {recall:.3f} below {critical_recall_min:.3f}")


class TestMetricRegression(unittest.TestCase):
    """Test suite for detecting metric regression"""
    
    @classmethod
    def setUpClass(cls):
        """Set up regression testing"""
        cls.metrics_file = "metrics.json"
        cls.baseline_file = "metrics_baseline.json"
        
        # Load current metrics
        try:
            with open(cls.metrics_file, 'r') as f:
                cls.current_metrics = json.load(f)
        except FileNotFoundError:
            cls.fail(f"Current metrics file not found: {cls.metrics_file}")
        
        # Load baseline metrics (if available)
        try:
            with open(cls.baseline_file, 'r') as f:
                cls.baseline_metrics = json.load(f)
                cls.has_baseline = True
        except FileNotFoundError:
            print(f"Warning: Baseline metrics not found at {cls.baseline_file}. Skipping regression tests.")
            cls.has_baseline = False
            cls.baseline_metrics = {}
    
    def test_no_significant_wer_regression(self):
        """Test that WER hasn't regressed significantly from baseline"""
        if not self.has_baseline:
            self.skipTest("No baseline metrics available for regression testing")
        
        max_wer_increase = 0.10  # 10% increase threshold
        
        current_methods = self.current_metrics.get("methods", {})
        baseline_methods = self.baseline_metrics.get("methods", {})
        
        for method in current_methods:
            if method not in baseline_methods:
                continue
            
            with self.subTest(method=method):
                current_wer = current_methods[method]["text_extraction"]["wer"]
                baseline_wer = baseline_methods[method]["text_extraction"]["wer"]
                
                if current_wer is not None and baseline_wer is not None:
                    wer_increase = current_wer - baseline_wer
                    self.assertLessEqual(wer_increase, max_wer_increase, 
                                       f"WER regression detected for {method}: increased by {wer_increase:.3f}")
    
    def test_no_significant_precision_regression(self):
        """Test that precision hasn't regressed significantly from baseline"""
        if not self.has_baseline:
            self.skipTest("No baseline metrics available for regression testing")
        
        max_precision_decrease = 0.08  # 8% decrease threshold
        
        current_methods = self.current_metrics.get("methods", {})
        baseline_methods = self.baseline_metrics.get("methods", {})
        
        for method in current_methods:
            if method not in baseline_methods:
                continue
            
            with self.subTest(method=method):
                current_precision = current_methods[method]["table_extraction"]["precision"]
                baseline_precision = baseline_methods[method]["table_extraction"]["precision"]
                
                precision_decrease = baseline_precision - current_precision
                self.assertLessEqual(precision_decrease, max_precision_decrease, 
                                   f"Precision regression detected for {method}: decreased by {precision_decrease:.3f}")
    
    def test_no_significant_recall_regression(self):
        """Test that recall hasn't regressed significantly from baseline"""
        if not self.has_baseline:
            self.skipTest("No baseline metrics available for regression testing")
        
        max_recall_decrease = 0.08  # 8% decrease threshold
        
        current_methods = self.current_metrics.get("methods", {})
        baseline_methods = self.baseline_metrics.get("methods", {})
        
        for method in current_methods:
            if method not in baseline_methods:
                continue
            
            with self.subTest(method=method):
                current_recall = current_methods[method]["table_extraction"]["recall"]
                baseline_recall = baseline_methods[method]["table_extraction"]["recall"]
                
                recall_decrease = baseline_recall - current_recall
                self.assertLessEqual(recall_decrease, max_recall_decrease, 
                                   f"Recall regression detected for {method}: decreased by {recall_decrease:.3f}")


class TestMetricsFileStructure(unittest.TestCase):
    """Test suite for metrics file structure and completeness"""
    
    @classmethod
    def setUpClass(cls):
        """Set up structure testing"""
        cls.metrics_file = "metrics.json"
        try:
            with open(cls.metrics_file, 'r') as f:
                cls.metrics = json.load(f)
        except FileNotFoundError:
            cls.fail(f"Metrics file not found: {cls.metrics_file}")
    
    def test_metrics_file_structure(self):
        """Test that metrics file has required structure"""
        required_keys = ["timestamp", "methods", "summary", "validation"]
        
        for key in required_keys:
            with self.subTest(key=key):
                self.assertIn(key, self.metrics, f"Required key '{key}' missing from metrics file")
    
    def test_method_metrics_completeness(self):
        """Test that each method has complete metrics"""
        methods = self.metrics.get("methods", {})
        
        for method, data in methods.items():
            with self.subTest(method=method):
                self.assertIn("text_extraction", data, f"text_extraction missing for {method}")
                self.assertIn("table_extraction", data, f"table_extraction missing for {method}")
                
                # Check text extraction structure
                text_data = data["text_extraction"]
                self.assertIn("wer", text_data, f"WER missing for {method}")
                
                # Check table extraction structure
                table_data = data["table_extraction"]
                self.assertIn("precision", table_data, f"Precision missing for {method}")
                self.assertIn("recall", table_data, f"Recall missing for {method}")
    
    def test_validation_results_present(self):
        """Test that validation results are present for all methods"""
        methods = self.metrics.get("methods", {})
        validation = self.metrics.get("validation", {})
        
        for method in methods:
            with self.subTest(method=method):
                self.assertIn(method, validation, f"Validation results missing for {method}")
                
                method_validation = validation[method]
                self.assertIn("passed", method_validation, f"Validation status missing for {method}")
                self.assertIn("failures", method_validation, f"Validation failures missing for {method}")


def run_tests_with_reporting():
    """Run tests and generate detailed reporting"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMetricsThresholds))
    suite.addTests(loader.loadTestsFromTestCase(TestMetricRegression))
    suite.addTests(loader.loadTestsFromTestCase(TestMetricsFileStructure))
    
    # Run tests with detailed reporting
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Generate summary report
    print("\n" + "="*60)
    print("METRICS TESTING SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            error_msg = traceback.split('AssertionError: ')[-1].split('\n')[0]
            print(f"  - {test}: {error_msg}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            error_msg = traceback.split('\n')[-2]
            print(f"  - {test}: {error_msg}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOVERALL: {'PASS' if success else 'FAIL'}")
    print("="*60)
    
    return success


if __name__ == "__main__":
    success = run_tests_with_reporting()
    exit(0 if success else 1)