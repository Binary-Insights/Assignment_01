#!/usr/bin/env python3
"""
Manual LayoutParser Model Download and Fix

This script manually downloads LayoutParser models and places them correctly
to bypass the query parameter issue entirely.
"""

import os
import requests
import hashlib
from pathlib import Path
import json

def download_file(url, filepath, description="file"):
    """Download a file with progress indication."""
    print(f"📥 Downloading {description}...")
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\r📥 {description}: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')
    
    print(f"\n✅ {description} downloaded successfully!")
    return filepath

def setup_layoutparser_model():
    """Manually set up LayoutParser model files."""
    # Create the cache directory structure
    model_hash = "dgy9c10wykk4lq4"  # Hash for faster_rcnn_R_50_FPN_3x model
    cache_dir = Path.home() / ".torch" / "iopath_cache" / "s" / model_hash
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Using cache directory: {cache_dir}")
    
    # Model URLs without query parameters
    config_url = "https://www.dropbox.com/s/dgy9c10wykk4lq4/config.yml"
    model_url = "https://www.dropbox.com/s/dgy9c10wykk4lq4/model_final.pth"
    
    # Download files
    config_path = cache_dir / "config.yml"
    model_path = cache_dir / "model_final.pth"
    
    try:
        if not config_path.exists():
            download_file(config_url + "?dl=1", config_path, "config.yml")
        else:
            print("✅ config.yml already exists")
        
        if not model_path.exists():
            download_file(model_url + "?dl=1", model_path, "model_final.pth (330MB)")
        else:
            print("✅ model_final.pth already exists")
        
        print("\n🎉 Model files are ready!")
        return True
        
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        return False

def test_layoutparser():
    """Test LayoutParser with manually downloaded models."""
    try:
        import layoutparser as lp
        
        print("🧪 Testing LayoutParser with manually prepared models...")
        
        model = lp.models.Detectron2LayoutModel(
            'lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config'
        )
        
        print("✅ LayoutParser model loaded successfully!")
        print(f"Model type: {type(model)}")
        
        return True
        
    except Exception as e:
        print(f"❌ LayoutParser test failed: {e}")
        return False

def main():
    """Main function for manual model setup."""
    print("=== Manual LayoutParser Model Setup ===")
    print("This script manually downloads and places LayoutParser model files.")
    print()
    
    # Step 1: Download and setup models manually
    print("Step 1: Setting up LayoutParser models manually...")
    setup_success = setup_layoutparser_model()
    
    if not setup_success:
        print("❌ Manual setup failed.")
        return
    
    # Step 2: Test LayoutParser
    print("\nStep 2: Testing LayoutParser...")
    test_success = test_layoutparser()
    
    if test_success:
        print("\n🎊 SUCCESS! LayoutParser is now working with manually downloaded models!")
        print("You can now use your enhanced LayoutParser extractor.")
    else:
        print("\n⚠️  Manual setup completed but LayoutParser still has issues.")
        print("The fallback mode in your extractor will still work for basic functionality.")

if __name__ == "__main__":
    main()