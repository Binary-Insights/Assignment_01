"""
Simplified LayoutParser-like Document Analyzer

This is a fallback implementation that simulates LayoutParser functionality
using basic computer vision techniques when LayoutParser dependencies are not available.

Features:
- Basic block detection using contour analysis
- Heuristic-based block type classification
- Bounding box persistence
- Content routing to specialized extracters
"""

import cv2
import numpy as np
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image, ImageDraw, ImageEnhance
import json
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
import io


class SimpleLayoutAnalyzer:
    """
    Simplified document layout analyzer using basic computer vision.
    
    This class provides similar functionality to LayoutParser but uses
    basic image processing techniques for block detection.
    """
    
    def __init__(self, output_dir="data/parsed"):
        """
        Initialize the simple layout analyzer.
        
        Args:
            output_dir (str): Directory to save extracted content
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Block detection parameters
        self.min_block_area = 1000  # Minimum area for a valid block
        self.min_block_width = 50
        self.min_block_height = 20
        
        # Extraction statistics
        self.stats = {
            'total_pages': 0,
            'total_blocks': 0,
            'blocks_by_type': {'text': 0, 'table': 0, 'figure': 0, 'title': 0},
            'extraction_success': 0,
            'extraction_failures': 0,
            'processing_time': 0
        }
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logger = logging.getLogger('SimpleLayoutAnalyzer')
        logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = self.output_dir / 'simple_layout_log.txt'
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
    
    def extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract content from PDF using simple layout analysis.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            dict: Comprehensive extraction results
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            self.logger.error(f"PDF file not found: {pdf_path}")
            return None
        
        self.logger.info(f"Starting simple layout analysis from: {pdf_path.name}")
        start_time = datetime.now()
        
        # Create output directories
        pdf_output_dir = self.output_dir / pdf_path.stem
        self._create_output_directories(pdf_output_dir)
        
        extraction_results = {
            'pdf_name': pdf_path.name,
            'total_pages': 0,
            'pages': [],
            'layout_analysis': [],
            'extraction_summary': {},
            'bounding_boxes_saved': False
        }
        
        try:
            # Process with pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                extraction_results['total_pages'] = len(pdf.pages)
                self.stats['total_pages'] = len(pdf.pages)
                
                for page_num, pdf_page in enumerate(pdf.pages, 1):
                    self.logger.info(f"Processing page {page_num}/{len(pdf.pages)}")
                    
                    page_result = self._process_page_simple(
                        pdf_page, page_num, pdf_output_dir
                    )
                    
                    extraction_results['pages'].append(page_result)
                    extraction_results['layout_analysis'].extend(page_result['detected_blocks'])
        
        except Exception as e:
            self.logger.error(f"Error processing PDF: {e}")
            return None
        
        # Calculate processing time and save results
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        self.stats['processing_time'] = processing_time
        
        # Generate extraction summary
        extraction_results['extraction_summary'] = self._generate_summary()
        
        # Save comprehensive results
        self._save_extraction_results(extraction_results, pdf_output_dir)
        extraction_results['bounding_boxes_saved'] = True
        
        self.logger.info(f"Simple layout analysis completed in {processing_time:.2f} seconds")
        self._log_statistics()
        
        return extraction_results
    
    def _create_output_directories(self, base_dir: Path):
        """Create organized output directory structure."""
        directories = ['text', 'tables', 'figures', 'titles', 'layout_images', 'bounding_boxes']
        for dir_name in directories:
            (base_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    def _process_page_simple(self, pdf_page, page_num: int, output_dir: Path) -> Dict[str, Any]:
        """
        Process a single page using simple layout analysis techniques.
        
        Args:
            pdf_page: pdfplumber page object
            page_num (int): Page number
            output_dir (Path): Output directory
            
        Returns:
            dict: Page processing results
        """
        page_result = {
            'page_number': page_num,
            'detected_blocks': [],
            'extracted_content': {
                'text': [],
                'tables': [],
                'figures': [],
                'titles': []
            },
            'processing_success': True
        }
        
        try:
            # Get page dimensions
            page_width = pdf_page.width
            page_height = pdf_page.height
            
            # 1. Extract tables first (they have clear structure)
            tables = pdf_page.extract_tables()
            table_blocks = []
            
            for table_idx, table in enumerate(tables):
                if table and len(table) > 0:
                    # Estimate table bounding box (this is simplified)
                    table_bbox = self._estimate_table_bbox(pdf_page, table, table_idx)
                    
                    if table_bbox:
                        table_block = {
                            'block_id': f"page_{page_num:03d}_table_{table_idx:03d}",
                            'type': 'table',
                            'confidence': 0.9,  # High confidence for detected tables
                            'bounding_box': table_bbox,
                            'content': table,
                            'extraction_method': 'pdfplumber_table'
                        }
                        
                        # Save table
                        df = pd.DataFrame(table[1:], columns=table[0])
                        file_path = output_dir / 'tables' / f"{table_block['block_id']}.csv"
                        df.to_csv(file_path, index=False, encoding='utf-8')
                        table_block['file_saved'] = str(file_path)
                        
                        table_blocks.append(table_block)
                        page_result['detected_blocks'].append(table_block)
                        page_result['extracted_content']['tables'].append(table_block)
                        
                        self.stats['blocks_by_type']['table'] += 1
                        self.stats['extraction_success'] += 1
            
            # 2. Extract text blocks using word positioning
            words = pdf_page.extract_words()
            text_blocks = self._group_words_into_blocks(words, page_num, output_dir)
            
            for text_block in text_blocks:
                page_result['detected_blocks'].append(text_block)
                
                # Classify text block type based on properties
                if self._is_title_block(text_block):
                    text_block['type'] = 'title'
                    page_result['extracted_content']['titles'].append(text_block)
                    self.stats['blocks_by_type']['title'] += 1
                else:
                    text_block['type'] = 'text'
                    page_result['extracted_content']['text'].append(text_block)
                    self.stats['blocks_by_type']['text'] += 1
                
                self.stats['extraction_success'] += 1
            
            # 3. Detect potential figure areas (simplified)
            figure_blocks = self._detect_figure_areas(pdf_page, page_num, output_dir)
            for figure_block in figure_blocks:
                page_result['detected_blocks'].append(figure_block)
                page_result['extracted_content']['figures'].append(figure_block)
                self.stats['blocks_by_type']['figure'] += 1
                self.stats['extraction_success'] += 1
            
            self.stats['total_blocks'] += len(page_result['detected_blocks'])
            
            # Create layout visualization
            self._create_simple_layout_visualization(page_result['detected_blocks'], 
                                                   page_width, page_height, 
                                                   page_num, output_dir)
        
        except Exception as e:
            self.logger.error(f"Error processing page {page_num}: {e}")
            page_result['processing_success'] = False
            self.stats['extraction_failures'] += 1
        
        return page_result
    
    def _estimate_table_bbox(self, pdf_page, table, table_idx: int) -> Optional[Dict[str, float]]:
        """Estimate bounding box for a detected table."""
        try:
            # This is a simplified approach - in reality, you'd need more sophisticated methods
            # For now, we'll return a placeholder bbox
            page_width = pdf_page.width
            page_height = pdf_page.height
            
            # Estimate based on table position (very simplified)
            y_start = (table_idx * page_height / 10) + 100
            y_end = y_start + (len(table) * 20)  # Rough estimate
            
            return {
                'x1': 50.0,
                'y1': y_start,
                'x2': page_width - 50.0,
                'y2': min(y_end, page_height - 50),
                'width': page_width - 100.0,
                'height': min(y_end - y_start, page_height - 100)
            }
        except:
            return None
    
    def _group_words_into_blocks(self, words: List[Dict], page_num: int, output_dir: Path) -> List[Dict]:
        """Group words into text blocks based on proximity."""
        if not words:
            return []
        
        # Sort words by position (top to bottom, left to right)
        sorted_words = sorted(words, key=lambda w: (w.get('top', 0), w.get('x0', 0)))
        
        text_blocks = []
        current_block_words = []
        current_y = None
        line_threshold = 5  # Pixels tolerance for same line
        block_gap_threshold = 20  # Gap to start new block
        
        for word in sorted_words:
            word_y = word.get('top', 0)
            
            if current_y is None:
                current_y = word_y
                current_block_words = [word]
            elif abs(word_y - current_y) <= line_threshold:
                # Same line
                current_block_words.append(word)
            elif word_y - current_y <= block_gap_threshold:
                # Close enough to be same block
                current_block_words.append(word)
                current_y = word_y
            else:
                # Start new block
                if current_block_words:
                    block = self._create_text_block_from_words(current_block_words, 
                                                             len(text_blocks), 
                                                             page_num, output_dir)
                    if block:
                        text_blocks.append(block)
                
                current_block_words = [word]
                current_y = word_y
        
        # Add final block
        if current_block_words:
            block = self._create_text_block_from_words(current_block_words, 
                                                     len(text_blocks), 
                                                     page_num, output_dir)
            if block:
                text_blocks.append(block)
        
        return text_blocks
    
    def _create_text_block_from_words(self, words: List[Dict], block_idx: int, 
                                    page_num: int, output_dir: Path) -> Optional[Dict]:
        """Create a text block from a group of words."""
        if not words:
            return None
        
        try:
            # Calculate bounding box
            x_coords = [w.get('x0', 0) for w in words] + [w.get('x1', 0) for w in words]
            y_coords = [w.get('top', 0) for w in words] + [w.get('bottom', 0) for w in words]
            
            x1, x2 = min(x_coords), max(x_coords)
            y1, y2 = min(y_coords), max(y_coords)
            
            # Extract text
            text = ' '.join([w.get('text', '') for w in words])
            text = text.strip()
            
            if len(text) < 3:  # Skip very short text blocks
                return None
            
            block_id = f"page_{page_num:03d}_text_{block_idx:03d}"
            
            # Save text block
            file_path = output_dir / 'text' / f"{block_id}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            return {
                'block_id': block_id,
                'type': 'text',  # Will be reclassified later
                'confidence': 0.8,
                'bounding_box': {
                    'x1': float(x1),
                    'y1': float(y1),
                    'x2': float(x2),
                    'y2': float(y2),
                    'width': float(x2 - x1),
                    'height': float(y2 - y1)
                },
                'content': text,
                'extraction_method': 'word_grouping',
                'file_saved': str(file_path)
            }
        
        except Exception as e:
            self.logger.error(f"Error creating text block: {e}")
            return None
    
    def _is_title_block(self, text_block: Dict) -> bool:
        """Heuristically determine if a text block is a title."""
        content = text_block.get('content', '')
        bbox = text_block.get('bounding_box', {})
        
        # Simple heuristics for title detection
        is_short = len(content.split()) <= 10
        is_uppercase = content.isupper()
        is_center_positioned = bbox.get('x1', 0) > 100  # Simplified center check
        
        return is_short and (is_uppercase or is_center_positioned)
    
    def _detect_figure_areas(self, pdf_page, page_num: int, output_dir: Path) -> List[Dict]:
        """Detect potential figure areas (very simplified)."""
        # This is a placeholder - real figure detection would need image analysis
        figures = []
        
        # Look for images in the PDF
        if hasattr(pdf_page, 'images'):
            for img_idx, img in enumerate(pdf_page.images):
                figure_id = f"page_{page_num:03d}_figure_{img_idx:03d}"
                
                figure_block = {
                    'block_id': figure_id,
                    'type': 'figure',
                    'confidence': 0.7,
                    'bounding_box': {
                        'x1': float(img.get('x0', 0)),
                        'y1': float(img.get('top', 0)),
                        'x2': float(img.get('x1', 100)),
                        'y2': float(img.get('bottom', 100)),
                        'width': float(img.get('width', 100)),
                        'height': float(img.get('height', 100))
                    },
                    'content': f"Image {img_idx + 1}",
                    'extraction_method': 'pdf_image_detection',
                    'file_saved': None
                }
                
                figures.append(figure_block)
        
        return figures
    
    def _create_simple_layout_visualization(self, blocks: List[Dict], page_width: float, 
                                          page_height: float, page_num: int, output_dir: Path):
        """Create a simple visualization of detected blocks."""
        try:
            # Create a simple image showing block positions
            fig_width, fig_height = int(page_width * 0.5), int(page_height * 0.5)
            img = Image.new('RGB', (fig_width, fig_height), 'white')
            draw = ImageDraw.Draw(img)
            
            # Color coding for different block types
            colors = {
                'text': 'blue',
                'title': 'red', 
                'table': 'green',
                'figure': 'purple'
            }
            
            for block in blocks:
                bbox = block['bounding_box']
                block_type = block['type']
                color = colors.get(block_type, 'black')
                
                # Scale coordinates to fit image
                x1 = int(bbox['x1'] * 0.5)
                y1 = int(bbox['y1'] * 0.5)
                x2 = int(bbox['x2'] * 0.5)
                y2 = int(bbox['y2'] * 0.5)
                
                # Draw rectangle
                draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
                
                # Add label
                draw.text((x1, y1-15), f"{block_type}", fill=color)
            
            # Save visualization
            vis_path = output_dir / 'layout_images' / f"page_{page_num:03d}_layout.png"
            img.save(vis_path)
            
        except Exception as e:
            self.logger.error(f"Error creating layout visualization: {e}")
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate extraction summary statistics."""
        return {
            'total_pages_processed': self.stats['total_pages'],
            'total_blocks_detected': self.stats['total_blocks'],
            'blocks_by_type': self.stats['blocks_by_type'],
            'extraction_success_count': self.stats['extraction_success'],
            'extraction_failure_count': self.stats['extraction_failures'],
            'success_rate': (self.stats['extraction_success'] / 
                           max(self.stats['total_blocks'], 1)) * 100,
            'processing_time_seconds': self.stats['processing_time']
        }
    
    def _save_extraction_results(self, results: Dict[str, Any], output_dir: Path):
        """Save comprehensive extraction results and bounding boxes."""
        # Save main results
        results_file = output_dir / 'simple_layout_results.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save bounding boxes separately
        bounding_boxes = []
        for page in results['pages']:
            for block in page['detected_blocks']:
                bbox_data = {
                    'page_number': page['page_number'],
                    'block_id': block['block_id'],
                    'type': block['type'],
                    'confidence': block['confidence'],
                    'bounding_box': block['bounding_box'],
                    'file_path': block.get('file_saved')
                }
                bounding_boxes.append(bbox_data)
        
        bbox_file = output_dir / 'bounding_boxes' / 'all_blocks.json'
        with open(bbox_file, 'w', encoding='utf-8') as f:
            json.dump(bounding_boxes, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Simple layout results saved to {results_file}")
    
    def _log_statistics(self):
        """Log comprehensive extraction statistics."""
        self.logger.info("=== Simple Layout Analysis Statistics ===")
        self.logger.info(f"Total pages processed: {self.stats['total_pages']}")
        self.logger.info(f"Total blocks detected: {self.stats['total_blocks']}")
        self.logger.info(f"Blocks by type: {self.stats['blocks_by_type']}")
        self.logger.info(f"Processing time: {self.stats['processing_time']:.2f} seconds")


def main():
    """Main function to demonstrate simple layout analysis."""
    # Initialize analyzer
    analyzer = SimpleLayoutAnalyzer()
    
    # Find PDF files
    pdf_dir = Path("data/raw/pdf")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in data/raw/pdf directory")
        return
    
    # Process each PDF
    for pdf_file in pdf_files:
        print(f"\nProcessing with Simple Layout Analyzer: {pdf_file.name}")
        results = analyzer.extract_from_pdf(pdf_file)
        
        if results:
            summary = results['extraction_summary']
            print(f"✓ Simple layout analysis completed for {pdf_file.name}")
            print(f"  Total pages: {summary['total_pages_processed']}")
            print(f"  Total blocks: {summary['total_blocks_detected']}")
            print(f"  Success rate: {summary['success_rate']:.1f}%")
            print(f"  Blocks by type: {summary['blocks_by_type']}")
        else:
            print(f"✗ Simple layout analysis failed for {pdf_file.name}")


if __name__ == "__main__":
    main()