# Metadata and Staging System Implementation Guide

## Overview

This document provides a comprehensive guide to the metadata and staging system for PDF content extraction. The system creates a unified representation of content extracted by multiple methods (Docling, LayoutParser, Traditional) with full provenance tracking.

## Architecture

### Core Components

1. **MetadataExtractor**: Main class that converts method-specific extractions to unified metadata
2. **ContentBlock**: Unified schema for all content blocks across methods
3. **DocumentMetadata**: Document-level metadata with processing information
4. **JSONL Storage**: Scalable line-delimited JSON format for large datasets
5. **Provenance Tracking**: Complete audit trail of extraction methods and configurations

### Design Principles

- **Method Agnostic**: Works with any extraction method
- **Scalable**: JSONL format allows streaming processing
- **Queryable**: Structured metadata enables complex queries
- **Provenance**: Full traceability of data lineage
- **Quality Metrics**: Built-in quality assessment
- **Extensible**: Easy to add new content types and methods

## Directory Structure

```
Assignment_01/
├── data/
│   ├── raw/pdf/                    # Original PDF files
│   ├── parsed/                     # Method-specific extractions
│   │   ├── docling/               # Docling extraction results
│   │   ├── layout_parser/         # LayoutParser results
│   │   └── traditional/           # Traditional method results
│   ├── metadata/                   # UNIFIED METADATA (Core System)
│   │   ├── documents/             # Document-level metadata
│   │   │   ├── doc_registry.json  # Master document registry
│   │   │   └── [doc_id].json      # Individual document metadata
│   │   ├── blocks/                # Block-level metadata (JSONL)
│   │   │   ├── docling/           # Docling blocks in unified format
│   │   │   │   └── [doc_id].jsonl # One JSONL per document
│   │   │   ├── layout_parser/     # LayoutParser blocks
│   │   │   │   └── [doc_id].jsonl
│   │   │   ├── traditional/       # Traditional method blocks
│   │   │   │   └── [doc_id].jsonl
│   │   │   └── unified/           # Cross-method unified blocks
│   │   │       └── [doc_id].jsonl # Best blocks from all methods
│   │   ├── provenance/            # Extraction provenance
│   │   │   ├── extraction_logs/   # Processing logs
│   │   │   ├── method_configs/    # Method configurations
│   │   │   └── quality_reports/   # Quality assessment reports
│   │   └── schemas/               # JSON schemas and validation
│   │       ├── document_schema.json
│   │       ├── block_schema.json
│   │       └── validation_rules.json
│   ├── staged/                     # Final staged outputs
│   │   ├── markdown/              # Markdown with embedded metadata
│   │   │   └── [doc_id].md        # Human-readable with provenance
│   │   ├── json/                  # Comprehensive JSON exports
│   │   │   └── [doc_id].json      # Full document + blocks
│   │   └── search_index/          # Search-optimized formats
│   │       ├── text_blocks.jsonl  # All text blocks
│   │       ├── table_blocks.jsonl # All table blocks
│   │       └── figure_blocks.jsonl# All figure blocks
│   └── analysis/                   # Cross-document analysis
│       ├── statistics/            # Processing statistics
│       ├── quality_metrics/       # Quality assessments
│       └── method_comparisons/    # Cross-method analysis
└── src/
    ├── metadata_extractor.py      # Main metadata extraction system
    ├── docling_extractor.py       # Docling extraction method
    ├── layout_parser_extractor.py # LayoutParser method
    └── traditional_extractor.py   # Traditional method
```

## Key Design Decisions

### Why JSONL in Metadata Directory? ✅ RECOMMENDED

**Advantages of storing JSONL files in `data/metadata/blocks/[method]/`:**

1. **Separation of Concerns**: Raw extractions vs. structured metadata
2. **Unified Schema**: All methods use the same block schema
3. **Method Comparison**: Easy to compare blocks across methods
4. **Scalability**: JSONL allows streaming processing of large documents
5. **Queryability**: Structured format enables complex queries
6. **Provenance**: Clear tracking of extraction method and configuration
7. **Quality Control**: Centralized validation and quality metrics

### Schema Design

#### Document Metadata Schema
```json
{
  "doc_id": "string",              // Unique identifier
  "doc_name": "string",            // Original filename
  "doc_path": "string",            // Full path
  "processing_timestamp": "ISO8601",
  "total_pages": "integer",
  "file_size_bytes": "integer",
  "checksum": "SHA-256",           // File integrity
  "extraction_methods": ["array"], // Methods applied
  "processing_status": "enum",     // success/partial/failed
  "processing_time_seconds": "float"
}
```

#### Content Block Schema (JSONL)
```json
{
  "doc_id": "string",              // Links to document
  "block_id": "string",            // Unique block identifier
  "extraction_method": "enum",     // docling/layout_parser/traditional/unified
  "page_number": "integer",        // 1-based page number
  "block_type": "enum",            // text/table/figure/title/list/formula
  "confidence": "float",           // 0.0-1.0
  "bounding_box": {                // Page coordinates (optional)
    "x1": "float", "y1": "float",
    "x2": "float", "y2": "float",
    "width": "float", "height": "float"
  },
  "content": {
    "text": "string",                // Raw text content
    "structured": "object",         // Type-specific structure
    "metadata": "object"            // Additional metadata
  },
  "provenance": {
    "source_file": "string",       // Path to extracted file
    "extraction_config": "object", // Method configuration
    "parent_blocks": ["array"],     // Hierarchical relationships
    "child_blocks": ["array"]
  },
  "semantic_tags": ["array"],      // Classification tags
  "quality_metrics": {
    "text_length": "integer",
    "word_count": "integer",
    "readability_score": "float",   // 0.0-1.0
    "completeness": "float"         // 0.0-1.0
  }
}
```

## Implementation Guide

### Phase 1: Setup and Schema Definition
```bash
# 1. Create directory structure
python -c "from pathlib import Path; [Path(f'data/metadata/{d}').mkdir(parents=True, exist_ok=True) for d in ['documents', 'blocks/docling', 'blocks/layout_parser', 'blocks/traditional', 'blocks/unified', 'provenance/extraction_logs', 'schemas']]"

# 2. Validate JSON schemas
python -c "import json; [print(f'✓ {f}') for f in ['document_schema.json', 'block_schema.json', 'validation_rules.json'] if json.load(open(f'data/metadata/schemas/{f}'))]"
```

### Phase 2: Extract Metadata from Existing Results
```python
from src.metadata_extractor import MetadataExtractor

# Initialize extractor
extractor = MetadataExtractor()

# Process all documents
results = extractor.process_all_documents()

# Results will be saved to:
# - data/metadata/documents/doc_registry.json
# - data/metadata/blocks/[method]/[doc_id].jsonl
# - data/staged/markdown/[doc_id].md
# - data/staged/json/[doc_id].json
```

### Phase 3: Query and Analysis
```python
# Load unified blocks for analysis
import json
from pathlib import Path

def load_unified_blocks(doc_id):
    jsonl_file = Path(f"data/metadata/blocks/unified/{doc_id}.jsonl")
    blocks = []
    with open(jsonl_file, 'r') as f:
        for line in f:
            blocks.append(json.loads(line))
    return blocks

# Cross-method comparison
def compare_methods(doc_id):
    methods = ['docling', 'layout_parser', 'traditional']
    comparison = {}
    
    for method in methods:
        jsonl_file = Path(f"data/metadata/blocks/{method}/{doc_id}.jsonl")
        if jsonl_file.exists():
            blocks = []
            with open(jsonl_file, 'r') as f:
                for line in f:
                    blocks.append(json.loads(line))
            
            comparison[method] = {
                'total_blocks': len(blocks),
                'blocks_by_type': {},
                'avg_confidence': sum(b['confidence'] for b in blocks) / len(blocks) if blocks else 0
            }
            
            for block in blocks:
                block_type = block['block_type']
                comparison[method]['blocks_by_type'][block_type] = \
                    comparison[method]['blocks_by_type'].get(block_type, 0) + 1
    
    return comparison
```

## Benefits of This Architecture

### 1. Unified Data Model
- All extraction methods conform to the same schema
- Consistent querying across different approaches
- Easy integration with downstream systems

### 2. Scalability
- JSONL format allows streaming processing
- Individual files per document enable parallel processing
- Minimal memory footprint for large corpora

### 3. Provenance and Reproducibility
- Complete audit trail of extraction processes
- Method configurations preserved
- Quality metrics for assessment

### 4. Flexibility
- Easy to add new extraction methods
- Schema evolution supported
- Multiple output formats (JSONL, JSON, Markdown)

### 5. Query Capabilities
```bash
# Find all tables with high confidence
jq 'select(.block_type == "table" and .confidence > 0.8)' data/metadata/blocks/unified/*.jsonl

# Compare extraction methods for a document
jq '.extraction_method' data/metadata/blocks/**/doc_001.jsonl | sort | uniq -c

# Quality metrics by method
jq '.quality_metrics.completeness' data/metadata/blocks/docling/*.jsonl | jq -s 'add/length'
```

## Usage Examples

### 1. Run Metadata Extraction
```bash
cd Assignment_01
python test_metadata_extraction.py
```

### 2. Examine Results
```bash
# View document registry
cat data/metadata/documents/doc_registry.json | jq '.'

# Count blocks by method
wc -l data/metadata/blocks/*/*.jsonl

# View sample unified block
head -1 data/metadata/blocks/unified/*.jsonl | jq '.'
```

### 3. Quality Analysis
```python
# Load and analyze quality metrics
import json
from pathlib import Path

def analyze_quality():
    quality_report = {}
    
    for method in ['docling', 'layout_parser', 'traditional', 'unified']:
        method_dir = Path(f"data/metadata/blocks/{method}")
        if not method_dir.exists():
            continue
            
        blocks = []
        for jsonl_file in method_dir.glob("*.jsonl"):
            with open(jsonl_file, 'r') as f:
                for line in f:
                    blocks.append(json.loads(line))
        
        if blocks:
            quality_report[method] = {
                'total_blocks': len(blocks),
                'avg_confidence': sum(b['confidence'] for b in blocks) / len(blocks),
                'avg_completeness': sum(b['quality_metrics']['completeness'] for b in blocks) / len(blocks),
                'blocks_by_type': {}
            }
            
            for block in blocks:
                block_type = block['block_type']
                quality_report[method]['blocks_by_type'][block_type] = \
                    quality_report[method]['blocks_by_type'].get(block_type, 0) + 1
    
    return quality_report
```

## Next Steps

1. **Test the System**: Run `python test_metadata_extraction.py`
2. **Examine Output**: Review generated JSONL and Markdown files
3. **Query Metadata**: Use the structured format for analysis
4. **Build Search Index**: Create search-optimized formats
5. **Cross-Method Analysis**: Compare extraction method performance
6. **Quality Assessment**: Evaluate and improve extraction quality

This metadata system provides a solid foundation for advanced PDF content analysis, search, and comparison across multiple extraction methods.