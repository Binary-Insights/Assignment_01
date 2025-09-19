#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append('src')

def test_layout_parser():
    print("=== Testing LayoutParser with Disabled Fallback ===")
    
    try:
        from layout_parser_extractor import LayoutParserExtractor
        print("✓ Module imported successfully")
        
        # Test initialization
        print("Testing initialization...")
        extractor = LayoutParserExtractor()
        print("✅ LayoutParser initialized - model is working!")
        
        # Test extraction if PDF exists
        pdf_path = Path("data/raw/pdf/nvda-20240128.pdf")
        if pdf_path.exists():
            print(f"Testing extraction on {pdf_path.name}...")
            results = extractor.extract_from_pdf(str(pdf_path))
            if results:
                summary = results['extraction_summary']
                print(f"✅ Extraction completed:")
                print(f"  Pages: {summary['total_pages_processed']}")
                print(f"  Blocks: {summary['total_blocks_detected']}")
                print(f"  Success rate: {summary['success_rate']:.1f}%")
            else:
                print("❌ Extraction returned None")
        else:
            print(f"⚠️ PDF not found: {pdf_path}")
            
    except RuntimeError as e:
        print(f"❌ RuntimeError (expected with disabled fallback): {e}")
        print("💡 This confirms fallback mode is properly disabled")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_layout_parser()
    exit(0 if success else 1)
