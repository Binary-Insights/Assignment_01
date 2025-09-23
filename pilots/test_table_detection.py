#!/usr/bin/env python3
"""
Simple pdfplumber table detection test

This script will quickly test if pdfplumber can detect any tables in the PDF
and provide diagnostic information.
"""

import pdfplumber
from pathlib import Path

def test_table_detection():
    """Test basic table detection capabilities."""
    
    pdf_dir = Path("data/raw/pdf")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in data/raw/pdf directory")
        return
    
    pdf_file = pdf_files[0]
    print(f"Testing table detection on: {pdf_file.name}")
    
    try:
        with pdfplumber.open(pdf_file) as pdf:
            print(f"PDF has {len(pdf.pages)} pages")
            
            total_tables = 0
            for page_num, page in enumerate(pdf.pages[:5], 1):  # Test first 5 pages
                print(f"\nPage {page_num}:")
                
                # Basic table detection
                tables = page.extract_tables()
                print(f"  Standard method found: {len(tables)} tables")
                
                if tables:
                    for i, table in enumerate(tables):
                        print(f"    Table {i+1}: {len(table)} rows, {len(table[0]) if table and table[0] else 0} columns")
                        if table and len(table) > 0:
                            print(f"      First row: {table[0][:3]}...")  # Show first 3 cells
                
                # Try with different settings
                table_settings_1 = {
                    "vertical_strategy": "text",
                    "horizontal_strategy": "text"
                }
                
                tables_text = page.extract_tables(table_settings_1)
                print(f"  Text-based method found: {len(tables_text)} tables")
                
                table_settings_2 = {
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines"
                }
                
                tables_lines = page.extract_tables(table_settings_2)
                print(f"  Lines-based method found: {len(tables_lines)} tables")
                
                total_tables += len(tables) + len(tables_text) + len(tables_lines)
                
                # Check if page has table-like content
                page_text = page.extract_text()
                if page_text:
                    lines = page_text.split('\n')
                    # Look for lines with multiple words/numbers that might be table rows
                    potential_table_lines = [line for line in lines if len(line.split()) >= 3]
                    print(f"  Potential table lines: {len(potential_table_lines)}")
                    
                    # Show a few potential table lines
                    for line in potential_table_lines[:3]:
                        print(f"    '{line[:60]}...'")
            
            print(f"\nTotal tables found across all methods: {total_tables}")
            
            if total_tables == 0:
                print("\n🔍 DIAGNOSTIC INFO:")
                print("No tables detected. Possible reasons:")
                print("1. PDF might have tables as images (need OCR)")
                print("2. Tables might not have clear borders/structure")
                print("3. Tables might use unconventional formatting")
                print("4. PDF might be scanned/image-based")
                
                # Check first page for diagnostic info
                first_page = pdf.pages[0]
                print(f"\nFirst page analysis:")
                print(f"  Lines detected: {len(first_page.lines)}")
                print(f"  Rectangles detected: {len(first_page.rects)}")
                print(f"  Words extracted: {len(first_page.extract_words())}")
                print(f"  Images embedded: {len(first_page.images)}")
    
    except Exception as e:
        print(f"Error during table detection test: {e}")


if __name__ == "__main__":
    test_table_detection()