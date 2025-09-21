# Metadata Schema and Staging Architecture

## Overview
This document defines the metadata schema and staging architecture for unified PDF content representation across multiple extraction methods (Docling, LayoutParser, Traditional).

## Metadata Schema

### Core Document Schema
```json
{
  "doc_id": "string",           // Unique document identifier (PDF filename without extension)
  "doc_name": "string",         // Original PDF filename
  "doc_path": "string",         // Original PDF file path
  "processing_timestamp": "string",  // ISO 8601 timestamp
  "total_pages": "integer",     // Total pages in document
  "file_size_bytes": "integer", // Original PDF file size
  "checksum": "string",         // SHA-256 hash of PDF file
  "extraction_methods": ["string"], // List of methods used ["docling", "layout_parser", "traditional"]
  "processing_status": "string", // "success", "partial", "failed"
  "processing_time_seconds": "float"
}
```

### Content Block Schema (JSONL)
Each line in .jsonl files represents a content block:
```json
{
  "doc_id": "string",           // Links to document
  "block_id": "string",         // Unique block identifier within document
  "extraction_method": "string", // "docling", "layout_parser", "traditional"
  "page_number": "integer",     // 1-based page number
  "block_type": "string",       // "text", "table", "figure", "title", "list", "formula", "header", "footer"
  "confidence": "float",        // Extraction confidence (0.0-1.0)
  "bounding_box": {             // Coordinates in page space
    "x1": "float",
    "y1": "float", 
    "x2": "float",
    "y2": "float",
    "width": "float",
    "height": "float"
  },
  "content": {                  // Content varies by block_type
    "text": "string",           // Raw text content
    "structured": "object",   // Structured representation (tables as arrays, etc.)
    "metadata": "object"      // Type-specific metadata
  },
  "provenance": {              // Extraction provenance
    "source_file": "string",  // Path to extracted file
    "extraction_config": "object", // Method-specific configuration
    "parent_blocks": ["string"], // References to parent blocks if hierarchical
    "child_blocks": ["string"]   // References to child blocks if hierarchical
  },
  "semantic_tags": ["string"], // Semantic annotations
  "quality_metrics": {         // Quality assessment
    "text_length": "integer",
    "word_count": "integer",
    "readability_score": "float",
    "completeness": "float"    // 0.0-1.0
  }
}
```

## Folder Structure

```
data/
├── raw/                     # Original PDF files
│   └── pdf/
├── parsed/                  # Method-specific extractions
│   ├── docling/
│   ├── layout_parser/
│   └── traditional/
├── metadata/                # Unified metadata and staging
│   ├── documents/           # Document-level metadata
│   │   ├── doc_registry.json
│   │   └── [doc_id].json    # Individual document metadata
│   ├── blocks/              # Block-level metadata (JSONL)
│   │   ├── docling/
│   │   │   └── [doc_id].jsonl
│   │   ├── layout_parser/
│   │   │   └── [doc_id].jsonl
│   │   ├── traditional/
│   │   │   └── [doc_id].jsonl
│   │   └── unified/         # Cross-method unified blocks
│   │       └── [doc_id].jsonl
│   ├── provenance/          # Detailed provenance tracking
│   │   ├── extraction_logs/
│   │   ├── method_configs/
│   │   └── quality_reports/
│   └── schemas/             # Schema definitions and validation
│       ├── block_schema.json
│       ├── document_schema.json
│       └── validation_rules.json
├── staged/                  # Final staged data for downstream use
│   ├── markdown/            # Markdown with embedded metadata
│   │   └── [doc_id].md
│   ├── json/                # JSON exports with full metadata
│   │   └── [doc_id].json
│   └── search_index/        # Search-optimized formats
│       ├── text_blocks.jsonl
│       ├── table_blocks.jsonl
│       └── figure_blocks.jsonl
└── analysis/                # Cross-document analysis
    ├── statistics/
    ├── quality_metrics/
    └── method_comparisons/
```

## Design Rationale

### Why JSONL in Metadata Directory?
✅ **RECOMMENDED**: Store JSONL files in `metadata/blocks/[method]/`

**Advantages:**
1. **Separation of Concerns**: Raw extractions vs. structured metadata
2. **Method Comparison**: Easy to compare blocks across methods
3. **Unified Processing**: Single location for all structured metadata
4. **Scalability**: JSONL format allows streaming processing of large documents
5. **Provenance**: Clear tracking of which method produced which blocks
6. **Quality Control**: Centralized location for validation and quality metrics

### Metadata Directory Benefits:
- **Queryability**: All structured data in one place
- **Integration**: Easy to join data across methods
- **Versioning**: Can version metadata independently from raw extractions
- **Analysis**: Centralized location for cross-method analysis
- **Search**: Optimized for building search indices

## Implementation Strategy

### Phase 1: Schema Implementation
1. Define JSON schemas for validation
2. Create metadata converters for each method
3. Implement unified block format

### Phase 2: Staging Pipeline
1. Extract metadata from existing parsed data
2. Generate JSONL files for each method
3. Create unified cross-method blocks
4. Generate markdown with provenance

### Phase 3: Quality & Analysis
1. Implement quality metrics
2. Create method comparison tools
3. Build search indices
4. Generate analysis reports