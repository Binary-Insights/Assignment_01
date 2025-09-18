#!/usr/bin/env python3
"""
Check docling-parse structure and find the correct module name
"""

print("=== Exploring docling_parse structure ===")

try:
    import docling_parse
    print("✓ docling_parse imported successfully")
    
    # Check what's actually in docling_parse
    import pkgutil
    print("\nAvailable docling_parse submodules:")
    for importer, modname, ispkg in pkgutil.walk_packages(docling_parse.__path__, docling_parse.__name__ + "."):
        print(f"  {modname}")
        
except Exception as e:
    print(f"✗ Error exploring docling_parse: {e}")

# Try to find what PDF parsing modules are available
print("\n=== Looking for PDF parsing modules ===")

# Check different possible module names
possible_modules = [
    'docling_parse.pdf_parsers',
    'docling_parse.pdf_parser', 
    'docling_parse.parsers',
    'docling_parse.parser',
    'docling_parse.pdf',
    'docling_parse.v4',
    'docling_parse.v2'
]

for module_name in possible_modules:
    try:
        __import__(module_name)
        print(f"✓ {module_name} - FOUND")
    except ImportError as e:
        print(f"✗ {module_name} - not found: {e}")

# Check what's in the main docling_parse module
try:
    import docling_parse
    print(f"\nAttributes in docling_parse: {dir(docling_parse)}")
except Exception as e:
    print(f"Error checking attributes: {e}")

print("\n=== Package version information ===")
try:
    import subprocess
    import sys
    result = subprocess.run([sys.executable, "-m", "pip", "show", "docling"], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("Docling package info:")
        print(result.stdout)
    
    result = subprocess.run([sys.executable, "-m", "pip", "show", "docling-parse"], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("Docling-parse package info:")
        print(result.stdout)
        
except Exception as e:
    print(f"Error getting package info: {e}")