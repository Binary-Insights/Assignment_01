import pdfplumber
import pytesseract
from PIL import Image
import os
import json
import logging
from pathlib import Path
from datetime import datetime
import io

class PDFTextExtractor:
    """
    A comprehensive PDF text extraction system with OCR fallback.
    
    Features:
    - Extract text per page using pdfplumber with layout parameters
    - OCR fallback for scanned pages using Tesseract
    - Word bounding box extraction for layout analysis
    - Logging of OCR usage and extraction metrics
    """
    
    def __init__(self, output_dir="data/parsed", log_level=logging.INFO):
        """
        Initialize the PDF text extractor.
        
        Args:
            output_dir (str): Directory to save extracted text files
            log_level: Logging level
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging with UTF-8 encoding
        self.logger = self._setup_logging(log_level)
        
        # OCR configuration
        self.ocr_config = '--psm 6 -l eng'  # Page segmentation mode for uniform text blocks
        
        # Extraction stats
        self.stats = {
            'total_pages': 0,
            'text_extracted_pages': 0,
            'ocr_pages': 0,
            'failed_pages': 0,
            'processing_time': 0
        }
    
    def _setup_logging(self, log_level):
        """Setup logging configuration with UTF-8 encoding for Windows compatibility."""
        logger = logging.getLogger('PDFTextExtractor')
        logger.setLevel(log_level)
        
        if not logger.handlers:
            # Create console handler with proper encoding
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            # Ensure encoding is set for the console
            import sys
            if sys.platform == 'win32':
                import codecs
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        
        return logger
    
    def extract_text_from_pdf(self, pdf_path, use_layout_params=True):
        """
        Extract text from PDF with OCR fallback.
        
        Args:
            pdf_path (str or Path): Path to PDF file
            use_layout_params (bool): Whether to use layout parameters for extraction
            
        Returns:
            dict: Extraction results including stats and success/failure information
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        start_time = datetime.now()
        
        # Create output directory for this PDF
        pdf_name = pdf_path.stem
        pdf_output_dir = self.output_dir / pdf_name
        pdf_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize extraction results
        extraction_results = {
            'pdf_name': pdf_name,
            'extraction_timestamp': datetime.now().isoformat(),
            'total_pages': 0,
            'ocr_pages': [],
            'failed_pages': [],
            'pages': []
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                extraction_results['total_pages'] = len(pdf.pages)
                self.stats['total_pages'] = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    self.logger.info(f"Processing page {page_num}/{len(pdf.pages)}")
                    
                    page_result = self._extract_page_text(
                        page, page_num, pdf_output_dir, use_layout_params
                    )
                    
                    extraction_results['pages'].append(page_result)
                    
                    # Track OCR usage
                    if page_result['used_ocr']:
                        extraction_results['ocr_pages'].append(page_num)
                        self.stats['ocr_pages'] += 1
                    else:
                        self.stats['text_extracted_pages'] += 1
                    
                    if not page_result['success']:
                        extraction_results['failed_pages'].append(page_num)
                        self.stats['failed_pages'] += 1
                
                # Extract and save word bounding boxes
                self._extract_word_boxes(pdf, pdf_output_dir)
                extraction_results['word_boxes_saved'] = True
        
        except Exception as e:
            self.logger.error(f"Error processing PDF: {e}")
            return None
        
        # Calculate processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        self.stats['processing_time'] = processing_time
        
        # Save extraction summary
        self._save_extraction_summary(extraction_results, pdf_output_dir)
        
        self.logger.info(f"Extraction completed in {processing_time:.2f} seconds")
        self.logger.info(f"Text extracted: {self.stats['text_extracted_pages']} pages")
        self.logger.info(f"OCR used: {self.stats['ocr_pages']} pages")
        self.logger.info(f"Failed: {self.stats['failed_pages']} pages")
        
        return extraction_results
    
    def _extract_page_text(self, page, page_num, output_dir, use_layout_params=True):
        """
        Extract text from a single page with OCR fallback.
        
        Args:
            page: pdfplumber page object
            page_num (int): Page number
            output_dir (Path): Output directory
            use_layout_params (bool): Whether to use layout parameters
            
        Returns:
            dict: Page extraction results
        """
        page_result = {
            'page_number': page_num,
            'text_length': 0,
            'used_ocr': False,
            'success': True,
            'extraction_method': 'pdfplumber'
        }
        
        try:
            # Create text directory
            text_dir = output_dir / 'text'
            text_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract text with layout parameters
            if use_layout_params:
                text = page.extract_text(
                    x_density=7.25,  # Increase for better word separation
                    y_density=13,   # Increase for better line separation
                    layout=True,
                    keep_blank_chars=False
                )
            else:
                text = page.extract_text()
            
            # If no text extracted, try OCR
            if not text or text.isspace():
                text = self._perform_ocr(page)
                if text:
                    page_result['used_ocr'] = True
                    page_result['extraction_method'] = 'tesseract_ocr'
            
            if text:
                # Save text to file
                page_file = text_dir / f'page_{page_num:03d}.txt'
                with open(page_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                page_result['text_length'] = len(text)
                page_result['text_file'] = f'page_{page_num:03d}.txt'
                self.logger.debug(f"Saved page {page_num} text to {page_file}")
            else:
                page_result['success'] = False
                self.logger.warning(f"No text extracted from page {page_num}")
        
        except Exception as e:
            self.logger.error(f"Error extracting text from page {page_num}: {e}")
            page_result['success'] = False
        
        return page_result
    
    def _perform_ocr(self, page):
        """
        Perform OCR on a page using Tesseract.
        
        Args:
            page: pdfplumber page object
            
        Returns:
            str: Extracted text from OCR
        """
        try:
            # Convert page to image
            page_image = page.to_image(resolution=300)  # High resolution for better OCR
            
            # Convert to PIL Image
            pil_image = page_image.annotated
            
            # Perform OCR
            text = pytesseract.image_to_string(pil_image, config=self.ocr_config)
            
            return text.strip()
        
        except Exception as e:
            self.logger.error(f"OCR failed: {e}")
            return None
    
    def _extract_word_boxes(self, pdf, output_dir):
        """
        Extract word bounding boxes for layout analysis.
        
        Args:
            pdf: pdfplumber PDF object
            output_dir (Path): Output directory
        """
        try:
            # Create text directory
            text_dir = output_dir / 'text'
            text_dir.mkdir(parents=True, exist_ok=True)
            
            word_boxes_data = []
            
            for page_num, page in enumerate(pdf.pages, 1):
                self.logger.info(f"Extracting word boxes from page {page_num}")
                
                # Use extract_words with more granular settings
                words = page.extract_words(
                    x_tolerance=3,  # Adjust space between letters
                    y_tolerance=3,  # Adjust line spacing
                    keep_blank_chars=False,
                    use_text_flow=True,  # Use text flow for better word grouping
                    horizontal_ltr=True  # Assume left-to-right text
                )
                
                page_words = {
                    'page_number': page_num,
                    'page_width': float(page.width),
                    'page_height': float(page.height),
                    'words': []
                }
                
                for word in words:
                    try:
                        word_data = {
                            'text': word['text'],
                            'x0': float(word['x0']),
                            'x1': float(word['x1']),
                            'y0': float(word.get('y0', word.get('top', 0))),  # Use 'top' if 'y0' not present
                            'y1': float(word.get('y1', word.get('bottom', 0))),  # Use 'bottom' if 'y1' not present
                            'font': word.get('fontname', ''),
                            'size': float(word.get('size', 0)),
                            'upright': bool(word.get('upright', True)),
                            'direction': word.get('direction', 'ltr')
                        }
                        
                        # Only add words with valid coordinates
                        if word_data['x0'] >= 0 and word_data['y0'] >= 0:
                            page_words['words'].append(word_data)
                    except (KeyError, ValueError, TypeError) as e:
                        # Log errors without unicode characters that might cause console issues
                        self.logger.debug(f"Page {page_num}: Error processing word: {str(e)}")
                
                # Only append pages that have words
                if page_words['words']:
                    word_boxes_data.append(page_words)
                else:
                    self.logger.warning(f"No words found on page {page_num}")
            
            if not word_boxes_data:
                self.logger.error("No word boxes extracted from any page")
                return
            
            # Save word boxes to JSON file in the text directory
            word_boxes_file = text_dir / 'word_boxes.json'
            with open(word_boxes_file, 'w', encoding='utf-8') as f:
                json.dump(word_boxes_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Word bounding boxes saved to {word_boxes_file}")
            
        except Exception as e:
            self.logger.error(f"Error extracting word boxes: {e}")
            raise  # Re-raise to ensure error is caught by caller
    
    def _save_extraction_summary(self, results, output_dir):
        """
        Save extraction summary and statistics.
        
        Args:
            results (dict): Extraction results
            output_dir (Path): Output directory
        """
        summary = {
            'extraction_timestamp': datetime.now().isoformat(),
            'pdf_info': {
                'name': results['pdf_name'],
                'total_pages': results['total_pages']
            },
            'text_extraction': {
                'total_pages': len(results['pages']),
                'ocr_pages': len(results['ocr_pages']),
                'failed_pages': len(results['failed_pages']),
                'processing_time_seconds': self.stats['processing_time']
            },
            'page_details': results['pages']
        }
        
        summary_file = output_dir / 'extraction_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)


def main():
    """Main function to demonstrate usage."""
    extractor = PDFTextExtractor()
    
    # Example PDF to process
    pdf_file = "data/raw/pdf/nvda-20240128.pdf"
    
    print(f"Processing: {pdf_file}")
    results = extractor.extract_text_from_pdf(pdf_file)
    
    if results:
        print("✓ Extraction completed for {pdf_name}".format(**results))
        print(f"  Total pages: {results['total_pages']}")
        print(f"  OCR pages: {len(results['ocr_pages'])}")
        print(f"  Failed pages: {len(results['failed_pages'])}")

if __name__ == "__main__":
    main()