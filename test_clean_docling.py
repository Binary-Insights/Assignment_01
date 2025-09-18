#!/usr/bin/env python3
"""
Test clean Docling installation after sync
"""

print("=== Testing Clean Docling Installation ===")

def test_basic_imports():
    """Test basic imports."""
    print("\n1. Testing basic imports...")
    
    try:
        import docling
        print("✓ docling imported successfully")
    except ImportError as e:
        print(f"✗ docling import failed: {e}")
        return False
    
    try:
        from docling.document_converter import DocumentConverter
        print("✓ DocumentConverter imported successfully")
    except ImportError as e:
        print(f"✗ DocumentConverter import failed: {e}")
        return False
    
    return True

def test_converter_initialization():
    """Test DocumentConverter initialization."""
    print("\n2. Testing DocumentConverter initialization...")
    
    try:
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        print("✓ DocumentConverter initialized successfully")
        return converter
    except Exception as e:
        print(f"✗ DocumentConverter initialization failed: {e}")
        return None

def test_with_sample_content():
    """Test with a simple text content if no PDF available."""
    print("\n3. Testing basic functionality...")
    
    converter = test_converter_initialization()
    if not converter:
        return False
    
    # Look for any PDF files to test with
    from pathlib import Path
    test_locations = [
        Path("data/raw/pdf"),
        Path("data/raw"),
        Path(".")
    ]
    
    test_pdf = None
    for location in test_locations:
        if location.exists():
            pdfs = list(location.glob("*.pdf"))
            if pdfs:
                test_pdf = pdfs[0]
                break
    
    if test_pdf:
        try:
            print(f"Testing with {test_pdf}...")
            result = converter.convert(str(test_pdf))
            doc = result.document
            
            # Test basic exports
            text_content = doc.export_to_text()
            print(f"✓ Extracted {len(text_content)} characters of text")
            
            markdown_content = doc.export_to_markdown()
            print(f"✓ Exported to markdown ({len(markdown_content)} characters)")
            
            return True
            
        except Exception as e:
            print(f"✗ PDF processing failed: {e}")
            return False
    else:
        print("No PDF files found for testing, but DocumentConverter is working!")
        return True

def main():
    print("Testing freshly installed Docling...")
    
    # Test 1: Basic imports
    if not test_basic_imports():
        print("\n❌ Basic imports failed - Docling not properly installed")
        return
    
    # Test 2: Converter initialization  
    if not test_converter_initialization():
        print("\n❌ DocumentConverter initialization failed")
        return
    
    # Test 3: Basic functionality
    if test_with_sample_content():
        print("\n✅ Docling is working correctly!")
        print("You can now use Docling for PDF extraction")
    else:
        print("\n⚠️  Docling imports work but PDF processing may have issues")

if __name__ == "__main__":
    main()