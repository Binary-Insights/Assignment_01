#!/usr/bin/env python3
"""
Unified PDF Extraction Pipeline with Cloud Fallback

This module provides a unified interface for PDF extraction that uses:
1. Primary: Docling (open-source) for initial extraction
2. Fallback: AWS Textract for quality enhancement and validation
3. Intelligent routing based on document complexity and quality thresholds

The pipeline provides:
- Quality-based fallback decision making
- Cost optimization through intelligent routing
- Comprehensive extraction with multiple validation sources
- Automatic quality scoring and confidence assessment
"""

import os
import json
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

# Import extractors
from docling_extractor import DoclingExtractor
import sys
sys.path.append(str(Path(__file__).parent))

try:
    import boto3
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    print("Warning: AWS SDK not available. Install with: pip install boto3")


class UnifiedExtractor:
    """
    Unified PDF extraction pipeline with intelligent cloud fallback.
    
    This class combines multiple extraction methods:
    1. Docling (open-source) - Primary extraction
    2. AWS Textract (cloud) - Fallback for quality enhancement
    3. Quality scoring and intelligent routing
    """
    
    def __init__(self, 
                 output_dir: str = "data/parsed/unified",
                 enable_aws_fallback: bool = True,
                 quality_threshold: float = 0.7,
                 cost_threshold: float = 10.0):
        """
        Initialize the unified extraction pipeline.
        
        Args:
            output_dir: Base directory for extraction outputs
            enable_aws_fallback: Whether to enable AWS Textract fallback
            quality_threshold: Quality score threshold for triggering fallback
            cost_threshold: Maximum acceptable cost per document (USD)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.enable_aws_fallback = enable_aws_fallback and AWS_AVAILABLE
        self.quality_threshold = quality_threshold
        self.cost_threshold = cost_threshold
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Initialize extractors
        self.docling_extractor = DoclingExtractor(
            output_dir=str(self.output_dir / "docling")
        )
        
        if self.enable_aws_fallback:
            self.aws_client = self._setup_aws_client()
        else:
            self.aws_client = None
            
        # Processing statistics
        self.stats = {
            'total_documents': 0,
            'docling_only': 0,
            'aws_fallback_used': 0,
            'total_cost': 0.0,
            'average_quality': 0.0,
            'processing_time': 0.0
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger('UnifiedExtractor')
        logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = self.output_dir / 'unified_extraction_log.txt'
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
    
    def _setup_aws_client(self):
        """Setup AWS Textract client."""
        try:
            client = boto3.client(
                'textract',
                region_name='us-east-1'  # Cheapest region
            )
            self.logger.info("✅ AWS Textract client initialized")
            return client
        except Exception as e:
            self.logger.warning(f"⚠️ AWS Textract setup failed: {e}")
            self.enable_aws_fallback = False
            return None
    
    def extract_from_pdf(self, pdf_path: str, 
                        force_aws: bool = False,
                        enable_fallback: bool = None) -> Dict[str, Any]:
        """
        Extract content from PDF with intelligent fallback logic.
        
        Args:
            pdf_path: Path to the PDF file
            force_aws: Force use of AWS Textract regardless of quality
            enable_fallback: Override instance fallback setting
            
        Returns:
            Comprehensive extraction results with quality metrics
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            self.logger.error(f"PDF file not found: {pdf_path}")
            return None
        
        # Use instance setting if not overridden
        if enable_fallback is None:
            enable_fallback = self.enable_aws_fallback
        
        self.logger.info(f"🚀 Starting unified extraction: {pdf_path.name}")
        start_time = datetime.now()
        
        # Create output directory for this document
        doc_output_dir = self.output_dir / pdf_path.stem
        doc_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize results structure
        results = {
            'pdf_name': pdf_path.name,
            'extraction_timestamp': start_time.isoformat(),
            'extraction_strategy': 'unified_pipeline',
            'docling_results': {},
            'aws_results': {},
            'quality_assessment': {},
            'cost_analysis': {},
            'final_recommendation': {},
            'processing_success': True
        }
        
        try:
            # Step 1: Always run Docling extraction (primary method)
            if not force_aws:
                results['docling_results'] = self._run_docling_extraction(
                    pdf_path, doc_output_dir
                )
                
                # Step 2: Assess quality and decide on fallback
                quality_score = self._assess_extraction_quality(
                    results['docling_results']
                )
                results['quality_assessment']['docling_quality'] = quality_score
                
                # Decision logic for fallback
                use_aws_fallback = self._should_use_aws_fallback(
                    quality_score, pdf_path, enable_fallback
                )
            else:
                self.logger.info("🔄 Force AWS mode - skipping Docling")
                use_aws_fallback = True
                quality_score = 0.0
            
            # Step 3: Run AWS Textract if needed
            if use_aws_fallback and self.aws_client:
                results['aws_results'] = self._run_aws_extraction(
                    pdf_path, doc_output_dir
                )
                
                # Update statistics
                self.stats['aws_fallback_used'] += 1
                
                # Calculate AWS quality if available
                if results['aws_results'].get('processing_success'):
                    aws_quality = self._assess_aws_quality(results['aws_results'])
                    results['quality_assessment']['aws_quality'] = aws_quality
            else:
                results['aws_results'] = {'processing_success': False, 'reason': 'Not triggered'}
                self.stats['docling_only'] += 1
            
            # Step 4: Cost analysis
            results['cost_analysis'] = self._analyze_costs(
                pdf_path, results['docling_results'], results['aws_results']
            )
            
            # Step 5: Final recommendation
            results['final_recommendation'] = self._generate_final_recommendation(
                results['docling_results'], 
                results['aws_results'],
                results['quality_assessment'],
                results['cost_analysis']
            )
            
        except Exception as e:
            self.logger.error(f"❌ Unified extraction error: {e}")
            results['processing_success'] = False
            results['error_message'] = str(e)
        
        # Calculate total processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        results['processing_time_seconds'] = processing_time
        
        # Update statistics
        self.stats['total_documents'] += 1
        self.stats['processing_time'] += processing_time
        
        # Save comprehensive results
        self._save_unified_results(results, doc_output_dir)
        
        self.logger.info(f"✅ Unified extraction completed in {processing_time:.2f}s")
        return results
    
    def _run_docling_extraction(self, pdf_path: Path, output_dir: Path) -> Dict[str, Any]:
        """Run Docling extraction with error handling."""
        try:
            self.logger.info("🔄 Running Docling extraction...")
            docling_results = self.docling_extractor.extract_from_pdf(str(pdf_path))
            
            if docling_results and docling_results.get('processing_success'):
                self.logger.info("✅ Docling extraction successful")
                return docling_results
            else:
                self.logger.warning("⚠️ Docling extraction failed or incomplete")
                return {'processing_success': False, 'error': 'Extraction failed'}
                
        except Exception as e:
            self.logger.error(f"❌ Docling extraction error: {e}")
            return {'processing_success': False, 'error': str(e)}
    
    def _run_aws_extraction(self, pdf_path: Path, output_dir: Path) -> Dict[str, Any]:
        """Run AWS Textract extraction with error handling."""
        try:
            self.logger.info("🔄 Running AWS Textract extraction...")
            
            # Calculate estimated cost first
            file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
            estimated_pages = max(1, int(file_size_mb * 10))  # Rough estimate
            estimated_cost = estimated_pages * 0.015  # $0.015 per page for tables
            
            if estimated_cost > self.cost_threshold:
                self.logger.warning(f"⚠️ AWS cost too high: ${estimated_cost:.2f} > ${self.cost_threshold}")
                return {
                    'processing_success': False, 
                    'reason': 'Cost threshold exceeded',
                    'estimated_cost': estimated_cost
                }
            
            # Run AWS extraction
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            
            response = self.aws_client.analyze_document(
                Document={'Bytes': pdf_bytes},
                FeatureTypes=['TABLES', 'FORMS']
            )
            
            # Process AWS response
            aws_results = self._process_aws_response(response, output_dir)
            aws_results['estimated_cost'] = estimated_cost
            aws_results['actual_pages'] = len(response.get('Blocks', []))
            
            self.logger.info("✅ AWS Textract extraction successful")
            return aws_results
            
        except Exception as e:
            self.logger.error(f"❌ AWS Textract extraction error: {e}")
            return {'processing_success': False, 'error': str(e)}
    
    def _process_aws_response(self, response: Dict, output_dir: Path) -> Dict[str, Any]:
        """Process AWS Textract response into structured format."""
        blocks = response.get('Blocks', [])
        
        # Extract tables
        tables = []
        table_blocks = [b for b in blocks if b.get('BlockType') == 'TABLE']
        
        for table_block in table_blocks:
            table_id = table_block.get('Id')
            confidence = table_block.get('Confidence', 0)
            
            # Extract table structure (simplified)
            table_data = {
                'table_id': table_id,
                'confidence': confidence,
                'rows': table_block.get('RowCount', 0),
                'columns': table_block.get('ColumnCount', 0),
                'bbox': table_block.get('Geometry', {}).get('BoundingBox', {})
            }
            tables.append(table_data)
        
        # Calculate quality metrics
        avg_confidence = sum(t['confidence'] for t in tables) / len(tables) if tables else 0
        
        aws_results = {
            'processing_success': True,
            'total_blocks': len(blocks),
            'tables_detected': len(tables),
            'tables': tables,
            'average_confidence': avg_confidence,
            'quality_score': avg_confidence / 100.0,  # Convert to 0-1 scale
            'extraction_timestamp': datetime.now().isoformat()
        }
        
        # Save detailed AWS results
        aws_file = output_dir / 'aws_textract_results.json'
        with open(aws_file, 'w') as f:
            json.dump(aws_results, f, indent=2)
        
        return aws_results
    
    def _assess_extraction_quality(self, docling_results: Dict[str, Any]) -> float:
        """Assess quality of Docling extraction results."""
        if not docling_results.get('processing_success'):
            return 0.0
        
        quality_factors = []
        
        # Factor 1: Table extraction success
        content_structure = docling_results.get('content_structure', {})
        tables = content_structure.get('tables', {})
        
        if isinstance(tables, dict):
            num_tables = tables.get('total_tables', 0)
            if num_tables > 0:
                quality_factors.append(0.8)  # Good table extraction
            else:
                quality_factors.append(0.3)  # No tables found
        
        # Factor 2: Processing success and completeness
        if docling_results.get('processing_success'):
            quality_factors.append(0.9)
        
        # Factor 3: Content richness
        document_analysis = docling_results.get('document_analysis', {})
        if document_analysis.get('total_pages', 0) > 0:
            quality_factors.append(0.7)
        
        # Calculate average quality score
        return sum(quality_factors) / len(quality_factors) if quality_factors else 0.0
    
    def _assess_aws_quality(self, aws_results: Dict[str, Any]) -> float:
        """Assess quality of AWS Textract results."""
        if not aws_results.get('processing_success'):
            return 0.0
        
        return aws_results.get('quality_score', 0.0)
    
    def _should_use_aws_fallback(self, quality_score: float, 
                                pdf_path: Path, enable_fallback: bool) -> bool:
        """Decide whether to use AWS Textract fallback."""
        if not enable_fallback or not self.aws_client:
            self.logger.info("🚫 AWS fallback disabled")
            return False
        
        # Quality-based decision
        if quality_score < self.quality_threshold:
            self.logger.info(f"🔄 Quality below threshold ({quality_score:.2f} < {self.quality_threshold})")
            return True
        
        # Document complexity-based decision  
        file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 50:  # Large documents might benefit from cloud processing
            self.logger.info(f"🔄 Large document detected ({file_size_mb:.1f}MB)")
            return True
        
        self.logger.info(f"✅ Quality sufficient ({quality_score:.2f}), using Docling only")
        return False
    
    def _analyze_costs(self, pdf_path: Path, 
                      docling_results: Dict, aws_results: Dict) -> Dict[str, Any]:
        """Analyze processing costs for both methods."""
        file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
        
        # Estimate pages
        estimated_pages = max(1, int(file_size_mb * 10))
        
        cost_analysis = {
            'pdf_size_mb': file_size_mb,
            'estimated_pages': estimated_pages,
            'docling_cost': 0.0,  # Open source - no direct cost
            'aws_cost': 0.0,
            'total_cost': 0.0,
            'cost_per_page': 0.0
        }
        
        # Calculate AWS cost if used
        if aws_results.get('processing_success'):
            aws_cost = estimated_pages * 0.015  # $0.015 per page for tables
            cost_analysis['aws_cost'] = aws_cost
            cost_analysis['total_cost'] = aws_cost
            cost_analysis['cost_per_page'] = aws_cost / estimated_pages
            
            # Update global statistics
            self.stats['total_cost'] += aws_cost
        
        return cost_analysis
    
    def _generate_final_recommendation(self, docling_results: Dict, aws_results: Dict,
                                     quality_assessment: Dict, cost_analysis: Dict) -> Dict[str, Any]:
        """Generate final recommendation based on all factors."""
        recommendation = {
            'primary_method': 'unknown',
            'confidence': 0.0,
            'reasoning': [],
            'cost_effectiveness': 'unknown',
            'quality_rating': 'unknown'
        }
        
        docling_quality = quality_assessment.get('docling_quality', 0.0)
        aws_quality = quality_assessment.get('aws_quality', 0.0)
        
        # Determine primary recommendation
        if aws_results.get('processing_success') and aws_quality > docling_quality:
            recommendation['primary_method'] = 'aws_textract'
            recommendation['confidence'] = aws_quality
            recommendation['reasoning'].append(f"AWS quality ({aws_quality:.2f}) > Docling ({docling_quality:.2f})")
        elif docling_results.get('processing_success'):
            recommendation['primary_method'] = 'docling'
            recommendation['confidence'] = docling_quality
            recommendation['reasoning'].append(f"Docling sufficient quality ({docling_quality:.2f})")
        else:
            recommendation['primary_method'] = 'fallback_needed'
            recommendation['confidence'] = 0.0
            recommendation['reasoning'].append("Both methods failed")
        
        # Cost effectiveness assessment
        total_cost = cost_analysis.get('total_cost', 0.0)
        if total_cost == 0.0:
            recommendation['cost_effectiveness'] = 'excellent'
        elif total_cost < 5.0:
            recommendation['cost_effectiveness'] = 'good'
        elif total_cost < 20.0:
            recommendation['cost_effectiveness'] = 'acceptable'
        else:
            recommendation['cost_effectiveness'] = 'expensive'
        
        # Quality rating
        max_quality = max(docling_quality, aws_quality)
        if max_quality > 0.8:
            recommendation['quality_rating'] = 'excellent'
        elif max_quality > 0.6:
            recommendation['quality_rating'] = 'good'
        elif max_quality > 0.4:
            recommendation['quality_rating'] = 'acceptable'
        else:
            recommendation['quality_rating'] = 'poor'
        
        return recommendation
    
    def _save_unified_results(self, results: Dict, output_dir: Path):
        """Save unified extraction results."""
        # Save main results
        results_file = output_dir / 'unified_extraction_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save processing summary
        summary = {
            'pdf_name': results['pdf_name'],
            'processing_time': results['processing_time_seconds'],
            'primary_method': results['final_recommendation']['primary_method'],
            'quality_rating': results['final_recommendation']['quality_rating'],
            'cost_effectiveness': results['final_recommendation']['cost_effectiveness'],
            'total_cost': results['cost_analysis']['total_cost'],
            'docling_success': results['docling_results'].get('processing_success', False),
            'aws_success': results['aws_results'].get('processing_success', False)
        }
        
        summary_file = output_dir / 'extraction_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get overall processing statistics."""
        stats = self.stats.copy()
        
        if stats['total_documents'] > 0:
            stats['aws_fallback_rate'] = stats['aws_fallback_used'] / stats['total_documents']
            stats['average_processing_time'] = stats['processing_time'] / stats['total_documents']
            stats['average_cost_per_document'] = stats['total_cost'] / stats['total_documents']
        else:
            stats['aws_fallback_rate'] = 0.0
            stats['average_processing_time'] = 0.0
            stats['average_cost_per_document'] = 0.0
        
        return stats


def main():
    """Example usage of the unified extraction pipeline."""
    
    # Initialize unified extractor
    extractor = UnifiedExtractor(
        output_dir="data/parsed/unified",
        enable_aws_fallback=True,
        quality_threshold=0.6,  # Trigger AWS if Docling quality < 60%
        cost_threshold=20.0     # Max $20 per document
    )
    
    # Test with sample PDF
    pdf_path = "data/raw/pdf/nvda-20240128.pdf"
    
    if Path(pdf_path).exists():
        print("🚀 Running unified extraction pipeline...")
        
        results = extractor.extract_from_pdf(pdf_path)
        
        if results:
            print("\n📊 Extraction Results:")
            print(f"Primary method: {results['final_recommendation']['primary_method']}")
            print(f"Quality rating: {results['final_recommendation']['quality_rating']}")
            print(f"Total cost: ${results['cost_analysis']['total_cost']:.2f}")
            print(f"Processing time: {results['processing_time_seconds']:.2f}s")
            
            # Print statistics
            stats = extractor.get_processing_stats()
            print(f"\n📈 Pipeline Statistics:")
            print(f"AWS fallback rate: {stats['aws_fallback_rate']:.1%}")
            print(f"Average cost per document: ${stats['average_cost_per_document']:.2f}")
        else:
            print("❌ Extraction failed")
    
    else:
        print(f"❌ PDF not found: {pdf_path}")


if __name__ == "__main__":
    main()