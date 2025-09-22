#!/usr/bin/env python3
"""
Main entry point for the unified PDF extraction pipeline.

This script provides a command-line interface for the Build vs Buy experiment,
allowing users to process documents with both open-source and cloud solutions.
"""

import sys
import argparse
from pathlib import Path
from unified_extractor import UnifiedExtractor


def main():
    """Main entry point with command-line interface."""
    parser = argparse.ArgumentParser(
        description="Unified PDF Extraction Pipeline - Build vs Buy Experiment"
    )
    
    parser.add_argument(
        'pdf_path',
        nargs='?',
        default='data/raw/pdf/nvda-20240128.pdf',
        help='Path to PDF file to process'
    )
    
    parser.add_argument(
        '--disable-aws',
        action='store_true',
        help='Disable AWS Textract fallback (Docling only)'
    )
    
    parser.add_argument(
        '--force-aws',
        action='store_true',
        help='Force use of AWS Textract (skip Docling)'
    )
    
    parser.add_argument(
        '--quality-threshold',
        type=float,
        default=0.6,
        help='Quality threshold for triggering AWS fallback (0.0-1.0)'
    )
    
    parser.add_argument(
        '--cost-threshold',
        type=float,
        default=20.0,
        help='Maximum cost threshold per document (USD)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='data/parsed/unified',
        help='Output directory for extraction results'
    )
    
    args = parser.parse_args()
    
    # Validate PDF path
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"❌ Error: PDF file not found: {pdf_path}")
        print(f"Available PDFs in data/raw/pdf/:")
        pdf_dir = Path('data/raw/pdf')
        if pdf_dir.exists():
            for pdf_file in pdf_dir.glob('*.pdf'):
                print(f"  - {pdf_file}")
        sys.exit(1)
    
    # Initialize unified extractor
    print("🚀 Initializing unified extraction pipeline...")
    extractor = UnifiedExtractor(
        output_dir=args.output_dir,
        enable_aws_fallback=not args.disable_aws,
        quality_threshold=args.quality_threshold,
        cost_threshold=args.cost_threshold
    )
    
    # Display configuration
    print(f"\n📋 Configuration:")
    print(f"  PDF: {pdf_path}")
    print(f"  AWS Fallback: {'Enabled' if not args.disable_aws else 'Disabled'}")
    print(f"  Force AWS: {'Yes' if args.force_aws else 'No'}")
    print(f"  Quality Threshold: {args.quality_threshold}")
    print(f"  Cost Threshold: ${args.cost_threshold}")
    print(f"  Output Directory: {args.output_dir}")
    
    # Run extraction
    print(f"\n🔄 Processing {pdf_path.name}...")
    results = extractor.extract_from_pdf(
        str(pdf_path),
        force_aws=args.force_aws,
        enable_fallback=not args.disable_aws
    )
    
    if results and results.get('processing_success'):
        print("\n✅ Extraction completed successfully!")
        
        # Display results summary
        recommendation = results['final_recommendation']
        cost_analysis = results['cost_analysis']
        
        print(f"\n📊 Results Summary:")
        print(f"  Primary Method: {recommendation['primary_method']}")
        print(f"  Quality Rating: {recommendation['quality_rating']}")
        print(f"  Cost Effectiveness: {recommendation['cost_effectiveness']}")
        print(f"  Total Cost: ${cost_analysis['total_cost']:.2f}")
        print(f"  Processing Time: {results['processing_time_seconds']:.2f}s")
        
        # Display reasoning
        if recommendation['reasoning']:
            print(f"\n💡 Reasoning:")
            for reason in recommendation['reasoning']:
                print(f"  - {reason}")
        
        # Display pipeline statistics
        stats = extractor.get_processing_stats()
        print(f"\n📈 Pipeline Statistics:")
        print(f"  Documents Processed: {stats['total_documents']}")
        print(f"  AWS Fallback Rate: {stats['aws_fallback_rate']:.1%}")
        print(f"  Average Cost/Document: ${stats['average_cost_per_document']:.2f}")
        print(f"  Average Processing Time: {stats['average_processing_time']:.2f}s")
        
        # Show output location
        output_path = Path(args.output_dir) / pdf_path.stem
        print(f"\n📁 Detailed results saved to: {output_path}")
        print(f"  - unified_extraction_results.json")
        print(f"  - extraction_summary.json")
        print(f"  - docling/ (if used)")
        print(f"  - aws_textract_results.json (if used)")
        
    else:
        print("❌ Extraction failed!")
        if results and results.get('error_message'):
            print(f"Error: {results['error_message']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
