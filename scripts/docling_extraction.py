#!/usr/bin/env python3
"""
Docling extraction stage for DVC pipeline
Extract content using Docling framework
"""

import os
import json
import argparse
from pathlib import Path
import sys

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

try:
    from docling_extractor import DoclingExtractor
except ImportError:
    print("⚠️  DoclingExtractor not available")
    DoclingExtractor = None

def ensure_directories():
    """Create necessary directories"""
    dirs = [
        "data/parsed/docling",
        "data/parsed/comparison"
    ]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def docling_extraction():
    """
    Extract content using Docling framework
    """
    print("🔬 Starting Docling extraction stage...")
    
    # Ensure directories exist
    ensure_directories()
    
    pdf_path = Path("data/raw/pdf/nvda-20240128.pdf")
    output_dir = Path("data/parsed/docling")
    comparison_path = Path("data/parsed/comparison/docling_layout_comparison.json")
    
    if not pdf_path.exists() or pdf_path.stat().st_size < 1000:
        print("❌ PDF file not found or too small")
        # Create placeholder outputs
        comparison = {
            "status": "failed",
            "reason": "PDF file not available",
            "tables_detected": 0,
            "pages_processed": 0
        }
        with open(comparison_path, 'w') as f:
            json.dump(comparison, f, indent=2)
        return
    
    success = False
    tables_detected = 0
    pages_processed = 0
    extraction_data = {}
    
    if DoclingExtractor:
        try:
            print("🔄 Running Docling extraction...")
            extractor = DoclingExtractor()
            
            # Extract content using Docling
            result = extractor.extract_from_pdf(str(pdf_path))
            
            if result.get("success", False):
                extraction_data = result
                tables_detected = len(result.get("tables", []))
                pages_processed = result.get("pages_processed", 0)
                
                # Save Docling extraction results
                docling_file = output_dir / "docling_extraction.json"
                with open(docling_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                
                # Save tables separately
                if result.get("tables"):
                    tables_file = output_dir / "docling_tables.json"
                    with open(tables_file, 'w', encoding='utf-8') as f:
                        json.dump(result["tables"], f, indent=2)
                
                # Save text content
                if result.get("text"):
                    text_file = output_dir / "docling_text.txt"
                    with open(text_file, 'w', encoding='utf-8') as f:
                        f.write(result["text"])
                
                success = True
                print(f"✅ Docling extracted {tables_detected} tables from {pages_processed} pages")
                
                # Create extraction log
                log_file = output_dir / "docling_extraction_log.txt"
                with open(log_file, 'w') as f:
                    f.write(f"Docling Extraction Log\n")
                    f.write(f"=====================\n")
                    f.write(f"Pages processed: {pages_processed}\n")
                    f.write(f"Tables detected: {tables_detected}\n")
                    f.write(f"Text length: {len(result.get('text', ''))}\n")
                    f.write(f"Success: {success}\n")
                
            else:
                print("❌ Docling extraction failed")
                
        except Exception as e:
            print(f"❌ DoclingExtractor failed: {e}")
    
    # Fallback: Create placeholder results
    if not success:
        print("🔄 Creating placeholder Docling results...")
        
        placeholder_result = {
            "status": "fallback",
            "extraction_method": "placeholder",
            "pages_processed": 0,
            "tables": [],
            "text": "",
            "metadata": {
                "extraction_time": 0,
                "confidence": 0.0
            }
        }
        
        # Save placeholder
        docling_file = output_dir / "docling_extraction.json"
        with open(docling_file, 'w', encoding='utf-8') as f:
            json.dump(placeholder_result, f, indent=2)
        
        print("⚠️  Created placeholder Docling results")
    
    # Create layout comparison
    comparison = {
        "status": "success" if success else "failed",
        "tables_detected": tables_detected,
        "pages_processed": pages_processed,
        "output_directory": str(output_dir),
        "extraction_method": "DoclingExtractor" if DoclingExtractor and success else "placeholder",
        "confidence_score": extraction_data.get("confidence", 0.0),
        "processing_time": extraction_data.get("processing_time", 0),
        "quality_metrics": {
            "tables_per_page": tables_detected / max(pages_processed, 1) if pages_processed > 0 else 0,
            "text_extracted": len(extraction_data.get("text", "")) > 0,
            "extraction_success": success
        }
    }
    
    with open(comparison_path, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    print(f"🔬 Docling extraction stage completed - {comparison['status']}")

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Docling extraction for DVC pipeline")
    parser.add_argument("--force", action="store_true", help="Force re-processing")
    args = parser.parse_args()
    
    docling_extraction()

if __name__ == "__main__":
    main()