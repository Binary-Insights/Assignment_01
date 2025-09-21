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
        
        # Setup logging
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
        """Setup logging configuration."""
        logger = logging.getLogger('PDFTextExtractor')
        logger.setLevel(log_level)
        
        # Create file handler
        log_file = self.output_dir / 'extraction_log.txt'
        handler = logging.FileHandler(log_file)
        handler.setLevel(log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        if not logger.handlers:
            logger.addHandler(handler)
        
        return logger
    
    def extract_text_from_pdf(self, pdf_path, use_layout_params=True):
        """
        Extract text from PDF with OCR fallback for scanned pages.
        
        Args:
            pdf_path (str): Path to the PDF file
            use_layout_params (bool): Use experimental layout parameters
            
        Returns:
            dict: Extraction results with page-wise data
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            self.logger.error(f"PDF file not found: {pdf_path}")
            return None
        
        self.logger.info(f"Starting text extraction from: {pdf_path.name}")
        start_time = datetime.now()
        
        # Create output directory for this PDF
        pdf_output_dir = self.output_dir / pdf_path.stem
        pdf_output_dir.mkdir(exist_ok=True)
        
        extraction_results = {
            'pdf_name': pdf_path.name,
            'total_pages': 0,
            'pages': [],
            'ocr_pages': [],
            'failed_pages': [],
            'word_boxes_saved': False
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
    
    def _extract_page_text(self, page, page_num, output_dir, use_layout_params):
        """
        Extract text from a single page with OCR fallback.
        
        Args:
            page: pdfplumber page object
            page_num (int): Page number
            output_dir (Path): Output directory for page files
            use_layout_params (bool): Use layout parameters
            
        Returns:
            dict: Page extraction results
        """
        page_result = {
            'page_number': page_num,
            'text_length': 0,
            'used_ocr': False,
            'success': True,
            'text_file': f"page_{page_num:03d}.txt",
            'extraction_method': 'pdfplumber'
        }
        
        try:
            # Try pdfplumber text extraction first
            if use_layout_params:
                # Use experimental layout parameters for better text ordering
                text = page.extract_text(
                    x_density=2.0,  # Horizontal density for character clustering
                    y_density=1.5   # Vertical density for line clustering
                )
            else:
                text = page.extract_text()
            
            # Check if meaningful text was extracted
            if text and len(text.strip()) > 10:  # Threshold for meaningful text
                page_result['text_length'] = len(text)
                page_result['extraction_method'] = 'pdfplumber'
            else:
                # Fallback to OCR
                self.logger.info(f"Page {page_num}: No text found, using OCR")
                text = self._perform_ocr(page)
                page_result['used_ocr'] = True
                page_result['text_length'] = len(text) if text else 0
                page_result['extraction_method'] = 'ocr'
            
            # Save page text to file
            if text:
                page_file = output_dir / page_result['text_file']
                with open(page_file, 'w', encoding='utf-8') as f:
                    f.write(text)
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
            word_boxes_data = []
            
            for page_num, page in enumerate(pdf.pages, 1):
                words = page.extract_words()
                
                page_words = {
                    'page_number': page_num,
                    'page_width': page.width,
                    'page_height': page.height,
                    'words': []
                }
                
                for word in words:
                    # Check if word has required coordinate properties
                    if all(key in word for key in ['text', 'x0', 'y0', 'x1', 'y1']):
                        word_data = {
                            'text': word['text'],
                            'x0': word['x0'],
                            'y0': word['y0'],
                            'x1': word['x1'],
                            'y1': word['y1'],
                            'font': word.get('fontname', ''),
                            'size': word.get('size', 0)
                        }
                        page_words['words'].append(word_data)
                    else:
                        # Log missing properties for debugging
                        missing_keys = [key for key in ['text', 'x0', 'y0', 'x1', 'y1'] if key not in word]
                        self.logger.debug(f"Page {page_num}: Word missing properties {missing_keys}: {word}")
                
                word_boxes_data.append(page_words)
            
            # Save word boxes to JSON file
            word_boxes_file = output_dir / 'word_boxes.json'
            with open(word_boxes_file, 'w', encoding='utf-8') as f:
                json.dump(word_boxes_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Word bounding boxes saved to {word_boxes_file}")
            
        except Exception as e:
            self.logger.error(f"Error extracting word boxes: {e}")
    
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
            'extraction_stats': {
                'pages_with_text': len([p for p in results['pages'] if not p['used_ocr']]),
                'pages_with_ocr': len(results['ocr_pages']),
                'failed_pages': len(results['failed_pages']),
                'success_rate': (results['total_pages'] - len(results['failed_pages'])) / results['total_pages'] * 100
            },
            'ocr_pages': results['ocr_pages'],
            'failed_pages': results['failed_pages'],
            'processing_time_seconds': self.stats['processing_time']
        }
        
        summary_file = output_dir / 'extraction_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Extraction summary saved to {summary_file}")


def main():
    """Main function to demonstrate PDF text extraction."""
    # Initialize extractor
    extractor = PDFTextExtractor()
    
    # Find PDF files in data/raw/pdf directory
    pdf_dir = Path("data/raw/pdf")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in data/raw/pdf directory")
        return
    
    # Process each PDF
    for pdf_file in pdf_files:
        print(f"\nProcessing: {pdf_file.name}")
        results = extractor.extract_text_from_pdf(pdf_file)
        
        if results:
            print(f"✓ Extraction completed for {pdf_file.name}")
            print(f"  Total pages: {results['total_pages']}")
            print(f"  OCR pages: {len(results['ocr_pages'])}")
            print(f"  Failed pages: {len(results['failed_pages'])}")
        else:
            print(f"✗ Extraction failed for {pdf_file.name}")


if __name__ == "__main__":
    main()