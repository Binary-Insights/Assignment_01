#!/usr/bin/env python3
"""
Test Docling imports and basic functionality
"""

print("Testing Docling imports...")

try:
    import docling
    print("✓ Basic docling import successful")
    print(f"  Available attributes: {dir(docling)}")
except ImportError as e:
    print(f"✗ Basic docling import failed: {e}")
    exit(1)

try:
    from docling.document_converter import DocumentConverter
    print("✓ DocumentConverter import successful")
    # Test initialization
    converter = DocumentConverter()
    print("✓ DocumentConverter initialization successful")
except ImportError as e:
    print(f"✗ DocumentConverter import failed: {e}")
except Exception as e:
    print(f"✗ DocumentConverter initialization failed: {e}")

try:
    from docling.datamodel.base_models import InputFormat
    print("✓ InputFormat import successful") 
except ImportError as e:
    print(f"✗ InputFormat import failed: {e}")

try:
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    print("✓ PdfPipelineOptions import successful")
except ImportError as e:
    print(f"✗ PdfPipelineOptions import failed: {e}")

try:
    from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
    print("✓ PyPdfiumDocumentBackend import successful")
except ImportError as e:
    print(f"✗ PyPdfiumDocumentBackend import failed: {e}")

# Test basic functionality
try:
    print("\nTesting basic DocumentConverter functionality...")
    converter = DocumentConverter()
    print("✓ DocumentConverter initialized successfully")
except Exception as e:
    print(f"✗ DocumentConverter initialization failed: {e}")

print("\nDocling imports test completed!")