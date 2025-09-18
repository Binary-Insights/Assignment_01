#!/usr/bin/env python3
"""
Install missing Docling dependencies
"""

import subprocess
import sys

def install_with_uv(package):
    """Install package with uv."""
    try:
        result = subprocess.run([
            "uv", "add", package
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print(f"✓ Successfully installed {package}")
            return True
        else:
            print(f"✗ Failed to install {package}: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error installing {package}: {e}")
        return False

def main():
    print("=== Installing Missing Docling Dependencies ===")
    
    # List of potential missing dependencies
    dependencies = [
        "pypdfium2",
        "pydantic",
        "requests",
        "pillow",
        "numpy"
    ]
    
    successful = 0
    for dep in dependencies:
        print(f"\nInstalling {dep}...")
        if install_with_uv(dep):
            successful += 1
    
    print(f"\n=== Installation Summary ===")
    print(f"Successfully installed: {successful}/{len(dependencies)} packages")
    
    if successful > 0:
        print("\nNow try running the Docling test again:")
        print("  python test_alternative_docling.py")

if __name__ == "__main__":
    main()