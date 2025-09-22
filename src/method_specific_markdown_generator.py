#!/usr/bin/env python3
"""
Method-Specific Markdown Generation

This module creates tailored markdown outputs for different extraction methods:
- Docling: Converts structured text to proper markdown
- LayoutParser: Reassembles blocks into structured sections  
- Traditional: Basic text-to-markdown conversion
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class MethodSpecificMarkdownGenerator:
    """
    Generate method-specific markdown outputs tailored to each extraction approach.
    """
    
    def __init__(self, output_dir: str = "data/reports/markdown"):
        """
        Initialize the markdown generator.
        
        Args:
            output_dir: Base directory to save generated markdown files
        """
        self.base_output_dir = Path(output_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create method-specific subdirectories
        self.docling_dir = self.base_output_dir / "docling"
        self.layout_parser_dir = self.base_output_dir / "layout_parser"
        self.hybrid_dir = self.base_output_dir / "hybrid"
        self.pdfplumber_tesseract_dir = self.base_output_dir / "pdfplumber_tesseract"
        # self.traditional_dir = self.base_output_dir / "traditional"
        
        # Create all method directories
        for method_dir in [self.docling_dir, self.layout_parser_dir, 
                          self.hybrid_dir, self.pdfplumber_tesseract_dir]:
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
        output_file = self.docling_dir / f"{doc_id}_docling_converted.md"
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
        output_file = self.layout_parser_dir / f"{doc_id}_layout_parser_reassembled.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ LayoutParser markdown saved: {output_file}")
        return str(output_file)
    
    def generate_traditional_markdown(self, doc_id: str) -> str:
        """
        Generate markdown from Traditional extraction output.
        
        Traditional methods typically provide simple text files.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            str: Path to generated markdown file
        """
        print(f"🔄 Converting Traditional extraction to Markdown for: {doc_id}")
        
        # Look for traditional extraction files
        traditional_dir = Path(f"data/parsed/traditional/{doc_id}")
        if not traditional_dir.exists():
            print(f"❌ Traditional extraction not found: {traditional_dir}")
            return None
        
        # Collect all text files
        text_files = list(traditional_dir.rglob("*.txt"))
        markdown_content = self._convert_traditional_files_to_markdown(text_files, doc_id)
        
        # Save markdown file in traditional-specific folder
        output_file = self.traditional_dir / f"{doc_id}_traditional_converted.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ Traditional markdown saved: {output_file}")
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
        summary_file = hybrid_dir / "complete_extraction_summary.json"
        if not summary_file.exists():
            print(f"❌ Hybrid summary not found: {summary_file}")
            return None
        
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        # Generate markdown content
        markdown_content = self._convert_hybrid_extraction_to_markdown(summary_data, doc_id, hybrid_dir)
        
        # Save markdown file in hybrid-specific folder
        output_file = self.hybrid_dir / f"{doc_id}_hybrid_extraction.md"
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
        summary_file = pdfplumber_dir / "table_extraction_summary.json"
        if not summary_file.exists():
            print(f"❌ PDFPlumber-Tesseract summary not found: {summary_file}")
            return None
        
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        # Generate markdown content
        markdown_content = self._convert_pdfplumber_tesseract_to_markdown(summary_data, doc_id, pdfplumber_dir)
        
        # Save markdown file in pdfplumber_tesseract-specific folder
        output_file = self.pdfplumber_tesseract_dir / f"{doc_id}_pdfplumber_tesseract.md"
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
    
    def _convert_traditional_files_to_markdown(self, text_files: List[Path], doc_id: str) -> str:
        """
        Convert traditional extraction files to markdown.
        
        Args:
            text_files: List of text file paths
            doc_id: Document identifier
            
        Returns:
            str: Formatted markdown content
        """
        markdown_lines = []
        
        # Document header
        markdown_lines.extend([
            f"# Document: {doc_id}",
            "## Extraction Method: 📝 Traditional (Rule-Based Extraction)",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"**Files Processed**: {len(text_files)}",
            "",
            "---",
            ""
        ])
        
        # Process each file
        for text_file in sorted(text_files):
            file_name = text_file.name
            relative_path = text_file.relative_to(Path(f"data/parsed/traditional/{doc_id}"))
            
            markdown_lines.extend([
                f"## {file_name}",
                f"*Source: {relative_path}*",
                ""
            ])
            
            try:
                with open(text_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                if content:
                    markdown_lines.append(content)
                else:
                    markdown_lines.append("*No content in this file*")
                
            except Exception as e:
                markdown_lines.append(f"*Error reading file: {e}*")
            
            markdown_lines.extend(["", "---", ""])
        
        # Add document footer
        markdown_lines.extend([
            "",
            "## Document Information",
            f"- **Source**: Traditional rule-based extraction",
            f"- **Files Processed**: {len(text_files)}",
            f"- **Processing Method**: Simple text file conversion",
            f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "*This document was converted from traditional extraction text files.*"
        ])
        
        return '\n'.join(markdown_lines)
    
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
                            # Show first 500 characters as preview
                            preview = content[:500] + "..." if len(content) > 500 else content
                            markdown_lines.extend([
                                "**Preview:**",
                                "```",
                                preview,
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


def main():
    """Demonstrate method-specific markdown generation."""
    print("=== Method-Specific Markdown Generation ===")
    print("Creating tailored markdown outputs for each extraction method")
    print()
    
    generator = MethodSpecificMarkdownGenerator()
    
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
    
    # Check for Traditional documents
    # traditional_dir = Path("data/parsed/traditional")
    # if traditional_dir.exists():
    #     for doc_dir in traditional_dir.iterdir():
    #         if doc_dir.is_dir():
    #             doc_ids.add(doc_dir.name)
    
    if not doc_ids:
        print("❌ No documents found. Please run the extractors first.")
        return
    
    print(f"Found {len(doc_ids)} documents: {', '.join(sorted(doc_ids))}")
    print()
    
    # Generate method-specific markdown for each document
    for doc_id in sorted(doc_ids):
        print(f"📄 Processing document: {doc_id}")
        
        # Try Docling conversion
        try:
            docling_file = generator.generate_docling_markdown(doc_id)
            if docling_file:
                print(f"  ✅ Docling: {docling_file}")
        except Exception as e:
            print(f"  ❌ Docling failed: {e}")
        
        # Try LayoutParser reassembly
        try:
            layout_parser_file = generator.generate_layout_parser_markdown(doc_id)
            if layout_parser_file:
                print(f"  ✅ LayoutParser: {layout_parser_file}")
        except Exception as e:
            print(f"  ❌ LayoutParser failed: {e}")
        
        # Try Hybrid conversion
        try:
            hybrid_file = generator.generate_hybrid_markdown(doc_id)
            if hybrid_file:
                print(f"  ✅ Hybrid: {hybrid_file}")
        except Exception as e:
            print(f"  ❌ Hybrid failed: {e}")
        
        # Try PDFPlumber-Tesseract conversion
        try:
            pdfplumber_file = generator.generate_pdfplumber_tesseract_markdown(doc_id)
            if pdfplumber_file:
                print(f"  ✅ PDFPlumber-Tesseract: {pdfplumber_file}")
        except Exception as e:
            print(f"  ❌ PDFPlumber-Tesseract failed: {e}")
        
        # Try Traditional conversion
        # try:
        #     traditional_file = generator.generate_traditional_markdown(doc_id)
        #     if traditional_file:
        #         print(f"  ✅ Traditional: {traditional_file}")
        # except Exception as e:
        #     print(f"  ❌ Traditional failed: {e}")
        
        print()
    
    print("🎉 Method-specific markdown generation complete!")
    print(f"📁 Base output directory: {generator.base_output_dir}")
    print(f"  - Docling: {generator.docling_dir}")
    print(f"  - LayoutParser: {generator.layout_parser_dir}")
    print(f"  - Hybrid: {generator.hybrid_dir}")
    print(f"  - PDFPlumber-Tesseract: {generator.pdfplumber_tesseract_dir}")
    # print(f"  - Traditional: {generator.traditional_dir}")


if __name__ == "__main__":
    main()