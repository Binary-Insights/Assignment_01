"""
Basic Layout-Aware PDF Extractor

This module provides layout-aware PDF extraction using existing dependencies
(pdfplumber, pytesseract, PIL) to detect and route different content types.

Features:
- Block detection using word positioning and table detection
- Content type classification (text, tables, titles)
- Bounding box persistence for layout reconstruction
- Routing to specialized extraction methods
"""

import pdfplumber
import pytesseract
from PIL import Image, ImageDraw
import json
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
import io
import pandas as pd


class BasicLayoutExtractor:
    """
    Basic layout-aware PDF extractor using existing dependencies.
    
    This class provides layout analysis functionality without requiring
    heavy deep learning dependencies like LayoutParser.
    """
    
    def __init__(self, output_dir="data/parsed"):
        """
        Initialize the basic layout extractor.
        
        Args:
            output_dir (str): Directory to save extracted content
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Block detection parameters
        self.line_height_threshold = 5  # Pixels for same line detection
        self.block_gap_threshold = 20   # Gap between blocks
        self.title_max_words = 10       # Max words for title classification
        
        # Extraction statistics
        self.stats = {
            'total_pages': 0,
            'total_blocks': 0,
            'blocks_by_type': {'text': 0, 'table': 0, 'title': 0},
            'extraction_success': 0,
            'extraction_failures': 0,
            'processing_time': 0
        }
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logger = logging.getLogger('BasicLayoutExtractor')
        logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = self.output_dir / 'basic_layout_log.txt'
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
        Extract content from PDF using basic layout analysis.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            dict: Comprehensive extraction results
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            self.logger.error(f"PDF file not found: {pdf_path}")
            return None
        
        self.logger.info(f"Starting basic layout extraction from: {pdf_path.name}")
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
                    
                    page_result = self._process_page_with_layout(
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
        
        self.logger.info(f"Basic layout extraction completed in {processing_time:.2f} seconds")
        self._log_statistics()
        
        return extraction_results
    
    def _create_output_directories(self, base_dir: Path):
        """Create organized output directory structure."""
        directories = ['text', 'tables', 'titles', 'layout_images', 'bounding_boxes']
        for dir_name in directories:
            (base_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    def _process_page_with_layout(self, pdf_page, page_num: int, output_dir: Path) -> Dict[str, Any]:
        """
        Process a single page using basic layout analysis.
        
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
                'titles': []
            },
            'processing_success': True
        }
        
        try:
            # Step 1: Extract tables first (they have clear structure)
            self.logger.debug(f"Page {page_num}: Extracting tables")
            table_blocks = self._extract_table_blocks(pdf_page, page_num, output_dir)
            page_result['detected_blocks'].extend(table_blocks)
            page_result['extracted_content']['tables'] = table_blocks
            
            # Step 2: Extract text blocks using word positioning
            self.logger.debug(f"Page {page_num}: Extracting text blocks")
            text_blocks = self._extract_text_blocks(pdf_page, page_num, output_dir, table_blocks)
            
            # Step 3: Classify text blocks into titles and regular text
            for text_block in text_blocks:
                if self._is_title_block(text_block):
                    text_block['type'] = 'title'
                    # Save to titles directory
                    self._save_title_block(text_block, output_dir)
                    page_result['extracted_content']['titles'].append(text_block)
                    self.stats['blocks_by_type']['title'] += 1
                else:
                    text_block['type'] = 'text'
                    page_result['extracted_content']['text'].append(text_block)
                    self.stats['blocks_by_type']['text'] += 1
                
                page_result['detected_blocks'].append(text_block)
                self.stats['extraction_success'] += 1
            
            self.stats['total_blocks'] += len(page_result['detected_blocks'])
            
            # Step 4: Create layout visualization
            self._create_layout_visualization(page_result['detected_blocks'], 
                                           pdf_page.width, pdf_page.height,
                                           page_num, output_dir)
        
        except Exception as e:
            self.logger.error(f"Error processing page {page_num}: {e}")
            page_result['processing_success'] = False
            self.stats['extraction_failures'] += 1
        
        return page_result
    
    def _extract_table_blocks(self, pdf_page, page_num: int, output_dir: Path) -> List[Dict]:
        """Extract table blocks from the page."""
        table_blocks = []
        
        try:
            tables = pdf_page.extract_tables()
            
            for table_idx, table in enumerate(tables):
                if table and len(table) > 1:  # Must have at least header + 1 row
                    table_id = f"page_{page_num:03d}_table_{table_idx:03d}"
                    
                    # Estimate table bounding box
                    table_bbox = self._estimate_table_bbox(pdf_page, table, table_idx)
                    
                    table_block = {
                        'block_id': table_id,
                        'type': 'table',
                        'confidence': 0.9,
                        'bounding_box': table_bbox,
                        'content': table,
                        'extraction_method': 'pdfplumber_table',
                        'file_saved': None
                    }
                    
                    # Save table to CSV
                    try:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        csv_path = output_dir / 'tables' / f"{table_id}.csv"
                        df.to_csv(csv_path, index=False, encoding='utf-8')
                        table_block['file_saved'] = str(csv_path)
                        
                        # Also save raw table data
                        json_path = output_dir / 'tables' / f"{table_id}.json"
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(table, f, indent=2, ensure_ascii=False)
                        
                        table_blocks.append(table_block)
                        self.stats['blocks_by_type']['table'] += 1
                        self.stats['extraction_success'] += 1
                        
                        self.logger.info(f"Extracted table {table_idx + 1} from page {page_num}: {len(table)} rows")
                    
                    except Exception as e:
                        self.logger.error(f"Error saving table {table_id}: {e}")
                        self.stats['extraction_failures'] += 1
        
        except Exception as e:
            self.logger.error(f"Error extracting tables from page {page_num}: {e}")
        
        return table_blocks
    
    def _extract_text_blocks(self, pdf_page, page_num: int, output_dir: Path, 
                           table_blocks: List[Dict]) -> List[Dict]:
        """Extract text blocks from the page, avoiding table areas."""
        text_blocks = []
        
        try:
            # Get all words from the page
            words = pdf_page.extract_words()
            if not words:
                return text_blocks
            
            # Filter out words that are within table areas
            filtered_words = self._filter_words_outside_tables(words, table_blocks)
            
            # Group words into text blocks
            grouped_blocks = self._group_words_into_text_blocks(filtered_words)
            
            # Create text block objects
            for block_idx, word_group in enumerate(grouped_blocks):
                text_block = self._create_text_block_from_words(
                    word_group, block_idx, page_num, output_dir
                )
                
                if text_block:
                    text_blocks.append(text_block)
        
        except Exception as e:
            self.logger.error(f"Error extracting text blocks from page {page_num}: {e}")
        
        return text_blocks
    
    def _filter_words_outside_tables(self, words: List[Dict], table_blocks: List[Dict]) -> List[Dict]:
        """Filter words that don't fall within table bounding boxes."""
        if not table_blocks:
            return words
        
        filtered_words = []
        
        for word in words:
            word_x = word.get('x0', 0)
            word_y = word.get('top', 0)
            
            # Check if word is inside any table
            inside_table = False
            for table_block in table_blocks:
                bbox = table_block['bounding_box']
                if (bbox['x1'] <= word_x <= bbox['x2'] and 
                    bbox['y1'] <= word_y <= bbox['y2']):
                    inside_table = True
                    break
            
            if not inside_table:
                filtered_words.append(word)
        
        return filtered_words
    
    def _group_words_into_text_blocks(self, words: List[Dict]) -> List[List[Dict]]:
        """Group words into coherent text blocks based on proximity."""
        if not words:
            return []
        
        # Sort words by position (top to bottom, left to right)
        sorted_words = sorted(words, key=lambda w: (w.get('top', 0), w.get('x0', 0)))
        
        text_blocks = []
        current_block = []
        
        for word in sorted_words:
            if not current_block:
                current_block = [word]
            else:
                # Check if word belongs to current block
                last_word = current_block[-1]
                
                # Calculate vertical distance
                vert_distance = word.get('top', 0) - last_word.get('bottom', 0)
                
                if vert_distance <= self.block_gap_threshold:
                    # Word belongs to current block
                    current_block.append(word)
                else:
                    # Start new block
                    if len(current_block) > 2:  # Only keep blocks with multiple words
                        text_blocks.append(current_block)
                    current_block = [word]
        
        # Add final block
        if len(current_block) > 2:
            text_blocks.append(current_block)
        
        return text_blocks
    
    def _create_text_block_from_words(self, words: List[Dict], block_idx: int,
                                    page_num: int, output_dir: Path) -> Optional[Dict]:
        """Create a text block object from a group of words."""
        if not words:
            return None
        
        try:
            # Calculate bounding box
            x_coords = []
            y_coords = []
            
            for word in words:
                x_coords.extend([word.get('x0', 0), word.get('x1', 0)])
                y_coords.extend([word.get('top', 0), word.get('bottom', 0)])
            
            x1, x2 = min(x_coords), max(x_coords)
            y1, y2 = min(y_coords), max(y_coords)
            
            # Extract text content
            text_content = ' '.join([word.get('text', '') for word in words])
            text_content = text_content.strip()
            
            if len(text_content) < 5:  # Skip very short text
                return None
            
            block_id = f"page_{page_num:03d}_text_{block_idx:03d}"
            
            # Save text content
            text_file = output_dir / 'text' / f"{block_id}.txt"
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            return {
                'block_id': block_id,
                'type': 'text',  # Will be reclassified as title if needed
                'confidence': 0.8,
                'bounding_box': {
                    'x1': float(x1),
                    'y1': float(y1),
                    'x2': float(x2),
                    'y2': float(y2),
                    'width': float(x2 - x1),
                    'height': float(y2 - y1)
                },
                'content': text_content,
                'extraction_method': 'word_grouping',
                'file_saved': str(text_file),
                'word_count': len(words)
            }
        
        except Exception as e:
            self.logger.error(f"Error creating text block: {e}")
            return None
    
    def _is_title_block(self, text_block: Dict) -> bool:
        """Determine if a text block is likely a title."""
        content = text_block.get('content', '')
        bbox = text_block.get('bounding_box', {})
        word_count = text_block.get('word_count', 0)
        
        # Title heuristics
        is_short = word_count <= self.title_max_words
        is_uppercase = content.isupper() or content.istitle()
        has_large_font = bbox.get('height', 0) > 20  # Assuming larger text
        is_centered = bbox.get('x1', 0) > 100  # Rough center check
        
        # Common title patterns
        ends_with_colon = content.strip().endswith(':')
        starts_with_number = content.strip().split()[0].replace('.', '').isdigit()
        
        title_score = sum([
            is_short * 2,
            is_uppercase * 1,
            has_large_font * 1,
            is_centered * 1,
            ends_with_colon * 2,
            starts_with_number * 1
        ])
        
        return title_score >= 3
    
    def _save_title_block(self, title_block: Dict, output_dir: Path):
        """Save title block to the titles directory."""
        try:
            title_file = output_dir / 'titles' / f"{title_block['block_id']}.txt"
            with open(title_file, 'w', encoding='utf-8') as f:
                f.write(title_block['content'])
            title_block['file_saved'] = str(title_file)
        except Exception as e:
            self.logger.error(f"Error saving title block: {e}")
    
    def _estimate_table_bbox(self, pdf_page, table: List[List], table_idx: int) -> Dict[str, float]:
        """Estimate bounding box for a table (simplified approach)."""
        page_width = pdf_page.width
        page_height = pdf_page.height
        
        # Simple estimation - in practice, you'd need more sophisticated methods
        rows = len(table)
        estimated_row_height = 15  # pixels per row
        
        # Place tables vertically based on their index
        y_start = 100 + (table_idx * 200)  # Rough spacing
        y_end = min(y_start + (rows * estimated_row_height), page_height - 50)
        
        return {
            'x1': 50.0,
            'y1': float(y_start),
            'x2': page_width - 50.0,
            'y2': float(y_end),
            'width': page_width - 100.0,
            'height': float(y_end - y_start)
        }
    
    def _create_layout_visualization(self, blocks: List[Dict], page_width: float,
                                   page_height: float, page_num: int, output_dir: Path):
        """Create a simple visualization of detected blocks."""
        try:
            # Create visualization image
            scale = 0.5  # Scale down for reasonable file size
            img_width, img_height = int(page_width * scale), int(page_height * scale)
            img = Image.new('RGB', (img_width, img_height), 'white')
            draw = ImageDraw.Draw(img)
            
            # Color coding for block types
            colors = {
                'text': 'blue',
                'title': 'red',
                'table': 'green'
            }
            
            for block in blocks:
                bbox = block['bounding_box']
                block_type = block['type']
                color = colors.get(block_type, 'black')
                
                # Scale coordinates
                x1 = int(bbox['x1'] * scale)
                y1 = int(bbox['y1'] * scale)
                x2 = int(bbox['x2'] * scale)
                y2 = int(bbox['y2'] * scale)
                
                # Draw bounding box
                draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
                
                # Add type label
                label_y = max(0, y1 - 12)
                draw.text((x1, label_y), block_type.upper(), fill=color)
            
            # Save visualization
            vis_path = output_dir / 'layout_images' / f"page_{page_num:03d}_layout.png"
            img.save(vis_path)
            
            self.logger.debug(f"Layout visualization saved: {vis_path}")
        
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
        results_file = output_dir / 'basic_layout_results.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save bounding boxes for layout reconstruction
        bounding_boxes = []
        for page in results['pages']:
            for block in page['detected_blocks']:
                bbox_data = {
                    'page_number': page['page_number'],
                    'block_id': block['block_id'],
                    'type': block['type'],
                    'confidence': block['confidence'],
                    'bounding_box': block['bounding_box'],
                    'file_path': block.get('file_saved'),
                    'extraction_method': block.get('extraction_method')
                }
                bounding_boxes.append(bbox_data)
        
        bbox_file = output_dir / 'bounding_boxes' / 'all_blocks.json'
        with open(bbox_file, 'w', encoding='utf-8') as f:
            json.dump(bounding_boxes, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Basic layout results saved to {results_file}")
        self.logger.info(f"Bounding boxes saved to {bbox_file}")
    
    def _log_statistics(self):
        """Log comprehensive extraction statistics."""
        self.logger.info("=== Basic Layout Extraction Statistics ===")
        self.logger.info(f"Total pages processed: {self.stats['total_pages']}")
        self.logger.info(f"Total blocks detected: {self.stats['total_blocks']}")
        self.logger.info(f"Blocks by type: {self.stats['blocks_by_type']}")
        self.logger.info(f"Successful extractions: {self.stats['extraction_success']}")
        self.logger.info(f"Failed extractions: {self.stats['extraction_failures']}")
        self.logger.info(f"Processing time: {self.stats['processing_time']:.2f} seconds")


def main():
    """Main function to demonstrate basic layout extraction."""
    # Initialize extractor
    extractor = BasicLayoutExtractor()
    
    # Find PDF files
    pdf_dir = Path("data/raw/pdf")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in data/raw/pdf directory")
        print("Expected structure: data/raw/pdf/*.pdf")
        return
    
    # Process each PDF
    for pdf_file in pdf_files:
        print(f"\nProcessing with Basic Layout Extractor: {pdf_file.name}")
        results = extractor.extract_from_pdf(pdf_file)
        
        if results:
            summary = results['extraction_summary']
            print(f"✓ Basic layout extraction completed for {pdf_file.name}")
            print(f"  Total pages: {summary['total_pages_processed']}")
            print(f"  Total blocks: {summary['total_blocks_detected']}")
            print(f"  Success rate: {summary['success_rate']:.1f}%")
            print(f"  Blocks by type: {summary['blocks_by_type']}")
            print(f"  Processing time: {summary['processing_time_seconds']:.2f}s")
        else:
            print(f"✗ Basic layout extraction failed for {pdf_file.name}")


if __name__ == "__main__":
    main()