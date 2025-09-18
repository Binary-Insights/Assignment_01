#!/usr/bin/env python3
"""
Explore Docling modules to see what's available for import
"""

import inspect
import pkgutil

def explore_module(module_path, description):
    """Explore a module and print available attributes."""
    print(f"\n=== {description} ===")
    print(f"Module: {module_path}")
    
    try:
        # Try to import the module
        module = __import__(module_path, fromlist=[''])
        print("✓ Module imported successfully")
        
        # Get all attributes
        all_attrs = dir(module)
        public_attrs = [attr for attr in all_attrs if not attr.startswith('_')]
        
        print(f"Total attributes: {len(all_attrs)}")
        print(f"Public attributes: {len(public_attrs)}")
        
        if public_attrs:
            print("\nPublic attributes:")
            for attr in sorted(public_attrs):
                attr_obj = getattr(module, attr)
                attr_type = type(attr_obj).__name__
                
                if inspect.isclass(attr_obj):
                    print(f"  📦 {attr} (class)")
                elif inspect.isfunction(attr_obj):
                    print(f"  🔧 {attr} (function)")
                elif inspect.ismodule(attr_obj):
                    print(f"  📁 {attr} (module)")
                else:
                    print(f"  📋 {attr} ({attr_type})")
        
        # Check if it has __all__
        if hasattr(module, '__all__'):
            print(f"\n__all__ exports: {module.__all__}")
        
        # Try to get docstring
        if hasattr(module, '__doc__') and module.__doc__:
            print(f"\nDocstring preview: {module.__doc__[:200]}...")
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
    except Exception as e:
        print(f"⚠ Error exploring module: {e}")

def test_specific_imports():
    """Test specific imports that are failing."""
    print("\n=== Testing Specific Imports ===")
    
    imports_to_test = [
        ("from docling.datamodel.base_models import InputFormat", "InputFormat"),
        ("from docling.datamodel.base_models import DocumentStream", "DocumentStream"),
        ("from docling.document_converter import PdfFormatOption", "PdfFormatOption"),
        ("from docling.datamodel.pipeline_options import PdfPipelineOptions", "PdfPipelineOptions"),
        ("from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend", "PyPdfiumDocumentBackend"),
    ]
    
    for import_stmt, name in imports_to_test:
        try:
            exec(import_stmt)
            print(f"✓ {name}: SUCCESS")
        except ImportError as e:
            print(f"✗ {name}: FAILED - {e}")
        except Exception as e:
            print(f"⚠ {name}: ERROR - {e}")

def main():
    print("=== Exploring Docling Modules ===")
    
    # First, let's see what's in the main docling package
    explore_module("docling", "Main Docling Package")
    
    # Explore datamodel
    explore_module("docling.datamodel", "Datamodel Package")
    
    # Try to explore base_models (note: it might be base_models, not base_model)
    explore_module("docling.datamodel.base_models", "Base Models Module")
    
    # Try alternative spellings
    explore_module("docling.datamodel.base_model", "Base Model Module (singular)")
    
    # Explore document converter
    explore_module("docling.document_converter", "Document Converter Module")
    
    # Explore pipeline options
    explore_module("docling.datamodel.pipeline_options", "Pipeline Options Module")
    
    # Explore backend
    explore_module("docling.backend", "Backend Package")
    explore_module("docling.backend.pypdfium2_backend", "PyPdfium2 Backend Module")
    
    # Test specific imports
    test_specific_imports()
    
    # Try to find what's actually available in datamodel
    print("\n=== Exploring Datamodel Submodules ===")
    try:
        import docling.datamodel
        if hasattr(docling.datamodel, '__path__'):
            for importer, modname, ispkg in pkgutil.iter_modules(docling.datamodel.__path__):
                print(f"  📁 docling.datamodel.{modname} {'(package)' if ispkg else '(module)'}")
    except Exception as e:
        print(f"Error exploring datamodel submodules: {e}")

if __name__ == "__main__":
    main()