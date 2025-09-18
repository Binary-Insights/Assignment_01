#!/usr/bin/env python3
"""
Alternative Docling approach - try different backends or minimal setup
"""

print("=== Testing Alternative Docling Approaches ===")

# Approach 1: Try using a specific backend that might not need pdf_parsers
print("\n1. Testing with specific backend...")
try:
    from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
    print("✓ PyPdfiumDocumentBackend import successful")
    
    # Try to create a simple converter with this backend
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    
    # Try with minimal configuration
    pipeline_options = PdfPipelineOptions()
    format_options = {
        InputFormat.PDF: {
            "pipeline_options": pipeline_options,
            "backend": PyPdfiumDocumentBackend
        }
    }
    
    converter = DocumentConverter(format_options=format_options)
    print("✓ DocumentConverter with PyPdfium backend successful!")
    
except Exception as e:
    print(f"✗ Backend approach failed: {e}")

# Approach 2: Try importing components individually to isolate the issue
print("\n2. Testing individual components...")
try:
    from docling.datamodel.base_models import InputFormat, DocumentStream
    print("✓ Base models import successful")
    
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    print("✓ Pipeline options import successful")
    
    from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
    print("✓ PyPdfium backend import successful")
    
except Exception as e:
    print(f"✗ Individual components failed: {e}")

# Approach 3: Try the simplest possible DocumentConverter
print("\n3. Testing minimal DocumentConverter...")
try:
    from docling.document_converter import DocumentConverter
    
    # Try without any configuration
    converter = DocumentConverter()
    print("✓ Minimal DocumentConverter successful!")
    
except Exception as e:
    print(f"✗ Minimal DocumentConverter failed: {e}")
    
    # If that fails, let's see exactly where it fails
    print("\n3.1. Debugging DocumentConverter import...")
    try:
        import docling.document_converter
        print("✓ docling.document_converter module exists")
        print(f"  Available attributes: {dir(docling.document_converter)}")
    except Exception as e2:
        print(f"✗ Module level import failed: {e2}")

# Approach 4: Check if we need additional dependencies
print("\n4. Checking for missing dependencies...")
missing_deps = []
required_modules = [
    'docling_parse.pdf_parsers',
    'docling_parse.pdf_parser', 
    'pypdfium2',
    'pydantic',
    'requests'
]

for module in required_modules:
    try:
        __import__(module)
        print(f"✓ {module} available")
    except ImportError:
        print(f"✗ {module} missing")
        missing_deps.append(module)

if missing_deps:
    print(f"\nMissing dependencies: {missing_deps}")
    print("Try installing:")
    for dep in missing_deps:
        if 'docling_parse' not in dep:  # Don't suggest installing docling_parse submodules
            print(f"  uv add {dep}")

print("\n=== Analysis Complete ===")