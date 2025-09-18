#!/usr/bin/env python3
"""
Simple Docling PDF Extractor

Based on the official Docling documentation example.
"""

def test_docling_import():
    """Test if Docling is properly installed and working."""
    try:
        from docling.document_converter import DocumentConverter
        print("✓ Docling DocumentConverter imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Docling import failed: {e}")
        print("\nTo install Docling:")
        print("  uv add docling")
        print("  or")
        print("  pip install docling")
        return False

def simple_docling_extract(pdf_path):
    """
    Simple PDF extraction using Docling's basic example.
    
    Args:
        pdf_path (str): Path to PDF file
    """
    try:
        from docling.document_converter import DocumentConverter
        
        print(f"Processing {pdf_path} with Docling...")
        
        # Initialize converter
        converter = DocumentConverter()
        
        # Convert document
        result = converter.convert(pdf_path)
        
        # Export to markdown
        markdown_content = result.document.export_to_markdown()
        
        # Save results
        output_file = f"data/parsed/docling_simple_{Path(pdf_path).stem}.md"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✓ Extraction completed! Output saved to: {output_file}")
        return True
        
    except Exception as e:
        print(f"✗ Extraction failed: {e}")
        return False

if __name__ == "__main__":
    import os
    from pathlib import Path
    
    print("=== Simple Docling PDF Extractor ===")
    
    # Test imports first
    if not test_docling_import():
        exit(1)
    
    # Find PDF files
    pdf_dir = Path("data/raw/pdf")
    if not pdf_dir.exists():
        print(f"PDF directory not found: {pdf_dir}")
        print("Expected structure: data/raw/pdf/*.pdf")
        exit(1)
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}")
        exit(1)
    
    # Process each PDF
    for pdf_file in pdf_files:
        print(f"\nProcessing: {pdf_file.name}")
        success = simple_docling_extract(pdf_file)
        if success:
            print(f"✓ Successfully processed {pdf_file.name}")
        else:
            print(f"✗ Failed to process {pdf_file.name}")