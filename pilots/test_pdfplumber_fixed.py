#!/usr/bin/env python3
"""
Simple test of the fixed pdfplumber extractor
"""

from src.pdfplumber_tess_extractor import PDFTableExtractor
from pathlib import Path

def test_extractor():
    """Test the fixed extractor with better error handling."""
    
    # Initialize extractor
    extractor = PDFTableExtractor()
    
    # Find PDF files
    pdf_dir = Path("data/raw/pdf")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in data/raw/pdf directory")
        return
    
    pdf_file = pdf_files[0]
    print(f"Testing extraction on: {pdf_file.name}")
    
    # Try text extraction only first
    print("\n1. Testing TEXT extraction only...")
    try:
        results = extractor.extract_from_pdf(
            pdf_file, 
            extract_text=True, 
            extract_tables=False  # Disable table extraction for now
        )
        
        if results:
            print("✅ Text extraction succeeded!")
            if 'text_results' in results:
                text_results = results['text_results']
                print(f"   Pages processed: {text_results['total_pages']}")
                print(f"   OCR pages: {len(text_results.get('ocr_pages', []))}")
        else:
            print("❌ Text extraction failed!")
    
    except Exception as e:
        print(f"❌ Text extraction error: {e}")
        import traceback
        traceback.print_exc()
    
    # Now try table extraction only
    print("\n2. Testing TABLE extraction only...")
    try:
        results = extractor.extract_from_pdf(
            pdf_file, 
            extract_text=False,  # Disable text extraction  
            extract_tables=True   # Enable table extraction
        )
        
        if results:
            print("✅ Table extraction succeeded!")
            if 'table_results' in results:
                table_results = results['table_results']
                print(f"   Tables found: {table_results['total_tables']}")
        else:
            print("❌ Table extraction failed!")
    
    except Exception as e:
        print(f"❌ Table extraction error: {e}")
        import traceback
        traceback.print_exc()
    
    # Finally try both together
    print("\n3. Testing BOTH text and table extraction...")
    try:
        results = extractor.extract_from_pdf(
            pdf_file, 
            extract_text=True, 
            extract_tables=True
        )
        
        if results:
            print("✅ Combined extraction succeeded!")
            print(f"   Processing time: {results['processing_time']:.2f} seconds")
        else:
            print("❌ Combined extraction failed!")
    
    except Exception as e:
        print(f"❌ Combined extraction error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_extractor()