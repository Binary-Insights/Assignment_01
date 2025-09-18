#!/usr/bin/env python3
"""
Test the improved table and figure extraction in DoclingExtractor
"""

import sys
from pathlib import Path

def test_table_figure_extraction():
    """Test that tables and figures are being properly extracted."""
    print("=== Testing Table and Figure Extraction ===")
    
    # Check if we have any processed PDFs
    data_dir = Path("data/parsed/docling")
    if not data_dir.exists():
        print("❌ No parsed data directory found")
        return False
    
    pdf_dirs = [d for d in data_dir.iterdir() if d.is_dir()]
    if not pdf_dirs:
        print("❌ No processed PDF directories found")
        return False
    
    for pdf_dir in pdf_dirs:
        print(f"\n📁 Checking {pdf_dir.name}:")
        
        # Check tables directory
        tables_dir = pdf_dir / 'tables'
        if tables_dir.exists():
            table_files = list(tables_dir.glob('*'))
            print(f"  📊 Tables: {len(table_files)} files")
            for table_file in table_files:
                print(f"    - {table_file.name}")
        else:
            print("  📊 Tables: No tables directory")
        
        # Check figures directory  
        figures_dir = pdf_dir / 'figures'
        if figures_dir.exists():
            figure_files = list(figures_dir.glob('*'))
            print(f"  🖼️  Figures: {len(figure_files)} files")
            for figure_file in figure_files:
                print(f"    - {figure_file.name}")
        else:
            print("  🖼️  Figures: No figures directory")
        
        # Check formulas directory
        formulas_dir = pdf_dir / 'formulas'
        if formulas_dir.exists():
            formula_files = list(formulas_dir.glob('*'))
            print(f"  🧮 Formulas: {len(formula_files)} files")
            for formula_file in formula_files:
                print(f"    - {formula_file.name}")
        else:
            print("  🧮 Formulas: No formulas directory")
        
        # Check text content for table patterns
        text_dir = pdf_dir / 'text'
        if text_dir.exists():
            text_files = list(text_dir.glob('*.txt'))
            for text_file in text_files:
                with open(text_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    table_lines = [line for line in content.split('\n') if '|' in line and line.count('|') >= 3]
                    if table_lines:
                        print(f"  📋 Found {len(table_lines)} table-like lines in {text_file.name}")
                        print(f"    Sample: {table_lines[0][:100]}...")
    
    print("\n=== Recommendations ===")
    print("1. Run the extractor again with the improved table/figure detection")
    print("2. Check the respective folders for extracted content")
    print("3. Tables should be saved as .csv and .txt files")
    print("4. Figures should be saved as .png files with metadata")
    print("5. Formulas should be saved as .txt files")

def show_extraction_summary():
    """Show summary of what gets extracted to which folders."""
    print("\n=== DoclingExtractor Output Structure ===")
    print("data/parsed/docling/[pdf_name]/")
    print("├── text/")
    print("│   ├── structured_content.txt    # Main text content (markdown)")
    print("│   └── full_document.txt         # Complete document text")
    print("├── tables/")
    print("│   ├── docling_table_001.csv     # Table data in CSV format")
    print("│   ├── docling_table_001.txt     # Table data in text format")
    print("│   └── docling_table_001_metadata.json  # Table metadata")
    print("├── figures/")
    print("│   ├── figure_001.png            # Extracted figure images")
    print("│   └── figure_001_info.txt       # Figure metadata")
    print("├── formulas/")
    print("│   └── formula_001.txt           # Mathematical formulas")
    print("├── markdown/")
    print("│   └── document.md               # Markdown export")
    print("├── json/")
    print("│   ├── document.json             # JSON export")
    print("│   └── document_doctags.xml      # DocTags XML export")
    print("└── comparison/")
    print("    └── docling_vs_traditional.json  # Comparison metrics")
    
    print("\n=== New Extraction Methods ===")
    print("🔍 Tables:")
    print("  1. Direct Docling table detection (docling_doc.tables)")
    print("  2. Document structure scanning (table labels)")
    print("  3. Markdown pattern detection (| table | format |)")
    print("\n🔍 Figures:")
    print("  1. Direct Docling figure detection (pictures/figures/images)")
    print("  2. Document structure scanning (figure labels)")
    print("  3. Image data extraction and saving")
    print("\n🔍 Formulas:")
    print("  1. Direct Docling formula detection (math labels)")
    print("  2. Text pattern scanning (mathematical symbols)")
    print("  3. Mathematical notation detection")

if __name__ == "__main__":
    show_extraction_summary()
    test_table_figure_extraction()