#!/usr/bin/env python3
"""
Docling Module Explorer

This script explores Docling v1.20.0 modules to identify:
1. What's available in docling.datamodel.base_models
2. Which imports from docling_extractor.py are working/failing
3. Alternative import paths for missing classes
"""

import inspect
import sys
from typing import Any

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def explore_module_attributes(module_name: str, module_obj: Any):
    """Explore and display module attributes in a formatted way."""
    attrs = dir(module_obj)
    public_attrs = [attr for attr in attrs if not attr.startswith('_')]
    
    print(f"\nModule: {module_name}")
    print(f"Total attributes: {len(attrs)}")
    print(f"Public attributes: {len(public_attrs)}")
    
    if public_attrs:
        print("\nAvailable imports:")
        classes = []
        functions = []
        modules = []
        others = []
        
        for attr in sorted(public_attrs):
            try:
                attr_obj = getattr(module_obj, attr)
                if inspect.isclass(attr_obj):
                    classes.append(f"  📦 {attr}")
                elif inspect.isfunction(attr_obj):
                    functions.append(f"  🔧 {attr}")
                elif inspect.ismodule(attr_obj):
                    modules.append(f"  📁 {attr}")
                else:
                    others.append(f"  📋 {attr} ({type(attr_obj).__name__})")
            except Exception as e:
                others.append(f"  ⚠️  {attr} (error: {e})")
        
        if classes:
            print("\nClasses:")
            for item in classes:
                print(item)
                
        if functions:
            print("\nFunctions:")
            for item in functions:
                print(item)
                
        if modules:
            print("\nSubmodules:")
            for item in modules:
                print(item)
                
        if others:
            print("\nOther:")
            for item in others:
                print(item)
    
    # Check for __all__
    if hasattr(module_obj, '__all__'):
        print(f"\n__all__ exports: {getattr(module_obj, '__all__')}")

def test_import(import_statement: str, description: str) -> bool:
    """Test an import statement and return success status."""
    try:
        namespace = {}
        exec(import_statement, namespace)
        print(f"✅ {description}: SUCCESS")
        return True
    except ImportError as e:
        print(f"❌ {description}: IMPORT ERROR - {e}")
        return False
    except Exception as e:
        print(f"⚠️  {description}: OTHER ERROR - {e}")
        return False

def main():
    print("Docling Module Explorer v1.0")
    print("Exploring Docling v1.20.0 modules and imports...")
    
    # Test basic Docling import first
    print_section("Basic Docling Import Test")
    if not test_import("import docling", "Basic docling import"):
        print("❌ Cannot proceed - Docling is not available!")
        sys.exit(1)
    
    # Explore main docling package
    print_section("Main Docling Package")
    try:
        import docling
        explore_module_attributes("docling", docling)
    except Exception as e:
        print(f"❌ Error exploring main docling package: {e}")
    
    # Test DocumentConverter (known to work)
    print_section("DocumentConverter Module")
    try:
        import docling.document_converter as dc
        explore_module_attributes("docling.document_converter", dc)
        
        print("\nTesting DocumentConverter initialization:")
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        print("✅ DocumentConverter() - SUCCESS")
        print(f"   Available methods: {[m for m in dir(converter) if not m.startswith('_') and callable(getattr(converter, m))]}")
        
    except Exception as e:
        print(f"❌ Error with DocumentConverter: {e}")
    
    # Explore datamodel package
    print_section("Datamodel Package")
    try:
        import docling.datamodel as dm
        explore_module_attributes("docling.datamodel", dm)
    except ImportError as e:
        print(f"❌ Cannot import docling.datamodel: {e}")
    except Exception as e:
        print(f"❌ Error exploring datamodel: {e}")
    
    # Test base_models module (the main focus)
    print_section("Base Models Module (docling.datamodel.base_models)")
    try:
        import docling.datamodel.base_models as base_models
        explore_module_attributes("docling.datamodel.base_models", base_models)
        
        print("\nTesting specific imports from base_models:")
        test_import("from docling.datamodel.base_models import InputFormat", "InputFormat")
        test_import("from docling.datamodel.base_models import DocumentStream", "DocumentStream")
        
        # If InputFormat exists, show its values
        try:
            from docling.datamodel.base_models import InputFormat
            if hasattr(InputFormat, '__members__'):
                print(f"   InputFormat enum values: {list(InputFormat.__members__.keys())}")
        except:
            pass
            
    except ImportError as e:
        print(f"❌ Cannot import docling.datamodel.base_models: {e}")
        
        # Try alternative names
        print("\nTrying alternative module names:")
        test_import("import docling.datamodel.base_model", "base_model (singular)")
        test_import("import docling.datamodel.models", "models")
        
    except Exception as e:
        print(f"❌ Error exploring base_models: {e}")
    
    # Test pipeline options
    print_section("Pipeline Options Module")
    try:
        import docling.datamodel.pipeline_options as po
        explore_module_attributes("docling.datamodel.pipeline_options", po)
        
        print("\nTesting PdfPipelineOptions import:")
        test_import("from docling.datamodel.pipeline_options import PdfPipelineOptions", "PdfPipelineOptions")
        
    except ImportError as e:
        print(f"❌ Cannot import pipeline_options: {e}")
    except Exception as e:
        print(f"❌ Error exploring pipeline_options: {e}")
    
    # Test backend
    print_section("Backend Module")
    try:
        import docling.backend.pypdfium2_backend as backend
        explore_module_attributes("docling.backend.pypdfium2_backend", backend)
        
        print("\nTesting PyPdfiumDocumentBackend import:")
        test_import("from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend", "PyPdfiumDocumentBackend")
        
    except ImportError as e:
        print(f"❌ Cannot import pypdfium2_backend: {e}")
    except Exception as e:
        print(f"❌ Error exploring pypdfium2_backend: {e}")
    
    # Test all problematic imports from docling_extractor.py
    print_section("Testing All Problematic Imports from docling_extractor.py")
    
    problematic_imports = [
        ("from docling.document_converter import DocumentConverter, PdfFormatOption", "DocumentConverter + PdfFormatOption"),
        ("from docling.datamodel.base_models import InputFormat, DocumentStream", "InputFormat + DocumentStream"),
        ("from docling.datamodel.pipeline_options import PdfPipelineOptions", "PdfPipelineOptions"),
        ("from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend", "PyPdfiumDocumentBackend"),
    ]
    
    working_imports = []
    failing_imports = []
    
    for import_stmt, desc in problematic_imports:
        if test_import(import_stmt, desc):
            working_imports.append((import_stmt, desc))
        else:
            failing_imports.append((import_stmt, desc))
    
    # Summary
    print_section("SUMMARY")
    print(f"✅ Working imports ({len(working_imports)}):")
    for stmt, desc in working_imports:
        print(f"   {desc}")
        print(f"   {stmt}")
    
    print(f"\n❌ Failing imports ({len(failing_imports)}):")
    for stmt, desc in failing_imports:
        print(f"   {desc}")
        print(f"   {stmt}")
    
    if failing_imports:
        print(f"\n💡 Recommendations:")
        print("   1. Use only the working imports")
        print("   2. Simplify DocumentConverter initialization (no custom options)")
        print("   3. Use basic converter.convert() instead of complex pipeline options")
        print("   4. Consider using converter.convert_single() for single documents")

if __name__ == "__main__":
    main()