"""
Metadata Extraction and Staging System

This module converts parsed PDF content from different extraction methods
(Docling, LayoutParser, Traditional) into a unified metadata format with
JSONL files and Markdown output with provenance tracking.

Features:
- Unified metadata schema across all extraction methods
- JSONL format for scalable block-level metadata
- Provenance tracking and quality metrics
- Cross-method comparison and unification
- Markdown generation with embedded metadata
"""

import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Generator, Tuple
import uuid
from dataclasses import dataclass, asdict
import csv
import io


@dataclass
class DocumentMetadata:
    """Document-level metadata schema"""
    doc_id: str
    doc_name: str
    doc_path: str
    processing_timestamp: str
    total_pages: int
    file_size_bytes: int
    checksum: str
    extraction_methods: List[str]
    processing_status: str
    processing_time_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BoundingBox:
    """Bounding box coordinates"""
    x1: float
    y1: float
    x2: float
    y2: float
    width: float
    height: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ContentBlock:
    """Unified content block schema"""
    doc_id: str
    block_id: str
    extraction_method: str
    page_number: int
    block_type: str
    confidence: float
    bounding_box: Optional[BoundingBox]
    content: Dict[str, Any]
    provenance: Dict[str, Any]
    semantic_tags: List[str]
    quality_metrics: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        if self.bounding_box:
            result['bounding_box'] = self.bounding_box.to_dict()
        return result


class MetadataExtractor:
    """
    Unified metadata extraction and staging system for PDF content.
    
    Converts method-specific extractions to unified metadata format
    with JSONL files and provenance tracking.
    """
    
    def __init__(self, 
                 raw_pdf_dir: str = "data/raw/pdf",
                 parsed_dir: str = "data/parsed", 
                 metadata_dir: str = "data/metadata",
                 staged_dir: str = "data/staged"):
        """
        Initialize metadata extractor.
        
        Args:
            raw_pdf_dir: Directory containing original PDF files
            parsed_dir: Directory containing method-specific extractions
            metadata_dir: Directory for unified metadata
            staged_dir: Directory for final staged outputs
        """
        self.raw_pdf_dir = Path(raw_pdf_dir)
        self.parsed_dir = Path(parsed_dir)
        self.metadata_dir = Path(metadata_dir)
        self.staged_dir = Path(staged_dir)
        
        # Create directory structure
        self._create_directory_structure()
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Method mappings
        self.extraction_methods = {
            'docling': 'docling',
            'layout_parser': 'layout_parser', 
            'traditional': 'traditional'
        }
        
        # Statistics
        self.stats = {
            'documents_processed': 0,
            'total_blocks_extracted': 0,
            'blocks_by_method': {},
            'blocks_by_type': {},
            'processing_time': 0
        }
    
    def _create_directory_structure(self):
        """Create the complete metadata directory structure."""
        directories = [
            self.metadata_dir / 'documents',
            self.metadata_dir / 'blocks' / 'docling',
            self.metadata_dir / 'blocks' / 'layout_parser',
            self.metadata_dir / 'blocks' / 'traditional',
            self.metadata_dir / 'blocks' / 'unified',
            self.metadata_dir / 'provenance' / 'extraction_logs',
            self.metadata_dir / 'provenance' / 'method_configs',
            self.metadata_dir / 'provenance' / 'quality_reports',
            self.metadata_dir / 'schemas',
            self.staged_dir / 'markdown',
            self.staged_dir / 'json',
            self.staged_dir / 'search_index',
            Path('data/analysis/statistics'),
            Path('data/analysis/quality_metrics'),
            Path('data/analysis/method_comparisons')
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logger = logging.getLogger('MetadataExtractor')
        logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = self.metadata_dir / 'provenance' / 'extraction_logs' / 'metadata_extraction.log'
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
    
    def process_all_documents(self) -> Dict[str, Any]:
        """
        Process all PDF documents and extract unified metadata.
        
        Returns:
            dict: Processing summary and statistics
        """
        self.logger.info("Starting unified metadata extraction for all documents")
        start_time = datetime.now()
        
        # Find all PDF files
        pdf_files = list(self.raw_pdf_dir.glob("*.pdf"))
        if not pdf_files:
            self.logger.warning(f"No PDF files found in {self.raw_pdf_dir}")
            return {'status': 'no_files', 'message': 'No PDF files found'}
        
        # Document registry for tracking all processed documents
        doc_registry = {}
        processing_results = []
        
        # Process each PDF
        for pdf_file in pdf_files:
            self.logger.info(f"Processing document: {pdf_file.name}")
            
            try:
                result = self.process_document(pdf_file)
                processing_results.append(result)
                
                if result['status'] == 'success':
                    doc_registry[result['doc_id']] = result['document_metadata']
                    self.stats['documents_processed'] += 1
                
            except Exception as e:
                self.logger.error(f"Error processing {pdf_file.name}: {e}")
                processing_results.append({
                    'doc_id': pdf_file.stem,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Save document registry
        registry_file = self.metadata_dir / 'documents' / 'doc_registry.json'
        with open(registry_file, 'w', encoding='utf-8') as f:
            json.dump(doc_registry, f, indent=2, ensure_ascii=False, default=str)
        
        # Calculate processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        self.stats['processing_time'] = processing_time
        
        # Generate processing summary
        summary = {
            'processing_timestamp': start_time.isoformat(),
            'total_pdfs_found': len(pdf_files),
            'documents_processed': self.stats['documents_processed'],
            'processing_results': processing_results,
            'statistics': self.stats,
            'processing_time_seconds': processing_time
        }
        
        # Save processing summary
        summary_file = self.metadata_dir / 'provenance' / 'quality_reports' / 'processing_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Metadata extraction completed in {processing_time:.2f} seconds")
        self._log_statistics()
        
        return summary
    
    def process_document(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Process a single PDF document and extract unified metadata.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            dict: Processing result with metadata
        """
        doc_id = pdf_path.stem
        self.logger.info(f"Processing document {doc_id}")
        
        # Create document metadata
        doc_metadata = self._create_document_metadata(pdf_path)
        
        # Extract blocks from each method
        all_blocks = []
        method_results = {}
        
        for method_name, method_key in self.extraction_methods.items():
            blocks = self._extract_blocks_from_method(doc_id, method_key)
            if blocks:
                all_blocks.extend(blocks)
                method_results[method_name] = len(blocks)
                
                # Save method-specific JSONL
                self._save_method_jsonl(blocks, doc_id, method_key)
        
        # Create unified blocks (cross-method consolidation)
        unified_blocks = self._create_unified_blocks(all_blocks, doc_id)
        
        # Save unified JSONL
        if unified_blocks:
            self._save_unified_jsonl(unified_blocks, doc_id)
        
        # Generate staged outputs
        self._generate_markdown_with_provenance(doc_metadata, unified_blocks, doc_id)
        self._generate_json_export(doc_metadata, unified_blocks, doc_id)
        
        # Save document metadata
        doc_metadata_file = self.metadata_dir / 'documents' / f'{doc_id}.json'
        with open(doc_metadata_file, 'w', encoding='utf-8') as f:
            json.dump(doc_metadata.to_dict(), f, indent=2, ensure_ascii=False, default=str)
        
        # Update statistics
        self.stats['total_blocks_extracted'] += len(all_blocks)
        for method, count in method_results.items():
            self.stats['blocks_by_method'][method] = self.stats['blocks_by_method'].get(method, 0) + count
        
        return {
            'doc_id': doc_id,
            'status': 'success',
            'document_metadata': doc_metadata.to_dict(),
            'total_blocks': len(all_blocks),
            'unified_blocks': len(unified_blocks) if unified_blocks else 0,
            'method_results': method_results
        }
    
    def _create_document_metadata(self, pdf_path: Path) -> DocumentMetadata:
        """Create document-level metadata."""
        # Calculate file checksum
        checksum = self._calculate_file_checksum(pdf_path)
        
        # Get file stats
        file_stats = pdf_path.stat()
        
        # Determine which extraction methods have results
        doc_id = pdf_path.stem
        extraction_methods = []
        
        for method_key in self.extraction_methods.values():
            method_dir = self.parsed_dir / method_key / doc_id
            if method_dir.exists():
                extraction_methods.append(method_key)
        
        return DocumentMetadata(
            doc_id=doc_id,
            doc_name=pdf_path.name,
            doc_path=str(pdf_path),
            processing_timestamp=datetime.now().isoformat(),
            total_pages=0,  # Will be updated from extraction results
            file_size_bytes=file_stats.st_size,
            checksum=checksum,
            extraction_methods=extraction_methods,
            processing_status='success',
            processing_time_seconds=0.0  # Will be updated
        )
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _extract_blocks_from_method(self, doc_id: str, method: str) -> List[ContentBlock]:
        """Extract blocks from a specific method's results."""
        blocks = []
        method_dir = self.parsed_dir / method / doc_id
        
        if not method_dir.exists():
            self.logger.warning(f"No {method} results found for {doc_id}")
            return blocks
        
        try:
            if method == 'docling':
                blocks = self._extract_docling_blocks(doc_id, method_dir)
            elif method == 'layout_parser':
                blocks = self._extract_layout_parser_blocks(doc_id, method_dir)
            elif method == 'traditional':
                blocks = self._extract_traditional_blocks(doc_id, method_dir)
            
            self.logger.info(f"Extracted {len(blocks)} blocks from {method} for {doc_id}")
            
        except Exception as e:
            self.logger.error(f"Error extracting {method} blocks for {doc_id}: {e}")
        
        return blocks
    
    def _extract_docling_blocks(self, doc_id: str, method_dir: Path) -> List[ContentBlock]:
        """Extract blocks from Docling results."""
        blocks = []
        
        # Load Docling extraction results
        results_file = method_dir / 'docling_extraction_results.json'
        if not results_file.exists():
            return blocks
        
        with open(results_file, 'r', encoding='utf-8') as f:
            docling_results = json.load(f)
        
        # Extract text blocks
        text_dir = method_dir / 'text'
        if text_dir.exists():
            for text_file in text_dir.glob('*.txt'):
                block = self._create_text_block(
                    doc_id=doc_id,
                    block_id=f"docling_{text_file.stem}",
                    method='docling',
                    file_path=text_file,
                    block_type='text'
                )
                if block:
                    blocks.append(block)
        
        # Extract table blocks
        tables_info = docling_results.get('content_structure', {}).get('tables', {})
        for table_info in tables_info.get('tables', []):
            block = self._create_table_block_from_docling(doc_id, table_info, method_dir)
            if block:
                blocks.append(block)
        
        # Extract figure blocks
        figures_info = docling_results.get('content_structure', {}).get('figures', {})
        for figure_info in figures_info.get('figures', []):
            block = self._create_figure_block_from_docling(doc_id, figure_info, method_dir)
            if block:
                blocks.append(block)
        
        # Extract formula blocks  
        formulas_info = docling_results.get('content_structure', {}).get('formulas', {})
        for formula_info in formulas_info.get('formulas', []):
            block = self._create_formula_block_from_docling(doc_id, formula_info, method_dir)
            if block:
                blocks.append(block)
        
        return blocks
    
    def _extract_layout_parser_blocks(self, doc_id: str, method_dir: Path) -> List[ContentBlock]:
        """Extract blocks from LayoutParser results."""
        blocks = []
        
        # Load LayoutParser extraction results
        results_file = method_dir / 'layout_parser_extraction_results.json'
        if not results_file.exists():
            return blocks
        
        with open(results_file, 'r', encoding='utf-8') as f:
            lp_results = json.load(f)
        
        # Process each page and its detected blocks
        for page_info in lp_results.get('pages', []):
            for block_info in page_info.get('detected_blocks', []):
                block = self._create_block_from_layout_parser(doc_id, block_info, method_dir)
                if block:
                    blocks.append(block)
        
        return blocks
    
    def _extract_traditional_blocks(self, doc_id: str, method_dir: Path) -> List[ContentBlock]:
        """Extract blocks from traditional extraction results."""
        blocks = []
        
        # Traditional method typically saves as simple text files
        # We'll create blocks from the directory structure
        
        # Text blocks
        text_dir = method_dir / 'text'
        if text_dir.exists():
            for text_file in text_dir.glob('*.txt'):
                block = self._create_text_block(
                    doc_id=doc_id,
                    block_id=f"traditional_{text_file.stem}",
                    method='traditional',
                    file_path=text_file,
                    block_type='text'
                )
                if block:
                    blocks.append(block)
        
        # Table blocks
        table_dir = method_dir / 'tables'
        if table_dir.exists():
            for table_file in table_dir.glob('*.csv'):
                block = self._create_table_block_from_file(
                    doc_id=doc_id,
                    block_id=f"traditional_{table_file.stem}",
                    method='traditional',
                    file_path=table_file
                )
                if block:
                    blocks.append(block)
        
        return blocks
    
    def _create_text_block(self, doc_id: str, block_id: str, method: str, 
                          file_path: Path, block_type: str) -> Optional[ContentBlock]:
        """Create a text content block from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read().strip()
            
            if not text_content:
                return None
            
            # Calculate quality metrics
            quality_metrics = {
                'text_length': len(text_content),
                'word_count': len(text_content.split()),
                'readability_score': 0.5,  # Placeholder
                'completeness': 1.0
            }
            
            return ContentBlock(
                doc_id=doc_id,
                block_id=block_id,
                extraction_method=method,
                page_number=1,  # Default, will be updated if available
                block_type=block_type,
                confidence=0.8,  # Default confidence for file-based extraction
                bounding_box=None,
                content={
                    'text': text_content,
                    'structured': None,
                    'metadata': {'source_file': str(file_path)}
                },
                provenance={
                    'source_file': str(file_path),
                    'extraction_config': {'method': method},
                    'parent_blocks': [],
                    'child_blocks': []
                },
                semantic_tags=[],
                quality_metrics=quality_metrics
            )
            
        except Exception as e:
            self.logger.error(f"Error creating text block from {file_path}: {e}")
            return None
    
    def _create_table_block_from_docling(self, doc_id: str, table_info: Dict[str, Any], 
                                       method_dir: Path) -> Optional[ContentBlock]:
        """Create table block from Docling table information."""
        try:
            block_id = f"docling_{table_info.get('table_id', 'unknown')}"
            
            # Load table content if available
            table_content = table_info.get('content', [])
            structured_content = None
            
            # Try to load from CSV file if available
            text_file = table_info.get('text_file')
            if text_file and Path(text_file).exists():
                with open(text_file, 'r', encoding='utf-8') as f:
                    table_text = f.read()
            else:
                table_text = '\n'.join(table_content) if table_content else ''
            
            # Create bounding box if available
            bbox = None
            if table_info.get('bbox'):
                bbox_data = table_info['bbox']
                bbox = BoundingBox(
                    x1=bbox_data.get('x1', 0),
                    y1=bbox_data.get('y1', 0),
                    x2=bbox_data.get('x2', 0),
                    y2=bbox_data.get('y2', 0),
                    width=bbox_data.get('width', 0),
                    height=bbox_data.get('height', 0)
                )
            
            return ContentBlock(
                doc_id=doc_id,
                block_id=block_id,
                extraction_method='docling',
                page_number=table_info.get('page', 1),
                block_type='table',
                confidence=table_info.get('confidence', 0.8),
                bounding_box=bbox,
                content={
                    'text': table_text,
                    'structured': table_content,
                    'metadata': table_info
                },
                provenance={
                    'source_file': text_file or '',
                    'extraction_config': {'method': 'docling'},
                    'parent_blocks': [],
                    'child_blocks': []
                },
                semantic_tags=['table'],
                quality_metrics={
                    'text_length': len(table_text),
                    'word_count': len(table_text.split()),
                    'readability_score': 0.7,
                    'completeness': 0.9
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error creating table block from Docling: {e}")
            return None
    
    def _create_figure_block_from_docling(self, doc_id: str, figure_info: Dict[str, Any],
                                        method_dir: Path) -> Optional[ContentBlock]:
        """Create figure block from Docling figure information."""
        try:
            block_id = f"docling_{figure_info.get('figure_id', 'unknown')}"
            
            # Create bounding box if available
            bbox = None
            if figure_info.get('bbox'):
                bbox_data = figure_info['bbox']
                bbox = BoundingBox(
                    x1=bbox_data.get('x1', 0),
                    y1=bbox_data.get('y1', 0),
                    x2=bbox_data.get('x2', 0),
                    y2=bbox_data.get('y2', 0),
                    width=bbox_data.get('width', 0),
                    height=bbox_data.get('height', 0)
                )
            
            return ContentBlock(
                doc_id=doc_id,
                block_id=block_id,
                extraction_method='docling',
                page_number=figure_info.get('page', 1),
                block_type='figure',
                confidence=figure_info.get('confidence', 0.7),
                bounding_box=bbox,
                content={
                    'text': figure_info.get('description', 'Figure'),
                    'structured': figure_info,
                    'metadata': {
                        'image_file': figure_info.get('image_file'),
                        'format': figure_info.get('format', 'unknown')
                    }
                },
                provenance={
                    'source_file': figure_info.get('image_file', ''),
                    'extraction_config': {'method': 'docling'},
                    'parent_blocks': [],
                    'child_blocks': []
                },
                semantic_tags=['figure', 'image'],
                quality_metrics={
                    'text_length': len(figure_info.get('description', '')),
                    'word_count': len(figure_info.get('description', '').split()),
                    'readability_score': 0.5,
                    'completeness': 0.7
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error creating figure block from Docling: {e}")
            return None
    
    def _create_formula_block_from_docling(self, doc_id: str, formula_info: Dict[str, Any],
                                         method_dir: Path) -> Optional[ContentBlock]:
        """Create formula block from Docling formula information."""
        try:
            block_id = f"docling_{formula_info.get('formula_id', 'unknown')}"
            
            return ContentBlock(
                doc_id=doc_id,
                block_id=block_id,
                extraction_method='docling',
                page_number=formula_info.get('page', 1),
                block_type='formula',
                confidence=formula_info.get('confidence', 0.6),
                bounding_box=None,  # Formulas may not have precise bounding boxes
                content={
                    'text': formula_info.get('content', ''),
                    'structured': formula_info,
                    'metadata': {
                        'notation_type': formula_info.get('notation_type', 'unknown'),
                        'complexity': formula_info.get('complexity', 'medium')
                    }
                },
                provenance={
                    'source_file': formula_info.get('source_file', ''),
                    'extraction_config': {'method': 'docling'},
                    'parent_blocks': [],
                    'child_blocks': []
                },
                semantic_tags=['formula', 'math'],
                quality_metrics={
                    'text_length': len(formula_info.get('content', '')),
                    'word_count': len(formula_info.get('content', '').split()),
                    'readability_score': 0.3,  # Formulas are typically less readable as text
                    'completeness': 0.8
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error creating formula block from Docling: {e}")
            return None
    
    def _create_block_from_layout_parser(self, doc_id: str, block_info: Dict[str, Any],
                                       method_dir: Path) -> Optional[ContentBlock]:
        """Create block from LayoutParser block information."""
        try:
            block_id = block_info.get('block_id', 'unknown')
            block_type = block_info.get('type', 'unknown')
            
            # Create bounding box
            bbox = None
            if block_info.get('bounding_box'):
                bbox_data = block_info['bounding_box']
                bbox = BoundingBox(
                    x1=bbox_data.get('x1', 0),
                    y1=bbox_data.get('y1', 0),
                    x2=bbox_data.get('x2', 0),
                    y2=bbox_data.get('y2', 0),
                    width=bbox_data.get('width', 0),
                    height=bbox_data.get('height', 0)
                )
            
            # Get content based on block type
            content_text = block_info.get('content', '')
            if isinstance(content_text, dict):
                content_text = str(content_text)
            
            return ContentBlock(
                doc_id=doc_id,
                block_id=block_id,
                extraction_method='layout_parser',
                page_number=1,  # Will be extracted from block_id if available
                block_type=block_type,
                confidence=block_info.get('confidence', 0.8),
                bounding_box=bbox,
                content={
                    'text': content_text,
                    'structured': block_info.get('content'),
                    'metadata': {
                        'extraction_method': block_info.get('extraction_method'),
                        'file_saved': block_info.get('file_saved')
                    }
                },
                provenance={
                    'source_file': block_info.get('file_saved', ''),
                    'extraction_config': {'method': 'layout_parser'},
                    'parent_blocks': [],
                    'child_blocks': []
                },
                semantic_tags=[block_type],
                quality_metrics={
                    'text_length': len(content_text),
                    'word_count': len(content_text.split()) if content_text else 0,
                    'readability_score': 0.7,
                    'completeness': 0.8
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error creating block from LayoutParser: {e}")
            return None
    
    def _create_table_block_from_file(self, doc_id: str, block_id: str, method: str,
                                    file_path: Path) -> Optional[ContentBlock]:
        """Create table block from CSV file."""
        try:
            # Read CSV file using built-in csv module
            table_data = []
            with open(file_path, 'r', encoding='utf-8') as f:
                csv_reader = csv.reader(f)
                table_data = list(csv_reader)
            
            if not table_data:
                return None
            
            # Convert to text representation
            table_text = '\n'.join([','.join(row) for row in table_data])
            
            # Convert to structured format (list of dictionaries)
            structured_data = []
            if len(table_data) > 1:
                headers = table_data[0]
                for row in table_data[1:]:
                    row_dict = {}
                    for i, cell in enumerate(row):
                        if i < len(headers):
                            row_dict[headers[i]] = cell
                    structured_data.append(row_dict)
            
            return ContentBlock(
                doc_id=doc_id,
                block_id=block_id,
                extraction_method=method,
                page_number=1,
                block_type='table',
                confidence=0.7,
                bounding_box=None,
                content={
                    'text': table_text,
                    'structured': structured_data,
                    'metadata': {
                        'source_file': str(file_path),
                        'rows': len(table_data) - 1 if len(table_data) > 1 else 0,
                        'columns': len(table_data[0]) if table_data else 0
                    }
                },
                provenance={
                    'source_file': str(file_path),
                    'extraction_config': {'method': method},
                    'parent_blocks': [],
                    'child_blocks': []
                },
                semantic_tags=['table'],
                quality_metrics={
                    'text_length': len(table_text),
                    'word_count': len(table_text.split()),
                    'readability_score': 0.8,
                    'completeness': 0.9
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error creating table block from {file_path}: {e}")
            return None
    
    def _create_unified_blocks(self, all_blocks: List[ContentBlock], doc_id: str) -> List[ContentBlock]:
        """Create unified blocks by consolidating across methods."""
        # This is a simplified approach - in practice, you might want more sophisticated
        # deduplication and consolidation logic
        
        unified_blocks = []
        
        # Group blocks by type and content similarity
        blocks_by_type = {}
        for block in all_blocks:
            block_type = block.block_type
            if block_type not in blocks_by_type:
                blocks_by_type[block_type] = []
            blocks_by_type[block_type].append(block)
        
        # For now, just take the best block of each type from each page
        for block_type, type_blocks in blocks_by_type.items():
            # Group by page
            blocks_by_page = {}
            for block in type_blocks:
                page = block.page_number
                if page not in blocks_by_page:
                    blocks_by_page[page] = []
                blocks_by_page[page].append(block)
            
            # Select best block from each page
            for page, page_blocks in blocks_by_page.items():
                # Sort by confidence and select best
                best_block = max(page_blocks, key=lambda b: b.confidence)
                
                # Create unified block
                unified_block = ContentBlock(
                    doc_id=doc_id,
                    block_id=f"unified_{block_type}_{page:03d}_{uuid.uuid4().hex[:8]}",
                    extraction_method='unified',
                    page_number=page,
                    block_type=block_type,
                    confidence=best_block.confidence,
                    bounding_box=best_block.bounding_box,
                    content=best_block.content,
                    provenance={
                        'source_methods': [b.extraction_method for b in page_blocks],
                        'best_method': best_block.extraction_method,
                        'consolidation_strategy': 'highest_confidence',
                        'alternative_blocks': [b.block_id for b in page_blocks if b != best_block]
                    },
                    semantic_tags=best_block.semantic_tags,
                    quality_metrics=best_block.quality_metrics
                )
                
                unified_blocks.append(unified_block)
        
        return unified_blocks
    
    def _save_method_jsonl(self, blocks: List[ContentBlock], doc_id: str, method: str):
        """Save method-specific blocks to JSONL file."""
        jsonl_file = self.metadata_dir / 'blocks' / method / f'{doc_id}.jsonl'
        
        with open(jsonl_file, 'w', encoding='utf-8') as f:
            for block in blocks:
                json.dump(block.to_dict(), f, ensure_ascii=False, default=str)
                f.write('\n')
        
        self.logger.info(f"Saved {len(blocks)} {method} blocks to {jsonl_file}")
    
    def _save_unified_jsonl(self, blocks: List[ContentBlock], doc_id: str):
        """Save unified blocks to JSONL file."""
        jsonl_file = self.metadata_dir / 'blocks' / 'unified' / f'{doc_id}.jsonl'
        
        with open(jsonl_file, 'w', encoding='utf-8') as f:
            for block in blocks:
                json.dump(block.to_dict(), f, ensure_ascii=False, default=str)  
                f.write('\n')
        
        self.logger.info(f"Saved {len(blocks)} unified blocks to {jsonl_file}")
    
    def _generate_markdown_with_provenance(self, doc_metadata: DocumentMetadata,
                                         blocks: List[ContentBlock], doc_id: str):
        """Generate Markdown output with embedded provenance metadata."""
        markdown_content = []
        
        # Document header with metadata
        markdown_content.append(f"# Document: {doc_metadata.doc_name}\n")
        markdown_content.append("## Document Metadata\n")
        markdown_content.append(f"- **Document ID**: {doc_metadata.doc_id}")
        markdown_content.append(f"- **Processing Date**: {doc_metadata.processing_timestamp}")
        markdown_content.append(f"- **Extraction Methods**: {', '.join(doc_metadata.extraction_methods)}")
        markdown_content.append(f"- **Total Pages**: {doc_metadata.total_pages}")
        markdown_content.append(f"- **File Size**: {doc_metadata.file_size_bytes:,} bytes")
        markdown_content.append(f"- **Checksum**: {doc_metadata.checksum[:16]}...")
        markdown_content.append("\n---\n")
        
        # Group blocks by page and type
        blocks_by_page = {}
        for block in blocks:
            page = block.page_number
            if page not in blocks_by_page:
                blocks_by_page[page] = {}
            
            block_type = block.block_type
            if block_type not in blocks_by_page[page]:
                blocks_by_page[page][block_type] = []
            blocks_by_page[page][block_type].append(block)
        
        # Generate content by page
        for page_num in sorted(blocks_by_page.keys()):
            markdown_content.append(f"## Page {page_num}\n")
            
            page_blocks = blocks_by_page[page_num]
            
            # Process block types in logical order
            for block_type in ['title', 'text', 'table', 'figure', 'formula', 'list']:
                if block_type not in page_blocks:
                    continue
                
                type_blocks = page_blocks[block_type]
                
                if block_type == 'title':
                    markdown_content.append("### Titles\n")
                elif block_type == 'text':
                    markdown_content.append("### Text Content\n")
                elif block_type == 'table':
                    markdown_content.append("### Tables\n")
                elif block_type == 'figure':
                    markdown_content.append("### Figures\n")
                elif block_type == 'formula':
                    markdown_content.append("### Formulas\n")
                elif block_type == 'list':
                    markdown_content.append("### Lists\n")
                
                for block in type_blocks:
                    # Add block content
                    content_text = block.content.get('text', '')
                    if content_text:
                        markdown_content.append(f"{content_text}\n")
                    
                    # Add provenance metadata as comment
                    provenance_info = [
                        f"<!-- Block Metadata:",
                        f"Block ID: {block.block_id}",
                        f"Extraction Method: {block.extraction_method}",
                        f"Confidence: {block.confidence:.2f}",
                        f"Quality Score: {block.quality_metrics.get('completeness', 0):.2f}",
                        f"-->\n"
                    ]
                    markdown_content.extend(provenance_info)
        
        # Save markdown file
        markdown_file = self.staged_dir / 'markdown' / f'{doc_id}.md'
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_content))
        
        self.logger.info(f"Generated markdown with provenance: {markdown_file}")
    
    def _generate_json_export(self, doc_metadata: DocumentMetadata,
                            blocks: List[ContentBlock], doc_id: str):
        """Generate comprehensive JSON export."""
        json_export = {
            'document_metadata': doc_metadata.to_dict(),
            'blocks': [block.to_dict() for block in blocks],
            'summary': {
                'total_blocks': len(blocks),
                'blocks_by_type': {},
                'extraction_methods_used': list(set(block.extraction_method for block in blocks)),
                'quality_statistics': self._calculate_quality_statistics(blocks)
            }
        }
        
        # Calculate blocks by type
        for block in blocks:
            block_type = block.block_type
            json_export['summary']['blocks_by_type'][block_type] = \
                json_export['summary']['blocks_by_type'].get(block_type, 0) + 1
        
        # Save JSON file
        json_file = self.staged_dir / 'json' / f'{doc_id}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_export, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Generated JSON export: {json_file}")
    
    def _calculate_quality_statistics(self, blocks: List[ContentBlock]) -> Dict[str, float]:
        """Calculate quality statistics for blocks."""
        if not blocks:
            return {}
        
        confidences = [block.confidence for block in blocks]
        completeness_scores = [block.quality_metrics.get('completeness', 0) for block in blocks]
        
        return {
            'average_confidence': sum(confidences) / len(confidences),
            'min_confidence': min(confidences),
            'max_confidence': max(confidences),
            'average_completeness': sum(completeness_scores) / len(completeness_scores),
            'total_text_length': sum(block.quality_metrics.get('text_length', 0) for block in blocks),
            'total_word_count': sum(block.quality_metrics.get('word_count', 0) for block in blocks)
        }
    
    def _log_statistics(self):
        """Log extraction statistics."""
        self.logger.info("=== Metadata Extraction Statistics ===")
        self.logger.info(f"Documents processed: {self.stats['documents_processed']}")
        self.logger.info(f"Total blocks extracted: {self.stats['total_blocks_extracted']}")
        self.logger.info(f"Blocks by method: {self.stats['blocks_by_method']}")
        self.logger.info(f"Blocks by type: {self.stats['blocks_by_type']}")
        self.logger.info(f"Processing time: {self.stats['processing_time']:.2f} seconds")


def main():
    """Main function to demonstrate metadata extraction."""
    print("=== PDF Metadata Extraction and Staging ===")
    print("Creating unified metadata from all extraction methods...")
    print()
    print("Directory structure:")
    print("data/metadata/")
    print("  ├── documents/           # Document-level metadata")
    print("  ├── blocks/             # Block-level JSONL files")
    print("  │   ├── docling/        # Docling method blocks")
    print("  │   ├── layout_parser/  # LayoutParser method blocks") 
    print("  │   ├── traditional/    # Traditional method blocks")
    print("  │   └── unified/        # Cross-method unified blocks")
    print("  ├── provenance/         # Extraction provenance")
    print("  └── schemas/            # Schema definitions")
    print()
    print("data/staged/")
    print("  ├── markdown/           # Markdown with provenance")
    print("  ├── json/               # JSON exports")
    print("  └── search_index/       # Search-optimized formats")
    print()
    
    try:
        # Initialize metadata extractor
        extractor = MetadataExtractor()
        
        # Process all documents
        results = extractor.process_all_documents()
        
        if results['status'] == 'no_files':
            print("No PDF files found. Please ensure PDF files are in data/raw/pdf/")
            return
        
        # Display results summary
        print(f"✓ Metadata extraction completed!")
        print(f"Documents processed: {results['documents_processed']}")
        print(f"Total blocks extracted: {extractor.stats['total_blocks_extracted']}")
        print(f"Processing time: {results['processing_time_seconds']:.2f} seconds")
        print()
        
        # Show method breakdown
        if extractor.stats['blocks_by_method']:
            print("Blocks by extraction method:")
            for method, count in extractor.stats['blocks_by_method'].items():
                print(f"  {method}: {count}")
            print()
        
        # Show type breakdown  
        if extractor.stats['blocks_by_type']:
            print("Blocks by content type:")
            for block_type, count in extractor.stats['blocks_by_type'].items():
                print(f"  {block_type}: {count}")
            print()
        
        print("Outputs generated:")
        print("✓ JSONL files with block-level metadata")
        print("✓ Markdown files with embedded provenance")
        print("✓ JSON exports with comprehensive metadata")
        print("✓ Document registry and processing logs")
        
    except Exception as e:
        print(f"Error during metadata extraction: {e}")
        raise


if __name__ == "__main__":
    main()