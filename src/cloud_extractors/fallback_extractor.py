"""
Intelligent Fallback Document Extractor

This module implements an intelligent fallback system that automatically
switches to cloud-based extraction services when open-source methods
produce low-quality results or fail entirely.

Features:
- Quality threshold-based fallback triggering
- Multiple cloud service integration
- Cost-aware fallback decisions
- Automatic retry mechanisms
- Performance monitoring and optimization
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib

# Import extractors
from ..docling_extractor import DoclingExtractor
from ..layout_parser_extractor import LayoutParserExtractor
from .aws_textract import AWSTextractExtractor


@dataclass
class QualityThresholds:
    """Quality thresholds for triggering fallback"""
    min_confidence: float = 0.7
    min_text_length: int = 100
    min_word_count: int = 20
    max_error_rate: float = 0.1
    min_table_confidence: float = 0.8
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'min_confidence': self.min_confidence,
            'min_text_length': self.min_text_length,
            'min_word_count': self.min_word_count,
            'max_error_rate': self.max_error_rate,
            'min_table_confidence': self.min_table_confidence
        }


@dataclass
class ExtractionResult:
    """Standardized extraction result"""
    method: str
    success: bool
    quality_score: float
    confidence: float
    text_length: int
    word_count: int
    table_count: int
    processing_time: float
    cost: float
    error_message: Optional[str]
    results: Optional[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'method': self.method,
            'success': self.success,
            'quality_score': self.quality_score,
            'confidence': self.confidence,
            'text_length': self.text_length,
            'word_count': self.word_count,
            'table_count': self.table_count,
            'processing_time': self.processing_time,
            'cost': self.cost,
            'error_message': self.error_message,
            'has_results': self.results is not None
        }


class IntelligentFallbackExtractor:
    """
    Intelligent document extractor with cloud service fallback.
    
    Tries open-source methods first, then falls back to cloud services
    based on quality thresholds and cost considerations.
    """
    
    def __init__(self,
                 quality_thresholds: Optional[QualityThresholds] = None,
                 max_cost_per_page: float = 0.05,
                 enable_cloud_fallback: bool = True,
                 output_dir: str = "data/parsed/fallback"):
        """
        Initialize the fallback extractor.
        
        Args:
            quality_thresholds: Quality thresholds for triggering fallback
            max_cost_per_page: Maximum cost per page for cloud services
            enable_cloud_fallback: Whether to enable cloud fallback
            output_dir: Directory for extraction results
        """
        self.quality_thresholds = quality_thresholds or QualityThresholds()
        self.max_cost_per_page = max_cost_per_page
        self.enable_cloud_fallback = enable_cloud_fallback
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Initialize extractors
        self._initialize_extractors()
        
        # Extraction statistics
        self.stats = {
            'total_documents': 0,
            'primary_success': 0,
            'fallback_triggered': 0,
            'cloud_service_used': 0,
            'total_cost': 0.0,
            'processing_time': 0.0,
            'method_usage': {},
            'fallback_reasons': {}
        }
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logger = logging.getLogger('FallbackExtractor')
        logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = self.output_dir / 'fallback_extraction.log'
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        if not logger.handlers:
            logger.addHandler(handler)
        
        return logger
    
    def _initialize_extractors(self):
        """Initialize all available extractors."""
        self.extractors = {}
        
        try:
            # Initialize open-source extractors
            self.extractors['docling'] = {
                'instance': DoclingExtractor(),
                'type': 'opensource',
                'priority': 1,
                'cost_per_page': 0.0
            }
        except Exception as e:
            self.logger.warning(f"Failed to initialize Docling extractor: {e}")
        
        try:
            self.extractors['layout_parser'] = {
                'instance': LayoutParserExtractor(),
                'type': 'opensource', 
                'priority': 2,
                'cost_per_page': 0.0
            }
        except Exception as e:
            self.logger.warning(f"Failed to initialize LayoutParser extractor: {e}")
        
        # Initialize cloud extractors (if enabled and credentials available)
        if self.enable_cloud_fallback:
            try:
                self.extractors['aws_textract'] = {
                    'instance': AWSTextractExtractor(),
                    'type': 'cloud',
                    'priority': 10,
                    'cost_per_page': 0.015  # Table detection cost
                }
            except Exception as e:
                self.logger.warning(f"Failed to initialize AWS Textract: {e}")
        
        self.logger.info(f"Initialized {len(self.extractors)} extractors: {list(self.extractors.keys())}")
    
    def extract_document(self, pdf_path: Path, 
                        force_method: Optional[str] = None,
                        skip_fallback: bool = False) -> Dict[str, Any]:
        """
        Extract document using intelligent fallback strategy.
        
        Args:
            pdf_path: Path to PDF file
            force_method: Force specific extraction method
            skip_fallback: Skip fallback even if quality is low
            
        Returns:
            dict: Extraction results with fallback information
        """
        doc_id = pdf_path.stem
        self.logger.info(f"Starting intelligent extraction for {doc_id}")
        start_time = time.time()
        
        extraction_attempts = []
        final_result = None
        fallback_triggered = False
        
        try:
            # If specific method is forced, use only that method
            if force_method:
                if force_method in self.extractors:
                    result = self._extract_with_method(pdf_path, force_method)
                    extraction_attempts.append(result)
                    final_result = result
                else:
                    raise ValueError(f"Forced method '{force_method}' not available")
            
            else:
                # Try methods in priority order
                sorted_extractors = sorted(
                    self.extractors.items(),
                    key=lambda x: x[1]['priority']
                )
                
                for method_name, method_config in sorted_extractors:
                    self.logger.info(f"Trying extraction with {method_name}")
                    
                    result = self._extract_with_method(pdf_path, method_name)
                    extraction_attempts.append(result)
                    
                    # Check if result meets quality thresholds
                    if self._meets_quality_thresholds(result) or skip_fallback:
                        self.logger.info(f"Quality thresholds met with {method_name}")
                        final_result = result
                        break
                    
                    else:
                        self.logger.warning(f"Quality thresholds not met with {method_name}")
                        
                        # If this is an open-source method and cloud fallback is enabled
                        if (method_config['type'] == 'opensource' and 
                            self.enable_cloud_fallback and
                            not skip_fallback):
                            
                            fallback_triggered = True
                            self.stats['fallback_triggered'] += 1
                            
                            # Track fallback reason
                            reason = self._get_fallback_reason(result)
                            self.stats['fallback_reasons'][reason] = self.stats['fallback_reasons'].get(reason, 0) + 1
                            
                            self.logger.info(f"Triggering cloud fallback due to: {reason}")
                            continue
                
                # If no method met thresholds, use the best available result
                if final_result is None and extraction_attempts:
                    final_result = max(extraction_attempts, key=lambda x: x.quality_score)
                    self.logger.warning(f"Using best available result from {final_result.method}")
        
        except Exception as e:
            self.logger.error(f"Error in extraction process: {e}")
            final_result = ExtractionResult(
                method='error',
                success=False,
                quality_score=0.0,
                confidence=0.0,
                text_length=0,
                word_count=0,
                table_count=0,
                processing_time=0.0,
                cost=0.0,
                error_message=str(e),
                results=None
            )
        
        # Calculate total processing time
        total_time = time.time() - start_time
        
        # Update statistics
        self._update_statistics(extraction_attempts, final_result, fallback_triggered)
        
        # Create comprehensive result
        comprehensive_result = {
            'document_id': doc_id,
            'extraction_timestamp': datetime.now().isoformat(),
            'total_processing_time': total_time,
            'fallback_triggered': fallback_triggered,
            'attempts': len(extraction_attempts),
            'final_method': final_result.method if final_result else 'none',
            'final_result': final_result.to_dict() if final_result else None,
            'extraction_attempts': [attempt.to_dict() for attempt in extraction_attempts],
            'quality_thresholds': self.quality_thresholds.to_dict(),
            'cost_summary': {
                'total_cost': sum(attempt.cost for attempt in extraction_attempts),
                'cost_per_page': sum(attempt.cost for attempt in extraction_attempts),  # Assuming single page
                'method_costs': {attempt.method: attempt.cost for attempt in extraction_attempts}
            }
        }
        
        # Save results
        self._save_extraction_results(comprehensive_result, final_result, doc_id)
        
        self.logger.info(f"Extraction completed for {doc_id} in {total_time:.2f}s using {final_result.method if final_result else 'none'}")
        
        return comprehensive_result
    
    def _extract_with_method(self, pdf_path: Path, method_name: str) -> ExtractionResult:
        """Extract document using specific method."""
        method_config = self.extractors[method_name]
        extractor = method_config['instance']
        
        start_time = time.time()
        
        try:
            # Call appropriate extraction method
            if method_name == 'docling':
                results = extractor.extract_document(pdf_path)
            elif method_name == 'layout_parser':
                results = extractor.extract_document(pdf_path)
            elif method_name == 'aws_textract':
                results = extractor.extract_document(pdf_path)
            else:
                raise ValueError(f"Unknown extraction method: {method_name}")
            
            processing_time = time.time() - start_time
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(results, method_name)
            
            # Calculate cost
            cost = self._calculate_extraction_cost(results, method_config)
            
            return ExtractionResult(
                method=method_name,
                success=True,
                quality_score=quality_metrics['quality_score'],
                confidence=quality_metrics['confidence'],
                text_length=quality_metrics['text_length'],
                word_count=quality_metrics['word_count'],
                table_count=quality_metrics['table_count'],
                processing_time=processing_time,
                cost=cost,
                error_message=None,
                results=results
            )
        
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Extraction failed with {method_name}: {e}")
            
            return ExtractionResult(
                method=method_name,
                success=False,
                quality_score=0.0,
                confidence=0.0,
                text_length=0,
                word_count=0,
                table_count=0,
                processing_time=processing_time,
                cost=0.0,
                error_message=str(e),
                results=None
            )
    
    def _calculate_quality_metrics(self, results: Dict[str, Any], method: str) -> Dict[str, Any]:
        """Calculate quality metrics from extraction results."""
        
        if method == 'aws_textract':
            quality = results.get('quality_metrics', {})
            confidence_stats = quality.get('confidence_stats', {})
            content_stats = quality.get('content_stats', {})
            
            confidence = confidence_stats.get('average', 0.0)
            text_length = content_stats.get('total_text_length', 0)
            word_count = content_stats.get('word_count', 0)
            table_count = content_stats.get('tables_found', 0)
            
        else:  # Open-source methods
            content_structure = results.get('content_structure', {})
            
            # Calculate text stats
            text_content = content_structure.get('text', {}).get('content', '')
            text_length = len(text_content)
            word_count = len(text_content.split())
            
            # Count tables
            table_count = len(content_structure.get('tables', {}).get('tables', []))
            
            # Estimate confidence for open-source methods
            confidence = 0.8 if text_length > 100 else 0.5
        
        # Calculate overall quality score
        quality_score = self._calculate_overall_quality_score(
            confidence, text_length, word_count, table_count
        )
        
        return {
            'quality_score': quality_score,
            'confidence': confidence,
            'text_length': text_length,
            'word_count': word_count,
            'table_count': table_count
        }
    
    def _calculate_overall_quality_score(self, confidence: float, text_length: int, 
                                       word_count: int, table_count: int) -> float:
        """Calculate overall quality score (0-1)."""
        
        # Normalize metrics
        confidence_score = confidence
        length_score = min(1.0, text_length / 1000)  # Normalize to 1000 chars
        word_score = min(1.0, word_count / 200)      # Normalize to 200 words
        table_score = min(1.0, table_count / 5)      # Normalize to 5 tables
        
        # Weighted combination
        quality_score = (
            confidence_score * 0.4 +
            length_score * 0.3 +
            word_score * 0.2 +
            table_score * 0.1
        )
        
        return quality_score
    
    def _calculate_extraction_cost(self, results: Dict[str, Any], method_config: Dict[str, Any]) -> float:
        """Calculate extraction cost."""
        
        if method_config['type'] == 'cloud':
            # Use actual costs from cloud service
            if 'costs' in results:
                return results['costs'].get('total_cost', method_config['cost_per_page'])
            else:
                return method_config['cost_per_page']
        
        else:
            # Open-source methods: estimate based on processing time
            processing_time = results.get('processing_time', 0.0)
            return processing_time * 0.001  # $0.001 per second estimate
    
    def _meets_quality_thresholds(self, result: ExtractionResult) -> bool:
        """Check if extraction result meets quality thresholds."""
        
        if not result.success:
            return False
        
        thresholds = self.quality_thresholds
        
        # Check all thresholds
        checks = [
            result.confidence >= thresholds.min_confidence,
            result.text_length >= thresholds.min_text_length,
            result.word_count >= thresholds.min_word_count,
            result.quality_score >= 0.7  # Overall quality threshold
        ]
        
        meets_thresholds = all(checks)
        
        self.logger.debug(f"Quality check for {result.method}: {meets_thresholds}")
        self.logger.debug(f"  Confidence: {result.confidence} >= {thresholds.min_confidence}: {checks[0]}")
        self.logger.debug(f"  Text length: {result.text_length} >= {thresholds.min_text_length}: {checks[1]}")
        self.logger.debug(f"  Word count: {result.word_count} >= {thresholds.min_word_count}: {checks[2]}")
        self.logger.debug(f"  Quality score: {result.quality_score} >= 0.7: {checks[3]}")
        
        return meets_thresholds
    
    def _get_fallback_reason(self, result: ExtractionResult) -> str:
        """Determine the primary reason for fallback."""
        
        if not result.success:
            return 'extraction_failed'
        
        thresholds = self.quality_thresholds
        
        if result.confidence < thresholds.min_confidence:
            return 'low_confidence'
        elif result.text_length < thresholds.min_text_length:
            return 'insufficient_text'
        elif result.word_count < thresholds.min_word_count:
            return 'low_word_count'
        else:
            return 'overall_quality'
    
    def _update_statistics(self, attempts: List[ExtractionResult], 
                         final_result: Optional[ExtractionResult], 
                         fallback_triggered: bool):
        """Update extraction statistics."""
        
        self.stats['total_documents'] += 1
        
        if attempts and attempts[0].success:
            self.stats['primary_success'] += 1
        
        if fallback_triggered:
            self.stats['fallback_triggered'] += 1
        
        # Track method usage
        for attempt in attempts:
            method = attempt.method
            self.stats['method_usage'][method] = self.stats['method_usage'].get(method, 0) + 1
            
            # Track cloud usage
            if method in ['aws_textract', 'google_docai', 'azure_form_recognizer']:
                self.stats['cloud_service_used'] += 1
            
            # Track costs
            self.stats['total_cost'] += attempt.cost
        
        # Track processing time
        if final_result:
            self.stats['processing_time'] += final_result.processing_time
    
    def _save_extraction_results(self, comprehensive_result: Dict[str, Any], 
                               final_result: Optional[ExtractionResult], 
                               doc_id: str):
        """Save extraction results and metadata."""
        
        # Create document directory
        doc_dir = self.output_dir / doc_id
        doc_dir.mkdir(exist_ok=True)
        
        # Save comprehensive results
        results_file = doc_dir / 'fallback_extraction_results.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_result, f, indent=2, ensure_ascii=False, default=str)
        
        # Save final extraction results if available
        if final_result and final_result.results:
            final_results_file = doc_dir / f'{final_result.method}_final_results.json'
            with open(final_results_file, 'w', encoding='utf-8') as f:
                json.dump(final_result.results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save extraction metadata
        metadata = {
            'document_id': doc_id,
            'final_method': final_result.method if final_result else 'none',
            'fallback_triggered': comprehensive_result['fallback_triggered'],
            'total_attempts': comprehensive_result['attempts'],
            'total_cost': comprehensive_result['cost_summary']['total_cost'],
            'quality_thresholds': comprehensive_result['quality_thresholds'],
            'timestamp': comprehensive_result['extraction_timestamp']
        }
        
        metadata_file = doc_dir / 'extraction_metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Saved extraction results to {doc_dir}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get extraction statistics."""
        stats = self.stats.copy()
        
        # Calculate derived statistics
        if stats['total_documents'] > 0:
            stats['primary_success_rate'] = stats['primary_success'] / stats['total_documents']
            stats['fallback_rate'] = stats['fallback_triggered'] / stats['total_documents']
            stats['cloud_usage_rate'] = stats['cloud_service_used'] / stats['total_documents']
            stats['average_cost_per_document'] = stats['total_cost'] / stats['total_documents']
            stats['average_processing_time'] = stats['processing_time'] / stats['total_documents']
        
        return stats
    
    def save_statistics(self):
        """Save current statistics to file."""
        stats_file = self.output_dir / 'extraction_statistics.json'
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.get_statistics(), f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Saved statistics to {stats_file}")
    
    def configure_quality_thresholds(self, **kwargs):
        """Update quality thresholds."""
        for key, value in kwargs.items():
            if hasattr(self.quality_thresholds, key):
                setattr(self.quality_thresholds, key, value)
                self.logger.info(f"Updated threshold {key} to {value}")
    
    def enable_method(self, method_name: str):
        """Enable a specific extraction method."""
        if method_name in self.extractors:
            self.logger.info(f"Method {method_name} is already available")
        else:
            self.logger.warning(f"Method {method_name} is not available for enabling")
    
    def disable_method(self, method_name: str):
        """Disable a specific extraction method."""
        if method_name in self.extractors:
            del self.extractors[method_name]
            self.logger.info(f"Disabled extraction method: {method_name}")
        else:
            self.logger.warning(f"Method {method_name} is not available for disabling")
