#!/usr/bin/env python3
"""
Fix LayoutParser Model Download Issue

This script fixes the common issue where LayoutParser downloads model files
with query parameters (?dl=1) in the filename, which causes Detectron2 to fail
when loading the checkpoints.
"""

import os
import glob
import shutil
from pathlib import Path

def fix_layoutparser_cache():
    """Fix all LayoutParser model files in the torch cache."""
    cache_base = Path.home() / ".torch" / "iopath_cache" / "s"
    
    if not cache_base.exists():
        print("No LayoutParser cache directory found.")
        return
    
    fixed_count = 0
    
    # Find all cache directories
    for cache_dir in cache_base.iterdir():
        if cache_dir.is_dir():
            print(f"Checking cache directory: {cache_dir}")
            
            # Look for files with query parameters
            problematic_files = list(cache_dir.glob("*?dl=1*"))
            
            for problem_file in problematic_files:
                # Create clean filename by removing query parameters
                clean_name = problem_file.name.split('?')[0]
                clean_path = cache_dir / clean_name
                
                if problem_file.name.endswith('.lock'):
                    # Just remove lock files
                    print(f"Removing lock file: {problem_file}")
                    problem_file.unlink()
                    continue
                
                # Check if clean file already exists
                if clean_path.exists():
                    print(f"Clean file already exists: {clean_path}")
                    print(f"Removing problematic file: {problem_file}")
                    problem_file.unlink()
                else:
                    print(f"Renaming: {problem_file.name} → {clean_name}")
                    problem_file.rename(clean_path)
                
                fixed_count += 1
    
    print(f"\nFixed {fixed_count} problematic files.")
    return fixed_count > 0

def test_layoutparser_model():
    """Test if LayoutParser can now load models successfully."""
    try:
        import layoutparser as lp
        print("\nTesting LayoutParser model initialization...")
        
        # Try to create a model
        model = lp.models.Detectron2LayoutModel(
            'lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config'
        )
        print("✅ LayoutParser model created successfully!")
        print(f"Model type: {type(model)}")
        return True
        
    except Exception as e:
        print(f"❌ LayoutParser model initialization failed: {e}")
        return False

def main():
    """Main function to fix LayoutParser and test it."""
    print("=== LayoutParser Model Fix Utility ===")
    print("This script fixes the common LayoutParser download issue.")
    print()
    
    # Fix the cache files
    print("Step 1: Fixing LayoutParser cache files...")
    fixed_any = fix_layoutparser_cache()
    
    if not fixed_any:
        print("No problematic files found in cache.")
    
    # Test the model
    print("\nStep 2: Testing LayoutParser model...")
    success = test_layoutparser_model()
    
    if success:
        print("\n🎉 LayoutParser is now working correctly!")
        print("You can now use LayoutParser for document layout analysis.")
    else:
        print("\n⚠️  LayoutParser still has issues.")
        print("You may need to clear the cache completely and try again.")
        print("Run: rm -rf ~/.torch/iopath_cache/")

if __name__ == "__main__":
    main()