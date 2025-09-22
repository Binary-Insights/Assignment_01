import pdfplumber
import pytesseract
import pandas as pd
import numpy as np
from PIL import Image
import os
import json
import logging
import csv
from pathlib import Path
from datetime import datetime

class PDFTableExtractor:
    """
    A comprehensive PDF table extraction system using pdfplumber.
    
    Features:
    - Extract text per page with OCR fallback (saved to text/ folder)
    - Extract tables using pdfplumber with different strategies
    - Save tables as CSV files with quality analysis
    - Compare different table extraction approaches
    """
    
    def __init__(self, output_dir="data/parsed/pdfplumber_tesseract", log_level=logging.INFO):
        """
        Initialize the PDF table extractor.
        
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
        logger = logging.getLogger('PDFTableExtractor')
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
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
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
        Extract tables using pdfplumber with different strategies.
        """
        table_results = {
            'total_tables': 0,
            'standard_extraction': {'tables': [], 'success_count': 0},
            'custom_settings': {'tables': [], 'success_count': 0},
            'financial_focused': {'tables': [], 'success_count': 0},
            'method_analysis': {}
        }
        
        try:
            # Standard table extraction
            self.logger.info("Extracting tables with standard pdfplumber settings...")
            standard_tables = self._extract_pdfplumber_tables_standard(pdf_path, tables_dir, 'standard')
            table_results['standard_extraction'] = standard_tables
            
            # Custom settings for better detection
            self.logger.info("Extracting tables with custom settings...")
            custom_tables = self._extract_pdfplumber_tables_custom(pdf_path, tables_dir, 'custom')
            table_results['custom_settings'] = custom_tables
            
            # Financial statement focused extraction
            self.logger.info("Extracting tables with financial statement focus...")
            financial_tables = self._extract_financial_tables(pdf_path, tables_dir, 'financial')
            table_results['financial_focused'] = financial_tables
            
            # Calculate total tables found
            total_tables = (standard_tables['success_count'] + 
                          custom_tables['success_count'] + 
                          financial_tables['success_count'])
            table_results['total_tables'] = total_tables
            self.stats['tables_found'] = total_tables
            
            # Generate method analysis
            table_results['method_analysis'] = self._analyze_table_methods(
                standard_tables, custom_tables, financial_tables
            )
            
            self.logger.info(f"Table extraction completed. Found {total_tables} tables total.")
            
        except Exception as e:
            self.logger.error(f"Error in table extraction: {e}")
        
        return table_results
    
    def _extract_pdfplumber_tables_standard(self, pdf_path, tables_dir, method_name):
        """Extract tables using standard pdfplumber settings."""
        results = {'tables': [], 'success_count': 0}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                table_count = 0
                
                for page_num, page in enumerate(pdf.pages, 1):
                    # Standard table extraction
                    tables = page.extract_tables()
                    self.logger.info(f"Page {page_num}: Found {len(tables)} tables with standard method")
                    
                    for i, table in enumerate(tables):
                        if table and len(table) > 1:
                            self.logger.info(f"Processing table {i+1} on page {page_num}: {len(table)} rows, {len(table[0]) if table[0] else 0} columns")
                            table_count += 1
                            
                            try:
                                # Convert to DataFrame
                                # Handle case where first row might be None or have different length
                                headers = table[0] if table[0] else [f"Col_{j}" for j in range(len(table[1]) if len(table) > 1 else 1)]
                                data_rows = table[1:] if len(table) > 1 else []
                                
                                # Ensure all rows have same number of columns
                                max_cols = max(len(row) if row else 0 for row in [headers] + data_rows) if table else 0
                                
                                # Normalize headers
                                if len(headers) < max_cols:
                                    headers.extend([f"Col_{j}" for j in range(len(headers), max_cols)])
                                headers = headers[:max_cols]
                                
                                # Normalize data rows
                                normalized_rows = []
                                for row in data_rows:
                                    if not row:
                                        row = [''] * max_cols
                                    elif len(row) < max_cols:
                                        row.extend([''] * (max_cols - len(row)))
                                    elif len(row) > max_cols:
                                        row = row[:max_cols]
                                    normalized_rows.append(row)
                                
                                df = pd.DataFrame(normalized_rows, columns=headers)
                                self.logger.info(f"Created DataFrame with shape: {df.shape}")
                                
                                # Clean the dataframe
                                df = self._clean_table_dataframe(df)
                                self.logger.info(f"Cleaned DataFrame with shape: {df.shape}")
                            
                            except Exception as df_error:
                                self.logger.error(f"Error creating DataFrame for table {table_count}: {df_error}")
                                continue
                            
                            # Generate filename
                            filename = f"{method_name}_page_{page_num:03d}_table_{i+1:03d}.csv"
                            filepath = tables_dir / filename
                            
                            # Save as CSV
                            df.to_csv(filepath, index=False)
                            
                            # Analyze table quality
                            quality_score = self._calculate_table_quality(df, table)
                            
                            # Store table info
                            table_info = {
                                'table_id': table_count,
                                'method': method_name,
                                'filename': filename,
                                'page': page_num,
                                'shape': df.shape,
                                'non_empty_cells': df.notna().sum().sum(),
                                'quality_score': quality_score,
                                'is_financial': self._is_financial_table(df)
                            }
                            results['tables'].append(table_info)
                            
                            self.logger.info(f"Saved {method_name} table {table_count} to {filename}")
                
                results['success_count'] = table_count
        
        except Exception as e:
            self.logger.error(f"Error in {method_name} table extraction: {e}")
        
        return results
    
    def _extract_pdfplumber_tables_custom(self, pdf_path, tables_dir, method_name):
        """Extract tables using custom pdfplumber settings for better detection."""
        results = {'tables': [], 'success_count': 0}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                table_count = 0
                
                for page_num, page in enumerate(pdf.pages, 1):
                    # Custom table extraction with adjusted settings
                    table_settings = {
                        "vertical_strategy": "lines_strict",
                        "horizontal_strategy": "lines_strict",
                        "explicit_vertical_lines": [],
                        "explicit_horizontal_lines": [],
                        "snap_tolerance": 3,
                        "join_tolerance": 3,
                        "edge_min_length": 3,
                        "min_words_vertical": 3,
                        "min_words_horizontal": 1,
                        "text_tolerance": 3,
                        "text_x_tolerance": 3,
                        "text_y_tolerance": 3,
                        "intersection_tolerance": 3,
                        "intersection_x_tolerance": 3,
                        "intersection_y_tolerance": 3,
                    }
                    
                    tables = page.extract_tables(table_settings)
                    
                    for i, table in enumerate(tables):
                        if table and len(table) > 1:
                            table_count += 1
                            
                            try:
                                # Convert to DataFrame with same robust approach
                                headers = table[0] if table[0] else [f"Col_{j}" for j in range(len(table[1]) if len(table) > 1 else 1)]
                                data_rows = table[1:] if len(table) > 1 else []
                                
                                # Ensure all rows have same number of columns
                                max_cols = max(len(row) if row else 0 for row in [headers] + data_rows) if table else 0
                                
                                # Normalize headers
                                if len(headers) < max_cols:
                                    headers.extend([f"Col_{j}" for j in range(len(headers), max_cols)])
                                headers = headers[:max_cols]
                                
                                # Normalize data rows
                                normalized_rows = []
                                for row in data_rows:
                                    if not row:
                                        row = [''] * max_cols
                                    elif len(row) < max_cols:
                                        row.extend([''] * (max_cols - len(row)))
                                    elif len(row) > max_cols:
                                        row = row[:max_cols]
                                    normalized_rows.append(row)
                                
                                df = pd.DataFrame(normalized_rows, columns=headers)
                                
                                # Clean the dataframe
                                df = self._clean_table_dataframe(df)
                            
                            except Exception as df_error:
                                self.logger.error(f"Error creating DataFrame for custom table {table_count}: {df_error}")
                                continue
                            
                            # Generate filename
                            filename = f"{method_name}_page_{page_num:03d}_table_{i+1:03d}.csv"
                            filepath = tables_dir / filename
                            
                            # Save as CSV
                            df.to_csv(filepath, index=False)
                            
                            # Analyze table quality
                            quality_score = self._calculate_table_quality(df, table)
                            
                            # Store table info
                            table_info = {
                                'table_id': table_count,
                                'method': method_name,
                                'filename': filename,
                                'page': page_num,
                                'shape': df.shape,
                                'non_empty_cells': df.notna().sum().sum(),
                                'quality_score': quality_score,
                                'is_financial': self._is_financial_table(df)
                            }
                            results['tables'].append(table_info)
                            
                            self.logger.info(f"Saved {method_name} table {table_count} to {filename}")
                
                results['success_count'] = table_count
        
        except Exception as e:
            self.logger.error(f"Error in {method_name} table extraction: {e}")
        
        return results
    
    def _extract_financial_tables(self, pdf_path, tables_dir, method_name):
        """Extract tables specifically looking for financial statements."""
        results = {'tables': [], 'success_count': 0}
        
        # Financial keywords to look for
        financial_keywords = [
            'revenue', 'income', 'expense', 'assets', 'liabilities', 'equity',
            'cash', 'receivables', 'inventory', 'depreciation', 'amortization',
            'gross profit', 'operating income', 'net income', 'balance sheet',
            'income statement', 'cash flow', 'earnings', 'loss', 'total'
        ]
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                table_count = 0
                
                for page_num, page in enumerate(pdf.pages, 1):
                    # Get page text to check for financial content
                    page_text = page.extract_text().lower() if page.extract_text() else ""
                    
                    # Check if page contains financial keywords
                    has_financial_content = any(keyword in page_text for keyword in financial_keywords)
                    
                    if has_financial_content:
                        # Use more aggressive table detection for financial pages
                        table_settings = {
                            "vertical_strategy": "text",
                            "horizontal_strategy": "text",
                            "snap_tolerance": 5,
                            "join_tolerance": 5,
                            "edge_min_length": 1,
                            "min_words_vertical": 1,
                            "min_words_horizontal": 1,
                            "text_tolerance": 5,
                        }
                        
                        tables = page.extract_tables(table_settings)
                        
                        for i, table in enumerate(tables):
                            if table and len(table) > 2:  # Financial tables usually have header + multiple rows
                                # Check if table looks financial
                                table_text = ' '.join([' '.join(row) for row in table]).lower()
                                financial_score = sum(1 for keyword in financial_keywords if keyword in table_text)
                                
                                if financial_score >= 2:  # At least 2 financial keywords
                                    table_count += 1
                                    
                                    try:
                                        # Convert to DataFrame with same robust approach
                                        headers = table[0] if table[0] else [f"Col_{j}" for j in range(len(table[1]) if len(table) > 1 else 1)]
                                        data_rows = table[1:] if len(table) > 1 else []
                                        
                                        # Ensure all rows have same number of columns
                                        max_cols = max(len(row) if row else 0 for row in [headers] + data_rows) if table else 0
                                        
                                        # Normalize headers
                                        if len(headers) < max_cols:
                                            headers.extend([f"Col_{j}" for j in range(len(headers), max_cols)])
                                        headers = headers[:max_cols]
                                        
                                        # Normalize data rows
                                        normalized_rows = []
                                        for row in data_rows:
                                            if not row:
                                                row = [''] * max_cols
                                            elif len(row) < max_cols:
                                                row.extend([''] * (max_cols - len(row)))
                                            elif len(row) > max_cols:
                                                row = row[:max_cols]
                                            normalized_rows.append(row)
                                        
                                        df = pd.DataFrame(normalized_rows, columns=headers)
                                        
                                        # Clean the dataframe
                                        df = self._clean_table_dataframe(df)
                                    
                                    except Exception as df_error:
                                        self.logger.error(f"Error creating DataFrame for financial table {table_count}: {df_error}")
                                        continue
                                    
                                    # Generate filename
                                    filename = f"{method_name}_page_{page_num:03d}_table_{i+1:03d}.csv"
                                    filepath = tables_dir / filename
                                    
                                    # Save as CSV
                                    df.to_csv(filepath, index=False)
                                    
                                    # Analyze table quality
                                    quality_score = self._calculate_table_quality(df, table)
                                    
                                    # Store table info
                                    table_info = {
                                        'table_id': table_count,
                                        'method': method_name,
                                        'filename': filename,
                                        'page': page_num,
                                        'shape': df.shape,
                                        'non_empty_cells': df.notna().sum().sum(),
                                        'quality_score': quality_score,
                                        'financial_score': financial_score,
                                        'is_financial': True
                                    }
                                    results['tables'].append(table_info)
                                    
                                    self.logger.info(f"Saved financial table {table_count} to {filename}")
                
                results['success_count'] = table_count
        
        except Exception as e:
            self.logger.error(f"Error in financial table extraction: {e}")
        
        return results
    
    def _clean_table_dataframe(self, df):
        """Clean and normalize table dataframe."""
        # Remove completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Replace None/NaN with empty strings for better CSV output
        df = df.fillna('')
        
        # Strip whitespace from string columns
        for col in df.columns:
            try:
                # Check if column contains string data that can be stripped
                if df[col].dtype == 'object' or df[col].dtype.name == 'object':
                    df[col] = df[col].astype(str).str.strip()
            except (AttributeError, TypeError):
                # Handle cases where dtype might not be accessible
                try:
                    # Try to convert to string and strip
                    df[col] = df[col].astype(str).str.strip()
                except:
                    # If all else fails, leave the column as is
                    pass
        
        return df
    
    def _calculate_table_quality(self, df, raw_table):
        """Calculate a quality score for the extracted table."""
        try:
            # Factors for quality scoring
            total_cells = df.shape[0] * df.shape[1]
            non_empty_cells = df.notna().sum().sum()
            
            # Basic quality metrics
            completeness = non_empty_cells / total_cells if total_cells > 0 else 0
            structure_score = min(df.shape[0], df.shape[1]) / max(df.shape[0], df.shape[1]) if max(df.shape) > 0 else 0
            
            # Check for numeric data (financial tables often have numbers)
            numeric_score = 0
            for col in df.columns:
                numeric_cells = pd.to_numeric(df[col], errors='coerce').notna().sum()
                numeric_score += numeric_cells / len(df) if len(df) > 0 else 0
            numeric_score = min(numeric_score / df.shape[1], 1.0) if df.shape[1] > 0 else 0
            
            # Overall quality score (0-100)
            quality_score = (completeness * 40 + structure_score * 30 + numeric_score * 30) * 100
            
            return round(quality_score, 2)
            
        except Exception:
            return 0.0
    
    def _is_financial_table(self, df):
        """Determine if a table appears to be a financial statement."""
        financial_indicators = [
            'revenue', 'income', 'expense', 'assets', 'liabilities', 'equity',
            'cash', 'total', 'net', 'gross', 'operating', '$', 'million', 'thousand'
        ]
        
        try:
            # Convert dataframe to text and check for financial keywords
            table_text = df.to_string().lower()
            financial_matches = sum(1 for indicator in financial_indicators if indicator in table_text)
            
            # Also check for numeric patterns typical in financial statements
            numeric_columns = 0
            for col in df.columns:
                try:
                    # Try to convert column to numeric and count non-null values
                    numeric_count = pd.to_numeric(df[col], errors='coerce').notna().sum()
                    if numeric_count > len(df) * 0.5:
                        numeric_columns += 1
                except Exception:
                    # Skip column if conversion fails
                    continue
            
            return financial_matches >= 3 or numeric_columns >= 2
        
        except Exception:
            # If any error occurs, default to False
            return False
    
    def _analyze_table_methods(self, standard_results, custom_results, financial_results):
        """Generate analysis comparing different table extraction methods."""
        analysis = {
            'method_comparison': {
                'standard': {
                    'tables_found': standard_results['success_count'],
                    'financial_tables': sum(1 for t in standard_results['tables'] if t.get('is_financial', False)),
                    'avg_quality': sum(t['quality_score'] for t in standard_results['tables']) / len(standard_results['tables']) if standard_results['tables'] else 0,
                    'best_for': "General table detection with default settings"
                },
                'custom': {
                    'tables_found': custom_results['success_count'],
                    'financial_tables': sum(1 for t in custom_results['tables'] if t.get('is_financial', False)),
                    'avg_quality': sum(t['quality_score'] for t in custom_results['tables']) / len(custom_results['tables']) if custom_results['tables'] else 0,
                    'best_for': "Tables with clear structure and consistent formatting"
                },
                'financial': {
                    'tables_found': financial_results['success_count'],
                    'financial_tables': financial_results['success_count'],  # All are financial by design
                    'avg_quality': sum(t['quality_score'] for t in financial_results['tables']) / len(financial_results['tables']) if financial_results['tables'] else 0,
                    'best_for': "Financial statements and accounting data"
                }
            },
            'recommendations': self._generate_table_recommendations(standard_results, custom_results, financial_results)
        }
        
        return analysis
    
    def _generate_table_recommendations(self, standard_results, custom_results, financial_results):
        """Generate recommendations based on table extraction results."""
        recommendations = []
        
        total_standard = standard_results['success_count']
        total_custom = custom_results['success_count']
        total_financial = financial_results['success_count']
        
        if total_financial > 0:
            recommendations.append(f"Financial-focused extraction found {total_financial} relevant tables - best for balance sheets and income statements")
        
        if total_custom > total_standard:
            recommendations.append("Custom settings performed better - suggests structured tables with consistent formatting")
        elif total_standard > total_custom:
            recommendations.append("Standard settings were sufficient - tables have clear borders and simple structure")
        
        if max(total_standard, total_custom, total_financial) == 0:
            recommendations.append("No tables detected - document may have unstructured data or images of tables requiring OCR")
        
        return recommendations
    
    def _convert_numpy_types(self, obj):
        """Convert numpy types to native Python types for JSON serialization."""
        if isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj

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
        
        # Convert numpy types to native Python types
        summary = self._convert_numpy_types(summary)
        
        summary_file = output_dir / 'table_extraction_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Table extraction summary saved to {summary_file}")


def main():
    """Main function to demonstrate PDF table extraction."""
    # Initialize extractor
    extractor = PDFTableExtractor()
    
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
                print(f"    Standard method: {table_results['standard_extraction']['success_count']}")
                print(f"    Custom settings: {table_results['custom_settings']['success_count']}")
                print(f"    Financial focused: {table_results['financial_focused']['success_count']}")
        else:
            print(f"✗ Extraction failed for {pdf_file.name}")


if __name__ == "__main__":
    main()