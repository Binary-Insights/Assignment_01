#!/usr/bin/env python3
"""
Debug Docling installation - check what's actually available
"""

print("=== Docling Installation Debug ===")

# Check basic docling
try:
    import docling
    print("✓ docling imported successfully")
    print(f"  Location: {docling.__file__ if hasattr(docling, '__file__') else 'unknown'}")
    print(f"  Version: {docling.__version__ if hasattr(docling, '__version__') else 'unknown'}")
except ImportError as e:
    print(f"✗ docling import failed: {e}")

# Check docling_parse
try:
    import docling_parse
    print("✓ docling_parse imported successfully")
    print(f"  Location: {docling_parse.__file__ if hasattr(docling_parse, '__file__') else 'unknown'}")
    print(f"  Available modules: {dir(docling_parse)}")
except ImportError as e:
    print(f"✗ docling_parse import failed: {e}")

# Check specific module that's failing
try:
    from docling_parse import pdf_parsers
    print("✓ docling_parse.pdf_parsers imported successfully")
except ImportError as e:
    print(f"✗ docling_parse.pdf_parsers import failed: {e}")

# Check what's in docling package
try:
    import docling
    import pkgutil
    print("\n=== Available docling submodules ===")
    for importer, modname, ispkg in pkgutil.walk_packages(docling.__path__, docling.__name__ + "."):
        print(f"  {modname}")
except Exception as e:
    print(f"Error exploring docling: {e}")

# Check installed packages
try:
    import subprocess
    import sys
    result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        docling_packages = [line for line in lines if 'docling' in line.lower()]
        print(f"\n=== Installed docling-related packages ===")
        for pkg in docling_packages:
            print(f"  {pkg}")
    else:
        print("Failed to get package list")
except Exception as e:
    print(f"Error getting package list: {e}")