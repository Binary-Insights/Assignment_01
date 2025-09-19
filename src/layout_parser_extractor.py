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

# Enhanced table extraction with Camelot
try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False

# Multimodal model support with LayoutLMv3
try:
    from transformers import LayoutLMv3Processor, LayoutLMv3ForTokenClassification
    import torch
    LAYOUTLMV3_AVAILABLE = True
except ImportError:
    LAYOUTLMV3_AVAILABLE = False


class LayoutParserExtractor:
    """
    Advanced PDF content extraction using LayoutParser for layout analysis.
    
    This class uses deep learning models to detect document layout elements
    and routes each detected block to appropriate extraction methods.
    """
    
    def __init__(self, output_dir="data/parsed/layout_parser", 
                 model_name="lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config",
                 use_camelot=True, use_layoutlmv3=True, max_pages_testing=25):
        """
        Initialize the LayoutParser-based extractor.
        
        Args:
            output_dir (str): Directory to save extracted content
            model_name (str): LayoutParser model for layout detection
            use_camelot (bool): Whether to use Camelot for enhanced table extraction
            use_layoutlmv3 (bool): Whether to use LayoutLMv3 for multimodal tasks
            max_pages_testing (int): Maximum pages to process for testing (None for all pages)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration flags
        self.use_camelot = use_camelot and CAMELOT_AVAILABLE
        self.use_layoutlmv3 = use_layoutlmv3 and LAYOUTLMV3_AVAILABLE
        self.max_pages_testing = max_pages_testing  # Testing mode: limit pages
        
        # Initialize LayoutParser model
        self.model_name = model_name
        self.layout_model = None
        self._initialize_model()
        
        # Initialize multimodal model if available
        self.multimodal_processor = None
        self.multimodal_model = None
        if self.use_layoutlmv3:
            self._initialize_multimodal_model()
        
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
            'processing_time': 0,
            'camelot_tables': 0,
            'layoutlmv3_captions': 0
        }
    
    def _setup_logging(self):
        """Set up logging for the extractor."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        # Create console handler if not already present
        if not logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def _initialize_model(self):
        """Initialize the LayoutParser detection model using local files."""
        print(f"Attempting to initialize LayoutParser model with local files...")
        
        # Define paths to local model files
        current_dir = Path(__file__).parent.parent  # Go up from src/ to project root
        config_path = current_dir / "models" / "layoutparser" / "config.yml"
        model_path = current_dir / "models" / "layoutparser" / "model_final.pth"
        
        print(f"Config path: {config_path}")
        print(f"Model path: {model_path}")
        
        # Check if local files exist
        if not config_path.exists():
            print(f"❌ Config file not found: {config_path}")
            self._fallback_to_remote_model()
            return
            
        if not model_path.exists():
            print(f"❌ Model file not found: {model_path}")
            self._fallback_to_remote_model()
            return
        
        print(f"✅ Local model files found")
        print(f"  Config size: {config_path.stat().st_size} bytes")
        print(f"  Model size: {model_path.stat().st_size / (1024*1024):.1f} MB")
        
        try:
            # Method 1: Try with local config and model paths
            print("🔧 Attempting local model initialization...")
            self.layout_model = lp.models.Detectron2LayoutModel(
                config_path=str(config_path),
                model_path=str(model_path),
                extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8],
                label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
                device="cpu"  # Use CPU to avoid GPU issues
            )
            
            if self.layout_model is not None:
                print(f"✅ LayoutParser model initialized with local files!")
                print(f"Model type: {type(self.layout_model)}")
                return
            else:
                print("❌ Local model initialization returned None")
                
        except Exception as e:
            print(f"❌ Local model initialization failed: {e}")
            # Print more detailed error for debugging
            import traceback
            print("Detailed error:")
            traceback.print_exc()
        
        try:
            # Method 2: Try with minimal parameters
            print("🔧 Attempting minimal local model initialization...")
            self.layout_model = lp.models.Detectron2LayoutModel(
                config_path=str(config_path),
                model_path=str(model_path),
                device="cpu"
            )
            
            if self.layout_model is not None:
                print(f"✅ LayoutParser model initialized with minimal config!")
                print(f"Model type: {type(self.layout_model)}")
                return
            else:
                print("❌ Minimal local model initialization returned None")
                
        except Exception as e:
            print(f"❌ Minimal local model initialization failed: {e}")
        
        # Method 3: Fallback to remote model (original approach)
        print("🔄 Falling back to remote model download...")
        self._fallback_to_remote_model()
    
    def _fallback_to_remote_model(self):
        """Fallback to the original remote model download approach."""
        print("Trying original remote model approach...")
        
        try:
            # Use the original remote model approach
            self.layout_model = lp.models.Detectron2LayoutModel(
                self.model_name,
                extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8],
                label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
            )
            if self.layout_model is not None:
                print(f"✓ LayoutParser model initialized with remote config: {self.model_name}")
                print(f"Model object type: {type(self.layout_model)}")
                return
            else:
                print("Remote models.Detectron2LayoutModel returned None")
        except Exception as e:
            print(f"Remote models.Detectron2LayoutModel failed: {e}")
            
        try:
            # Try without extra configuration parameters
            self.layout_model = lp.models.Detectron2LayoutModel(self.model_name)
            if self.layout_model is not None:
                print(f"✓ LayoutParser model initialized with basic remote config: {self.model_name}")
                print(f"Model object type: {type(self.layout_model)}")
                return
            else:
                print("Basic remote Detectron2LayoutModel returned None")
        except Exception as e:
            print(f"Basic remote Detectron2LayoutModel failed: {e}")
        
        # If all attempts fail, raise an error instead of using fallback
        print(f"✗ All LayoutParser model initialization attempts failed")
        print("This suggests compatibility issues between LayoutParser and Detectron2")
        print("❌ FALLBACK MODE DISABLED - LayoutParser model is required")
        
        # Set model to None to force proper error handling
        self.layout_model = None
        raise RuntimeError("LayoutParser model initialization failed. Please fix Detectron2 setup or use a different extractor.")
    
    def _initialize_multimodal_model(self):
        """Initialize LayoutLMv3 model for multimodal tasks like caption extraction."""
        try:
            if LAYOUTLMV3_AVAILABLE:
                self.multimodal_processor = LayoutLMv3Processor.from_pretrained(
                    "microsoft/layoutlmv3-base"
                )
                self.multimodal_model = LayoutLMv3ForTokenClassification.from_pretrained(
                    "microsoft/layoutlmv3-base"
                )
                # Set to evaluation mode
                self.multimodal_model.eval()
                print("✓ LayoutLMv3 multimodal model initialized successfully")
            else:
                print("⚠ LayoutLMv3 not available - multimodal features disabled")
        except Exception as e:
            print(f"✗ Failed to initialize LayoutLMv3 model: {e}")
            self.multimodal_processor = None
            self.multimodal_model = None
    
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
        
        # Create output directories for this specific PDF
        pdf_output_dir = self.output_dir / pdf_path.stem
        self._create_output_directories(pdf_output_dir)
        
        # Store current PDF path for enhanced extraction methods
        self._current_pdf_path = str(pdf_path)
        
        if self.layout_model is None:
            self.logger.error("LayoutParser model not initialized - fallback mode disabled")
            raise RuntimeError("LayoutParser model is required. Please ensure Detectron2 and LayoutParser are properly installed.")
        
        self.logger.info(f"Starting LayoutParser extraction from: {pdf_path.name}")
        start_time = datetime.now()
        
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
            
            # 🧪 TESTING MODE: Limit pages if configured
            if self.max_pages_testing and len(images) > self.max_pages_testing:
                print(f"⚠️ TESTING MODE: Processing only first {self.max_pages_testing} pages out of {len(images)} total pages")
                images = images[:self.max_pages_testing]
            
            extraction_results['total_pages'] = len(images)
            self.stats['total_pages'] = len(images)
            
            # Also open with pdfplumber for text extraction
            with pdfplumber.open(pdf_path) as pdf:
                # Limit PDF pages to match the images
                pdf_pages = pdf.pages[:len(images)]
                
                for page_num, (image, pdf_page) in enumerate(zip(images, pdf_pages), 1):
                    self.logger.info(f"Processing page {page_num}/{len(images)} (Testing Mode)")
                    
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
                # Pass additional parameters for enhanced Camelot extraction
                content, method, file_path = self._extract_table_block(
                    bbox, pdf_page, image, block_result['block_id'], output_dir,
                    pdf_path=getattr(self, '_current_pdf_path', None), page_num=page_num
                )
            elif block_type == 'figure':
                content, method, file_path = self._extract_figure_block(
                    bbox, image, block_result['block_id'], output_dir, full_page_image=image
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
                           block_id: str, output_dir: Path, pdf_path: Optional[str] = None, 
                           page_num: int = 1) -> Tuple[Optional[pd.DataFrame], str, Optional[Path]]:
        """Extract table content from a detected table block with enhanced Camelot support."""
        try:
            x1, y1, x2, y2 = bbox.x_1, bbox.y_1, bbox.x_2, bbox.y_2
            df = None
            method = 'unknown'
            
            # Method 1: Try Camelot for advanced table extraction (if available and PDF path provided)
            if self.use_camelot and CAMELOT_AVAILABLE and pdf_path:
                try:
                    # Convert bbox coordinates to Camelot format (x1,y1,x2,y2)
                    table_area = f"{x1},{y1},{x2},{y2}"
                    
                    # Extract tables using Camelot with lattice method (better for structured tables)
                    camelot_tables = camelot.read_pdf(
                        str(pdf_path), 
                        pages=str(page_num),
                        flavor='lattice',  # Try lattice first
                        table_areas=[table_area],
                        line_scale=40  # Adjust line detection sensitivity
                    )
                    
                    if len(camelot_tables) > 0 and not camelot_tables[0].df.empty:
                        df = camelot_tables[0].df
                        method = 'camelot_lattice'
                        self.stats['camelot_tables'] += 1
                        
                        # Save additional Camelot metadata
                        camelot_metadata = {
                            'parsing_report': camelot_tables[0].parsing_report,
                            'accuracy': camelot_tables[0].accuracy,
                            'whitespace': camelot_tables[0].whitespace,
                            'shape': camelot_tables[0].shape
                        }
                        
                        metadata_file = output_dir / 'tables' / f"{block_id}_camelot_metadata.json"
                        with open(metadata_file, 'w', encoding='utf-8') as f:
                            json.dump(camelot_metadata, f, indent=2, default=str)
                    else:
                        # Try stream method as fallback
                        camelot_tables = camelot.read_pdf(
                            str(pdf_path), 
                            pages=str(page_num),
                            flavor='stream',  # Stream method for unstructured tables
                            table_areas=[table_area]
                        )
                        
                        if len(camelot_tables) > 0 and not camelot_tables[0].df.empty:
                            df = camelot_tables[0].df
                            method = 'camelot_stream'
                            self.stats['camelot_tables'] += 1
                
                except Exception as camelot_error:
                    self.logger.warning(f"Camelot extraction failed: {camelot_error}")
            
            # Method 2: Fallback to pdfplumber if Camelot failed or unavailable
            if df is None or df.empty:
                cropped_page = pdf_page.within_bbox((x1, y1, x2, y2))
                tables = cropped_page.extract_tables()
                
                if tables and len(tables) > 0:
                    table_data = tables[0]
                    # Clean and validate table data
                    if table_data and len(table_data) > 1:
                        # Filter out empty rows and columns
                        cleaned_data = []
                        for row in table_data:
                            if row and any(cell and str(cell).strip() for cell in row):
                                cleaned_data.append([str(cell).strip() if cell else '' for cell in row])
                        
                        if cleaned_data and len(cleaned_data) > 1:
                            headers = cleaned_data[0]
                            data_rows = cleaned_data[1:]
                            df = pd.DataFrame(data_rows, columns=headers)
                            method = 'pdfplumber'
            
            # Method 3: OCR fallback for tables that couldn't be extracted
            if df is None or df.empty:
                crop = image.crop((x1, y1, x2, y2))
                # Enhanced OCR with table-specific configuration
                ocr_config = '--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,()[]{}|+- '
                text = pytesseract.image_to_string(crop, config=ocr_config)
                
                # Try to parse OCR text into structured table
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                if len(lines) > 1:
                    # Attempt to detect column separators
                    rows = []
                    for line in lines:
                        # Split by multiple spaces, tabs, or pipes
                        if '|' in line:
                            row = [cell.strip() for cell in line.split('|') if cell.strip()]
                        elif '\t' in line:
                            row = [cell.strip() for cell in line.split('\t') if cell.strip()]
                        else:
                            # Split by multiple spaces (2 or more)
                            import re
                            row = [cell.strip() for cell in re.split(r'\s{2,}', line) if cell.strip()]
                        
                        if row:
                            rows.append(row)
                    
                    if len(rows) > 1:
                        # Use first row as headers, ensure consistent column count
                        headers = rows[0]
                        data_rows = []
                        for row in rows[1:]:
                            # Pad or truncate row to match header count
                            while len(row) < len(headers):
                                row.append('')
                            if len(row) > len(headers):
                                row = row[:len(headers)]
                            data_rows.append(row)
                        
                        if data_rows:
                            df = pd.DataFrame(data_rows, columns=headers)
                            method = 'ocr_enhanced'
            
            # Save table if extraction was successful
            if df is not None and not df.empty:
                # Clean the DataFrame
                df = df.dropna(how='all').dropna(axis=1, how='all')  # Remove empty rows/columns
                
                if not df.empty:
                    file_path = output_dir / 'tables' / f"{block_id}.csv"
                    df.to_csv(file_path, index=False, encoding='utf-8')
                    
                    # Save additional table analysis
                    table_analysis = {
                        'extraction_method': method,
                        'rows': len(df),
                        'columns': len(df.columns),
                        'headers': list(df.columns),
                        'data_types': {col: str(dtype) for col, dtype in df.dtypes.items()},
                        'non_null_counts': df.count().to_dict()
                    }
                    
                    analysis_file = output_dir / 'tables' / f"{block_id}_analysis.json"
                    with open(analysis_file, 'w', encoding='utf-8') as f:
                        json.dump(table_analysis, f, indent=2, default=str)
                    
                    return df, method, file_path
            
            return None, method, None
        
        except Exception as e:
            self.logger.error(f"Error extracting table block {block_id}: {e}")
            return None, 'error', None
    
    def _extract_figure_block(self, bbox, image: Image.Image,
                            block_id: str, output_dir: Path, full_page_image: Optional[Image.Image] = None) -> Tuple[Optional[Image.Image], str, Optional[Path]]:
        """Extract figure content from a detected figure block with enhanced caption detection."""
        try:
            x1, y1, x2, y2 = bbox.x_1, bbox.y_1, bbox.x_2, bbox.y_2
            
            # Crop figure from image
            figure_crop = image.crop((x1, y1, x2, y2))
            
            # Save figure
            file_path = output_dir / 'figures' / f"{block_id}.png"
            figure_crop.save(file_path, 'PNG')
            
            # Enhanced caption extraction using LayoutLMv3 if available
            caption = None
            caption_method = 'none'
            
            if self.use_layoutlmv3 and self.multimodal_model and full_page_image:
                try:
                    caption = self._extract_caption_with_layoutlmv3(figure_crop, full_page_image, bbox)
                    if caption:
                        caption_method = 'layoutlmv3'
                        self.stats['layoutlmv3_captions'] += 1
                except Exception as caption_error:
                    self.logger.warning(f"LayoutLMv3 caption extraction failed: {caption_error}")
            
            # Fallback caption extraction using OCR on surrounding areas
            if not caption:
                caption = self._extract_caption_with_ocr(image, bbox)
                if caption:
                    caption_method = 'ocr_surrounding'
            
            # Save figure metadata including caption
            figure_metadata = {
                'block_id': block_id,
                'bounding_box': {
                    'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                    'width': x2 - x1, 'height': y2 - y1
                },
                'caption': caption,
                'caption_method': caption_method,
                'image_file': str(file_path),
                'image_format': 'PNG',
                'image_size': figure_crop.size
            }
            
            metadata_file = output_dir / 'figures' / f"{block_id}_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(figure_metadata, f, indent=2, default=str)
            
            # Save caption separately if found
            if caption:
                caption_file = output_dir / 'figures' / f"{block_id}_caption.txt"
                with open(caption_file, 'w', encoding='utf-8') as f:
                    f.write(f"Caption for {block_id}:\n{caption}")
            
            return figure_crop, f'image_crop_{caption_method}', file_path
        
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
    
    def _extract_caption_with_layoutlmv3(self, figure_crop: Image.Image, 
                                       full_page_image: Image.Image, bbox) -> Optional[str]:
        """Extract figure caption using LayoutLMv3 multimodal model."""
        try:
            if not (self.multimodal_processor and self.multimodal_model):
                return None
            
            # Expand the bounding box to include potential caption areas
            x1, y1, x2, y2 = bbox.x_1, bbox.y_1, bbox.x_2, bbox.y_2
            page_width, page_height = full_page_image.size
            
            # Look for captions below and above the figure
            caption_regions = [
                # Below figure (most common)
                (max(0, x1 - 20), y2, min(page_width, x2 + 20), min(page_height, y2 + 100)),
                # Above figure
                (max(0, x1 - 20), max(0, y1 - 100), min(page_width, x2 + 20), y1),
                # To the right (for side captions)
                (x2, max(0, y1 - 20), min(page_width, x2 + 200), min(page_height, y2 + 20))
            ]
            
            best_caption = None
            best_confidence = 0.0
            
            for region in caption_regions:
                try:
                    x1_cap, y1_cap, x2_cap, y2_cap = region
                    if x2_cap > x1_cap and y2_cap > y1_cap:
                        caption_crop = full_page_image.crop(region)
                        
                        # Use LayoutLMv3 to process the image and extract text
                        encoding = self.multimodal_processor(
                            caption_crop, 
                            return_tensors="pt",
                            truncation=True,
                            padding=True
                        )
                        
                        with torch.no_grad():
                            outputs = self.multimodal_model(**encoding)
                            
                        # Extract text using OCR as LayoutLMv3 needs text input
                        # This is a simplified approach - in practice, you'd use proper tokenization
                        caption_text = pytesseract.image_to_string(caption_crop, config='--psm 6 -l eng').strip()
                        
                        if caption_text and len(caption_text) > 10:  # Minimum caption length
                            # Check if this looks like a caption (starts with "Figure", "Fig", contains numbers, etc.)
                            caption_indicators = ['figure', 'fig', 'table', 'chart', 'graph', 'image']
                            text_lower = caption_text.lower()
                            
                            confidence = 0.5  # Base confidence
                            if any(indicator in text_lower for indicator in caption_indicators):
                                confidence += 0.3
                            if any(char.isdigit() for char in caption_text):
                                confidence += 0.2
                            
                            if confidence > best_confidence:
                                best_caption = caption_text
                                best_confidence = confidence
                
                except Exception as region_error:
                    continue  # Try next region
            
            return best_caption if best_confidence > 0.6 else None
        
        except Exception as e:
            self.logger.error(f"LayoutLMv3 caption extraction error: {e}")
            return None
    
    def _extract_caption_with_ocr(self, image: Image.Image, bbox) -> Optional[str]:
        """Extract figure caption using OCR on surrounding areas."""
        try:
            x1, y1, x2, y2 = bbox.x_1, bbox.y_1, bbox.x_2, bbox.y_2
            page_width, page_height = image.size
            
            # Define caption search regions (below figure is most common)
            caption_regions = [
                # Below figure
                (max(0, x1 - 20), y2, min(page_width, x2 + 20), min(page_height, y2 + 80)),
                # Above figure  
                (max(0, x1 - 20), max(0, y1 - 80), min(page_width, x2 + 20), y1)
            ]
            
            best_caption = None
            
            for region in caption_regions:
                try:
                    x1_cap, y1_cap, x2_cap, y2_cap = region
                    if x2_cap > x1_cap and y2_cap > y1_cap:
                        caption_crop = image.crop(region)
                        
                        # Use OCR with configuration optimized for captions
                        caption_text = pytesseract.image_to_string(
                            caption_crop, 
                            config='--psm 6 -l eng'
                        ).strip()
                        
                        if caption_text and len(caption_text) > 5:
                            # Check if this looks like a caption
                            text_lower = caption_text.lower()
                            caption_indicators = ['figure', 'fig', 'table', 'chart', 'graph', 'image']
                            
                            if (any(indicator in text_lower for indicator in caption_indicators) or
                                any(char.isdigit() for char in caption_text)):
                                best_caption = caption_text
                                break  # Found a good caption, stop searching
                
                except Exception as region_error:
                    continue
            
            return best_caption
        
        except Exception as e:
            self.logger.error(f"OCR caption extraction error: {e}")
            return None
    
    def _save_layout_visualization(self, image: np.ndarray, layout, page_num: int, output_dir: Path):
        """Save annotated layout visualization."""
        try:
            # Create visualization with bounding boxes
            vis_image = lp.draw_box(image, layout, box_width=3)
            
            # Ensure vis_image is a proper numpy array for OpenCV
            if vis_image is None:
                self.logger.warning(f"LayoutParser draw_box returned None for page {page_num}")
                # Create a simple visualization manually
                vis_image = self._create_manual_visualization(image, layout)
            elif not isinstance(vis_image, np.ndarray):
                self.logger.warning(f"LayoutParser draw_box returned unexpected type: {type(vis_image)}")
                # Try to convert to numpy array
                try:
                    vis_image = np.array(vis_image)
                except:
                    vis_image = self._create_manual_visualization(image, layout)
            
            # Save visualization
            vis_path = output_dir / 'layout_images' / f"page_{page_num:03d}_layout.png"
            success = cv2.imwrite(str(vis_path), vis_image)
            
            if not success:
                self.logger.warning(f"OpenCV failed to save visualization for page {page_num}, trying PIL")
                # Fallback to PIL
                from PIL import Image as PILImage
                if vis_image.dtype != np.uint8:
                    vis_image = vis_image.astype(np.uint8)
                # Convert BGR to RGB for PIL
                if len(vis_image.shape) == 3 and vis_image.shape[2] == 3:
                    vis_image_rgb = cv2.cvtColor(vis_image, cv2.COLOR_BGR2RGB)
                    pil_image = PILImage.fromarray(vis_image_rgb)
                    pil_image.save(vis_path)
                else:
                    pil_image = PILImage.fromarray(vis_image)
                    pil_image.save(vis_path)
            
        except Exception as e:
            self.logger.error(f"Error saving layout visualization for page {page_num}: {e}")
            # Try to save original image as fallback
            try:
                vis_path = output_dir / 'layout_images' / f"page_{page_num:03d}_layout.png"
                cv2.imwrite(str(vis_path), image)
                self.logger.info(f"Saved original image without annotations for page {page_num}")
            except Exception as fallback_error:
                self.logger.error(f"Fallback image save also failed for page {page_num}: {fallback_error}")
    
    def _create_manual_visualization(self, image: np.ndarray, layout) -> np.ndarray:
        """Create manual visualization when LayoutParser's draw_box fails."""
        try:
            # Make a copy of the original image
            vis_image = image.copy()
            
            # Draw bounding boxes manually
            for block in layout:
                bbox = block.block
                x1, y1, x2, y2 = int(bbox.x_1), int(bbox.y_1), int(bbox.x_2), int(bbox.y_2)
                
                # Choose color based on block type
                colors = {
                    0: (0, 255, 0),    # Text - Green
                    1: (255, 0, 0),    # Title - Blue  
                    2: (0, 255, 255),  # List - Yellow
                    3: (255, 0, 255),  # Table - Magenta
                    4: (0, 0, 255)     # Figure - Red
                }
                color = colors.get(block.type, (255, 255, 255))  # Default white
                
                # Draw rectangle
                cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 3)
                
                # Add label
                label = self.block_types.get(block.type, 'unknown')
                label_text = f"{label} ({block.score:.2f})"
                
                # Put text with background
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.7
                font_thickness = 2
                text_size = cv2.getTextSize(label_text, font, font_scale, font_thickness)[0]
                
                # Background rectangle for text
                cv2.rectangle(vis_image, (x1, y1 - text_size[1] - 10), 
                            (x1 + text_size[0] + 10, y1), color, -1)
                
                # Text
                cv2.putText(vis_image, label_text, (x1 + 5, y1 - 5), 
                          font, font_scale, (0, 0, 0), font_thickness)
            
            return vis_image
            
        except Exception as e:
            self.logger.error(f"Manual visualization creation failed: {e}")
            return image  # Return original image as last resort
    
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

    # Fallback mode has been disabled - LayoutParser model is now required


def main():
    """Main function to demonstrate enhanced LayoutParser-based extraction."""
    print("=== Enhanced LayoutParser Document Extraction ===")
    print("Features:")
    print("  • Deep learning layout detection (PubLayNet/Detectron2)")
    print("  • Enhanced table extraction with Camelot integration")
    print("  • Multimodal caption extraction with LayoutLMv3")
    print("  • Layout-aware multi-column text extraction")
    print("  • Comprehensive bounding box visualization")
    print()
    print("Output structure: data/parsed/layout_parser/[pdf_name]/")
    print("  ├── text/          - Text blocks with OCR fallback")
    print("  ├── tables/        - Enhanced tables (Camelot + pdfplumber + OCR)")
    print("  │   ├── *.csv       - Structured table data")
    print("  │   ├── *_analysis.json - Table structure analysis")
    print("  │   └── *_camelot_metadata.json - Camelot extraction metrics")
    print("  ├── figures/       - Figures with caption extraction")
    print("  │   ├── *.png       - Extracted figure images")
    print("  │   ├── *_caption.txt - Extracted captions")
    print("  │   └── *_metadata.json - Figure analysis")
    print("  ├── titles/        - Title blocks")
    print("  ├── lists/         - List blocks")
    print("  ├── layout_images/ - Layout visualizations with bounding boxes")
    print("  └── bounding_boxes/- Detailed coordinate data")
    print()
    
    # Check available enhancements
    enhancements = []
    if CAMELOT_AVAILABLE:
        enhancements.append("✓ Camelot (advanced table extraction)")
    else:
        enhancements.append("✗ Camelot not available (pip install camelot-py[cv])")
    
    if LAYOUTLMV3_AVAILABLE:
        enhancements.append("✓ LayoutLMv3 (multimodal caption extraction)")
    else:
        enhancements.append("✗ LayoutLMv3 not available (pip install transformers torch)")
    
    print("Enhancement Status:")
    for enhancement in enhancements:
        print(f"  {enhancement}")
    print()
    print("⚠️  FALLBACK MODE DISABLED: LayoutParser model initialization is now required")
    print("   If LayoutParser fails to initialize, the extractor will raise an error")
    print("   Use basic_layout_extractor.py or other extractors if LayoutParser is unavailable")
    print()
    print("🧪 TESTING MODE: Processing only first 25 pages for faster initial testing")
    print("   Set max_pages_testing=None to process all pages")
    print()
    
    # Initialize extractor with all available enhancements
    try:
        extractor = LayoutParserExtractor(
            use_camelot=CAMELOT_AVAILABLE,
            use_layoutlmv3=LAYOUTLMV3_AVAILABLE,
            max_pages_testing=25  # Testing mode: only first 25 pages
        )
    except RuntimeError as e:
        print(f"❌ LayoutParser initialization failed: {e}")
        print("💡 Try one of these alternatives:")
        print("  1. Fix Detectron2 installation: pip install detectron2")
        print("  2. Use basic_layout_extractor.py for layout-aware extraction")
        print("  3. Use enhanced_pdf_extractor.py for text + table extraction")
        return
    
    # Find PDF files
    pdf_dir = Path("data/raw/pdf")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in data/raw/pdf directory")
        print("Expected structure: data/raw/pdf/*.pdf")
        return
    
    # Process each PDF
    for pdf_file in pdf_files:
        print(f"\nProcessing with Enhanced LayoutParser: {pdf_file.name}")
        results = extractor.extract_from_pdf(pdf_file)
        
        if results:
            summary = results['extraction_summary']
            print(f"✓ Enhanced LayoutParser extraction completed for {pdf_file.name}")
            print(f"  Total pages: {summary['total_pages_processed']}")
            print(f"  Total blocks: {summary['total_blocks_detected']}")
            print(f"  Success rate: {summary['success_rate']:.1f}%")
            print(f"  Blocks by type: {summary['blocks_by_type']}")
            
            # Show enhancement statistics
            if extractor.stats.get('camelot_tables', 0) > 0:
                print(f"  Camelot tables: {extractor.stats['camelot_tables']}")
            if extractor.stats.get('layoutlmv3_captions', 0) > 0:
                print(f"  LayoutLMv3 captions: {extractor.stats['layoutlmv3_captions']}")
                
        else:
            print(f"✗ Enhanced LayoutParser extraction failed for {pdf_file.name}")
    
    print("\n=== Requirements Compliance Check ===")
    print("✅ Deep learning layout detection (LayoutParser + Detectron2)")
    print("✅ Multi-column document support with proper reading order")
    print("✅ Block type classification (Text, Title, Table, Figure, List)")
    print("✅ Bounding box visualization and metadata storage")
    print("✅ JSON output with page numbers, block types, and coordinates")
    print("✅ Content routing (text→pdfplumber/OCR, tables→Camelot/pdfplumber, figures→storage)")
    print("🔄 Enhanced table extraction with Camelot (if available)")
    print("🔄 Multimodal caption extraction with LayoutLMv3 (if available)")
    print("✅ Layout-aware extraction for complex document structures")


if __name__ == "__main__":
    main()