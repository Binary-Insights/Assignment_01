#!/usr/bin/env python3
"""
Parse documents stage for DVC pipeline
Extracts text content from PDF documents
"""

import os
import json
import argparse
from pathlib import Path
import sys

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

try:
    from text_extractor import TextExtractor
except ImportError:
    print("⚠️  TextExtractor not available, using fallback")
    TextExtractor = None

def ensure_directories():
    """Create necessary directories"""
    dirs = [
        "data/parsed/nvda-20240128/text",
        "data/parsed/nvda-20240128"
    ]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def parse_documents():
    """
    Parse PDF documents and extract text content
    """
    print("📄 Starting parse stage...")
    
    # Ensure directories exist
    ensure_directories()
    
    pdf_path = Path("data/raw/pdf/nvda-20240128.pdf")
    output_dir = Path("data/parsed/nvda-20240128/text")
    summary_path = Path("data/parsed/nvda-20240128/extraction_summary.json")
    
    if not pdf_path.exists() or pdf_path.stat().st_size < 1000:
        print("❌ PDF file not found or too small")
        # Create placeholder outputs
        summary = {
            "status": "failed",
            "reason": "PDF file not available",
            "pages_processed": 0,
            "text_files_created": 0
        }
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        return
    
    # Try to extract text using available methods
    success = False
    pages_processed = 0
    
    if TextExtractor:
        try:
            extractor = TextExtractor()
            result = extractor.extract_text(pdf_path)
            if result and len(result) > 100:
                # Save text to file
                text_file = output_dir / "extracted_text.txt"
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(result)
                success = True
                pages_processed = 1  # Simplified for now
                print("✅ Text extraction completed using TextExtractor")
        except Exception as e:
            print(f"⚠️  TextExtractor failed: {e}")
    
    # Fallback: create basic text extraction using pypdf or similar
    if not success:
        try:
            import pypdf
            with open(pdf_path, 'rb') as file:
                reader = pypdf.PdfReader(file)
                pages_processed = len(reader.pages)
                
                all_text = []
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    all_text.append(text)
                    
                    # Save individual page text
                    page_file = output_dir / f"page_{i+1:03d}.txt"
                    with open(page_file, 'w', encoding='utf-8') as f:
                        f.write(text)
                
                # Save combined text
                combined_file = output_dir / "extracted_text.txt"
                with open(combined_file, 'w', encoding='utf-8') as f:
                    f.write("\n\n".join(all_text))
                
                success = True
                print(f"✅ Text extraction completed using pypdf ({pages_processed} pages)")
                
        except ImportError:
            print("⚠️  pypdf not available")
        except Exception as e:
            print(f"❌ Text extraction failed: {e}")
    
    # Create summary
    summary = {
        "status": "success" if success else "failed",
        "pages_processed": pages_processed,
        "text_files_created": len(list(output_dir.glob("*.txt"))) if output_dir.exists() else 0,
        "output_directory": str(output_dir),
        "extraction_method": "TextExtractor" if TextExtractor and success else "pypdf_fallback"
    }
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"📄 Parse stage completed - {summary['status']}")

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Parse documents for DVC pipeline")
    parser.add_argument("--force", action="store_true", help="Force re-processing")
    args = parser.parse_args()
    
    parse_documents()

if __name__ == "__main__":
    main()