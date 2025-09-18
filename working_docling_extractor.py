#!/usr/bin/env python3
"""
Working Docling PDF Extractor

Based on actual available Docling modules and the official documentation example.
This version uses only the modules that are confirmed to be available.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

def test_docling_availability():
    """Test if Docling is available and working."""
    try:
        from docling.document_converter import DocumentConverter
        return True, None
    except ImportError as e:
        return False, str(e)

class WorkingDoclingExtractor:
    """
    Simple Docling PDF extractor using confirmed available modules.
    """
    
    def __init__(self, output_dir="data/parsed/docling"):
        """Initialize the extractor."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Test availability
        available, error = test_docling_availability()
        if not available:
            raise ImportError(f"Docling not available: {error}")
        
        # Import here after confirming availability
        from docling.document_converter import DocumentConverter
        
        # Initialize converter with basic configuration
        self.converter = DocumentConverter()
        
        print("✓ Docling DocumentConverter initialized successfully")
    
    def extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract content from PDF using Docling.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            dict: Extraction results
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            print(f"✗ PDF file not found: {pdf_path}")
            return None
        
        print(f"Processing: {pdf_path.name}")
        start_time = datetime.now()
        
        # Create output directory for this PDF
        pdf_output_dir = self.output_dir / pdf_path.stem
        pdf_output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {
            'pdf_name': pdf_path.name,
            'timestamp': start_time.isoformat(),
            'success': False,
            'files_created': {},
            'error': None
        }
        
        try:
            # Convert document
            print("  Converting document...")
            result = self.converter.convert(str(pdf_path))
            
            # Get the document
            doc = result.document
            
            # Export to different formats
            print("  Exporting to formats...")
            
            # 1. Export to Markdown
            try:
                markdown_content = doc.export_to_markdown()
                markdown_file = pdf_output_dir / f"{pdf_path.stem}.md"
                with open(markdown_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                results['files_created']['markdown'] = str(markdown_file)
                print(f"    ✓ Markdown: {markdown_file}")
            except Exception as e:
                print(f"    ✗ Markdown export failed: {e}")
            
            # 2. Export to JSON (DoclingDocument format)
            try:
                json_content = doc.export_to_dict()
                json_file = pdf_output_dir / f"{pdf_path.stem}.json"
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(json_content, f, indent=2, ensure_ascii=False, default=str)
                results['files_created']['json'] = str(json_file)
                print(f"    ✓ JSON: {json_file}")
            except Exception as e:
                print(f"    ✗ JSON export failed: {e}")
            
            # 3. Export to HTML
            try:
                html_content = doc.export_to_html()
                html_file = pdf_output_dir / f"{pdf_path.stem}.html"
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                results['files_created']['html'] = str(html_file)
                print(f"    ✓ HTML: {html_file}")
            except Exception as e:
                print(f"    ✗ HTML export failed: {e}")
            
            # 4. Export plain text
            try:
                text_content = doc.export_to_text()
                text_file = pdf_output_dir / f"{pdf_path.stem}.txt"
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                results['files_created']['text'] = str(text_file)
                print(f"    ✓ Text: {text_file}")
            except Exception as e:
                print(f"    ✗ Text export failed: {e}")
            
            # Calculate processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            results['processing_time_seconds'] = processing_time
            results['success'] = True
            
            print(f"  ✓ Extraction completed in {processing_time:.2f} seconds")
            
        except Exception as e:
            results['error'] = str(e)
            print(f"  ✗ Extraction failed: {e}")
        
        # Save results summary
        results_file = pdf_output_dir / 'extraction_results.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        return results

def main():
    """Main function to run Docling extraction."""
    print("=== Working Docling PDF Extractor ===")
    
    try:
        # Initialize extractor
        extractor = WorkingDoclingExtractor()
        
        # Find PDF files
        pdf_dir = Path("data/raw/pdf")
        if not pdf_dir.exists():
            print(f"PDF directory not found: {pdf_dir}")
            print("Please create the directory and add PDF files:")
            print("  mkdir -p data/raw/pdf")  
            print("  # Add your PDF files to data/raw/pdf/")
            return
        
        pdf_files = list(pdf_dir.glob("*.pdf"))
        if not pdf_files:
            print(f"No PDF files found in {pdf_dir}")
            return
        
        print(f"Found {len(pdf_files)} PDF file(s)")
        
        # Process each PDF
        successful = 0
        for pdf_file in pdf_files:
            print(f"\n--- Processing: {pdf_file.name} ---")
            results = extractor.extract_from_pdf(pdf_file)
            
            if results and results.get('success', False):
                successful += 1
                print(f"✓ Success! Files created:")
                for format_name, file_path in results['files_created'].items():
                    print(f"  - {format_name}: {file_path}")
            else:
                print(f"✗ Failed to process {pdf_file.name}")
                if results and results.get('error'):
                    print(f"  Error: {results['error']}")
        
        print(f"\n=== Summary ===")
        print(f"Processed: {successful}/{len(pdf_files)} files successfully")
        print(f"Output directory: {extractor.output_dir}")
        
    except ImportError as e:
        print(f"✗ Docling not available: {e}")
        print("\nTo install Docling:")
        print("  uv add docling")
        print("  uv add docling-parse")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    main()