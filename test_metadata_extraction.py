"""
Test Metadata Extraction System

This script demonstrates the metadata extraction and staging system
by processing existing PDF extraction results and converting them
to unified JSONL format with provenance tracking.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / 'src'))

from metadata_extractor import MetadataExtractor


def test_metadata_extraction():
    """Test the metadata extraction system."""
    print("=== Testing Metadata Extraction System ===")
    print()
    
    # Check if we have existing extraction results
    parsed_dir = Path("data/parsed")
    if not parsed_dir.exists():
        print("❌ No parsed data directory found.")
        print("Please run the extraction methods first:")
        print("  1. python src/docling_extractor.py")
        print("  2. python src/layout_parser_extractor.py")  
        print("  3. python src/traditional_extractor.py")
        return
    
    # Check for extraction results
    methods_found = []
    for method in ['docling', 'layout_parser', 'traditional']:
        method_dir = parsed_dir / method
        if method_dir.exists() and any(method_dir.iterdir()):
            methods_found.append(method)
    
    if not methods_found:
        print("❌ No extraction results found in data/parsed/")
        print("Please run at least one extraction method first.")
        return
    
    print(f"✓ Found extraction results for: {', '.join(methods_found)}")
    print()
    
    # Initialize metadata extractor
    print("Initializing metadata extractor...")
    extractor = MetadataExtractor()
    
    # Process all documents
    print("Processing all documents...")
    results = extractor.process_all_documents()
    
    # Display results
    print("\n=== Processing Results ===")
    
    if results.get('status') == 'no_files':
        print("❌ No PDF files found in data/raw/pdf/")
        print("Please add PDF files to process.")
        return
    
    print(f"✓ Documents processed: {results['documents_processed']}")
    print(f"✓ Total blocks extracted: {extractor.stats['total_blocks_extracted']}")
    print(f"✓ Processing time: {results['processing_time_seconds']:.2f} seconds")
    
    # Show method breakdown
    if extractor.stats['blocks_by_method']:
        print("\nBlocks by extraction method:")
        for method, count in extractor.stats['blocks_by_method'].items():
            print(f"  • {method}: {count} blocks")
    
    # Show type breakdown
    if extractor.stats['blocks_by_type']:
        print("\nBlocks by content type:")
        for block_type, count in extractor.stats['blocks_by_type'].items():
            print(f"  • {block_type}: {count} blocks")
    
    print("\n=== Generated Outputs ===")
    
    # Check generated files
    metadata_dir = Path("data/metadata")
    staged_dir = Path("data/staged")
    
    # Document metadata
    doc_registry = metadata_dir / "documents" / "doc_registry.json"
    if doc_registry.exists():
        print(f"✓ Document registry: {doc_registry}")
    
    # JSONL files
    jsonl_dirs = [
        metadata_dir / "blocks" / "docling",
        metadata_dir / "blocks" / "layout_parser", 
        metadata_dir / "blocks" / "traditional",
        metadata_dir / "blocks" / "unified"
    ]
    
    for jsonl_dir in jsonl_dirs:
        if jsonl_dir.exists():
            jsonl_files = list(jsonl_dir.glob("*.jsonl"))
            if jsonl_files:
                print(f"✓ {jsonl_dir.name} JSONL files: {len(jsonl_files)}")
    
    # Staged outputs
    if staged_dir.exists():
        markdown_files = list((staged_dir / "markdown").glob("*.md"))
        json_files = list((staged_dir / "json").glob("*.json"))
        
        if markdown_files:
            print(f"✓ Markdown files with provenance: {len(markdown_files)}")
        if json_files:
            print(f"✓ JSON export files: {len(json_files)}")
    
    print("\n=== Directory Structure Created ===")
    print("data/metadata/")
    print("  ├── documents/           # Document-level metadata")
    print("  ├── blocks/             # Block-level JSONL files")
    print("  │   ├── docling/        # Method-specific blocks")
    print("  │   ├── layout_parser/")
    print("  │   ├── traditional/")
    print("  │   └── unified/        # Cross-method unified blocks")
    print("  ├── provenance/         # Processing logs and configs")
    print("  └── schemas/            # JSON schemas")
    print()
    print("data/staged/")
    print("  ├── markdown/           # Markdown with embedded metadata")
    print("  ├── json/               # Comprehensive JSON exports")
    print("  └── search_index/       # Future: search-optimized formats")
    
    print("\n=== Next Steps ===")
    print("1. Examine JSONL files for block-level metadata")
    print("2. Review markdown files with embedded provenance")
    print("3. Use JSON exports for downstream analysis")
    print("4. Query metadata for cross-method comparisons")
    print("5. Build search indices from structured metadata")


def examine_sample_outputs():
    """Examine sample output files to show the metadata structure."""
    print("\n=== Sample Output Examination ===")
    
    # Check for sample files
    metadata_dir = Path("data/metadata")
    staged_dir = Path("data/staged")
    
    # Show sample document metadata
    doc_registry = metadata_dir / "documents" / "doc_registry.json"
    if doc_registry.exists():
        print("\n📄 Sample Document Registry:")
        try:
            import json
            with open(doc_registry, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            
            for doc_id, doc_info in list(registry.items())[:1]:  # Show first document
                print(f"Document ID: {doc_id}")
                print(f"  Name: {doc_info.get('doc_name', 'Unknown')}")
                print(f"  Methods: {doc_info.get('extraction_methods', [])}")
                print(f"  Pages: {doc_info.get('total_pages', 0)}")
                print(f"  Checksum: {doc_info.get('checksum', '')[:16]}...")
                break
        except Exception as e:
            print(f"Error reading registry: {e}")
    
    # Show sample JSONL structure
    unified_dir = metadata_dir / "blocks" / "unified"
    if unified_dir.exists():
        jsonl_files = list(unified_dir.glob("*.jsonl"))
        if jsonl_files:
            print(f"\n📋 Sample JSONL Block (from {jsonl_files[0].name}):")
            try:
                with open(jsonl_files[0], 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line:
                        import json
                        block = json.loads(first_line)
                        print(f"  Block ID: {block.get('block_id', 'Unknown')}")
                        print(f"  Type: {block.get('block_type', 'Unknown')}")
                        print(f"  Method: {block.get('extraction_method', 'Unknown')}")
                        print(f"  Confidence: {block.get('confidence', 0):.2f}")
                        print(f"  Text Length: {len(block.get('content', {}).get('text', ''))}")
            except Exception as e:
                print(f"Error reading JSONL: {e}")
    
    # Show sample markdown structure
    markdown_dir = staged_dir / "markdown"
    if markdown_dir.exists():
        md_files = list(markdown_dir.glob("*.md"))
        if md_files:
            print(f"\n📝 Sample Markdown Structure (from {md_files[0].name}):")
            try:
                with open(md_files[0], 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:20]  # First 20 lines
                    for line in lines:
                        print(f"  {line.rstrip()}")
                    if len(lines) == 20:
                        print("  ... (truncated)")
            except Exception as e:
                print(f"Error reading markdown: {e}")


if __name__ == "__main__":
    try:
        test_metadata_extraction()
        examine_sample_outputs()
        
        print("\n✅ Metadata extraction system test completed!")
        print("\nThe metadata system provides:")
        print("• Unified schema across all extraction methods")
        print("• JSONL format for scalable processing")
        print("• Provenance tracking for reproducibility")
        print("• Quality metrics for assessment")
        print("• Cross-method comparison capabilities")
        print("• Search-optimized structured formats")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        raise