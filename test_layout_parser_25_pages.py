#!/usr/bin/env python3
"""
Test LayoutParser extractor with first 25 pages only
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.append('src')

def test_layout_parser_25_pages():
    """Test LayoutParser with limited pages for faster testing"""
    
    print("=== Testing LayoutParser with First 25 Pages ===")
    
    try:
        from layout_parser_extractor import LayoutParserExtractor
        print("✓ LayoutParser module imported successfully")
        
        # Initialize extractor in testing mode
        print("Initializing LayoutParser in testing mode (25 pages max)...")
        extractor = LayoutParserExtractor(
            use_camelot=True,
            use_layoutlmv3=True, 
            max_pages_testing=25  # Only process first 25 pages
        )
        print("✅ LayoutParser initialized successfully!")
        
        # Test extraction if PDF exists
        pdf_path = Path("data/raw/pdf/nvda-20240128.pdf")
        if pdf_path.exists():
            print(f"\n📄 Testing extraction on {pdf_path.name}...")
            print(f"   Processing only first 25 pages for faster testing")
            
            results = extractor.extract_from_pdf(str(pdf_path))
            
            if results:
                summary = results['extraction_summary']
                print(f"\n✅ Extraction completed successfully!")
                print(f"  📊 Results Summary:")
                print(f"     Pages processed: {summary['total_pages_processed']}")
                print(f"     Total blocks detected: {summary['total_blocks_detected']}")
                print(f"     Success rate: {summary['success_rate']:.1f}%")
                print(f"     Processing time: {summary['processing_time_seconds']:.2f}s")
                print(f"     Blocks by type: {summary['blocks_by_type']}")
                
                # Show enhancement statistics
                if extractor.stats.get('camelot_tables', 0) > 0:
                    print(f"     Camelot tables extracted: {extractor.stats['camelot_tables']}")
                if extractor.stats.get('layoutlmv3_captions', 0) > 0:
                    print(f"     LayoutLMv3 captions: {extractor.stats['layoutlmv3_captions']}")
                
                print(f"\n📁 Output saved to: data/parsed/layout_parser/{pdf_path.stem}/")
                return True
            else:
                print("❌ Extraction returned None - check logs for errors")
                return False
                
        else:
            print(f"❌ PDF not found: {pdf_path}")
            print("💡 Place your PDF file in data/raw/pdf/ directory")
            return False
            
    except RuntimeError as e:
        print(f"❌ LayoutParser initialization failed: {e}")
        print("💡 This confirms fallback mode is properly disabled")
        print("💡 Try one of these alternatives:")
        print("   1. Fix Detectron2/LayoutParser installation")
        print("   2. Use basic_layout_extractor.py instead")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_different_page_limits():
    """Test with different page limits"""
    
    print("\n=== Testing Different Page Limits ===")
    
    test_cases = [
        (5, "Quick test - 5 pages"),
        (10, "Medium test - 10 pages"), 
        (25, "Standard test - 25 pages"),
        (None, "Full processing - all pages")
    ]
    
    for max_pages, description in test_cases:
        print(f"\n🧪 {description}")
        
        try:
            from layout_parser_extractor import LayoutParserExtractor
            
            extractor = LayoutParserExtractor(
                max_pages_testing=max_pages,
                use_camelot=False,  # Disable for faster testing
                use_layoutlmv3=False
            )
            
            print(f"   ✓ Extractor configured for {max_pages if max_pages else 'all'} pages")
            
        except Exception as e:
            print(f"   ❌ Configuration failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting LayoutParser Testing...")
    
    # Test with 25 pages
    success = test_layout_parser_25_pages()
    
    # Test different configurations
    test_different_page_limits()
    
    print(f"\n{'✅ Testing completed successfully!' if success else '❌ Testing failed - check errors above'}")
    
    if success:
        print("\n💡 Next steps:")
        print("   • Check output in data/parsed/layout_parser/")
        print("   • Increase max_pages_testing for more pages")
        print("   • Set max_pages_testing=None for full document processing")
    
    exit(0 if success else 1)