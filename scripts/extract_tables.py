#!/usr/bin/env python3
"""
Extract tables stage for DVC pipeline
Extracts and normalizes table data from documents
"""

import os
import json
import argparse
from pathlib import Path
import sys

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

try:
    from pdfplumber_tess_extractor import PDFPlumberTessExtractor
    from table_normalizer import TableNormalizer
except ImportError:
    print("⚠️  Table extraction modules not available")
    PDFPlumberTessExtractor = None
    TableNormalizer = None

def ensure_directories():
    """Create necessary directories"""
    dirs = [
        "data/parsed/nvda-20240128/tables",
        "data/parsed/nvda-20240128/tables_enhanced"
    ]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def extract_tables():
    """
    Extract tables from PDF documents
    """
    print("📊 Starting table extraction stage...")
    
    # Ensure directories exist
    ensure_directories()
    
    pdf_path = Path("data/raw/pdf/nvda-20240128.pdf")
    output_dir = Path("data/parsed/nvda-20240128/tables")
    enhanced_dir = Path("data/parsed/nvda-20240128/tables_enhanced")
    summary_path = Path("data/parsed/nvda-20240128/table_extraction_summary.json")
    
    if not pdf_path.exists() or pdf_path.stat().st_size < 1000:
        print("❌ PDF file not found or too small")
        # Create placeholder outputs
        summary = {
            "status": "failed",
            "reason": "PDF file not available",
            "tables_extracted": 0,
            "pages_processed": 0
        }
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        return
    
    success = False
    tables_extracted = 0
    pages_processed = 0
    
    if PDFPlumberTessExtractor:
        try:
            print("🔄 Extracting tables using PDFPlumberTessExtractor...")
            extractor = PDFPlumberTessExtractor()
            
            # Extract tables
            result = extractor.extract_from_pdf(str(pdf_path))
            
            if result.get("success", False):
                tables_data = result.get("tables", [])
                tables_extracted = len(tables_data)
                pages_processed = result.get("pages_processed", 0)
                
                # Save individual table files
                for i, table in enumerate(tables_data):
                    table_file = output_dir / f"table_{i+1:03d}.json"
                    with open(table_file, 'w', encoding='utf-8') as f:
                        json.dump(table, f, indent=2)
                
                # Save combined tables
                all_tables_file = output_dir / "all_tables.json"
                with open(all_tables_file, 'w', encoding='utf-8') as f:
                    json.dump(tables_data, f, indent=2)
                
                success = True
                print(f"✅ Extracted {tables_extracted} tables from {pages_processed} pages")
                
                # Apply table normalization if available
                if TableNormalizer:
                    try:
                        normalizer = TableNormalizer()
                        for i, table in enumerate(tables_data):
                            normalized = normalizer.normalize_table(table)
                            enhanced_file = enhanced_dir / f"table_{i+1:03d}_enhanced.json"
                            with open(enhanced_file, 'w', encoding='utf-8') as f:
                                json.dump(normalized, f, indent=2)
                        print(f"✅ Enhanced {len(tables_data)} tables")
                    except Exception as e:
                        print(f"⚠️  Table normalization failed: {e}")
                
            else:
                print("❌ Table extraction failed")
                
        except Exception as e:
            print(f"❌ PDFPlumberTessExtractor failed: {e}")
    
    # Fallback: Try pdfplumber directly
    if not success:
        try:
            import pdfplumber
            
            print("🔄 Fallback: Using pdfplumber directly...")
            tables_data = []
            
            with pdfplumber.open(pdf_path) as pdf:
                pages_processed = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table_idx, table in enumerate(page_tables):
                            table_data = {
                                "page": page_num + 1,
                                "table_index": table_idx,
                                "data": table,
                                "extraction_method": "pdfplumber_direct"
                            }
                            tables_data.append(table_data)
                
                tables_extracted = len(tables_data)
                
                # Save tables
                if tables_data:
                    for i, table in enumerate(tables_data):
                        table_file = output_dir / f"table_{i+1:03d}.json"
                        with open(table_file, 'w', encoding='utf-8') as f:
                            json.dump(table, f, indent=2)
                    
                    all_tables_file = output_dir / "all_tables.json"
                    with open(all_tables_file, 'w', encoding='utf-8') as f:
                        json.dump(tables_data, f, indent=2)
                    
                    success = True
                    print(f"✅ Extracted {tables_extracted} tables using pdfplumber directly")
                
        except ImportError:
            print("⚠️  pdfplumber not available")
        except Exception as e:
            print(f"❌ Direct pdfplumber extraction failed: {e}")
    
    # Create summary
    summary = {
        "status": "success" if success else "failed",
        "tables_extracted": tables_extracted,
        "pages_processed": pages_processed,
        "output_directory": str(output_dir),
        "enhanced_directory": str(enhanced_dir),
        "extraction_method": "PDFPlumberTessExtractor" if PDFPlumberTessExtractor and success else "pdfplumber_direct"
    }
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"📊 Table extraction stage completed - {summary['status']}")

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Extract tables for DVC pipeline")
    parser.add_argument("--force", action="store_true", help="Force re-processing")
    args = parser.parse_args()
    
    extract_tables()

if __name__ == "__main__":
    main()