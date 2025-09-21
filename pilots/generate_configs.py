#!/usr/bin/env python3
"""
Quick script to generate method configuration files
"""

from src.metadata_extractor import MetadataExtractor

if __name__ == "__main__":
    print("Generating method configuration files...")
    extractor = MetadataExtractor()
    print("✓ Method configuration files generated!")
    print(f"Files saved to: {extractor.metadata_dir / 'provenance' / 'method_configs'}")