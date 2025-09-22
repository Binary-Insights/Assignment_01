import pdfplumber
import pytesseract
import camelot
import pandas as pd
from PIL import Image
import os
import json
import logging
import csv
from pathlib import Path
from datetime import datetime
import cv2
import numpy as np


class HybridPDFExtractor:
    """
    A comprehensive PDF extraction system with text and table extraction.
    
    Features:
    - Extract text per page with OCR fallback (saved to text/ folder)
    - Extract tables using Camelot (lattice + stream modes) and pdfplumber
    - Hybrid table extraction with heuristics
    - Save tables as CSV files with method analysis
    """
    
    def _convert_numpy_types(self, obj):
        """Convert numpy types to native Python types for JSON serialization."""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        else:
            return obj
    
    def __init__(self, output_dir="data/parsed/hybrid", log_level=logging.INFO):
        """
        Initialize the hybrid PDF extractor.
        
        Args:
            output_dir (str): Base directory to save extracted files
            log_level: Logging level
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = self._setup_logging(log_level)
        
        # OCR configuration
        self.ocr_config = '--psm 6 -l eng'
        
        # Extraction stats
        self.stats = {
            'total_pages': 0,
            'text_extracted_pages': 0,
            'ocr_pages': 0,
            'failed_pages': 0,
            'tables_found': 0,
            'processing_time': 0
        }
    
    def _setup_logging(self, log_level):
        """Setup logging configuration."""
        logger = logging.getLogger('HybridPDFExtractor')
        logger.setLevel(log_level)
        
        # Clear existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create file handler
        log_file = self.output_dir / 'extraction_log.txt'
        handler = logging.FileHandler(log_file, mode='a')
        handler.setLevel(log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger
    
    def extract_from_pdf(self, pdf_path, extract_text=True, extract_tables=True, use_layout_params=True):
        """
        Extract both text and tables from PDF.
        
        Args:
            pdf_path (str): Path to the PDF file
            extract_text (bool): Whether to extract text
            extract_tables (bool): Whether to extract tables
            use_layout_params (bool): Use experimental layout parameters
            
        Returns:
            dict: Complete extraction results
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            self.logger.error(f"PDF file not found: {pdf_path}")
            return None
        
        self.logger.info(f"Starting extraction from: {pdf_path.name}")
        start_time = datetime.now()
        
        # Create output directories for this PDF
        pdf_output_dir = self.output_dir / pdf_path.stem
        pdf_output_dir.mkdir(exist_ok=True)
        
        text_dir = pdf_output_dir / 'text'
        tables_dir = pdf_output_dir / 'tables'
        text_dir.mkdir(exist_ok=True)
        tables_dir.mkdir(exist_ok=True)
        
        extraction_results = {
            'pdf_name': pdf_path.name,
            'total_pages': 0,
            'text_results': {},
            'table_results': {},
            'processing_time': 0
        }
        
        try:
            # Extract text if requested
            if extract_text:
                self.logger.info("Starting text extraction...")
                text_results = self._extract_text_from_pdf(
                    pdf_path, text_dir, use_layout_params
                )
                extraction_results['text_results'] = text_results
            
            # Extract tables if requested
            if extract_tables:
                self.logger.info("Starting table extraction...")
                table_results = self._extract_tables_from_pdf(pdf_path, tables_dir)
                extraction_results['table_results'] = table_results
            
            # Calculate processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            extraction_results['processing_time'] = processing_time
            self.stats['processing_time'] = processing_time
            
            # Save combined summary
            self._save_combined_summary(extraction_results, pdf_output_dir)
            
            self.logger.info(f"Complete extraction finished in {processing_time:.2f} seconds")
            
        except Exception as e:
            self.logger.error(f"Error during extraction: {e}")
            return None
        
        return extraction_results
    
    def _extract_text_from_pdf(self, pdf_path, text_dir, use_layout_params=True):
        """Extract text and save to text/ directory."""
        text_results = {
            'total_pages': 0,
            'pages': [],
            'ocr_pages': [],
            'failed_pages': [],
            'word_boxes_saved': False
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_results['total_pages'] = len(pdf.pages)
                self.stats['total_pages'] = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    self.logger.info(f"Processing text from page {page_num}/{len(pdf.pages)}")
                    
                    page_result = self._extract_page_text(
                        page, page_num, text_dir, use_layout_params
                    )
                    
                    text_results['pages'].append(page_result)
                    
                    if page_result['used_ocr']:
                        text_results['ocr_pages'].append(page_num)
                        self.stats['ocr_pages'] += 1
                    else:
                        self.stats['text_extracted_pages'] += 1
                    
                    if not page_result['success']:
                        text_results['failed_pages'].append(page_num)
                        self.stats['failed_pages'] += 1
                
                # Extract word boxes
                self._extract_word_boxes(pdf, text_dir)
                text_results['word_boxes_saved'] = True
        
        except Exception as e:
            self.logger.error(f"Error in text extraction: {e}")
        
        return text_results
    
    def _extract_page_text(self, page, page_num, text_dir, use_layout_params):
        """Extract text from a single page."""
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
                text = page.extract_text(x_density=2.0, y_density=1.5)
            else:
                text = page.extract_text()
            
            # Check if meaningful text was extracted
            if text and len(text.strip()) > 10:
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
                page_file = text_dir / page_result['text_file']
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
        """Perform OCR on a page using Tesseract."""
        try:
            page_image = page.to_image(resolution=300)
            pil_image = page_image.annotated
            text = pytesseract.image_to_string(pil_image, config=self.ocr_config)
            return text.strip()
        except Exception as e:
            self.logger.error(f"OCR failed: {e}")
            return None
    
    def _extract_word_boxes(self, pdf, text_dir):
        """Extract word bounding boxes for layout analysis."""
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
                
                word_boxes_data.append(page_words)
            
            # Save word boxes to JSON file
            word_boxes_file = text_dir / 'word_boxes.json'
            with open(word_boxes_file, 'w', encoding='utf-8') as f:
                json.dump(word_boxes_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Word bounding boxes saved to {word_boxes_file}")
            
        except Exception as e:
            self.logger.error(f"Error extracting word boxes: {e}")
    
    def _extract_tables_from_pdf(self, pdf_path, tables_dir):
        """
        Extract tables using multiple methods: Camelot (lattice + stream) and pdfplumber.
        """
        table_results = {
            'total_tables': 0,
            'camelot_lattice': {'tables': [], 'success_count': 0},
            'camelot_stream': {'tables': [], 'success_count': 0},
            'pdfplumber': {'tables': [], 'success_count': 0},
            'hybrid_results': [],
            'method_analysis': {}
        }
        
        try:
            # Try Camelot lattice mode (relies on ruling lines)
            self.logger.info("Extracting tables with Camelot lattice mode...")
            lattice_tables = camelot.read_pdf(str(pdf_path), flavor='lattice', pages='all')
            table_results['camelot_lattice']['tables'] = self._process_camelot_tables(
                lattice_tables, tables_dir, 'lattice'
            )
            table_results['camelot_lattice']['success_count'] = len(lattice_tables)
            
            # Try Camelot stream mode (infers columns by grouping text spans)
            self.logger.info("Extracting tables with Camelot stream mode...")
            stream_tables = camelot.read_pdf(str(pdf_path), flavor='stream', pages='all')
            table_results['camelot_stream']['tables'] = self._process_camelot_tables(
                stream_tables, tables_dir, 'stream'
            )
            table_results['camelot_stream']['success_count'] = len(stream_tables)
            
            # Try pdfplumber table extraction
            self.logger.info("Extracting tables with pdfplumber...")
            pdfplumber_tables = self._extract_pdfplumber_tables(pdf_path, tables_dir)
            table_results['pdfplumber'] = pdfplumber_tables
            
            # Perform hybrid analysis
            hybrid_results = self._perform_hybrid_analysis(
                pdf_path, lattice_tables, stream_tables, pdfplumber_tables['tables'], tables_dir
            )
            table_results['hybrid_results'] = hybrid_results
            
            # Calculate total tables found
            total_tables = (len(lattice_tables) + len(stream_tables) + 
                          len(pdfplumber_tables['tables']))
            table_results['total_tables'] = total_tables
            self.stats['tables_found'] = total_tables
            
            # Generate method analysis
            table_results['method_analysis'] = self._analyze_extraction_methods(
                lattice_tables, stream_tables, pdfplumber_tables['tables']
            )
            
            self.logger.info(f"Table extraction completed. Found {total_tables} tables total.")
            
        except Exception as e:
            self.logger.error(f"Error in table extraction: {e}")
        
        return table_results
    
    def _process_camelot_tables(self, tables, tables_dir, method):
        """Process and save Camelot tables."""
        processed_tables = []
        
        for i, table in enumerate(tables):
            try:
                # Generate filename
                filename = f"camelot_{method}_table_{i+1:03d}.csv"
                filepath = tables_dir / filename
                
                # Save as CSV
                table.to_csv(str(filepath))
                
                # Store table info
                table_info = {
                    'table_id': i + 1,
                    'method': f'camelot_{method}',
                    'filename': filename,
                    'page': table.page,
                    'accuracy': table.accuracy if hasattr(table, 'accuracy') else 0,
                    'shape': table.df.shape,
                    'whitespace': table.whitespace if hasattr(table, 'whitespace') else 0
                }
                processed_tables.append(table_info)
                
                self.logger.info(f"Saved {method} table {i+1} to {filename}")
                
            except Exception as e:
                self.logger.error(f"Error processing {method} table {i+1}: {e}")
        
        return processed_tables
    
    def _extract_pdfplumber_tables(self, pdf_path, tables_dir):
        """Extract tables using pdfplumber."""
        pdfplumber_results = {
            'tables': [],
            'success_count': 0
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                table_count = 0
                
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract tables from page
                    tables = page.extract_tables()
                    
                    for i, table in enumerate(tables):
                        if table and len(table) > 1:  # Valid table with header and data
                            table_count += 1
                            
                            # Convert to DataFrame
                            df = pd.DataFrame(table[1:], columns=table[0])
                            
                            # Generate filename
                            filename = f"pdfplumber_page_{page_num:03d}_table_{i+1:03d}.csv"
                            filepath = tables_dir / filename
                            
                            # Save as CSV
                            df.to_csv(filepath, index=False)
                            
                            # Store table info
                            table_info = {
                                'table_id': table_count,
                                'method': 'pdfplumber',
                                'filename': filename,
                                'page': page_num,
                                'shape': df.shape,
                                'non_empty_cells': df.notna().sum().sum()
                            }
                            pdfplumber_results['tables'].append(table_info)
                            
                            self.logger.info(f"Saved pdfplumber table {table_count} to {filename}")
                
                pdfplumber_results['success_count'] = table_count
        
        except Exception as e:
            self.logger.error(f"Error in pdfplumber table extraction: {e}")
        
        return pdfplumber_results
    
    def _perform_hybrid_analysis(self, pdf_path, lattice_tables, stream_tables, pdfplumber_tables, tables_dir):
        """
        Perform hybrid analysis to choose the best extraction method for each page.
        """
        hybrid_results = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Detect ruling lines to determine best method
                    has_ruling_lines = self._detect_ruling_lines(page)
                    
                    # Get tables for this page from each method
                    page_lattice = [t for t in lattice_tables if t.page == page_num]
                    page_stream = [t for t in stream_tables if t.page == page_num]
                    page_pdfplumber = [t for t in pdfplumber_tables if t['page'] == page_num]
                    
                    # Choose best method based on heuristics
                    recommended_method = self._choose_best_method(
                        has_ruling_lines, page_lattice, page_stream, page_pdfplumber
                    )
                    
                    hybrid_result = {
                        'page': page_num,
                        'has_ruling_lines': has_ruling_lines,
                        'lattice_tables': len(page_lattice),
                        'stream_tables': len(page_stream),
                        'pdfplumber_tables': len(page_pdfplumber),
                        'recommended_method': recommended_method,
                        'reasoning': self._get_method_reasoning(
                            recommended_method, has_ruling_lines, 
                            len(page_lattice), len(page_stream), len(page_pdfplumber)
                        )
                    }
                    
                    hybrid_results.append(hybrid_result)
        
        except Exception as e:
            self.logger.error(f"Error in hybrid analysis: {e}")
        
        return hybrid_results
    
    def _detect_ruling_lines(self, page):
        """
        Detect if a page has ruling lines (borders/grid lines) that would favor lattice mode.
        """
        try:
            # Extract line objects from the page
            lines = page.lines
            
            # Check for horizontal and vertical lines
            horizontal_lines = [line for line in lines if abs(line['y0'] - line['y1']) < 1]
            vertical_lines = [line for line in lines if abs(line['x0'] - line['x1']) < 1]
            
            # Heuristic: if we have both horizontal and vertical lines, likely has ruling lines
            return len(horizontal_lines) > 2 and len(vertical_lines) > 2
            
        except Exception:
            return False
    
    def _choose_best_method(self, has_ruling_lines, lattice_tables, stream_tables, pdfplumber_tables):
        """Choose the best extraction method based on heuristics."""
        
        # If page has ruling lines, prefer lattice mode
        if has_ruling_lines and len(lattice_tables) > 0:
            return 'camelot_lattice'
        
        # If no ruling lines but stream found tables, prefer stream
        elif not has_ruling_lines and len(stream_tables) > 0:
            return 'camelot_stream'
        
        # If pdfplumber found tables and others didn't, use pdfplumber
        elif len(pdfplumber_tables) > 0 and (len(lattice_tables) == 0 and len(stream_tables) == 0):
            return 'pdfplumber'
        
        # If multiple methods found tables, prefer the one with higher accuracy
        elif len(lattice_tables) > 0 or len(stream_tables) > 0:
            lattice_avg_acc = sum(t.accuracy for t in lattice_tables) / len(lattice_tables) if lattice_tables else 0
            stream_avg_acc = sum(t.accuracy for t in stream_tables) / len(stream_tables) if stream_tables else 0
            
            if lattice_avg_acc > stream_avg_acc:
                return 'camelot_lattice'
            else:
                return 'camelot_stream'
        
        else:
            return 'none_suitable'
    
    def _get_method_reasoning(self, method, has_ruling_lines, lattice_count, stream_count, pdfplumber_count):
        """Generate reasoning for method choice."""
        reasoning_map = {
            'camelot_lattice': f"Ruling lines detected ({has_ruling_lines}) and lattice found {lattice_count} tables",
            'camelot_stream': f"No ruling lines or stream performed better ({stream_count} tables vs {lattice_count} lattice)",
            'pdfplumber': f"PDFPlumber found {pdfplumber_count} tables when Camelot methods failed",
            'none_suitable': "No tables detected by any method"
        }
        return reasoning_map.get(method, "Unknown reasoning")
    
    def _analyze_extraction_methods(self, lattice_tables, stream_tables, pdfplumber_tables):
        """Generate analysis comparing different extraction methods."""
        analysis = {
            'method_comparison': {
                'camelot_lattice': {
                    'tables_found': len(lattice_tables),
                    'avg_accuracy': sum(t.accuracy for t in lattice_tables) / len(lattice_tables) if lattice_tables else 0,
                    'best_for': "Tables with clear borders and ruling lines"
                },
                'camelot_stream': {
                    'tables_found': len(stream_tables),
                    'avg_accuracy': sum(t.accuracy for t in stream_tables) / len(stream_tables) if stream_tables else 0,
                    'best_for': "Borderless tables with consistent spacing"
                },
                'pdfplumber': {
                    'tables_found': len(pdfplumber_tables),
                    'avg_accuracy': 'N/A',
                    'best_for': "Complex layouts where camelot fails"
                }
            },
            'recommendations': self._generate_method_recommendations(lattice_tables, stream_tables, pdfplumber_tables)
        }
        
        return analysis
    
    def _generate_method_recommendations(self, lattice_tables, stream_tables, pdfplumber_tables):
        """Generate recommendations based on extraction results."""
        recommendations = []
        
        if len(lattice_tables) > len(stream_tables) and len(lattice_tables) > 0:
            recommendations.append("Camelot lattice mode works best for this document - suggests tables with clear borders")
        elif len(stream_tables) > len(lattice_tables) and len(stream_tables) > 0:
            recommendations.append("Camelot stream mode works best - suggests borderless tables with text alignment")
        
        if len(pdfplumber_tables) > 0 and (len(lattice_tables) == 0 and len(stream_tables) == 0):
            recommendations.append("Only pdfplumber detected tables - consider using it for complex layouts")
        
        if not recommendations:
            recommendations.append("No clear winner - consider manual inspection or different parameters")
        
        return recommendations
    
    def _save_combined_summary(self, results, output_dir):
        """Save a comprehensive summary of both text and table extraction."""
        summary = {
            'extraction_timestamp': datetime.now().isoformat(),
            'pdf_info': {
                'name': results['pdf_name'],
                'processing_time_seconds': results['processing_time']
            },
            'text_extraction': results.get('text_results', {}),
            'table_extraction': results.get('table_results', {}),
            'overall_stats': self.stats
        }
        
        # Convert numpy types to native Python types for JSON serialization
        summary = self._convert_numpy_types(summary)
        
        summary_file = output_dir / 'hybrid_extraction_results.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Complete extraction summary saved to {summary_file}")


def main():
    """Main function to demonstrate hybrid PDF extraction."""
    # Initialize extractor
    extractor = HybridPDFExtractor()
    
    # Find PDF files in data/raw/pdf directory
    pdf_dir = Path("data/raw/pdf")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in data/raw/pdf directory")
        return
    
    # Process each PDF
    for pdf_file in pdf_files:
        print(f"\nProcessing: {pdf_file.name}")
        results = extractor.extract_from_pdf(
            pdf_file, 
            extract_text=True, 
            extract_tables=True
        )
        
        if results:
            print(f"✓ Extraction completed for {pdf_file.name}")
            print(f"  Processing time: {results['processing_time']:.2f} seconds")
            
            if 'text_results' in results:
                text_results = results['text_results']
                print(f"  Text: {text_results['total_pages']} pages processed")
                print(f"  OCR used: {len(text_results.get('ocr_pages', []))} pages")
            
            if 'table_results' in results:
                table_results = results['table_results']
                print(f"  Tables found: {table_results['total_tables']}")
                print(f"    Camelot lattice: {table_results['camelot_lattice']['success_count']}")
                print(f"    Camelot stream: {table_results['camelot_stream']['success_count']}")
                print(f"    PDFPlumber: {table_results['pdfplumber']['success_count']}")
        else:
            print(f"✗ Extraction failed for {pdf_file.name}")


if __name__ == "__main__":
    main()