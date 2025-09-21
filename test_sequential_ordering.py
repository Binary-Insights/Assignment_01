#!/usr/bin/env python3
"""
Test Sequential Ordering of LayoutParser Blocks

This script analyzes and improves the sequential ordering of LayoutParser blocks
to ensure proper reading order in the reassembled markdown.
"""

import json
from pathlib import Path
from typing import Dict, List, Any

def analyze_block_ordering(jsonl_file: str) -> None:
    """
    Analyze the current ordering of LayoutParser blocks.
    
    Args:
        jsonl_file: Path to the JSONL file containing blocks
    """
    blocks = []
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                blocks.append(json.loads(line.strip()))
    
    print(f"📄 Analyzing {len(blocks)} blocks from {jsonl_file}")
    
    # Current sorting (page + y1)
    current_sorted = sorted(blocks, key=lambda b: (
        b.get('page_number', 1),
        b.get('bounding_box', {}).get('y1', 0) if b.get('bounding_box') else 0
    ))
    
    # Improved sorting (page + y1 + x1 for same-row items)
    improved_sorted = sorted(blocks, key=lambda b: (
        b.get('page_number', 1),
        round(b.get('bounding_box', {}).get('y1', 0) / 50) * 50 if b.get('bounding_box') else 0,  # Group by rows (50px tolerance)
        b.get('bounding_box', {}).get('x1', 0) if b.get('bounding_box') else 0  # Left to right within row
    ))
    
    print("\n🔍 Current vs Improved Ordering Comparison:")
    print("-" * 80)
    
    # Group blocks by page
    pages = {}
    for block in improved_sorted:
        page_num = block.get('page_number', 1)
        if page_num not in pages:
            pages[page_num] = []
        pages[page_num].append(block)
    
    # Analyze first page in detail
    if pages:
        first_page = min(pages.keys())
        page_blocks = pages[first_page]
        
        print(f"\n📋 Page {first_page} Block Analysis:")
        print("Block ID | Type | Y1 | X1 | Content Preview")
        print("-" * 80)
        
        for block in page_blocks[:20]:  # Show first 20 blocks
            block_id = block.get('block_id', 'unknown')
            block_type = block.get('block_type', 'unknown')
            bbox = block.get('bounding_box', {})
            y1 = bbox.get('y1', 0) if bbox else 0
            x1 = bbox.get('x1', 0) if bbox else 0
            
            content = block.get('content', {})
            text = content.get('text', '') if content else ''
            preview = text[:50].replace('\n', ' ') if text else 'No text'
            
            print(f"{block_id[:20]:<20} | {block_type:<8} | {y1:>4.0f} | {x1:>4.0f} | {preview}")
    
    # Check for reading order issues
    print(f"\n🔄 Reading Order Analysis:")
    reading_order_issues = detect_reading_order_issues(improved_sorted)
    
    if reading_order_issues:
        print(f"❌ Found {len(reading_order_issues)} potential reading order issues:")
        for issue in reading_order_issues[:5]:  # Show first 5 issues
            print(f"  - {issue}")
    else:
        print("✅ No obvious reading order issues detected")
    
    return improved_sorted

def detect_reading_order_issues(blocks: List[Dict]) -> List[str]:
    """
    Detect potential reading order issues in the sorted blocks.
    
    Args:
        blocks: List of sorted blocks
        
    Returns:
        List of issue descriptions
    """
    issues = []
    
    # Group by page
    pages = {}
    for block in blocks:
        page_num = block.get('page_number', 1)
        if page_num not in pages:
            pages[page_num] = []
        pages[page_num].append(block)
    
    for page_num, page_blocks in pages.items():
        # Check for titles appearing after text content
        for i, block in enumerate(page_blocks[:-1]):
            current_type = block.get('block_type', '')
            next_block = page_blocks[i + 1]
            next_type = next_block.get('block_type', '')
            
            # Title after text might indicate ordering issue
            if current_type == 'text' and next_type == 'title':
                current_y1 = block.get('bounding_box', {}).get('y1', 0)
                next_y1 = next_block.get('bounding_box', {}).get('y1', 0)
                
                # If title is significantly above the text, it's likely out of order
                if next_y1 < current_y1 - 100:  # 100px tolerance
                    current_id = block.get('block_id', 'unknown')
                    next_id = next_block.get('block_id', 'unknown')
                    issues.append(f"Page {page_num}: Title '{next_id}' appears after text '{current_id}' but is positioned above it")
    
    return issues

def create_improved_sequential_sorter():
    """
    Create an improved sorting function for LayoutParser blocks.
    
    Returns:
        Function that sorts blocks in proper reading order
    """
    def improved_sort_key(block: Dict) -> tuple:
        """
        Generate sort key for proper reading order.
        
        Args:
            block: LayoutParser block dictionary
            
        Returns:
            Tuple for sorting (page, row_group, x_position)
        """
        page_num = block.get('page_number', 1)
        bbox = block.get('bounding_box', {})
        
        if not bbox:
            return (page_num, 0, 0)
        
        y1 = bbox.get('y1', 0)
        x1 = bbox.get('x1', 0)
        
        # Group blocks by rows (100px tolerance for same row)
        row_group = round(y1 / 100) * 100
        
        # Special handling for titles and headers
        block_type = block.get('block_type', '')
        if block_type == 'title':
            # Titles get slight priority within their row
            row_group -= 1
        
        return (page_num, row_group, x1)
    
    return improved_sort_key

def test_improved_markdown_generation(doc_id: str = "nvda-20240128"):
    """
    Test the improved markdown generation with better sequential ordering.
    
    Args:
        doc_id: Document identifier to test
    """
    print(f"🧪 Testing improved markdown generation for {doc_id}")
    
    # Read blocks
    jsonl_file = f"data/metadata/blocks/layout_parser/{doc_id}.jsonl"
    if not Path(jsonl_file).exists():
        print(f"❌ Blocks file not found: {jsonl_file}")
        return
    
    blocks = []
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                blocks.append(json.loads(line.strip()))
    
    # Apply improved sorting
    sort_key_func = create_improved_sequential_sorter()
    sorted_blocks = sorted(blocks, key=sort_key_func)
    
    print(f"📊 Sequential Ordering Results:")
    print(f"  - Total blocks: {len(blocks)}")
    print(f"  - Pages: {min(b.get('page_number', 1) for b in blocks)} - {max(b.get('page_number', 1) for b in blocks)}")
    
    # Show first page ordering
    page_1_blocks = [b for b in sorted_blocks if b.get('page_number', 1) == 1]
    print(f"  - Page 1 blocks: {len(page_1_blocks)}")
    
    print(f"\n📋 First 10 blocks in reading order:")
    for i, block in enumerate(sorted_blocks[:10], 1):
        block_id = block.get('block_id', 'unknown')
        block_type = block.get('block_type', 'unknown')
        bbox = block.get('bounding_box', {})
        y1 = bbox.get('y1', 0) if bbox else 0
        x1 = bbox.get('x1', 0) if bbox else 0
        
        content = block.get('content', {})
        text = content.get('text', '') if content else ''
        preview = text[:40].replace('\n', ' ') if text else 'No text'
        
        print(f"{i:2}. {block_type:<8} ({y1:4.0f},{x1:4.0f}) | {preview}")
    
    # Generate markdown sample
    print(f"\n📝 Sample Markdown Output (first 5 blocks):")
    print("-" * 60)
    
    for block in sorted_blocks[:5]:
        content = block.get('content', {})
        text = content.get('text', '') if content else ''
        block_type = block.get('block_type', 'unknown')
        
        if text:
            if block_type == 'title':
                print(f"\n## {text.strip()}\n")
            else:
                print(f"{text.strip()}\n")
    
    return sorted_blocks

def main():
    """Test the sequential ordering analysis."""
    print("=== LayoutParser Sequential Ordering Analysis ===")
    
    # Find LayoutParser JSONL files
    layout_parser_dir = Path("data/metadata/blocks/layout_parser")
    if not layout_parser_dir.exists():
        print("❌ LayoutParser blocks directory not found")
        return
    
    jsonl_files = list(layout_parser_dir.glob("*.jsonl"))
    if not jsonl_files:
        print("❌ No LayoutParser block files found")
        return
    
    print(f"Found {len(jsonl_files)} documents with LayoutParser blocks")
    
    # Analyze first document
    first_file = jsonl_files[0]
    doc_id = first_file.stem
    
    print(f"\n🔍 Analyzing sequential ordering for: {doc_id}")
    analyze_block_ordering(str(first_file))
    
    print(f"\n🧪 Testing improved markdown generation:")
    test_improved_markdown_generation(doc_id)

if __name__ == "__main__":
    main()