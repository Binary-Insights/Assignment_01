#!/usr/bin/env python3
"""
pdfplumber vs LayoutParser: Layout Parsing Comparison

This script demonstrates the different layout parsing approaches between 
pdfplumber and LayoutParser, showing their respective strengths and capabilities.
"""

import pdfplumber
from pathlib import Path
import json
from typing import Dict, List, Any
import pandas as pd

class PDFPlumberLayoutAnalyzer:
    """
    Analyze document layout using pdfplumber's built-in layout features.
    
    pdfplumber provides:
    - Word-level bounding boxes with font information
    - Line detection and grouping
    - Table extraction with structure preservation
    - Character-level positioning
    - Font-based content classification
    """
    
    def __init__(self):
        self.results = {
            'pages': [],
            'layout_features': {
                'words': [],
                'lines': [],
                'rects': [],
                'curves': [],
                'images': [],
                'tables': []
            }
        }
    
    def analyze_pdf_layout(self, pdf_path: str) -> Dict[str, Any]:
        """
        Analyze PDF layout using pdfplumber's native capabilities.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dict containing comprehensive layout analysis
        """
        print("🔍 Analyzing PDF layout with pdfplumber...")
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"📄 Processing page {page_num}")
                
                page_analysis = self._analyze_page_layout(page, page_num)
                self.results['pages'].append(page_analysis)
        
        self._classify_content_types()
        return self.results
    
    def _analyze_page_layout(self, page, page_num: int) -> Dict[str, Any]:
        """
        Analyze layout elements on a single page.
        
        pdfplumber provides these layout objects:
        - chars: Individual characters with fonts, sizes, positions
        - words: Grouped characters forming words
        - lines: Horizontal/vertical lines in the document  
        - rects: Rectangle shapes
        - curves: Curved shapes and paths
        - images: Embedded images
        - tables: Detected table structures
        """
        
        page_analysis = {
            'page_number': page_num,
            'page_dimensions': {
                'width': page.width,
                'height': page.height
            },
            'layout_objects': {
                'chars': len(page.chars),
                'words': len(page.extract_words()),
                'lines': len(page.lines),
                'rects': len(page.rects),
                'curves': len(page.curves),
                'images': len(page.images)
            },
            'content_classification': {},
            'table_detection': {}
        }
        
        # 1. WORD-LEVEL ANALYSIS (Similar to LayoutParser blocks)
        words = page.extract_words()
        word_groups = self._group_words_by_properties(words)
        page_analysis['content_classification'] = word_groups
        
        # 2. TABLE DETECTION (pdfplumber's strength)
        tables = page.find_tables()
        page_analysis['table_detection'] = {
            'tables_found': len(tables),
            'table_data': [self._extract_table_data(table, i) for i, table in enumerate(tables)]
        }
        
        # 3. FONT-BASED CONTENT CLASSIFICATION
        font_analysis = self._analyze_fonts(page.chars)
        page_analysis['font_analysis'] = font_analysis
        
        # 4. SPATIAL LAYOUT ANALYSIS
        spatial_layout = self._analyze_spatial_layout(page)
        page_analysis['spatial_layout'] = spatial_layout
        
        return page_analysis
    
    def _group_words_by_properties(self, words: List[Dict]) -> Dict[str, List]:
        """
        Group words by visual properties to simulate block detection.
        
        This is pdfplumber's approach to content classification:
        - Use font size, style, position to infer content types
        - Group spatially related words
        - Classify based on formatting patterns
        """
        
        content_groups = {
            'potential_titles': [],
            'potential_headers': [],
            'body_text': [],
            'small_text': [],
            'bold_text': [],
            'italic_text': []
        }
        
        if not words:
            return content_groups
        
        # Calculate font size statistics
        font_sizes = [w.get('size', 12) for w in words if w.get('size')]
        if font_sizes:
            avg_font_size = sum(font_sizes) / len(font_sizes)
            max_font_size = max(font_sizes)
        else:
            avg_font_size = 12
            max_font_size = 12
        
        for word in words:
            font_size = word.get('size', 12)
            font_name = word.get('fontname', '').lower()
            text = word.get('text', '')
            
            # Classification logic (rule-based, unlike LayoutParser's AI)
            if font_size > avg_font_size * 1.5:
                content_groups['potential_titles'].append(word)
            elif font_size > avg_font_size * 1.2:
                content_groups['potential_headers'].append(word)
            elif 'bold' in font_name or 'Black' in font_name:
                content_groups['bold_text'].append(word)
            elif 'italic' in font_name or 'Oblique' in font_name:
                content_groups['italic_text'].append(word)
            elif font_size < avg_font_size * 0.8:
                content_groups['small_text'].append(word)
            else:
                content_groups['body_text'].append(word)
        
        return content_groups
    
    def _extract_table_data(self, table, table_index: int) -> Dict[str, Any]:
        """
        Extract structured table data using pdfplumber's table detection.
        
        This is where pdfplumber excels - it can extract actual table structure,
        not just detect that a table exists (like LayoutParser).
        """
        try:
            # Extract table data as list of lists
            table_data = table.extract()
            
            return {
                'table_index': table_index,
                'bbox': table.bbox,
                'rows': len(table_data) if table_data else 0,
                'cols': len(table_data[0]) if table_data and table_data[0] else 0,
                'data': table_data[:5] if table_data else [],  # First 5 rows as sample
                'extraction_method': 'pdfplumber_table_detection'
            }
        except Exception as e:
            return {
                'table_index': table_index,
                'error': str(e),
                'extraction_method': 'pdfplumber_table_detection'
            }
    
    def _analyze_fonts(self, chars: List[Dict]) -> Dict[str, Any]:
        """
        Analyze font usage patterns to infer document structure.
        
        pdfplumber provides detailed font information that can be used
        for content classification similar to LayoutParser's block types.
        """
        if not chars:
            return {}
        
        # Collect font statistics
        fonts = {}
        for char in chars:
            font_name = char.get('fontname', 'Unknown')
            font_size = char.get('size', 12)
            
            if font_name not in fonts:
                fonts[font_name] = {
                    'char_count': 0,
                    'sizes': [],
                    'sample_text': ''
                }
            
            fonts[font_name]['char_count'] += 1
            fonts[font_name]['sizes'].append(font_size)
            fonts[font_name]['sample_text'] += char.get('text', '')
            
            if len(fonts[font_name]['sample_text']) > 100:
                fonts[font_name]['sample_text'] = fonts[font_name]['sample_text'][:100] + '...'
        
        # Calculate font statistics
        font_analysis = {}
        for font_name, data in fonts.items():
            sizes = data['sizes']
            font_analysis[font_name] = {
                'character_count': data['char_count'],
                'avg_size': sum(sizes) / len(sizes) if sizes else 0,
                'size_range': f"{min(sizes)}-{max(sizes)}" if sizes else "N/A",
                'sample_text': data['sample_text'],
                'likely_content_type': self._infer_content_type_from_font(font_name, sizes)
            }
        
        return font_analysis
    
    def _infer_content_type_from_font(self, font_name: str, sizes: List[float]) -> str:
        """
        Infer content type based on font characteristics.
        
        This is pdfplumber's approach - rule-based inference vs LayoutParser's AI.
        """
        font_name_lower = font_name.lower()
        avg_size = sum(sizes) / len(sizes) if sizes else 12
        
        if any(keyword in font_name_lower for keyword in ['bold', 'black', 'heavy']):
            if avg_size > 16:
                return 'title'
            elif avg_size > 14:
                return 'heading'
            else:
                return 'emphasized_text'
        elif any(keyword in font_name_lower for keyword in ['italic', 'oblique']):
            return 'italic_text'
        elif avg_size > 16:
            return 'large_text'
        elif avg_size < 10:
            return 'small_text'
        else:
            return 'body_text'
    
    def _analyze_spatial_layout(self, page) -> Dict[str, Any]:
        """
        Analyze spatial layout patterns using coordinate information.
        
        pdfplumber provides precise coordinates that can be used for
        layout analysis similar to LayoutParser's bounding boxes.
        """
        words = page.extract_words()
        if not words:
            return {}
        
        # Analyze text distribution
        x_positions = [w['x0'] for w in words]
        y_positions = [w['top'] for w in words]
        
        spatial_analysis = {
            'text_distribution': {
                'left_margin': min(x_positions) if x_positions else 0,
                'right_margin': max([w['x1'] for w in words]) if words else 0,
                'top_margin': min(y_positions) if y_positions else 0,
                'bottom_margin': max([w['bottom'] for w in words]) if words else 0
            },
            'column_analysis': self._detect_columns(words),
            'line_spacing_analysis': self._analyze_line_spacing(words)
        }
        
        return spatial_analysis
    
    def _detect_columns(self, words: List[Dict]) -> Dict[str, Any]:
        """
        Detect column layout using word positions.
        
        This demonstrates how pdfplumber can achieve layout understanding
        through coordinate analysis rather than AI detection.
        """
        if not words:
            return {'columns_detected': 0}
        
        # Group words by approximate X position
        x_positions = [w['x0'] for w in words]
        
        # Simple column detection - look for gaps in X distribution
        x_positions.sort()
        gaps = []
        
        for i in range(1, len(x_positions)):
            gap = x_positions[i] - x_positions[i-1]
            if gap > 50:  # Significant gap threshold
                gaps.append((x_positions[i-1], x_positions[i], gap))
        
        return {
            'columns_detected': len(gaps) + 1 if gaps else 1,
            'significant_gaps': gaps[:3],  # Top 3 gaps
            'layout_pattern': 'multi_column' if len(gaps) > 0 else 'single_column'
        }
    
    def _analyze_line_spacing(self, words: List[Dict]) -> Dict[str, Any]:
        """
        Analyze line spacing patterns to infer document structure.
        """
        if not words:
            return {}
        
        # Group words by approximate Y position (lines)
        lines = {}
        for word in words:
            y_pos = round(word['top'])
            if y_pos not in lines:
                lines[y_pos] = []
            lines[y_pos].append(word)
        
        # Calculate line spacing
        y_positions = sorted(lines.keys())
        line_spacings = []
        
        for i in range(1, len(y_positions)):
            spacing = y_positions[i] - y_positions[i-1]
            line_spacings.append(spacing)
        
        if line_spacings:
            avg_spacing = sum(line_spacings) / len(line_spacings)
            return {
                'average_line_spacing': avg_spacing,
                'line_count': len(lines),
                'spacing_variation': max(line_spacings) - min(line_spacings) if line_spacings else 0
            }
        
        return {'line_count': len(lines)}
    
    def _classify_content_types(self):
        """
        Final content type classification based on all analyzed features.
        
        This simulates LayoutParser's block type classification using
        pdfplumber's rule-based approach.
        """
        for page in self.results['pages']:
            content_types = {
                'titles': 0,
                'headers': 0,
                'body_text': 0,
                'tables': 0,
                'small_text': 0
            }
            
            # Count different content types
            classification = page.get('content_classification', {})
            
            content_types['titles'] = len(classification.get('potential_titles', []))
            content_types['headers'] = len(classification.get('potential_headers', []))
            content_types['body_text'] = len(classification.get('body_text', []))
            content_types['tables'] = page.get('table_detection', {}).get('tables_found', 0)
            content_types['small_text'] = len(classification.get('small_text', []))
            
            page['content_type_summary'] = content_types


def compare_layout_approaches():
    """
    Compare LayoutParser vs pdfplumber layout parsing approaches.
    """
    print("=" * 80)
    print("LAYOUT PARSING COMPARISON: LayoutParser vs pdfplumber")
    print("=" * 80)
    
    comparison = {
        'LayoutParser': {
            'approach': 'AI/Deep Learning',
            'block_types': ['Text', 'Title', 'Table', 'Figure', 'List'],
            'strengths': [
                'Semantic understanding of content',
                'Pre-trained models for document layout',
                'Confidence scores for detections',
                'Works well with complex layouts',
                'Handles scanned documents'
            ],
            'weaknesses': [
                'Requires heavy ML dependencies',
                'Black box - hard to customize',
                'May miss subtle layout patterns',
                'Computationally expensive',
                'Limited table structure extraction'
            ],
            'output': 'Bounding boxes + content type classification'
        },
        'pdfplumber': {
            'approach': 'Rule-based + Coordinate Analysis',
            'block_types': ['Font-based classification', 'Spatial grouping', 'Table structure'],
            'strengths': [
                'Precise coordinate information',
                'Excellent table extraction with structure',
                'Font and styling analysis',
                'Fast and lightweight',
                'Highly customizable rules',
                'Works with text-based PDFs'
            ],
            'weaknesses': [
                'No semantic understanding',
                'Struggles with complex layouts',
                'Poor performance on scanned documents',
                'Requires manual rule tuning',
                'Limited figure detection'
            ],
            'output': 'Word/character coordinates + table data + font information'
        }
    }
    
    for method, details in comparison.items():
        print(f"\n🔍 {method}")
        print(f"   Approach: {details['approach']}")
        print(f"   Block Types: {', '.join(details['block_types'])}")
        print(f"   Output: {details['output']}")
        
        print(f"   ✅ Strengths:")
        for strength in details['strengths']:
            print(f"      • {strength}")
        
        print(f"   ❌ Weaknesses:")
        for weakness in details['weaknesses']:
            print(f"      • {weakness}")


def main():
    """Demonstrate pdfplumber's layout analysis capabilities."""
    print("=== pdfplumber Layout Analysis Demo ===")
    
    # Find a PDF to analyze
    pdf_dir = Path("data/raw/pdf")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in data/raw/pdf directory")
        compare_layout_approaches()
        return
    
    # Analyze first PDF with pdfplumber
    pdf_file = pdf_files[0]
    print(f"Analyzing {pdf_file.name} with pdfplumber...")
    
    analyzer = PDFPlumberLayoutAnalyzer()
    results = analyzer.analyze_pdf_layout(str(pdf_file))
    
    # Save results
    output_file = Path("data/analysis/pdfplumber_layout_analysis.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📊 Analysis Results Summary:")
    print(f"   Pages analyzed: {len(results['pages'])}")
    
    for page in results['pages'][:3]:  # Show first 3 pages
        page_num = page['page_number']
        layout_objects = page['layout_objects']
        content_summary = page.get('content_type_summary', {})
        
        print(f"\n   Page {page_num}:")
        print(f"     Layout objects: {sum(layout_objects.values())} total")
        print(f"     Content types: {dict(content_summary)}")
        print(f"     Tables found: {page.get('table_detection', {}).get('tables_found', 0)}")
    
    print(f"\n💾 Full analysis saved to: {output_file}")
    
    # Show comparison
    compare_layout_approaches()


if __name__ == "__main__":
    main()