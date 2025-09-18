"""
LayoutParser-based Document Layout Analysis and Content Extraction

This module uses LayoutParser to detect different block types (text, titles, tables, figures)
in PDF documents and routes each block to specialized extraction methods.

Features:
- Deep learning-based layout detection using pre-trained models
- Block type classification (text, title, table, figure, list)
- Bounding box persistence for layout reconstruction
- Specialized extractors for each content type
- Comprehensive logging and metrics tracking
"""

import layoutparser as lp
import cv2
import numpy as np
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image, ImageDraw
import pdf2image
import json
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
import io


class LayoutParserExtractor:
    """
    Advanced PDF content extraction using LayoutParser for layout analysis.
    
    This class uses deep learning models to detect document layout elements
    and routes each detected block to appropriate extraction methods.
    """
    
    def __init__(self, output_dir="data/parsed/layout_parser", model_name="lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config"):
        """
        Initialize the LayoutParser-based extractor.
        
        Args:
            output_dir (str): Directory to save extracted content
            model_name (str): LayoutParser model for layout detection
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize LayoutParser model
        self.model_name = model_name
        self.layout_model = None
        self._initialize_model()
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Block type mapping
        self.block_types = {
            0: 'text',
            1: 'title', 
            2: 'list',
            3: 'table',
            4: 'figure'
        }
        
        # Extraction statistics
        self.stats = {
            'total_pages': 0,
            'total_blocks': 0,
            'blocks_by_type': {block_type: 0 for block_type in self.block_types.values()},
            'extraction_success': 0,
            'extraction_failures': 0,
            'processing_time': 0
        }
    
    def _initialize_model(self):
        """Initialize the LayoutParser detection model."""
        try:
            self.layout_model = lp.Detectron2LayoutModel(
                self.model_name,
                extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8],
                label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
            )
            self.logger.info(f"LayoutParser model initialized: {self.model_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize LayoutParser model: {e}")
            self.layout_model = None
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logger = logging.getLogger('LayoutParserExtractor')
        logger.setLevel(logging.INFO)
        
        # Create file handler in layout_parser directory
        log_file = self.output_dir / 'layout_parser_extraction_log.txt'
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
        Extract content from PDF using LayoutParser for layout analysis.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            dict: Comprehensive extraction results
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            self.logger.error(f"PDF file not found: {pdf_path}")
            return None
        
        if self.layout_model is None:
            self.logger.error("LayoutParser model not initialized")
            return None
        
        self.logger.info(f"Starting LayoutParser extraction from: {pdf_path.name}")
        start_time = datetime.now()
        
        # Create output directories for this specific PDF
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
            # Convert PDF to images for LayoutParser processing
            images = pdf2image.convert_from_path(pdf_path, dpi=300)
            extraction_results['total_pages'] = len(images)
            self.stats['total_pages'] = len(images)
            
            # Also open with pdfplumber for text extraction
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, (image, pdf_page) in enumerate(zip(images, pdf.pages), 1):
                    self.logger.info(f"Processing page {page_num}/{len(images)}")
                    
                    page_result = self._process_page(
                        image, pdf_page, page_num, pdf_output_dir
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
        
        self.logger.info(f"LayoutParser extraction completed in {processing_time:.2f} seconds")
        self._log_statistics()
        
        return extraction_results
    
    def _create_output_directories(self, base_dir: Path):
        """Create organized output directory structure."""
        directories = ['text', 'tables', 'figures', 'titles', 'lists', 'layout_images', 'bounding_boxes']
        for dir_name in directories:
            (base_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    def _process_page(self, image: Image.Image, pdf_page, page_num: int, output_dir: Path) -> Dict[str, Any]:
        """
        Process a single page using LayoutParser and extract content by block type.
        
        Args:
            image (PIL.Image): Page image for layout detection
            pdf_page: pdfplumber page object for text extraction
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
                'titles': [],
                'lists': []
            },
            'processing_success': True
        }
        
        try:
            # Convert PIL image to OpenCV format for LayoutParser
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Detect layout elements
            layout = self.layout_model.detect(cv_image)
            
            self.logger.info(f"Page {page_num}: Detected {len(layout)} blocks")
            self.stats['total_blocks'] += len(layout)
            
            # Process each detected block
            for block_idx, block in enumerate(layout):
                block_result = self._process_block(
                    block, block_idx, image, pdf_page, page_num, output_dir
                )
                
                page_result['detected_blocks'].append(block_result)
                
                # Add to appropriate content category
                block_type = block_result['type']
                if block_type in page_result['extracted_content']:
                    page_result['extracted_content'][block_type].append(block_result)
                
                # Update statistics
                if block_type in self.stats['blocks_by_type']:
                    self.stats['blocks_by_type'][block_type] += 1
            
            # Create annotated layout image
            self._save_layout_visualization(cv_image, layout, page_num, output_dir)
        
        except Exception as e:
            self.logger.error(f"Error processing page {page_num}: {e}")
            page_result['processing_success'] = False
            self.stats['extraction_failures'] += 1
        
        return page_result
    
    def _process_block(self, block, block_idx: int, image: Image.Image, 
                      pdf_page, page_num: int, output_dir: Path) -> Dict[str, Any]:
        """
        Process a detected layout block and extract content based on its type.
        
        Args:
            block: LayoutParser block object
            block_idx (int): Block index within the page
            image (PIL.Image): Full page image
            pdf_page: pdfplumber page object
            page_num (int): Page number
            output_dir (Path): Output directory
            
        Returns:
            dict: Block processing results
        """
        # Get block properties
        block_type = self.block_types.get(block.type, 'unknown')
        bbox = block.block
        
        block_result = {
            'block_id': f"page_{page_num:03d}_block_{block_idx:03d}",
            'type': block_type,
            'confidence': float(block.score),
            'bounding_box': {
                'x1': float(bbox.x_1),
                'y1': float(bbox.y_1),
                'x2': float(bbox.x_2),
                'y2': float(bbox.y_2),
                'width': float(bbox.width),
                'height': float(bbox.height)
            },
            'content': None,
            'extraction_method': None,
            'file_saved': None
        }
        
        try:
            # Route block to appropriate extraction method
            if block_type == 'text':
                content, method, file_path = self._extract_text_block(
                    bbox, pdf_page, image, block_result['block_id'], output_dir
                )
            elif block_type == 'title':
                content, method, file_path = self._extract_title_block(
                    bbox, pdf_page, image, block_result['block_id'], output_dir
                )
            elif block_type == 'table':
                content, method, file_path = self._extract_table_block(
                    bbox, pdf_page, image, block_result['block_id'], output_dir
                )
            elif block_type == 'figure':
                content, method, file_path = self._extract_figure_block(
                    bbox, image, block_result['block_id'], output_dir
                )
            elif block_type == 'list':
                content, method, file_path = self._extract_list_block(
                    bbox, pdf_page, image, block_result['block_id'], output_dir
                )
            else:
                content, method, file_path = None, 'unknown_type', None
            
            block_result['content'] = content
            block_result['extraction_method'] = method
            block_result['file_saved'] = str(file_path) if file_path else None
            
            if content:
                self.stats['extraction_success'] += 1
            else:
                self.stats['extraction_failures'] += 1
        
        except Exception as e:
            self.logger.error(f"Error processing block {block_result['block_id']}: {e}")
            self.stats['extraction_failures'] += 1
        
        return block_result
    
    def _extract_text_block(self, bbox, pdf_page, image: Image.Image, 
                           block_id: str, output_dir: Path) -> Tuple[str, str, Optional[Path]]:
        """Extract text content from a detected text block."""
        try:
            # Try pdfplumber first (more accurate for text)
            x1, y1, x2, y2 = bbox.x_1, bbox.y_1, bbox.x_2, bbox.y_2
            
            # Extract text from PDF page within bounding box
            cropped_page = pdf_page.within_bbox((x1, y1, x2, y2))
            text = cropped_page.extract_text()
            
            if text and len(text.strip()) > 5:
                method = 'pdfplumber'
            else:
                # Fallback to OCR on image crop
                crop = image.crop((x1, y1, x2, y2))
                text = pytesseract.image_to_string(crop, config='--psm 6 -l eng')
                method = 'ocr'
            
            # Save text to file
            if text and text.strip():
                file_path = output_dir / 'text' / f"{block_id}.txt"
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text.strip())
                return text.strip(), method, file_path
            
            return None, method, None
        
        except Exception as e:
            self.logger.error(f"Error extracting text block {block_id}: {e}")
            return None, 'error', None
    
    def _extract_title_block(self, bbox, pdf_page, image: Image.Image,
                           block_id: str, output_dir: Path) -> Tuple[str, str, Optional[Path]]:
        """Extract title content from a detected title block."""
        # Similar to text extraction but saved in titles directory
        text, method, _ = self._extract_text_block(bbox, pdf_page, image, block_id, output_dir)
        
        if text:
            file_path = output_dir / 'titles' / f"{block_id}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return text, method, file_path
        
        return None, method, None
    
    def _extract_table_block(self, bbox, pdf_page, image: Image.Image,
                           block_id: str, output_dir: Path) -> Tuple[Optional[pd.DataFrame], str, Optional[Path]]:
        """Extract table content from a detected table block."""
        try:
            x1, y1, x2, y2 = bbox.x_1, bbox.y_1, bbox.x_2, bbox.y_2
            
            # Try pdfplumber table extraction within bounding box
            cropped_page = pdf_page.within_bbox((x1, y1, x2, y2))
            tables = cropped_page.extract_tables()
            
            if tables and len(tables) > 0:
                # Convert first table to DataFrame
                table_data = tables[0]
                df = pd.DataFrame(table_data[1:], columns=table_data[0])
                method = 'pdfplumber'
            else:
                # Fallback: OCR on table image crop
                crop = image.crop((x1, y1, x2, y2))
                # This is a simplified approach - you might want to use specialized table OCR
                text = pytesseract.image_to_string(crop, config='--psm 6 -l eng')
                # Convert text to simple DataFrame (basic parsing)
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                if len(lines) > 1:
                    df = pd.DataFrame([line.split() for line in lines[1:]], 
                                    columns=lines[0].split())
                    method = 'ocr'
                else:
                    return None, 'ocr_failed', None
            
            # Save table to CSV
            if not df.empty:
                file_path = output_dir / 'tables' / f"{block_id}.csv"
                df.to_csv(file_path, index=False, encoding='utf-8')
                return df, method, file_path
            
            return None, method, None
        
        except Exception as e:
            self.logger.error(f"Error extracting table block {block_id}: {e}")
            return None, 'error', None
    
    def _extract_figure_block(self, bbox, image: Image.Image,
                            block_id: str, output_dir: Path) -> Tuple[Optional[Image.Image], str, Optional[Path]]:
        """Extract figure content from a detected figure block."""
        try:
            x1, y1, x2, y2 = bbox.x_1, bbox.y_1, bbox.x_2, bbox.y_2
            
            # Crop figure from image
            figure_crop = image.crop((x1, y1, x2, y2))
            
            # Save figure
            file_path = output_dir / 'figures' / f"{block_id}.png"
            figure_crop.save(file_path, 'PNG')
            
            return figure_crop, 'image_crop', file_path
        
        except Exception as e:
            self.logger.error(f"Error extracting figure block {block_id}: {e}")
            return None, 'error', None
    
    def _extract_list_block(self, bbox, pdf_page, image: Image.Image,
                          block_id: str, output_dir: Path) -> Tuple[str, str, Optional[Path]]:
        """Extract list content from a detected list block."""
        # Similar to text extraction but saved in lists directory
        text, method, _ = self._extract_text_block(bbox, pdf_page, image, block_id, output_dir)
        
        if text:
            file_path = output_dir / 'lists' / f"{block_id}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return text, method, file_path
        
        return None, method, None
    
    def _save_layout_visualization(self, image: np.ndarray, layout, page_num: int, output_dir: Path):
        """Save annotated layout visualization."""
        try:
            # Create visualization with bounding boxes
            vis_image = lp.draw_box(image, layout, box_width=3)
            
            # Save visualization
            vis_path = output_dir / 'layout_images' / f"page_{page_num:03d}_layout.png"
            cv2.imwrite(str(vis_path), vis_image)
            
        except Exception as e:
            self.logger.error(f"Error saving layout visualization for page {page_num}: {e}")
    
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
        results_file = output_dir / 'layout_parser_extraction_results.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save bounding boxes separately for layout reconstruction
        bounding_boxes = []
        for page in results['pages']:
            for block in page['detected_blocks']:
                bbox_data = {
                    'page_number': page['page_number'],
                    'block_id': block['block_id'],
                    'type': block['type'],
                    'confidence': block['confidence'],
                    'bounding_box': block['bounding_box'],
                    'file_path': block['file_saved']
                }
                bounding_boxes.append(bbox_data)
        
        bbox_file = output_dir / 'bounding_boxes' / 'layout_parser_blocks.json'
        with open(bbox_file, 'w', encoding='utf-8') as f:
            json.dump(bounding_boxes, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"LayoutParser extraction results saved to {results_file}")
        self.logger.info(f"LayoutParser bounding boxes saved to {bbox_file}")
    
    def _log_statistics(self):
        """Log comprehensive extraction statistics."""
        self.logger.info("=== LayoutParser Extraction Statistics ===")
        self.logger.info(f"Total pages processed: {self.stats['total_pages']}")
        self.logger.info(f"Total blocks detected: {self.stats['total_blocks']}")
        self.logger.info(f"Blocks by type: {self.stats['blocks_by_type']}")
        self.logger.info(f"Successful extractions: {self.stats['extraction_success']}")
        self.logger.info(f"Failed extractions: {self.stats['extraction_failures']}")
        self.logger.info(f"Processing time: {self.stats['processing_time']:.2f} seconds")


def main():
    """Main function to demonstrate LayoutParser-based extraction."""
    print("=== LayoutParser Document Extraction ===")
    print("Output structure: data/parsed/layout_parser/[pdf_name]/")
    print("  ├── text/          - Text blocks")
    print("  ├── tables/        - Tables as CSV files") 
    print("  ├── figures/       - Extracted figures")
    print("  ├── titles/        - Title blocks")
    print("  ├── lists/         - List blocks")
    print("  ├── layout_images/ - Layout visualizations")
    print("  └── bounding_boxes/- Block coordinates")
    print()
    
    # Initialize extractor (will create data/parsed/layout_parser/)
    extractor = LayoutParserExtractor()
    
    # Find PDF files
    pdf_dir = Path("data/raw/pdf")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in data/raw/pdf directory")
        print("Expected structure: data/raw/pdf/*.pdf")
        return
    
    # Process each PDF
    for pdf_file in pdf_files:
        print(f"\nProcessing with LayoutParser: {pdf_file.name}")
        results = extractor.extract_from_pdf(pdf_file)
        
        if results:
            summary = results['extraction_summary']
            print(f"✓ LayoutParser extraction completed for {pdf_file.name}")
            print(f"  Total pages: {summary['total_pages_processed']}")
            print(f"  Total blocks: {summary['total_blocks_detected']}")
            print(f"  Success rate: {summary['success_rate']:.1f}%")
            print(f"  Blocks by type: {summary['blocks_by_type']}")
        else:
            print(f"✗ LayoutParser extraction failed for {pdf_file.name}")


if __name__ == "__main__":
    main()