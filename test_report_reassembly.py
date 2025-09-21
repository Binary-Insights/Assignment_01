#!/usr/bin/env python3
"""
Test script for report section reassembly functionality.

This script demonstrates the report reassembly feature that groups
records with the same section label for EACH extraction method independently.
Creates separate reports for LayoutParser, Docling, and Traditional methods.
"""

from src.metadata_extractor import MetadataExtractor
from pathlib import Path
import json
from datetime import datetime

def test_method_specific_reassembly():
    """Test report reassembly for each extraction method independently."""
    print("=== Testing Method-Specific Report Section Reassembly ===")
    print("Creating separate reports for each extraction method:")
    print("  🤖 LayoutParser - Deep learning layout detection")
    print("  📄 Docling - AI-powered document understanding") 
    print("  📝 Traditional - Rule-based extraction")
    print()
    
    # Initialize metadata extractor
    extractor = MetadataExtractor()
    
    # Define extraction methods to test
    methods = {
        'layout_parser': {
            'name': 'LayoutParser',
            'icon': '🤖',
            'description': 'Deep learning-based layout detection with OCR'
        },
        'docling': {
            'name': 'Docling', 
            'icon': '📄',
            'description': 'AI-powered document understanding'
        },
        'traditional': {
            'name': 'Traditional',
            'icon': '📝', 
            'description': 'Rule-based extraction methods'
        }
    }
    
    # Find available documents for each method
    documents_found = {}
    for method_key, method_info in methods.items():
        method_blocks_dir = Path(f"data/metadata/blocks/{method_key}")
        if method_blocks_dir.exists():
            jsonl_files = list(method_blocks_dir.glob("*.jsonl"))
            documents_found[method_key] = jsonl_files
            print(f"{method_info['icon']} {method_info['name']}: {len(jsonl_files)} documents")
        else:
            documents_found[method_key] = []
            print(f"{method_info['icon']} {method_info['name']}: ❌ No data directory found")
    
    if not any(documents_found.values()):
        print("\n❌ No extraction method data found. Please run the extractors first.")
        return
    
    print()
    
    # Process each method independently
    for method_key, method_info in methods.items():
        jsonl_files = documents_found[method_key]
        if not jsonl_files:
            print(f"⏭️ Skipping {method_info['name']} - no data available")
            continue
            
        print(f"🔄 Processing {method_info['name']} ({method_info['description']})")
        print(f"   Found {len(jsonl_files)} documents:")
        for jsonl_file in jsonl_files:
            print(f"     - {jsonl_file.stem}")
        print()
        
        # Process each document for this method
        for jsonl_file in jsonl_files:
            doc_id = jsonl_file.stem
            print(f"  � Document: {doc_id}")
            
            # Test different grouping approaches
            grouping_methods = [
                ('block_type', 'Block Type'),
                ('semantic_tags', 'Semantic Tags')
            ]
            
            for field, display_name in grouping_methods:
                print(f"    📊 Reassembling by {display_name}...")
                
                try:
                    # Generate method-specific reassembled report
                    report_content = reassemble_method_specific_report(
                        jsonl_file, method_key, method_info, field, doc_id
                    )
                    
                    # Save the report
                    output_filename = f"{doc_id}_{method_key}_reassembled_by_{field}.md"
                    output_path = Path("data/staged/markdown") / output_filename
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(report_content)
                    
                    # Show preview
                    preview_lines = report_content.split('\n')[:15]
                    print(f"      ✓ Report generated ({len(report_content)} chars)")
                    print(f"      📄 Saved to: {output_path}")
                    print(f"      🔍 Preview (first 15 lines):")
                    for line in preview_lines:
                        print(f"        {line}")
                    total_lines = len(report_content.split('\n'))
                    if total_lines > 15:
                        remaining_lines = total_lines - 15
                        print(f"        ... ({remaining_lines} more lines)")
                    print()
                    
                except Exception as e:
                    print(f"      ❌ Error generating report: {e}")
                    print()
        
        print(f"✅ Completed {method_info['name']} processing")
        print("-" * 60)
        print()

def reassemble_method_specific_report(jsonl_file: Path, method_key: str, 
                                    method_info: dict, section_field: str, doc_id: str) -> str:
    """
    Reassemble report sections for a specific extraction method.
    
    Args:
        jsonl_file: Path to the method-specific JSONL file
        method_key: Method identifier (layout_parser, docling, traditional)
        method_info: Method information dictionary
        section_field: Field to group by ('block_type', 'semantic_tags')
        doc_id: Document identifier
        
    Returns:
        str: Markdown content with reassembled sections
    """
    # Read blocks from method-specific JSONL
    blocks = []
    try:
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    block_data = json.loads(line.strip())
                    blocks.append(block_data)
    except Exception as e:
        return f"# Document: {doc_id} - {method_info['name']}\n\n**Error**: Failed to load blocks - {e}\n"
    
    if not blocks:
        return f"# Document: {doc_id} - {method_info['name']}\n\n**No blocks found in this document.**\n"
    
    # Group blocks by section labels
    sections = {}
    for block in blocks:
        # Determine section label based on specified field
        if section_field == 'semantic_tags':
            labels = block.get('semantic_tags', ['uncategorized'])
            section_label = labels[0] if labels else 'uncategorized'
        elif section_field == 'block_type':
            section_label = block.get('block_type', 'unknown')
        else:
            section_label = block.get(section_field, 'unknown')
        
        if section_label not in sections:
            sections[section_label] = []
        sections[section_label].append(block)
    
    # Sort blocks within each section by page number (handle None values)
    for section_blocks in sections.values():
        section_blocks.sort(key=lambda b: b.get('page_number') or 0)
    
    # Generate markdown content
    markdown_content = []
    
    # Document header
    markdown_content.append(f"# Document: {doc_id}")
    markdown_content.append(f"## Extraction Method: {method_info['icon']} {method_info['name']}")
    markdown_content.append(f"**Description**: {method_info['description']}")
    markdown_content.append(f"**Grouped by**: {section_field}")
    markdown_content.append("")
    
    # Document summary (handle None page numbers)
    total_blocks = len(blocks)
    pages = set(block.get('page_number') or 1 for block in blocks)
    avg_confidence = sum(block.get('confidence', 0) for block in blocks) / total_blocks if total_blocks > 0 else 0
    
    markdown_content.append("## Document Summary")
    markdown_content.append(f"- **Total Blocks**: {total_blocks}")
    markdown_content.append(f"- **Pages Covered**: {min(pages) if pages else 0} - {max(pages) if pages else 0}")
    markdown_content.append(f"- **Sections Found**: {len(sections)}")
    markdown_content.append(f"- **Average Confidence**: {avg_confidence:.3f}")
    markdown_content.append("")
    
    # Section overview table
    markdown_content.append("## Section Overview")
    markdown_content.append("| Section | Blocks | Pages | Avg Confidence |")
    markdown_content.append("|---------|--------|-------|----------------|")
    
    for section_name, section_blocks in sorted(sections.items()):
        block_count = len(section_blocks)
        section_pages = set(block.get('page_number') or 1 for block in section_blocks)
        page_range = f"{min(section_pages)}-{max(section_pages)}" if len(section_pages) > 1 else str(min(section_pages)) if section_pages else "Unknown"
        section_confidence = sum(block.get('confidence', 0) for block in section_blocks) / block_count if block_count > 0 else 0
        
        markdown_content.append(f"| {section_name} | {block_count} | {page_range} | {section_confidence:.3f} |")
    
    markdown_content.append("")
    markdown_content.append("---")
    markdown_content.append("")
    
    # Generate content for each section
    for section_name, section_blocks in sorted(sections.items()):
        markdown_content.append(f"## Section: {section_name}")
        markdown_content.append(f"*{len(section_blocks)} blocks from {method_info['name']}*")
        markdown_content.append("")
        
        for i, block in enumerate(section_blocks, 1):
            block_id = block.get('block_id', 'unknown')
            page_num = block.get('page_number') or 'unknown'
            confidence = block.get('confidence', 0)
            
            markdown_content.append(f"### Block {i}: {block_id}")
            markdown_content.append(f"**Page**: {page_num} | **Confidence**: {confidence:.3f}")
            markdown_content.append("")
            
            # Add content based on block type
            content = block.get('content', {})
            text_content = content.get('text', '')
            
            if text_content:
                # Check if content is already markdown formatted (common with Docling)
                is_already_markdown_table = ('|' in text_content and 
                                           text_content.count('|') > 2 and 
                                           '\n' in text_content)
                
                if block.get('block_type') == 'table':
                    if is_already_markdown_table:
                        # Content is already a markdown table, use as-is
                        markdown_content.append(text_content.strip())
                    elif ',' in text_content and '\n' in text_content:
                        # CSV-like content, convert to markdown table
                        lines = text_content.strip().split('\n')
                        if len(lines) > 1:
                            # Create header
                            header_cells = [cell.strip() for cell in lines[0].split(',')]
                            markdown_content.append("| " + " | ".join(header_cells) + " |")
                            markdown_content.append("|" + "---|" * len(header_cells))
                            
                            # Add data rows
                            for line in lines[1:]:
                                if line.strip():
                                    data_cells = [cell.strip() for cell in line.split(',')]
                                    # Pad with empty cells if needed
                                    while len(data_cells) < len(header_cells):
                                        data_cells.append("")
                                    markdown_content.append("| " + " | ".join(data_cells) + " |")
                        else:
                            markdown_content.append(f"```\n{text_content}\n```")
                    else:
                        # Plain text table, show in code block
                        markdown_content.append(f"```\n{text_content}\n```")
                else:
                    # Regular text content
                    if len(text_content) > 500:
                        preview = text_content[:500] + "..."
                        markdown_content.append(f"{preview}")
                        markdown_content.append(f"\n*[Content truncated - full length: {len(text_content)} characters]*")
                    else:
                        markdown_content.append(f"{text_content}")
            else:
                markdown_content.append("*No text content available*")
            
            # Add metadata comment
            markdown_content.append("")
            markdown_content.append(f"<!-- Method: {method_key}, Block ID: {block_id}, Page: {page_num}, Confidence: {confidence:.3f} -->")
            markdown_content.append("")
    
    # Add method-specific statistics
    markdown_content.append("---")
    markdown_content.append("")
    markdown_content.append(f"## {method_info['name']} Statistics")
    
    # Block type distribution
    block_types = {}
    for block in blocks:
        block_type = block.get('block_type', 'unknown')
        block_types[block_type] = block_types.get(block_type, 0) + 1
    
    markdown_content.append("### Block Type Distribution")
    markdown_content.append("| Type | Count | Percentage |")
    markdown_content.append("|------|-------|------------|")
    for block_type, count in sorted(block_types.items()):
        percentage = (count / total_blocks) * 100 if total_blocks > 0 else 0
        markdown_content.append(f"| {block_type} | {count} | {percentage:.1f}% |")
    
    markdown_content.append("")
    markdown_content.append(f"*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    markdown_content.append(f"*Source: {jsonl_file}*")
    
    return '\n'.join(markdown_content)

def show_reassembly_features():
    """Show the features of the report reassembly system."""
    print("=== Report Section Reassembly Features ===")
    print()
    print("🎯 **Purpose**: Group records with the same section label and create readable reports")
    print()
    print("📋 **Features**:")
    print("  ✓ Groups blocks by configurable section labels (block_type, semantic_tags, etc.)")
    print("  ✓ Sorts content by page number within each section")
    print("  ✓ Creates structured Markdown with headings and tables")
    print("  ✓ Special formatting for tables (attempts markdown table format)")
    print("  ✓ Special formatting for figures (with descriptions)")
    print("  ✓ Includes document summary and section overview table")
    print("  ✓ Adds processing provenance and quality statistics")
    print("  ✓ Preserves metadata as HTML comments")
    print()
    print("📊 **Section Overview Table**: Shows block count, page range, and content types")
    print("📈 **Quality Statistics**: Confidence scores and extraction method breakdown")
    print("🔍 **Provenance Tracking**: Shows which extraction methods contributed to each section")
    print()
    print("🎨 **Output Format**: Clean, readable Markdown with:")
    print("  - Hierarchical headings (##, ###)")
    print("  - Tables for structured data")
    print("  - Code blocks for complex content")
    print("  - Metadata comments for traceability")
    print()

if __name__ == "__main__":
    show_reassembly_features()
    print()
    test_method_specific_reassembly()