#!/usr/bin/env python3
"""
Method-Specific Markdown Generation

This module creates tailored markdown outputs for different extraction methods:
- Docling: Converts structured text to proper markdown
- LayoutParser: Reassembles blocks into structured sections  
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class MethodSpecificReportGenerator:
    """
    Generate method-specific outputs in multiple formats (markdown, JSON, text) 
    tailored to each extraction approach.
    """
    
    def __init__(self, base_reports_dir: str = "data/reports"):
        """
        Initialize the multi-format report generator.
        
        Args:
            base_reports_dir: Base directory to save generated reports
        """
        self.base_reports_dir = Path(base_reports_dir)
        self.base_reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Create format-specific base directories
        self.markdown_base_dir = self.base_reports_dir / "markdown"
        self.json_base_dir = self.base_reports_dir / "json"
        self.text_base_dir = self.base_reports_dir / "text"
        
        for format_dir in [self.markdown_base_dir, self.json_base_dir, self.text_base_dir]:
            format_dir.mkdir(parents=True, exist_ok=True)
        
        # Create method-specific subdirectories for each format
        self.methods = ["docling", "layout_parser", "hybrid", "pdfplumber_tesseract"]
        
        # Markdown directories
        self.docling_md_dir = self.markdown_base_dir / "docling"
        self.layout_parser_md_dir = self.markdown_base_dir / "layout_parser"
        self.hybrid_md_dir = self.markdown_base_dir / "hybrid"
        self.pdfplumber_tesseract_md_dir = self.markdown_base_dir / "pdfplumber_tesseract"
        
        # JSON directories
        self.docling_json_dir = self.json_base_dir / "docling"
        self.layout_parser_json_dir = self.json_base_dir / "layout_parser"
        self.hybrid_json_dir = self.json_base_dir / "hybrid"
        self.pdfplumber_tesseract_json_dir = self.json_base_dir / "pdfplumber_tesseract"
        
        # Text directories
        self.docling_text_dir = self.text_base_dir / "docling"
        self.layout_parser_text_dir = self.text_base_dir / "layout_parser"
        self.hybrid_text_dir = self.text_base_dir / "hybrid"
        self.pdfplumber_tesseract_text_dir = self.text_base_dir / "pdfplumber_tesseract"

        
        # Create all method directories for all formats
        all_dirs = [
            # Markdown
            self.docling_md_dir, self.layout_parser_md_dir, self.hybrid_md_dir,
            self.pdfplumber_tesseract_md_dir,
            # JSON
            self.docling_json_dir, self.layout_parser_json_dir, self.hybrid_json_dir,
            self.pdfplumber_tesseract_json_dir,
            # Text
            self.docling_text_dir, self.layout_parser_text_dir, self.hybrid_text_dir,
            self.pdfplumber_tesseract_text_dir,
        ]
        
        for method_dir in all_dirs:
            method_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_docling_markdown(self, doc_id: str) -> str:
        """
        Generate markdown from Docling's structured text output.
        
        Docling provides well-structured text that just needs proper markdown formatting.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            str: Path to generated markdown file
        """
        print(f"🔄 Converting Docling structured text to Markdown for: {doc_id}")
        
        # Read Docling's structured content
        docling_text_file = Path(f"data/parsed/docling/{doc_id}/text/structured_content.txt")
        if not docling_text_file.exists():
            print(f"❌ Docling structured content not found: {docling_text_file}")
            return None
        
        with open(docling_text_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Convert structured text to proper markdown
        markdown_content = self._convert_docling_text_to_markdown(content, doc_id)
        
        # Save markdown file in docling-specific folder
        output_file = self.docling_md_dir / f"{doc_id}_docling_converted.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ Docling markdown saved: {output_file}")
        return str(output_file)
    
    def generate_layout_parser_markdown(self, doc_id: str) -> str:
        """
        Generate markdown from LayoutParser's block-based output.
        
        LayoutParser extracts individual blocks that need to be reassembled into sections.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            str: Path to generated markdown file
        """
        print(f"🔄 Reassembling LayoutParser blocks to Markdown for: {doc_id}")
        
        # Read LayoutParser blocks
        layout_parser_jsonl = Path(f"data/metadata/blocks/layout_parser/{doc_id}.jsonl")
        if not layout_parser_jsonl.exists():
            print(f"❌ LayoutParser blocks not found: {layout_parser_jsonl}")
            return None
        
        blocks = []
        with open(layout_parser_jsonl, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    blocks.append(json.loads(line.strip()))
        
        # Reassemble blocks into markdown
        markdown_content = self._reassemble_layout_parser_blocks(blocks, doc_id)
        
        # Save markdown file in layout_parser-specific folder
        output_file = self.layout_parser_md_dir / f"{doc_id}_layout_parser_reassembled.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ LayoutParser markdown saved: {output_file}")
        return str(output_file)
    
    
    def generate_hybrid_markdown(self, doc_id: str) -> str:
        """
        Generate markdown from Hybrid extraction output.
        
        Hybrid extraction uses multiple table detection methods (Camelot + pdfplumber).
        
        Args:
            doc_id: Document identifier
            
        Returns:
            str: Path to generated markdown file
        """
        print(f"🔄 Converting Hybrid extraction to Markdown for: {doc_id}")
        
        # Look for hybrid extraction files
        hybrid_dir = Path(f"data/parsed/hybrid/{doc_id}")
        if not hybrid_dir.exists():
            print(f"❌ Hybrid extraction not found: {hybrid_dir}")
            return None
        
        # Read the extraction summary JSON
        summary_file = hybrid_dir / "hybrid_extraction_results.json"
        if not summary_file.exists():
            print(f"❌ Hybrid summary not found: {summary_file}")
            return None
        
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        # Generate markdown content
        markdown_content = self._convert_hybrid_extraction_to_markdown(summary_data, doc_id, hybrid_dir)
        
        # Save markdown file in hybrid-specific folder
        output_file = self.hybrid_md_dir / f"{doc_id}_hybrid_extraction.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ Hybrid markdown saved: {output_file}")
        return str(output_file)
    
    def generate_pdfplumber_tesseract_markdown(self, doc_id: str) -> str:
        """
        Generate markdown from PDFPlumber-Tesseract extraction output.
        
        PDFPlumber-Tesseract provides text extraction with OCR fallback and table detection.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            str: Path to generated markdown file
        """
        print(f"🔄 Converting PDFPlumber-Tesseract extraction to Markdown for: {doc_id}")
        
        # Look for pdfplumber_tesseract extraction files
        pdfplumber_dir = Path(f"data/parsed/pdfplumber_tesseract/{doc_id}")
        if not pdfplumber_dir.exists():
            print(f"❌ PDFPlumber-Tesseract extraction not found: {pdfplumber_dir}")
            return None
        
        # Read the extraction summary JSON
        summary_file = pdfplumber_dir / "pdfplumber_tesseract_extraction_results.json"
        if not summary_file.exists():
            print(f"❌ PDFPlumber-Tesseract summary not found: {summary_file}")
            return None
        
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        # Generate markdown content
        markdown_content = self._convert_pdfplumber_tesseract_to_markdown(summary_data, doc_id, pdfplumber_dir)
        
        # Save markdown file in pdfplumber_tesseract-specific folder
        output_file = self.pdfplumber_tesseract_md_dir / f"{doc_id}_pdfplumber_tesseract.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ PDFPlumber-Tesseract markdown saved: {output_file}")
        return str(output_file)
    
    def _convert_docling_text_to_markdown(self, content: str, doc_id: str) -> str:
        """
        Convert Docling's structured text to proper markdown format.
        
        Args:
            content: Docling structured text content
            doc_id: Document identifier
            
        Returns:
            str: Formatted markdown content
        """
        lines = content.split('\n')
        markdown_lines = []
        
        # Document header
        markdown_lines.extend([
            f"# Document: {doc_id}",
            "## Extraction Method: 📄 Docling (AI-Powered Document Understanding)",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            ""
        ])
        
        in_table = False
        table_lines = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines unless we're building a table
            if not line and not in_table:
                if markdown_lines and markdown_lines[-1] != "":
                    markdown_lines.append("")
                continue
            
            # Detect and convert table content
            if self._is_table_line(line):
                if not in_table:
                    in_table = True
                    table_lines = []
                    if markdown_lines and markdown_lines[-1] != "":
                        markdown_lines.append("")
                
                table_lines.append(line)
                
                # Check if table ends (next line is not a table line or end of content)
                next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                if not self._is_table_line(next_line):
                    # End of table, process it
                    markdown_lines.extend(self._format_table_lines(table_lines))
                    markdown_lines.append("")
                    in_table = False
                    table_lines = []
                
                continue
            
            # Handle headings (lines that look like section headers)
            if self._is_heading_line(line):
                level = self._get_heading_level(line)
                markdown_lines.append(f"{'#' * level} {line}")
                markdown_lines.append("")
                continue
            
            # Handle form fields and checkboxes
            if '☐' in line or '☒' in line or 'Yes' in line and 'No' in line:
                # Format checkbox lines nicely
                formatted_line = self._format_checkbox_line(line)
                markdown_lines.append(formatted_line)
                continue
            
            # Handle URLs and links
            if 'http' in line or 'www.' in line:
                formatted_line = self._format_links(line)
                markdown_lines.append(formatted_line)
                continue
            
            # Regular text content
            markdown_lines.append(line)
        
        # Add document footer
        markdown_lines.extend([
            "",
            "---",
            "",
            "## Document Information",
            f"- **Source**: Docling AI-powered extraction",
            f"- **Processing Method**: Structured text conversion to Markdown", 
            f"- **Original File**: `data/parsed/docling/{doc_id}/text/structured_content.txt`",
            f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "*This document was automatically converted from Docling's structured text output.*"
        ])
        
        return '\n'.join(markdown_lines)
    
    def _is_table_line(self, line: str) -> bool:
        """Check if a line appears to be part of a table."""
        # Look for table indicators
        if '|' in line and line.count('|') >= 2:
            return True
        if line.startswith('|') and line.endswith('|'):
            return True
        # Table separator lines
        if re.match(r'^[\|\-\s]+$', line) and '|' in line:
            return True
        return False
    
    def _format_table_lines(self, table_lines: List[str]) -> List[str]:
        """Format table lines into proper markdown table."""
        if not table_lines:
            return []
        
        # If already properly formatted markdown table, return as-is
        if all('|' in line for line in table_lines[:3]):
            return table_lines
        
        # Try to parse and reformat
        formatted_lines = []
        for line in table_lines:
            if line.strip():
                formatted_lines.append(line)
        
        return formatted_lines
    
    def _is_heading_line(self, line: str) -> bool:
        """Check if a line should be treated as a heading."""
        # Common heading patterns
        heading_patterns = [
            r'^Part\s+[IVX]+',  # Part I, Part II, etc.
            r'^Item\s+\d+[A-Z]?\.?',  # Item 1., Item 1A., etc.
            r'^[A-Z][A-Z\s]+$',  # ALL CAPS lines (shorter ones)
            r'^Business$|^Risk Factors$|^Properties$',  # Common SEC filing sections
            r'^Our Company$|^Forward-Looking Statements$',  # NVIDIA specific sections
        ]
        
        for pattern in heading_patterns:
            if re.match(pattern, line):
                return True
        
        # All caps lines that aren't too long (likely headers)
        if line.isupper() and len(line) < 50 and len(line.split()) <= 6:
            return True
        
        return False
    
    def _get_heading_level(self, line: str) -> int:
        """Determine appropriate heading level for a line."""
        if re.match(r'^Part\s+[IVX]+', line):
            return 2
        elif re.match(r'^Item\s+\d+', line):
            return 3
        elif line in ['Our Company', 'Business', 'Risk Factors']:
            return 2
        elif line.isupper() and len(line) < 30:
            return 3
        else:
            return 4
    
    def _format_checkbox_line(self, line: str) -> str:
        """Format lines with checkboxes for better markdown display."""
        # Replace checkbox symbols with markdown checkboxes
        line = line.replace('☐', '- [ ]')
        line = line.replace('☒', '- [x]')
        return line
    
    def _format_links(self, line: str) -> str:
        """Format URLs in the line as proper markdown links."""
        # Find URLs and wrap them in markdown link format
        url_pattern = r'https?://[^\s<>"{}|\\^`[\]]+|www\.[^\s<>"{}|\\^`[\]]+'
        
        def replace_url(match):
            url = match.group(0)
            if not url.startswith('http'):
                url = 'http://' + url
            return f"[{match.group(0)}]({url})"
        
        return re.sub(url_pattern, replace_url, line)
    
    def _reassemble_layout_parser_blocks(self, blocks: List[Dict], doc_id: str) -> str:
        """
        Reassemble LayoutParser blocks into structured markdown.
        
        Args:
            blocks: List of LayoutParser block dictionaries
            doc_id: Document identifier
            
        Returns:
            str: Formatted markdown content
        """
        # Sort blocks by page and position with improved reading order
        sorted_blocks = sorted(blocks, key=lambda b: (
            b.get('page_number', 1),
            # Group by rows (50px tolerance for same-row elements)
            round(b.get('bounding_box', {}).get('y1', 0) / 50) * 50 if b.get('bounding_box') else 0,
            # Left to right within the same row
            b.get('bounding_box', {}).get('x1', 0) if b.get('bounding_box') else 0
        ))
        
        markdown_lines = []
        
        # Document header
        markdown_lines.extend([
            f"# Document: {doc_id}",
            "## Extraction Method: 🤖 LayoutParser (Deep Learning Layout Detection)",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"**Total Blocks**: {len(blocks)}",
            f"**Pages**: {min(b.get('page_number', 1) for b in blocks)} - {max(b.get('page_number', 1) for b in blocks)}",
            "",
            "---",
            ""
        ])
        
        # Group blocks by page
        pages = {}
        for block in sorted_blocks:
            page_num = block.get('page_number', 1)
            if page_num not in pages:
                pages[page_num] = []
            pages[page_num].append(block)
        
        # Process each page
        for page_num in sorted(pages.keys()):
            page_blocks = pages[page_num]
            
            markdown_lines.extend([
                f"## Page {page_num}",
                f"*{len(page_blocks)} blocks detected*",
                ""
            ])
            
            # Process blocks in sequential reading order (don't group by type)
            # This maintains the natural document flow
            for i, block in enumerate(page_blocks, 1):
                content = block.get('content', {})
                text_content = content.get('text', '') or content.get('structured', '')
                
                if isinstance(text_content, dict):
                    text_content = str(text_content)
                
                if not text_content.strip():
                    continue  # Skip empty blocks
                
                block_type = block.get('block_type', 'unknown')
                confidence = block.get('confidence', 0)
                block_id = block.get('block_id', 'unknown')
                
                # Format content based on block type
                if block_type == 'title':
                    # Determine heading level based on text characteristics
                    heading_level = self._determine_heading_level(text_content)
                    markdown_lines.extend([
                        f"{'#' * heading_level} {text_content.strip()}",
                        ""
                    ])
                elif block_type == 'table':
                    markdown_lines.extend([
                        f"**Table {i}** (Confidence: {confidence:.2f})",
                        "",
                        "```",
                        text_content.strip(),
                        "```",
                        ""
                    ])
                elif block_type == 'figure':
                    markdown_lines.extend([
                        f"**Figure {i}** (Confidence: {confidence:.2f})",
                        "",
                        text_content.strip(),
                        ""
                    ])
                else:  # text, list, and other types
                    # Regular text content
                    markdown_lines.extend([
                        text_content.strip(),
                        ""
                    ])
                
                # Add confidence annotation as HTML comment
                markdown_lines.append(f"<!-- Block: {block_id}, Type: {block_type}, Confidence: {confidence:.3f} -->")
                markdown_lines.append("")
            
            markdown_lines.append("")
        
        # Add document footer
        markdown_lines.extend([
            "---",
            "",
            "## Document Information",
            f"- **Source**: LayoutParser deep learning extraction",
            f"- **Processing Method**: Block detection and reassembly",
            f"- **Total Blocks Processed**: {len(blocks)}",
            f"- **Block Types**: {', '.join(set(b.get('block_type', 'unknown') for b in blocks))}",
            f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "*This document was reassembled from LayoutParser's block-based extraction.*"
        ])
        
        return '\n'.join(markdown_lines)
    
    def _determine_heading_level(self, text: str) -> int:
        """
        Determine appropriate heading level for title text.
        
        Args:
            text: Title text content
            
        Returns:
            int: Heading level (2-4)
        """
        text = text.strip().upper()
        
        # Level 2: Major document sections
        if any(phrase in text for phrase in [
            'SECURITIES AND EXCHANGE COMMISSION',
            'ANNUAL REPORT',
            'FORM 10-K',
            'PART I', 'PART II', 'PART III', 'PART IV'
        ]):
            return 2
        
        # Level 3: Company info and major items
        if any(phrase in text for phrase in [
            'NVIDIA CORPORATION',
            'ITEM 1', 'ITEM 2', 'ITEM 3', 'ITEM 4', 'ITEM 5',
            'BUSINESS', 'RISK FACTORS', 'PROPERTIES'
        ]):
            return 3
        
        # Level 4: Everything else
        return 4
    
    def _add_block_type_section(self, markdown_lines: List[str], block_type: str, blocks: List[Dict]):
        """Add a section for a specific block type."""
        type_names = {
            'title': 'Titles',
            'text': 'Text Content', 
            'table': 'Tables',
            'figure': 'Figures',
            'list': 'Lists'
        }
        
        section_name = type_names.get(block_type, block_type.title())
        markdown_lines.extend([
            f"### {section_name}",
            ""
        ])
        
        for i, block in enumerate(blocks, 1):
            content = block.get('content', {})
            text_content = content.get('text', '') or content.get('structured', '')
            
            if isinstance(text_content, dict):
                text_content = str(text_content)
            
            confidence = block.get('confidence', 0)
            block_id = block.get('block_id', 'unknown')
            
            markdown_lines.extend([
                f"#### {section_name} {i} (Confidence: {confidence:.2f})",
                ""
            ])
            
            if text_content:
                if block_type == 'table' and len(text_content) > 100:
                    # For tables, show in code block to preserve formatting
                    markdown_lines.extend([
                        "```",
                        text_content.strip(),
                        "```"
                    ])
                else:
                    markdown_lines.append(text_content.strip())
            else:
                markdown_lines.append("*No text content extracted*")
            
            markdown_lines.extend([
                "",
                f"<!-- Block ID: {block_id}, Confidence: {confidence:.3f} -->",
                ""
            ])
      
    def _convert_hybrid_extraction_to_markdown(self, summary_data: Dict, doc_id: str, hybrid_dir: Path) -> str:
        """
        Convert hybrid extraction results to markdown with proper sequencing.
        
        Args:
            summary_data: JSON summary from hybrid extraction
            doc_id: Document identifier  
            hybrid_dir: Path to hybrid extraction directory
            
        Returns:
            str: Formatted markdown content
        """
        markdown_lines = []
        
        # Document header
        markdown_lines.extend([
            f"# Document: {doc_id}",
            "## Extraction Method: 🔬 Hybrid (Camelot + PDFPlumber Multi-Method)",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            ""
        ])
        
        # Processing summary
        pdf_info = summary_data.get('pdf_info', {})
        overall_stats = summary_data.get('overall_stats', {})
        
        markdown_lines.extend([
            "## Processing Summary",
            f"- **PDF**: {pdf_info.get('name', 'Unknown')}",
            f"- **Processing Time**: {pdf_info.get('processing_time_seconds', 0):.2f} seconds",
            f"- **Total Pages**: {overall_stats.get('total_pages', 0)}",
            f"- **Text Pages**: {overall_stats.get('text_extracted_pages', 0)}",
            f"- **OCR Pages**: {overall_stats.get('ocr_pages', 0)}",
            f"- **Tables Found**: {overall_stats.get('tables_found', 0)}",
            "",
            "---",
            ""
        ])
        
        # Text extraction results - maintain page sequence
        text_results = summary_data.get('text_extraction', {})
        if text_results:
            markdown_lines.extend([
                "## Text Extraction (Page Sequence)",
                ""
            ])
            
            # Process pages in sequential order
            pages = text_results.get('pages', [])
            sorted_pages = sorted(pages, key=lambda p: p.get('page_number', 0))
            
            for page in sorted_pages:
                page_num = page.get('page_number', 'Unknown')
                text_file = page.get('text_file', '')
                extraction_method = page.get('extraction_method', 'unknown')
                text_length = page.get('text_length', 0)
                
                markdown_lines.extend([
                    f"### Page {page_num}",
                    f"- **Method**: {extraction_method.title()}",
                    f"- **Text Length**: {text_length:,} characters",
                    f"- **Source File**: `text/{text_file}`",
                    ""
                ])
                
                # Include actual text content if file exists
                text_file_path = hybrid_dir / "text" / text_file
                if text_file_path.exists():
                    try:
                        with open(text_file_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        if content and len(content) > 50:
                            # Show full content instead of preview
                            markdown_lines.extend([
                                "**Full Content:**",
                                "```",
                                content,
                                "```",
                                ""
                            ])
                    except Exception as e:
                        markdown_lines.append(f"*Error reading text file: {e}*")
                        markdown_lines.append("")
            
            markdown_lines.extend(["---", ""])
        
        # Table extraction results - organized by method with quality analysis
        table_results = summary_data.get('table_extraction', {})
        if table_results:
            markdown_lines.extend([
                "## Table Extraction Analysis",
                f"**Total Tables Found**: {table_results.get('total_tables', 0)}",
                ""
            ])
            
            # Method comparison
            method_analysis = table_results.get('method_analysis', {})
            if method_analysis:
                method_comparison = method_analysis.get('method_comparison', {})
                
                for method, stats in method_comparison.items():
                    method_name = method.replace('_', ' ').title()
                    markdown_lines.extend([
                        f"### {method_name}",
                        f"- **Tables Found**: {stats.get('tables_found', 0)}",
                        f"- **Average Accuracy**: {stats.get('avg_accuracy', 'N/A')}",
                        f"- **Best For**: {stats.get('best_for', 'General use')}",
                        ""
                    ])
                
                # Recommendations
                recommendations = method_analysis.get('recommendations', [])
                if recommendations:
                    markdown_lines.extend([
                        "### Recommendations",
                        ""
                    ])
                    for rec in recommendations:
                        markdown_lines.append(f"- {rec}")
                    markdown_lines.append("")
            
            # Hybrid analysis results
            hybrid_results = table_results.get('hybrid_results', [])
            if hybrid_results:
                markdown_lines.extend([
                    "### Page-by-Page Analysis",
                    ""
                ])
                
                for result in sorted(hybrid_results, key=lambda r: r.get('page', 0)):
                    page_num = result.get('page', 'Unknown')
                    recommended = result.get('recommended_method', 'none').replace('_', ' ').title()
                    reasoning = result.get('reasoning', 'No reasoning provided')
                    
                    markdown_lines.extend([
                        f"**Page {page_num}**",
                        f"- **Recommended Method**: {recommended}",
                        f"- **Reasoning**: {reasoning}",
                        f"- **Has Ruling Lines**: {result.get('has_ruling_lines', False)}",
                        ""
                    ])
        
        # Add document footer
        markdown_lines.extend([
            "---",
            "",
            "## Document Information",
            f"- **Source**: Hybrid extraction (Camelot lattice/stream + PDFPlumber)",
            f"- **Processing Method**: Multi-method table detection with heuristic selection",
            f"- **Text Files**: Sequential page-by-page with OCR fallback",
            f"- **Table Files**: Method-specific CSV outputs with quality analysis",
            f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "*This document combines multiple extraction methods for optimal results.*"
        ])
        
        return '\n'.join(markdown_lines)
    
    def _convert_pdfplumber_tesseract_to_markdown(self, summary_data: Dict, doc_id: str, pdfplumber_dir: Path) -> str:
        """
        Convert PDFPlumber-Tesseract extraction results to markdown with proper sequencing.
        
        Args:
            summary_data: JSON summary from pdfplumber extraction
            doc_id: Document identifier
            pdfplumber_dir: Path to pdfplumber extraction directory
            
        Returns:
            str: Formatted markdown content
        """
        markdown_lines = []
        
        # Document header
        markdown_lines.extend([
            f"# Document: {doc_id}",
            "## Extraction Method: 📄 PDFPlumber + Tesseract (OCR-Enhanced Text & Tables)",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            ""
        ])
        
        # Processing summary
        pdf_info = summary_data.get('pdf_info', {})
        overall_stats = summary_data.get('overall_stats', {})
        
        markdown_lines.extend([
            "## Processing Summary",
            f"- **PDF**: {pdf_info.get('name', 'Unknown')}",
            f"- **Processing Time**: {pdf_info.get('processing_time_seconds', 0):.2f} seconds",
            f"- **Total Pages**: {overall_stats.get('total_pages', 0)}",
            f"- **Text Extraction Pages**: {overall_stats.get('text_extracted_pages', 0)}",
            f"- **OCR Pages**: {overall_stats.get('ocr_pages', 0)}",
            f"- **Failed Pages**: {overall_stats.get('failed_pages', 0)}",
            f"- **Tables Found**: {overall_stats.get('tables_found', 0)}",
            "",
            "---",
            ""
        ])
        
        # Text extraction with page sequence
        text_results = summary_data.get('text_extraction', {})
        if text_results:
            markdown_lines.extend([
                "## Text Extraction (Sequential by Page)",
                f"**Word Boxes Extracted**: {text_results.get('word_boxes_saved', False)}",
                "",
                "*Note: Full text content is shown for each page (not just previews)*",
                ""
            ])
            
            # Process pages in order
            pages = text_results.get('pages', [])
            sorted_pages = sorted(pages, key=lambda p: p.get('page_number', 0))
            
            for page in sorted_pages:
                page_num = page.get('page_number', 'Unknown')
                method = page.get('extraction_method', 'unknown')
                text_length = page.get('text_length', 0)
                used_ocr = page.get('used_ocr', False)
                success = page.get('success', True)
                
                status_icon = "✅" if success else "❌"
                method_icon = "🔍" if method == "ocr" else "📄"
                
                markdown_lines.extend([
                    f"### {status_icon} Page {page_num} {method_icon}",
                    f"- **Extraction Method**: {method.upper()}",
                    f"- **Text Length**: {text_length:,} characters",
                    f"- **Used OCR**: {'Yes' if used_ocr else 'No'}",
                    f"- **Status**: {'Success' if success else 'Failed'}",
                    ""
                ])
                
                # Include text preview if available
                text_file = page.get('text_file', '')
                if text_file:
                    text_file_path = pdfplumber_dir / "text" / text_file
                    if text_file_path.exists():
                        try:
                            with open(text_file_path, 'r', encoding='utf-8') as f:
                                content = f.read().strip()
                            if content and len(content) > 50:
                                # Show full content instead of preview
                                markdown_lines.extend([
                                    "**Full Text Content:**",
                                    "",
                                    content,  # Full content, not preview
                                    "",
                                    "---",
                                    ""
                                ])
                        except Exception as e:
                            markdown_lines.append(f"*Error reading text: {e}*")
                            markdown_lines.append("")
            
            markdown_lines.extend(["---", ""])
            
            # Add combined text section
            markdown_lines.extend([
                "## Combined Document Text",
                "*All pages combined in reading order*",
                "",
                "```",
            ])
            
            # Combine all page text in sequence
            for page in sorted_pages:
                text_file = page.get('text_file', '')
                page_num = page.get('page_number', 'Unknown')
                if text_file:
                    text_file_path = pdfplumber_dir / "text" / text_file
                    if text_file_path.exists():
                        try:
                            with open(text_file_path, 'r', encoding='utf-8') as f:
                                content = f.read().strip()
                            if content:
                                markdown_lines.extend([
                                    f"=== PAGE {page_num} ===",
                                    content,
                                    ""
                                ])
                        except Exception:
                            markdown_lines.append(f"[Error reading page {page_num}]")
            
            markdown_lines.extend([
                "```",
                "",
                "---",
                ""
            ])
        
        # Table extraction analysis
        table_results = summary_data.get('table_extraction', {})
        if table_results:
            markdown_lines.extend([
                "## Table Extraction Analysis",
                f"**Total Tables Found**: {table_results.get('total_tables', 0)}",
                ""
            ])
            
            # Method comparison
            methods = ['standard_extraction', 'custom_settings', 'financial_focused']
            method_names = {
                'standard_extraction': 'Standard PDFPlumber',
                'custom_settings': 'Custom Settings',
                'financial_focused': 'Financial-Focused'
            }
            
            for method in methods:
                if method in table_results:
                    method_data = table_results[method]
                    method_name = method_names.get(method, method.title())
                    
                    markdown_lines.extend([
                        f"### {method_name}",
                        f"- **Tables Found**: {method_data.get('success_count', 0)}",
                        ""
                    ])
                    
                    # Show individual tables
                    tables = method_data.get('tables', [])
                    for i, table in enumerate(tables, 1):
                        quality = table.get('quality_score', 0)
                        is_financial = table.get('is_financial', False)
                        shape = table.get('shape', [0, 0])
                        
                        markdown_lines.extend([
                            f"**Table {i}**",
                            f"- Quality Score: {quality}/100",
                            f"- Dimensions: {shape[0]} rows × {shape[1]} columns",
                            f"- Financial Table: {'Yes' if is_financial else 'No'}",
                            f"- File: `tables/{table.get('filename', 'unknown')}`",
                            ""
                        ])
            
            # Method analysis
            method_analysis = table_results.get('method_analysis', {})
            if method_analysis:
                recommendations = method_analysis.get('recommendations', [])
                if recommendations:
                    markdown_lines.extend([
                        "### Extraction Recommendations",
                        ""
                    ])
                    for rec in recommendations:
                        markdown_lines.append(f"- {rec}")
                    markdown_lines.append("")
        
        # Add document footer
        markdown_lines.extend([
            "---",
            "",
            "## Document Information",
            f"- **Source**: PDFPlumber with Tesseract OCR fallback",
            f"- **Processing Method**: Sequential page processing with multiple table strategies",
            f"- **Text Extraction**: Native PDF text with OCR backup",
            f"- **Table Detection**: Standard, custom, and financial-focused approaches",
            f"- **Quality Analysis**: Automated scoring and financial table detection",
            f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "*This document uses PDFPlumber's advanced text extraction with intelligent OCR fallback.*"
        ])
        
        return '\n'.join(markdown_lines)

    # =============================================================================
    # JSON Generation Methods
    # =============================================================================
    
    def generate_docling_json(self, doc_id: str) -> str:
        """
        Generate JSON from Docling's structured data with comprehensive provenance.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            str: Path to generated JSON file
        """
        print(f"🔄 Converting Docling data to JSON for: {doc_id}")
        
        # Read Docling's structured content
        docling_text_file = Path(f"data/parsed/docling/{doc_id}/text/structured_content.txt")
        if not docling_text_file.exists():
            print(f"❌ Docling structured content not found: {docling_text_file}")
            return None
        
        with open(docling_text_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Read original extraction results for metadata
        extraction_results_file = Path(f"data/parsed/docling/{doc_id}/docling_extraction_results.json")
        extraction_metadata = {}
        if extraction_results_file.exists():
            with open(extraction_results_file, 'r', encoding='utf-8') as f:
                extraction_metadata = json.load(f)
        
        # Extract structured sections
        structured_sections = self._extract_docling_sections(content)
        
        # Create comprehensive JSON data with provenance
        json_data = {
            "document_id": doc_id,
            "extraction_method": "docling",
            "timestamp": datetime.now().isoformat(),
            "content": {
                "raw_text": content,
                "structured_sections": structured_sections,
                "metadata": {
                    "word_count": len(content.split()),
                    "character_count": len(content),
                    "line_count": len(content.split('\n')),
                    "section_count": len(structured_sections)
                }
            },
            "provenance": {
                "source_file": extraction_metadata.get("pdf_name", f"{doc_id}.pdf"),
                "extraction_config": {
                    "method": "docling",
                    "version": extraction_metadata.get("docling_version", "latest"),
                    "extraction_timestamp": extraction_metadata.get("extraction_timestamp"),
                    "document_type": extraction_metadata.get("document_analysis", {}).get("document_type", "pdf"),
                    "total_pages": extraction_metadata.get("document_analysis", {}).get("total_pages", 0)
                },
                "processing_info": {
                    "content_elements_found": len(extraction_metadata.get("document_analysis", {}).get("content_elements", [])),
                    "has_figures": any("figures" in str(section) for section in structured_sections),
                    "has_tables": any("table" in str(section).lower() for section in structured_sections),
                    "has_formulas": any("formula" in str(section).lower() for section in structured_sections)
                }
            },
            "semantic_tags": self._generate_semantic_tags(content, structured_sections),
            "quality_metrics": {
                "content_coverage": min(1.0, len(content) / 10000),  # Normalized content length
                "structure_quality": min(1.0, len(structured_sections) / 50),  # Normalized section count
                "extraction_confidence": 0.95 if extraction_metadata else 0.8,  # High confidence for docling
                "text_coherence": self._calculate_text_coherence(content)
            }
        }
        
        # Save JSON file
        output_file = self.docling_json_dir / f"{doc_id}_docling_structured.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Docling JSON saved: {output_file}")
        return str(output_file)
    
    def generate_layout_parser_json(self, doc_id: str) -> str:
        """
        Generate JSON from LayoutParser block data.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            str: Path to generated JSON file
        """
        print(f"🔄 Converting LayoutParser blocks to JSON for: {doc_id}")
        
        # Read LayoutParser blocks
        blocks_file = Path(f"data/metadata/blocks/layout_parser/{doc_id}.jsonl")
        if not blocks_file.exists():
            print(f"❌ LayoutParser blocks not found: {blocks_file}")
            return None
        
        blocks = []
        with open(blocks_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    blocks.append(json.loads(line))
        
        # Create structured JSON data
        json_data = {
            "document_id": doc_id,
            "extraction_method": "layout_parser",
            "timestamp": datetime.now().isoformat(),
            "content": {
                "total_blocks": len(blocks),
                "blocks_by_type": self._group_blocks_by_type(blocks),
                "raw_blocks": blocks,
                "metadata": {
                    "block_types": list(set(block.get('type', 'unknown') for block in blocks)),
                    "total_confidence": sum(block.get('confidence', 0) for block in blocks) / len(blocks) if blocks else 0
                }
            }
        }
        
        # Save JSON file
        output_file = self.layout_parser_json_dir / f"{doc_id}_layout_parser_blocks.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ LayoutParser JSON saved: {output_file}")
        return str(output_file)
    
    
    def generate_hybrid_json(self, doc_id: str) -> str:
        """
        Generate JSON from Hybrid extraction data with comprehensive provenance.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            str: Path to generated JSON file
        """
        print(f"🔄 Converting Hybrid extraction to JSON for: {doc_id}")
        
        hybrid_dir = Path(f"data/parsed/hybrid/{doc_id}")
        if not hybrid_dir.exists():
            print(f"❌ Hybrid extraction directory not found: {hybrid_dir}")
            return None
        
        # Read summary data
        summary_file = hybrid_dir / "hybrid_extraction_results.json"
        if not summary_file.exists():
            print(f"❌ Hybrid summary not found: {summary_file}")
            return None
        
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        # Extract content from pages
        pages_data = summary_data.get("text_extraction", {}).get("pages", [])
        total_content = ""
        page_statistics = []
        
        for page in pages_data:
            page_file = hybrid_dir / "text" / page.get("text_file", "")
            if page_file.exists():
                with open(page_file, 'r', encoding='utf-8') as f:
                    page_content = f.read()
                    total_content += page_content + "\n"
                    page_statistics.append({
                        "page_number": page.get("page_number"),
                        "text_length": len(page_content),
                        "used_ocr": page.get("used_ocr", False),
                        "success": page.get("success", False)
                    })
        
        # Create comprehensive JSON data with provenance
        json_data = {
            "document_id": doc_id,
            "extraction_method": "hybrid",
            "timestamp": datetime.now().isoformat(),
            "content": {
                "raw_text": total_content,
                "page_breakdown": page_statistics,
                "extraction_summary": summary_data.get("text_extraction", {}),
                "metadata": {
                    "total_pages": summary_data.get("text_extraction", {}).get("total_pages", 0),
                    "word_count": len(total_content.split()),
                    "character_count": len(total_content),
                    "pages_with_ocr": sum(1 for p in pages_data if p.get("used_ocr", False)),
                    "successful_pages": sum(1 for p in pages_data if p.get("success", False))
                }
            },
            "provenance": {
                "source_file": summary_data.get("pdf_info", {}).get("name", f"{doc_id}.pdf"),
                "extraction_config": {
                    "method": "hybrid_pdfplumber_tesseract_ocr",
                    "extraction_timestamp": summary_data.get("extraction_timestamp"),
                    "processing_time_seconds": summary_data.get("pdf_info", {}).get("processing_time_seconds", 0),
                    "ocr_fallback_enabled": any(p.get("used_ocr", False) for p in pages_data),
                    "total_pages": summary_data.get("text_extraction", {}).get("total_pages", 0)
                },
                "processing_info": {
                    "extraction_methods": ["pdfplumber", "tesseract_ocr"],
                    "pages_processed": len(pages_data),
                    "ocr_usage_rate": sum(1 for p in pages_data if p.get("used_ocr", False)) / len(pages_data) if pages_data else 0,
                    "success_rate": sum(1 for p in pages_data if p.get("success", False)) / len(pages_data) if pages_data else 0
                }
            },
            "semantic_tags": self._generate_semantic_tags(total_content, []),
            "quality_metrics": {
                "content_coverage": min(1.0, len(total_content) / 10000),
                "extraction_success_rate": sum(1 for p in pages_data if p.get("success", False)) / len(pages_data) if pages_data else 0,
                "ocr_dependency": sum(1 for p in pages_data if p.get("used_ocr", False)) / len(pages_data) if pages_data else 0,
                "text_coherence": self._calculate_text_coherence(total_content),
                "processing_efficiency": 1.0 / (summary_data.get("pdf_info", {}).get("processing_time_seconds", 1) / 60)  # pages per minute
            }
        }
        
        # Save JSON file
        output_file = self.hybrid_json_dir / f"{doc_id}_hybrid_extraction.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Hybrid JSON saved: {output_file}")
        return str(output_file)
    
    def generate_pdfplumber_tesseract_json(self, doc_id: str) -> str:
        """
        Generate JSON from PDFPlumber-Tesseract extraction data with comprehensive provenance.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            str: Path to generated JSON file
        """
        print(f"🔄 Converting PDFPlumber-Tesseract extraction to JSON for: {doc_id}")
        
        pdfplumber_dir = Path(f"data/parsed/pdfplumber_tesseract/{doc_id}")
        if not pdfplumber_dir.exists():
            print(f"❌ PDFPlumber-Tesseract extraction directory not found: {pdfplumber_dir}")
            return None
        
        # Read summary data
        summary_file = pdfplumber_dir / "pdfplumber_tesseract_extraction_results.json"
        if not summary_file.exists():
            print(f"❌ PDFPlumber-Tesseract summary not found: {summary_file}")
            return None
        
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        # Extract content from pages
        pages_data = summary_data.get("text_extraction", {}).get("pages", [])
        total_content = ""
        page_statistics = []
        
        for page in pages_data:
            page_file = pdfplumber_dir / "text" / page.get("text_file", "")
            if page_file.exists():
                with open(page_file, 'r', encoding='utf-8') as f:
                    page_content = f.read()
                    total_content += page_content + "\n"
                    page_statistics.append({
                        "page_number": page.get("page_number"),
                        "text_length": len(page_content),
                        "used_ocr": page.get("used_ocr", False),
                        "success": page.get("success", False)
                    })
        
        # Create comprehensive JSON data with provenance
        json_data = {
            "document_id": doc_id,
            "extraction_method": "pdfplumber_tesseract",
            "timestamp": datetime.now().isoformat(),
            "content": {
                "raw_text": total_content,
                "page_breakdown": page_statistics,
                "extraction_summary": summary_data.get("text_extraction", {}),
                "metadata": {
                    "total_pages": summary_data.get("text_extraction", {}).get("total_pages", 0),
                    "word_count": len(total_content.split()),
                    "character_count": len(total_content),
                    "pages_with_ocr": sum(1 for p in pages_data if p.get("used_ocr", False)),
                    "successful_pages": sum(1 for p in pages_data if p.get("success", False))
                }
            },
            "provenance": {
                "source_file": summary_data.get("pdf_info", {}).get("name", f"{doc_id}.pdf"),
                "extraction_config": {
                    "method": "pdfplumber_tesseract_ocr",
                    "extraction_timestamp": summary_data.get("extraction_timestamp"),
                    "processing_time_seconds": summary_data.get("pdf_info", {}).get("processing_time_seconds", 0),
                    "ocr_enabled": any(p.get("used_ocr", False) for p in pages_data),
                    "total_pages": summary_data.get("text_extraction", {}).get("total_pages", 0)
                },
                "processing_info": {
                    "extraction_methods": ["pdfplumber", "tesseract_ocr"],
                    "pages_processed": len(pages_data),
                    "ocr_usage_rate": sum(1 for p in pages_data if p.get("used_ocr", False)) / len(pages_data) if pages_data else 0,
                    "success_rate": sum(1 for p in pages_data if p.get("success", False)) / len(pages_data) if pages_data else 0,
                    "primary_extraction_method": "pdfplumber"
                }
            },
            "semantic_tags": self._generate_semantic_tags(total_content, []),
            "quality_metrics": {
                "content_coverage": min(1.0, len(total_content) / 10000),
                "extraction_success_rate": sum(1 for p in pages_data if p.get("success", False)) / len(pages_data) if pages_data else 0,
                "ocr_dependency": sum(1 for p in pages_data if p.get("used_ocr", False)) / len(pages_data) if pages_data else 0,
                "text_coherence": self._calculate_text_coherence(total_content),
                "processing_efficiency": 1.0 / (summary_data.get("pdf_info", {}).get("processing_time_seconds", 1) / 60),  # pages per minute
                "extraction_confidence": 0.85 if sum(1 for p in pages_data if not p.get("used_ocr", False)) > len(pages_data) * 0.5 else 0.7
            }
        }
        
        # Save JSON file
        output_file = self.pdfplumber_tesseract_json_dir / f"{doc_id}_pdfplumber_tesseract.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ PDFPlumber-Tesseract JSON saved: {output_file}")
        return str(output_file)
    
    # Helper methods for JSON generation
    def _extract_docling_sections(self, content: str) -> List[Dict]:
        """Extract structured sections from Docling content."""
        sections = []
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            if line.strip() and (line.startswith('#') or self._is_heading_line(line)):
                # Save previous section
                if current_section:
                    sections.append({
                        "title": current_section,
                        "content": '\n'.join(current_content).strip(),
                        "word_count": len(' '.join(current_content).split())
                    })
                
                # Start new section
                current_section = line.strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections.append({
                "title": current_section,
                "content": '\n'.join(current_content).strip(),
                "word_count": len(' '.join(current_content).split())
            })
        
        return sections
    
    def _group_blocks_by_type(self, blocks: List[Dict]) -> Dict:
        """Group blocks by their type."""
        grouped = {}
        for block in blocks:
            block_type = block.get('type', 'unknown')
            if block_type not in grouped:
                grouped[block_type] = []
            grouped[block_type].append(block)
        
        # Add summary statistics
        for block_type, type_blocks in grouped.items():
            grouped[block_type] = {
                "count": len(type_blocks),
                "blocks": type_blocks,
                "avg_confidence": sum(b.get('confidence', 0) for b in type_blocks) / len(type_blocks) if type_blocks else 0
            }
        
        return grouped

    # =============================================================================
    # Text Generation Methods
    # =============================================================================
    
    def generate_docling_text(self, doc_id: str) -> str:
        """
        Generate clean text from Docling's structured data.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            str: Path to generated text file
        """
        print(f"🔄 Converting Docling data to clean text for: {doc_id}")
        
        # Read Docling's structured content
        docling_text_file = Path(f"data/parsed/docling/{doc_id}/text/structured_content.txt")
        if not docling_text_file.exists():
            print(f"❌ Docling structured content not found: {docling_text_file}")
            return None
        
        with open(docling_text_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Include tables in the text content
        tables_content = self._extract_docling_tables_text(doc_id)
        
        # Create clean text output with tables
        text_content = self._convert_to_clean_text_with_tables(content, tables_content, "Docling", doc_id)
        
        # Save text file
        output_file = self.docling_text_dir / f"{doc_id}_docling_clean.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        print(f"✅ Docling text saved: {output_file}")
        return str(output_file)
    
    def generate_layout_parser_text(self, doc_id: str) -> str:
        """
        Generate clean text from LayoutParser block data.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            str: Path to generated text file
        """
        print(f"🔄 Converting LayoutParser blocks to clean text for: {doc_id}")
        
        # Read LayoutParser blocks
        blocks_file = Path(f"data/metadata/blocks/layout_parser/{doc_id}.jsonl")
        if not blocks_file.exists():
            print(f"❌ LayoutParser blocks not found: {blocks_file}")
            return None
        
        blocks = []
        with open(blocks_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    blocks.append(json.loads(line))
        
        # Extract text from blocks in order
        text_lines = [
            f"DOCUMENT: {doc_id}",
            f"EXTRACTION METHOD: LayoutParser",
            f"GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"TOTAL BLOCKS: {len(blocks)}",
            "",
            "=" * 50,
            "EXTRACTED TEXT CONTENT",
            "=" * 50,
            ""
        ]
        
        # Sort blocks by position (top to bottom, left to right)
        sorted_blocks = sorted(blocks, key=lambda b: (
            b.get('page_number', 0), 
            b.get('bounding_box', {}).get('y1', 0), 
            b.get('bounding_box', {}).get('x1', 0)
        ))
        
        for i, block in enumerate(sorted_blocks, 1):
            block_type = block.get('block_type', 'unknown')
            # Get text from content.text field
            text = block.get('content', {}).get('text', '').strip()
            confidence = block.get('confidence', 0)
            page_number = block.get('page_number', 0)
            
            if text:
                text_lines.extend([
                    f"[Page {page_number}, Block {i}] {block_type.upper()} (Confidence: {confidence:.2f})",
                    text,
                    ""
                ])
        
        text_content = '\n'.join(text_lines)
        
        # Save text file
        output_file = self.layout_parser_text_dir / f"{doc_id}_layout_parser_clean.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        print(f"✅ LayoutParser text saved: {output_file}")
        return str(output_file)

    
    def generate_hybrid_text(self, doc_id: str) -> str:
        """
        Generate clean text from Hybrid extraction data.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            str: Path to generated text file
        """
        print(f"🔄 Converting Hybrid extraction to clean text for: {doc_id}")
        
        hybrid_dir = Path(f"data/parsed/hybrid/{doc_id}")
        if not hybrid_dir.exists():
            print(f"❌ Hybrid extraction directory not found: {hybrid_dir}")
            return None
        
        # Read summary data
        summary_file = hybrid_dir / "hybrid_extraction_results.json"
        if not summary_file.exists():
            print(f"❌ Hybrid summary not found: {summary_file}")
            return None
        
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        # Extract content from text files
        text_lines = [
            f"DOCUMENT: {doc_id}",
            f"EXTRACTION METHOD: Hybrid",
            f"GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "=" * 50,
            "HYBRID EXTRACTION RESULTS",
            "=" * 50,
            ""
        ]
        
        # Get text extraction data
        text_extraction = summary_data.get("text_extraction", {})
        pages = text_extraction.get("pages", [])
        total_pages = text_extraction.get("total_pages", 0)
        
        text_lines.extend([
            f"Total Pages: {total_pages}",
            f"Successfully Extracted Pages: {len([p for p in pages if p.get('success', False)])}",
            f"Pages Using OCR: {len([p for p in pages if p.get('used_ocr', False)])}",
            "",
            "EXTRACTED TEXT CONTENT:",
            "-" * 50,
            ""
        ])
        
        # Read text content from individual page files
        text_dir = hybrid_dir / "text"
        if text_dir.exists():
            for page_info in sorted(pages, key=lambda p: p.get('page_number', 0)):
                page_num = page_info.get('page_number')
                text_file_name = page_info.get('text_file')
                used_ocr = page_info.get('used_ocr', False)
                success = page_info.get('success', False)
                
                if text_file_name and success:
                    text_file_path = text_dir / text_file_name
                    if text_file_path.exists():
                        try:
                            with open(text_file_path, 'r', encoding='utf-8') as f:
                                page_content = f.read().strip()
                            
                            if page_content:
                                extraction_method = "OCR" if used_ocr else "PDFPlumber"
                                text_lines.extend([
                                    f"=== PAGE {page_num} ({extraction_method}) ===",
                                    "",
                                    page_content,
                                    "",
                                    ""
                                ])
                        except Exception as e:
                            text_lines.extend([
                                f"=== PAGE {page_num} (ERROR) ===",
                                f"Error reading file: {e}",
                                "",
                                ""
                            ])
        
        # Add tables section
        tables_content = self._extract_hybrid_tables_text(hybrid_dir)
        if tables_content:
            text_lines.extend([
                "",
                "=" * 50,
                "EXTRACTED TABLES",
                "=" * 50,
                "",
                tables_content
            ])
        
        text_content = '\n'.join(text_lines)
        
        # Save text file
        output_file = self.hybrid_text_dir / f"{doc_id}_hybrid_clean.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        print(f"✅ Hybrid text saved: {output_file}")
        return str(output_file)
    
    def generate_pdfplumber_tesseract_text(self, doc_id: str) -> str:
        """
        Generate clean text from PDFPlumber-Tesseract extraction data.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            str: Path to generated text file
        """
        print(f"🔄 Converting PDFPlumber-Tesseract extraction to clean text for: {doc_id}")
        
        pdfplumber_dir = Path(f"data/parsed/pdfplumber_tesseract/{doc_id}")
        if not pdfplumber_dir.exists():
            print(f"❌ PDFPlumber-Tesseract extraction directory not found: {pdfplumber_dir}")
            return None
        
        # Read summary data  
        summary_file = pdfplumber_dir / "pdfplumber_tesseract_extraction_results.json"
        if not summary_file.exists():
            print(f"❌ PDFPlumber-Tesseract summary not found: {summary_file}")
            return None
        
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        # Extract content from text files
        text_lines = [
            f"DOCUMENT: {doc_id}",
            f"EXTRACTION METHOD: PDFPlumber-Tesseract",
            f"GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "=" * 50,
            "PDFPLUMBER-TESSERACT EXTRACTION RESULTS",
            "=" * 50,
            ""
        ]
        
        # Get text extraction data
        text_extraction = summary_data.get("text_extraction", {})
        pages = text_extraction.get("pages", [])
        total_pages = text_extraction.get("total_pages", 0)
        
        text_lines.extend([
            f"Total Pages: {total_pages}",
            f"Successfully Extracted Pages: {len([p for p in pages if p.get('success', False)])}",
            f"Pages Using OCR: {len([p for p in pages if p.get('used_ocr', False)])}",
            "",
            "EXTRACTED TEXT CONTENT:",
            "-" * 50,
            ""
        ])
        
        # Read text content from individual page files
        text_dir = pdfplumber_dir / "text"
        if text_dir.exists():
            for page_info in sorted(pages, key=lambda p: p.get('page_number', 0)):
                page_num = page_info.get('page_number')
                text_file_name = page_info.get('text_file')
                used_ocr = page_info.get('used_ocr', False)
                success = page_info.get('success', False)
                
                if text_file_name and success:
                    text_file_path = text_dir / text_file_name
                    if text_file_path.exists():
                        try:
                            with open(text_file_path, 'r', encoding='utf-8') as f:
                                page_content = f.read().strip()
                            
                            if page_content:
                                extraction_method = "OCR" if used_ocr else "PDFPlumber"
                                text_lines.extend([
                                    f"=== PAGE {page_num} ({extraction_method}) ===",
                                    "",
                                    page_content,
                                    "",
                                    ""
                                ])
                        except Exception as e:
                            text_lines.extend([
                                f"=== PAGE {page_num} (ERROR) ===",
                                f"Error reading file: {e}",
                                "",
                                ""
                            ])
        
        # Add tables section
        tables_content = self._extract_pdfplumber_tables_text(pdfplumber_dir)
        if tables_content:
            text_lines.extend([
                "",
                "=" * 50,
                "EXTRACTED TABLES",
                "=" * 50,
                "",
                tables_content
            ])
        
        text_content = '\n'.join(text_lines)
        
        # Save text file
        output_file = self.pdfplumber_tesseract_text_dir / f"{doc_id}_pdfplumber_tesseract_clean.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        print(f"✅ PDFPlumber-Tesseract text saved: {output_file}")
        return str(output_file)
    
    def _convert_to_clean_text(self, content: str, method: str, doc_id: str) -> str:
        """Convert content to clean, formatted text."""
        lines = [
            f"DOCUMENT: {doc_id}",
            f"EXTRACTION METHOD: {method}",
            f"GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "=" * 50,
            "EXTRACTED TEXT CONTENT",
            "=" * 50,
            "",
            content.strip()
        ]
        
        return '\n'.join(lines)

    # =============================================================================
    # Unified Generation Methods
    # =============================================================================
    
    def generate_all_formats(self, doc_id: str, method: str) -> Dict[str, str]:
        """
        Generate all formats (markdown, JSON, text) for a specific method.
        
        Args:
            doc_id: Document identifier
            method: Extraction method ('docling', 'layout_parser', 'hybrid', 'pdfplumber_tesseract')
            
        Returns:
            Dict[str, str]: Paths to generated files {'markdown': path, 'json': path, 'text': path}
        """
        results = {'markdown': None, 'json': None, 'text': None}
        
        method_generators = {
            'docling': {
                'markdown': self.generate_docling_markdown,
                'json': self.generate_docling_json,
                'text': self.generate_docling_text
            },
            'layout_parser': {
                'markdown': self.generate_layout_parser_markdown,
                'json': self.generate_layout_parser_json,
                'text': self.generate_layout_parser_text
            },
            'hybrid': {
                'markdown': self.generate_hybrid_markdown,
                'json': self.generate_hybrid_json,
                'text': self.generate_hybrid_text
            },
            'pdfplumber_tesseract': {
                'markdown': self.generate_pdfplumber_tesseract_markdown,
                'json': self.generate_pdfplumber_tesseract_json,
                'text': self.generate_pdfplumber_tesseract_text
            }
        }
        
        if method not in method_generators:
            print(f"❌ Unknown method: {method}")
            return results
        
        generators = method_generators[method]
        
        # Generate each format
        for format_type, generator_func in generators.items():
            try:
                result_path = generator_func(doc_id)
                results[format_type] = result_path
            except Exception as e:
                print(f"  ❌ {format_type.title()} generation failed: {e}")
        
        return results
    
    def generate_all_methods_all_formats(self, doc_id: str) -> Dict[str, Dict[str, str]]:
        """
        Generate all formats for all available methods for a document.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            Dict[str, Dict[str, str]]: Nested dict with method -> format -> path mapping
        """
        all_results = {}
        
        # Check which methods have data for this document
        available_methods = []
        
        if Path(f"data/parsed/docling/{doc_id}/text/structured_content.txt").exists():
            available_methods.append('docling')
        
        if Path(f"data/metadata/blocks/layout_parser/{doc_id}.jsonl").exists():
            available_methods.append('layout_parser')
        
        if Path(f"data/parsed/hybrid/{doc_id}/hybrid_extraction_results.json").exists():
            available_methods.append('hybrid')
        
        if Path(f"data/parsed/pdfplumber_tesseract/{doc_id}/pdfplumber_tesseract_extraction_results.json").exists():
            available_methods.append('pdfplumber_tesseract')
        
        print(f"📄 Generating all formats for {doc_id} using methods: {', '.join(available_methods)}")
        
        for method in available_methods:
            print(f"  🔄 Processing {method}...")
            all_results[method] = self.generate_all_formats(doc_id, method)
        
        return all_results
    
    def _generate_semantic_tags(self, content: str, structured_sections: list) -> list:
        """
        Generate semantic tags based on content analysis.
        
        Args:
            content: Text content to analyze
            structured_sections: List of structured sections (for docling)
            
        Returns:
            list: List of semantic tags
        """
        tags = []
        content_lower = content.lower()
        
        # Document type indicators
        if any(word in content_lower for word in ["financial", "annual report", "10-k", "earnings", "revenue"]):
            tags.append("financial_document")
        
        if any(word in content_lower for word in ["technical", "specification", "manual", "documentation"]):
            tags.append("technical_document")
        
        if any(word in content_lower for word in ["research", "study", "analysis", "methodology"]):
            tags.append("research_document")
        
        # Content features
        if "table" in content_lower or len([s for s in structured_sections if "table" in str(s).lower()]) > 0:
            tags.append("contains_tables")
        
        if "figure" in content_lower or "chart" in content_lower or "graph" in content_lower:
            tags.append("contains_figures")
        
        if any(word in content_lower for word in ["formula", "equation", "calculation"]):
            tags.append("contains_formulas")
        
        # Length indicators
        word_count = len(content.split())
        if word_count > 10000:
            tags.append("long_document")
        elif word_count < 1000:
            tags.append("short_document")
        else:
            tags.append("medium_document")
        
        # Structure indicators
        if len(structured_sections) > 10:
            tags.append("well_structured")
        elif len(structured_sections) < 3:
            tags.append("minimal_structure")
        
        return tags
    
    def _calculate_text_coherence(self, content: str) -> float:
        """
        Calculate a simple text coherence score based on various metrics.
        
        Args:
            content: Text content to analyze
            
        Returns:
            float: Coherence score between 0 and 1
        """
        if not content or len(content.strip()) == 0:
            return 0.0
        
        # Basic metrics
        words = content.split()
        sentences = content.split('.')
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        if len(words) == 0:
            return 0.0
        
        # Calculate various coherence indicators
        avg_word_length = sum(len(word) for word in words) / len(words)
        avg_sentence_length = len(words) / max(len(sentences), 1)
        paragraph_consistency = len(paragraphs) / max(len(content.split('\n')), 1)
        
        # Normalize metrics (rough heuristics)
        word_length_score = min(1.0, avg_word_length / 6.0)  # Assume 6 chars is optimal
        sentence_length_score = min(1.0, avg_sentence_length / 20.0)  # Assume 20 words is optimal
        structure_score = min(1.0, paragraph_consistency * 2)  # Reward paragraph structure
        
        # Check for repeated patterns (low coherence indicator)
        unique_words = len(set(word.lower() for word in words))
        vocabulary_diversity = unique_words / len(words)
        
        # Combined score
        coherence_score = (
            word_length_score * 0.2 +
            sentence_length_score * 0.3 +
            structure_score * 0.2 +
            vocabulary_diversity * 0.3
        )
        
        return min(1.0, coherence_score)
    
    def _convert_to_clean_text_with_tables(self, content: str, tables_content: str, method: str, doc_id: str) -> str:
        """Convert content to clean, formatted text including tables."""
        lines = [
            f"DOCUMENT: {doc_id}",
            f"EXTRACTION METHOD: {method}",
            f"GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "=" * 50,
            "EXTRACTED TEXT CONTENT",
            "=" * 50,
            "",
            content.strip()
        ]
        
        if tables_content:
            lines.extend([
                "",
                "",
                "=" * 50,
                "EXTRACTED TABLES",
                "=" * 50,
                "",
                tables_content
            ])
        
        return '\n'.join(lines)
    
    def _extract_docling_tables_text(self, doc_id: str) -> str:
        """Extract table content from Docling tables directory."""
        tables_dir = Path(f"data/parsed/docling/{doc_id}/tables")
        if not tables_dir.exists():
            return ""
        
        table_lines = []
        table_files = sorted(tables_dir.glob("markdown_table_*.txt"))
        
        for i, table_file in enumerate(table_files, 1):
            try:
                with open(table_file, 'r', encoding='utf-8') as f:
                    table_content = f.read().strip()
                
                if table_content:
                    table_lines.extend([
                        f"--- TABLE {i} ---",
                        f"Source: {table_file.name}",
                        "",
                        table_content,
                        "",
                        ""
                    ])
            except Exception as e:
                table_lines.extend([
                    f"--- TABLE {i} (ERROR) ---",
                    f"Error reading {table_file.name}: {e}",
                    "",
                    ""
                ])
        
        return '\n'.join(table_lines)
    
    def _extract_hybrid_tables_text(self, hybrid_dir: Path) -> str:
        """Extract table content from Hybrid tables directory."""
        tables_dir = hybrid_dir / "tables"
        if not tables_dir.exists():
            return ""
        
        table_lines = []
        
        # Group tables by method
        camelot_lattice_files = sorted(tables_dir.glob("camelot_lattice_*.csv"))
        camelot_stream_files = sorted(tables_dir.glob("camelot_stream_*.csv"))
        pdfplumber_files = sorted(tables_dir.glob("pdfplumber_*.csv"))
        
        # Process Camelot Lattice tables
        if camelot_lattice_files:
            table_lines.extend([
                "--- CAMELOT LATTICE TABLES ---",
                ""
            ])
            for i, table_file in enumerate(camelot_lattice_files, 1):
                table_content = self._read_csv_as_text(table_file)
                if table_content:
                    table_lines.extend([
                        f"Table {i}: {table_file.name}",
                        "",
                        table_content,
                        "",
                        ""
                    ])
        
        # Process Camelot Stream tables
        if camelot_stream_files:
            table_lines.extend([
                "--- CAMELOT STREAM TABLES ---",
                ""
            ])
            for i, table_file in enumerate(camelot_stream_files, 1):
                table_content = self._read_csv_as_text(table_file)
                if table_content:
                    table_lines.extend([
                        f"Table {i}: {table_file.name}",
                        "",
                        table_content,
                        "",
                        ""
                    ])
        
        # Process PDFPlumber tables
        if pdfplumber_files:
            table_lines.extend([
                "--- PDFPLUMBER TABLES ---",
                ""
            ])
            for i, table_file in enumerate(pdfplumber_files, 1):
                table_content = self._read_csv_as_text(table_file)
                if table_content:
                    table_lines.extend([
                        f"Table {i}: {table_file.name}",
                        "",
                        table_content,
                        "",
                        ""
                    ])
        
        return '\n'.join(table_lines)
    
    def _extract_pdfplumber_tables_text(self, pdfplumber_dir: Path) -> str:
        """Extract table content from PDFPlumber-Tesseract tables directory."""
        tables_dir = pdfplumber_dir / "tables"
        if not tables_dir.exists():
            return ""
        
        table_lines = []
        
        # Group tables by type
        standard_files = sorted(tables_dir.glob("standard_*.csv"))
        financial_files = sorted(tables_dir.glob("financial_*.csv"))
        custom_files = sorted(tables_dir.glob("custom_*.csv"))
        
        # Process Standard tables
        if standard_files:
            table_lines.extend([
                "--- STANDARD TABLES ---",
                ""
            ])
            for i, table_file in enumerate(standard_files, 1):
                table_content = self._read_csv_as_text(table_file)
                if table_content:
                    table_lines.extend([
                        f"Table {i}: {table_file.name}",
                        "",
                        table_content,
                        "",
                        ""
                    ])
        
        # Process Financial tables
        if financial_files:
            table_lines.extend([
                "--- FINANCIAL TABLES ---",
                ""
            ])
            for i, table_file in enumerate(financial_files, 1):
                table_content = self._read_csv_as_text(table_file)
                if table_content:
                    table_lines.extend([
                        f"Table {i}: {table_file.name}",
                        "",
                        table_content,
                        "",
                        ""
                    ])
        
        # Process Custom tables
        if custom_files:
            table_lines.extend([
                "--- CUSTOM TABLES ---",
                ""
            ])
            for i, table_file in enumerate(custom_files, 1):
                table_content = self._read_csv_as_text(table_file)
                if table_content:
                    table_lines.extend([
                        f"Table {i}: {table_file.name}",
                        "",
                        table_content,
                        "",
                        ""
                    ])
        
        return '\n'.join(table_lines)
    
    def _read_csv_as_text(self, csv_file: Path) -> str:
        """Read CSV file and convert to formatted text."""
        try:
            import csv
            with open(csv_file, 'r', encoding='utf-8') as f:
                csv_reader = csv.reader(f)
                rows = list(csv_reader)
            
            if not rows:
                return ""
            
            # Convert to text table format
            text_lines = []
            for row in rows:
                # Join row cells with tab separator for better alignment
                text_lines.append('\t'.join(str(cell).strip() for cell in row))
            
            return '\n'.join(text_lines)
        except Exception as e:
            return f"Error reading CSV: {e}"


def main():
    """Demonstrate multi-format report generation for all extraction methods. Thhnf"""
    print("=== Multi-Format Report Generation ===")
    print("Creating tailored outputs in markdown, JSON, and text formats for each extraction method")
    print()
    
    generator = MethodSpecificReportGenerator()
    
    # Find available documents
    doc_ids = set()
    
    # Check for Docling documents
    docling_dir = Path("data/parsed/docling")
    if docling_dir.exists():
        for doc_dir in docling_dir.iterdir():
            if doc_dir.is_dir():
                doc_ids.add(doc_dir.name)
    
    # Check for LayoutParser documents
    layout_parser_dir = Path("data/metadata/blocks/layout_parser")
    if layout_parser_dir.exists():
        for jsonl_file in layout_parser_dir.glob("*.jsonl"):
            doc_ids.add(jsonl_file.stem)
    
    # Check for Hybrid documents
    hybrid_dir = Path("data/parsed/hybrid")
    if hybrid_dir.exists():
        for doc_dir in hybrid_dir.iterdir():
            if doc_dir.is_dir():
                doc_ids.add(doc_dir.name)
    
    # Check for PDFPlumber-Tesseract documents
    pdfplumber_tesseract_dir = Path("data/parsed/pdfplumber_tesseract")
    if pdfplumber_tesseract_dir.exists():
        for doc_dir in pdfplumber_tesseract_dir.iterdir():
            if doc_dir.is_dir():
                doc_ids.add(doc_dir.name)
    
    if not doc_ids:
        print("❌ No documents found. Please run the extractors first.")
        return
    
    print(f"Found {len(doc_ids)} documents: {', '.join(sorted(doc_ids))}")
    print()
    
    # Generate all formats for each document
    for doc_id in sorted(doc_ids):
        print(f"📄 Processing document: {doc_id}")
        results = generator.generate_all_methods_all_formats(doc_id)
        
        # Display results for each method
        for method, format_results in results.items():
            print(f"  🔄 {method.upper()}:")
            for format_type, file_path in format_results.items():
                if file_path:
                    print(f"    ✅ {format_type.title()}: {file_path}")
                else:
                    print(f"    ❌ {format_type.title()}: Failed")
        
        print()
    
    print("🎉 Multi-format report generation complete!")
    print(f"📁 Base output directory: {generator.base_reports_dir}")
    print()
    print("Generated formats:")
    print(f"  📝 Markdown: {generator.markdown_base_dir}")
    print(f"  📊 JSON: {generator.json_base_dir}")
    print(f"  📄 Text: {generator.text_base_dir}")
    print()
    print("Available methods:")
    for method in generator.methods:
        print(f"  - {method}")
    print()
    print("Example output structure:")
    print("  data/reports/")
    print("  ├── markdown/")
    print("  │   ├── docling/")
    print("  │   ├── layout_parser/")
    print("  │   └── ...")
    print("  ├── json/")
    print("  │   ├── docling/")
    print("  │   ├── layout_parser/")
    print("  │   └── ...")
    print("  └── text/")
    print("      ├── docling/")
    print("      ├── layout_parser/")
    print("      └── ...")


if __name__ == "__main__":
    main()