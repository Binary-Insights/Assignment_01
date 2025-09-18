#!/usr/bin/env python3
"""
Fix Docling import issue by creating the missing module alias
"""

import sys

print("=== Attempting to fix docling_parse.pdf_parsers import ===")

try:
    # Import the actual module
    import docling_parse.pdf_parser as pdf_parser_module
    print("✓ Successfully imported docling_parse.pdf_parser")
    
    # Create the alias that DocumentConverter is looking for
    import docling_parse
    docling_parse.pdf_parsers = pdf_parser_module
    print("✓ Created alias: docling_parse.pdf_parsers -> docling_parse.pdf_parser")
    
    # Now try to import DocumentConverter
    from docling.document_converter import DocumentConverter
    print("✓ DocumentConverter import successful!")
    
    # Test initialization
    converter = DocumentConverter()
    print("✓ DocumentConverter initialization successful!")
    
    print("\n=== Docling is now working! ===")
    
except Exception as e:
    print(f"✗ Fix attempt failed: {e}")

print("Fix attempt completed.")