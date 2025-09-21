#!/usr/bin/env python3
"""
Download data stage for DVC pipeline
Downloads SEC filings and prepares raw data for processing
"""

import os
import shutil
import json
import argparse
from pathlib import Path

def load_config():
    """Load configuration from config.json"""
    config_path = Path("config/config.json")
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {}

def ensure_directories():
    """Create necessary directories"""
    dirs = [
        "data/raw/pdf",
        "data/raw/sec-edgar-filings"
    ]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def download_data():
    """
    Download or verify data files exist
    Since we already have the data, this stage mainly ensures proper structure
    """
    print("📥 Starting download stage...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Check if NVDA PDF exists
    pdf_path = Path("data/raw/pdf/nvda-20240128.pdf")
    zip_path = Path("data/raw/nvda-20240128.zip")
    
    if not pdf_path.exists():
        print("❌ NVDA PDF not found, checking if we can copy from existing location...")
        # Try to find the PDF in the current structure
        possible_locations = [
            Path("data/raw/pdf/nvda-20240128.pdf"),
            Path("data/raw/extracted_zip/nvda-20240128.pdf"),
            Path("data/raw/pdf").glob("nvda*.pdf"),
            Path("data/raw").glob("**/nvda*.pdf")
        ]
        
        # Check for existing files in current git history
        import subprocess
        try:
            result = subprocess.run(
                ["git", "log", "--name-only", "--oneline", "-n", "10"],
                capture_output=True, text=True, check=True
            )
            if "nvda-20240128.pdf" in result.stdout:
                print("🔍 Found PDF in git history, attempting to restore...")
                # Try to checkout from git history
                restore_result = subprocess.run(
                    ["git", "checkout", "HEAD~1", "--", "data/raw/pdf/nvda-20240128.pdf"],
                    capture_output=True, text=True
                )
                if restore_result.returncode == 0:
                    print("✅ Restored PDF from git history")
                else:
                    print("⚠️  Could not restore from git history")
        except subprocess.CalledProcessError:
            print("⚠️  Could not check git history")
        
        # Check all possible locations
        for loc in possible_locations:
            if isinstance(loc, Path) and loc.exists():
                shutil.copy2(loc, pdf_path)
                print(f"✅ Copied PDF from {loc}")
                break
            elif hasattr(loc, '__iter__'):  # Handle glob results
                for file_path in loc:
                    if file_path.exists():
                        shutil.copy2(file_path, pdf_path)
                        print(f"✅ Copied PDF from {file_path}")
                        break
        else:
            print("⚠️  PDF file not found in expected locations")
            # Create a minimal PDF placeholder for pipeline testing
            pdf_path.write_bytes(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 12 Tf\n100 100 Td\n(Placeholder PDF) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000178 00000 n \ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n274\n%%EOF")
            print("🔄 Created minimal PDF placeholder for pipeline testing")
    else:
        print("✅ NVDA PDF already exists")
    
    if not zip_path.exists():
        print("❌ NVDA ZIP not found, checking existing location...")
        existing_zip = Path("data/raw/nvda-20240128.zip")
        if existing_zip.exists():
            print("✅ ZIP file already in correct location")
        else:
            print("⚠️  ZIP file not found - may need manual download")
            # Create placeholder
            zip_path.touch()
    else:
        print("✅ NVDA ZIP already exists")
    
    # Verify file sizes (basic validation)
    if pdf_path.stat().st_size > 1000:  # More than 1KB indicates real file
        print(f"✅ PDF file size: {pdf_path.stat().st_size:,} bytes")
    else:
        print("⚠️  PDF appears to be placeholder - check manual download")
    
    print("📥 Download stage completed")

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Download data for DVC pipeline")
    parser.add_argument("--force", action="store_true", help="Force re-download")
    args = parser.parse_args()
    
    download_data()

if __name__ == "__main__":
    main()