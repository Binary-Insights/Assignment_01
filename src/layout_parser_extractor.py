"""
LayoutParser-based Document Layout Analysis and Content Extraction

This module uses LayoutParser for layout detection and OCR for content extraction.
Simplified to use only LayoutParser + pytesseract for reliable extraction.

Features:
- Deep learning-based layout detection using LayoutParser with Detectron2
- Block type classification (text, title, table, figure, list)
- Pure OCR-based content extraction for all block types
- Bounding box persistence for layout reconstruction
- Comprehensive logging and metrics tracking
"""

import layoutparser as lp
import cv2
import numpy as np
import pytesseract
from PIL import Image
import pdf2image
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, Optional, Any


class LayoutParserExtractor:
    """
    PDF content extraction using LayoutParser for layout analysis and OCR for content extraction.
    
    This class uses deep learning models to detect document layout elements
    and uses OCR to extract content from each detected block.
    """
    
    def __init__(self, output_dir="data/parsed/layout_parser", 
                 model_name="lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config",
                 max_pages_testing=None):
        """
        Initialize the LayoutParser-based extractor.
        
        Args:
            output_dir (str): Directory to save extracted content
            model_name (str): LayoutParser model for layout detection
            max_pages_testing (int): Maximum pages to process for testing (None for all pages)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration flags
        self.max_pages_testing = max_pages_testing  # None = process all pages
        
        # Initialize LayoutParser model
        self.model_name = model_name
        self.layout_model = None
        self._initialize_model()
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Block type mapping - LayoutParser returns capitalized string types
        self.block_types = {
            'Text': 'text',
            'Title': 'title', 
            'List': 'list',
            'Table': 'table',
            'Figure': 'figure'
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
    
    def _setup_logging(self):
        """Set up logging for the extractor."""
        logger = logging.getLogger('LayoutParserExtractor')
        logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = self.output_dir / 'extraction_log.txt'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger if not already present
        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def _initialize_model(self):
        """Initialize the LayoutParser detection model."""
        print(f"Initializing LayoutParser model...")
        
        # Due to local model compatibility issues, let's use the reliable remote model
        print("� Using remote model for reliable detection...")
        self._fallback_to_remote_model()
    
    def _fallback_to_remote_model(self):
        """Fallback to the original remote model download approach."""
        print("Trying original remote model approach with lower threshold...")
        
        try:
            # Use the original remote model approach with lower threshold
            self.layout_model = lp.models.Detectron2LayoutModel(
                self.model_name,
                extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.3],  # Much lower threshold
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
            
            # Process all pages unless max_pages_testing is specifically set
            if self.max_pages_testing and len(images) > self.max_pages_testing:
                print(f"⚠️ TESTING MODE: Processing only first {self.max_pages_testing} pages out of {len(images)} total pages")
                images = images[:self.max_pages_testing]
            else:
                print(f"📄 Processing all {len(images)} pages in the document")
            
            extraction_results['total_pages'] = len(images)
            self.stats['total_pages'] = len(images)
            
            # Process each page with LayoutParser and OCR
            for page_num, image in enumerate(images, 1):
                self.logger.info(f"Processing page {page_num}/{len(images)}")
                
                page_result = self._process_page(
                    image, page_num, pdf_output_dir
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
    
    def _process_page(self, image: Image.Image, page_num: int, output_dir: Path) -> Dict[str, Any]:
        """
        Process a single page using LayoutParser and extract content by block type.
        
        Args:
            image (PIL.Image): Page image for layout detection
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
            print(f"🖼️ Image converted to OpenCV format: shape={cv_image.shape}, dtype={cv_image.dtype}")
            
            # Detect layout elements
            print(f"🔍 Running layout detection on page {page_num}...")
            layout = self.layout_model.detect(cv_image)
            print(f"📊 Raw detection result: {type(layout)}, length={len(layout) if hasattr(layout, '__len__') else 'N/A'}")
            
            # Debug: Check if any blocks were detected at all (even with low confidence)
            if hasattr(layout, '__iter__'):
                for i, block in enumerate(layout):
                    if hasattr(block, 'score') and hasattr(block, 'type'):
                        print(f"   Block {i}: type={block.type}, confidence={block.score:.3f}")
            
            self.logger.info(f"Page {page_num}: Detected {len(layout)} blocks")
            self.stats['total_blocks'] += len(layout)
            
            # Process each detected block
            for block_idx, block in enumerate(layout):
                block_result = self._process_block(
                    block, block_idx, image, page_num, output_dir
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
                      page_num: int, output_dir: Path) -> Dict[str, Any]:
        """
        Process a detected layout block and extract content based on its type.
        
        Args:
            block: LayoutParser block object
            block_idx (int): Block index within the page
            image (PIL.Image): Full page image
            page_num (int): Page number
            output_dir (Path): Output directory
            
        Returns:
            dict: Block processing results
        """
        # Get block properties
        print(f"🔍 Raw block.type: {block.type} (type: {type(block.type)})")
        block_type = self.block_types.get(block.type, 'unknown')
        print(f"🏷️ Mapped block_type: '{block_type}'")
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
            # Route block to appropriate extraction method using only OCR
            if block_type == 'text':
                content, method, file_path = self._extract_text_block(
                    bbox, image, block_result['block_id'], output_dir
                )
            elif block_type == 'title':
                content, method, file_path = self._extract_title_block(
                    bbox, image, block_result['block_id'], output_dir
                )
            elif block_type == 'table':
                print('Inside Table block .........................')
                content, method, file_path = self._extract_table_block(
                    bbox, image, block_result['block_id'], output_dir
                )
            elif block_type == 'figure':
                content, method, file_path = self._extract_figure_block(
                    bbox, image, block_result['block_id'], output_dir
                )
            elif block_type == 'list':
                content, method, file_path = self._extract_list_block(
                    bbox, image, block_result['block_id'], output_dir
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
    
    def _extract_text_block(self, bbox, image: Image.Image, 
                           block_id: str, output_dir: Path) -> Tuple[str, str, Optional[Path]]:
        """Extract text content from a detected text block using OCR."""
        try:
            x1, y1, x2, y2 = bbox.x_1, bbox.y_1, bbox.x_2, bbox.y_2
            print(f"🔍 Processing text block {block_id}: bbox=({x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f})")
            
            # Crop the text region from the image
            crop = image.crop((x1, y1, x2, y2))
            print(f"📏 Cropped image size: {crop.size}")
            
            # Use OCR to extract text
            text = pytesseract.image_to_string(crop, config='--psm 6 -l eng')
            method = 'ocr'
            print(f"📝 OCR result for {block_id}: '{text.strip()[:50]}...' (length: {len(text.strip())})")
            
            # Save text to file if we got meaningful content
            if text and text.strip():
                file_path = output_dir / 'text' / f"{block_id}.txt"
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text.strip())
                print(f"💾 Saved text block to: {file_path}")
                return text.strip(), method, file_path
            else:
                print(f"⚠️ No meaningful text extracted from {block_id}")
            
            return None, method, None
        
        except Exception as e:
            self.logger.error(f"Error extracting text block {block_id}: {e}")
            print(f"❌ Exception in text extraction: {e}")
            return None, 'error', None
    
    def _extract_title_block(self, bbox, image: Image.Image,
                           block_id: str, output_dir: Path) -> Tuple[str, str, Optional[Path]]:
        """Extract title content from a detected title block."""
        # Similar to text extraction but saved in titles directory
        text, method, _ = self._extract_text_block(bbox, image, block_id, output_dir)
        
        if text:
            file_path = output_dir / 'titles' / f"{block_id}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return text, method, file_path
        
        return None, method, None
    
    def _extract_table_block(self, bbox, image: Image.Image,
                           block_id: str, output_dir: Path) -> Tuple[Optional[str], str, Optional[Path]]:
        """Extract table content from a detected table block using OCR."""
        try:
            x1, y1, x2, y2 = bbox.x_1, bbox.y_1, bbox.x_2, bbox.y_2
            
            # Crop the table region from the image
            crop = image.crop((x1, y1, x2, y2))
            
            # Use OCR with table-specific configuration
            ocr_config = '--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,()[]{}|+- '
            text = pytesseract.image_to_string(crop, config=ocr_config)
            method = 'ocr'
            
            # Save table text to file if we got meaningful content
            if text and text.strip():
                file_path = output_dir / 'tables' / f"{block_id}.txt"
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text.strip())
                return text.strip(), method, file_path
            
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
    
    def _extract_list_block(self, bbox, image: Image.Image,
                          block_id: str, output_dir: Path) -> Tuple[str, str, Optional[Path]]:
        """Extract list content from a detected list block."""
        # Similar to text extraction but saved in lists directory
        text, method, _ = self._extract_text_block(bbox, image, block_id, output_dir)
        
        if text:
            file_path = output_dir / 'lists' / f"{block_id}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return text, method, file_path
        
        return None, method, None
    

    
    def _save_layout_visualization(self, image: np.ndarray, layout, page_num: int, output_dir: Path):
        """Save enhanced annotated layout visualization with detailed bounding boxes."""
        try:
            # Always use our enhanced manual visualization for better annotations
            print(f"📊 Creating enhanced layout visualization for page {page_num} with {len(layout)} blocks")
            vis_image = self._create_manual_visualization(image, layout)
            
            # Save visualization
            vis_path = output_dir / 'layout_images' / f"page_{page_num:03d}_layout_annotated.png"
            success = cv2.imwrite(str(vis_path), vis_image)
            
            if success:
                print(f"✅ Saved enhanced layout visualization: {vis_path}")
            else:
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
                    print(f"✅ Saved enhanced layout visualization via PIL: {vis_path}")
                else:
                    pil_image = PILImage.fromarray(vis_image)
                    pil_image.save(vis_path)
                    print(f"✅ Saved enhanced layout visualization via PIL: {vis_path}")
            
            # Also save a simple version using LayoutParser's draw_box for comparison
            try:
                simple_vis = lp.draw_box(image, layout, box_width=3)
                if simple_vis is not None and isinstance(simple_vis, np.ndarray):
                    simple_path = output_dir / 'layout_images' / f"page_{page_num:03d}_layout_simple.png"
                    cv2.imwrite(str(simple_path), simple_vis)
                    print(f"📄 Also saved simple layout visualization: {simple_path}")
            except Exception as simple_error:
                print(f"⚠️ Could not create simple visualization: {simple_error}")
            
        except Exception as e:
            self.logger.error(f"Error saving layout visualization for page {page_num}: {e}")
            # Try to save original image as fallback
            try:
                vis_path = output_dir / 'layout_images' / f"page_{page_num:03d}_layout_fallback.png"
                cv2.imwrite(str(vis_path), image)
                self.logger.info(f"Saved original image without annotations for page {page_num}")
            except Exception as fallback_error:
                self.logger.error(f"Fallback image save also failed for page {page_num}: {fallback_error}")
    
    def _create_manual_visualization(self, image: np.ndarray, layout) -> np.ndarray:
        """Create enhanced manual visualization with detailed bounding box annotations."""
        try:
            # Make a copy of the original image
            vis_image = image.copy()
            
            # Define enhanced colors for better visibility
            type_colors = {
                'Text': (0, 255, 0),      # Green
                'Title': (255, 0, 0),     # Blue
                'List': (0, 255, 255),    # Yellow
                'Table': (255, 0, 255),   # Magenta
                'Figure': (0, 0, 255),    # Red
                'unknown': (128, 128, 128) # Gray
            }
            
            # Draw bounding boxes with enhanced annotations
            for i, block in enumerate(layout):
                bbox = block.block
                x1, y1, x2, y2 = int(bbox.x_1), int(bbox.y_1), int(bbox.x_2), int(bbox.y_2)
                
                # Get block type and color
                block_type = self.block_types.get(block.type, 'unknown')
                color = type_colors.get(block_type, (128, 128, 128))
                
                # Draw thicker rectangle for better visibility
                cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 4)
                
                # Create detailed label with bounding box coordinates
                confidence = block.score if hasattr(block, 'score') else 0.0
                label_text = f"{block_type} {i+1}"
                detail_text = f"Conf: {confidence:.2f}"
                bbox_text = f"({x1},{y1})-({x2},{y2})"
                size_text = f"{x2-x1}x{y2-y1}"
                
                # Font settings
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6
                font_thickness = 2
                line_height = 25
                
                # Calculate text dimensions
                label_size = cv2.getTextSize(label_text, font, font_scale, font_thickness)[0]
                detail_size = cv2.getTextSize(detail_text, font, font_scale-0.1, font_thickness-1)[0]
                bbox_size = cv2.getTextSize(bbox_text, font, font_scale-0.1, font_thickness-1)[0]
                
                # Determine label position (above or below box)
                label_y = y1 - 10 if y1 > 80 else y2 + 30
                
                # Draw background rectangle for all text
                bg_width = max(label_size[0], detail_size[0], bbox_size[0]) + 20
                bg_height = line_height * 3 + 10
                bg_y = label_y - bg_height if y1 > 80 else label_y - 5
                
                cv2.rectangle(vis_image, (x1, bg_y), (x1 + bg_width, bg_y + bg_height), color, -1)
                cv2.rectangle(vis_image, (x1, bg_y), (x1 + bg_width, bg_y + bg_height), (0, 0, 0), 2)
                
                # Draw text labels
                text_y = bg_y + 20
                cv2.putText(vis_image, label_text, (x1 + 5, text_y), 
                          font, font_scale, (255, 255, 255), font_thickness)
                
                text_y += line_height
                cv2.putText(vis_image, detail_text, (x1 + 5, text_y), 
                          font, font_scale-0.1, (255, 255, 255), font_thickness-1)
                
                text_y += line_height
                cv2.putText(vis_image, bbox_text, (x1 + 5, text_y), 
                          font, font_scale-0.1, (255, 255, 255), font_thickness-1)
                
                # Add small corner markers for precise positioning
                corner_size = 10
                # Top-left corner
                cv2.line(vis_image, (x1, y1), (x1 + corner_size, y1), color, 3)
                cv2.line(vis_image, (x1, y1), (x1, y1 + corner_size), color, 3)
                
                # Top-right corner
                cv2.line(vis_image, (x2, y1), (x2 - corner_size, y1), color, 3)
                cv2.line(vis_image, (x2, y1), (x2, y1 + corner_size), color, 3)
                
                # Bottom-left corner
                cv2.line(vis_image, (x1, y2), (x1 + corner_size, y2), color, 3)
                cv2.line(vis_image, (x1, y2), (x1, y2 - corner_size), color, 3)
                
                # Bottom-right corner
                cv2.line(vis_image, (x2, y2), (x2 - corner_size, y2), color, 3)
                cv2.line(vis_image, (x2, y2), (x2, y2 - corner_size), color, 3)
            
            # Add legend in the top-right corner
            self._add_legend_to_visualization(vis_image, type_colors)
            
            return vis_image
            
        except Exception as e:
            self.logger.error(f"Manual visualization creation failed: {e}")
            return image  # Return original image as last resort
    
    def _add_legend_to_visualization(self, vis_image: np.ndarray, type_colors: dict):
        """Add a legend to the visualization showing block type colors."""
        try:
            height, width = vis_image.shape[:2]
            legend_width = 200
            legend_height = len(type_colors) * 30 + 40
            
            # Position legend in top-right corner
            legend_x = width - legend_width - 20
            legend_y = 20
            
            # Draw legend background
            cv2.rectangle(vis_image, (legend_x, legend_y), 
                         (legend_x + legend_width, legend_y + legend_height), 
                         (255, 255, 255), -1)
            cv2.rectangle(vis_image, (legend_x, legend_y), 
                         (legend_x + legend_width, legend_y + legend_height), 
                         (0, 0, 0), 2)
            
            # Add legend title
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(vis_image, "Block Types", (legend_x + 10, legend_y + 25), 
                       font, 0.6, (0, 0, 0), 2)
            
            # Add legend entries
            y_offset = 50
            for block_type, color in type_colors.items():
                if block_type != 'unknown':  # Skip unknown type in legend
                    # Draw color square
                    cv2.rectangle(vis_image, (legend_x + 10, legend_y + y_offset - 10), 
                                 (legend_x + 30, legend_y + y_offset + 5), color, -1)
                    cv2.rectangle(vis_image, (legend_x + 10, legend_y + y_offset - 10), 
                                 (legend_x + 30, legend_y + y_offset + 5), (0, 0, 0), 1)
                    
                    # Add type label
                    cv2.putText(vis_image, block_type, (legend_x + 40, legend_y + y_offset), 
                               font, 0.5, (0, 0, 0), 1)
                    y_offset += 30
                    
        except Exception as e:
            self.logger.warning(f"Failed to add legend to visualization: {e}")
    
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
    """Main function to demonstrate LayoutParser-based extraction with OCR."""
    print("=== LayoutParser Document Extraction ===")
    print("Features:")
    print("  • Deep learning layout detection (LayoutParser + Detectron2)")
    print("  • OCR-based content extraction for all block types")
    print("  • Layout visualization with bounding boxes")
    print()
    print("Output structure: data/parsed/layout_parser/[pdf_name]/")
    print("  ├── text/          - Text blocks (OCR)")
    print("  ├── tables/        - Table content (OCR)")
    print("  ├── figures/       - Extracted figure images")
    print("  ├── titles/        - Title blocks (OCR)")
    print("  ├── lists/         - List blocks (OCR)")
    print("  ├── layout_images/ - Layout visualizations with bounding boxes")
    print("  └── bounding_boxes/- Detailed coordinate data")
    print()
    print("📄 FULL DOCUMENT MODE: Processing all pages in each document")
    print("   Set max_pages_testing=N to limit pages for testing")
    print()
    
    # Initialize extractor
    try:
        extractor = LayoutParserExtractor(
            max_pages_testing=None  # Process all pages
        )
    except RuntimeError as e:
        print(f"❌ LayoutParser initialization failed: {e}")
        print("💡 Please ensure LayoutParser and Detectron2 are properly installed")
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
    


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract content from PDF using LayoutParser')
    parser.add_argument('--pdf_path', type=str, help='Path to PDF file to process')
    parser.add_argument('--output_dir', type=str, default='data/parsed/layout_parser', 
                       help='Output directory for extracted content')
    parser.add_argument('--max_pages', type=int, default=None, 
                       help='Maximum pages to process (None for all pages)')
    
    args = parser.parse_args()
    
    if args.pdf_path:
        # Process specific PDF
        extractor = LayoutParserExtractor(
            output_dir=args.output_dir,
            max_pages_testing=args.max_pages
        )
        results = extractor.extract_from_pdf(args.pdf_path)
        
        if results:
            summary = results['extraction_summary']
            print(f"✓ Enhanced LayoutParser extraction completed for {Path(args.pdf_path).name}")
            print(f"  Total pages: {summary['total_pages_processed']}")
            print(f"  Total blocks: {summary['total_blocks_detected']}")
            print(f"  Success rate: {summary['success_rate']:.1f}%")
            print(f"  Blocks by type: {summary['blocks_by_type']}")
            print(f"  All content extracted using OCR")
        else:
            print(f"✗ LayoutParser extraction failed for {Path(args.pdf_path).name}")
    else:
        # Run main demo
        main()