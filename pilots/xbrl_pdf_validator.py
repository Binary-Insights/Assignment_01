import os
import json
import logging
from datetime import datetime
from pilots.arelle import XBRLParser
from src.table_normalizer import PDFTableLoader
from src.data_comparator import DataComparator
from src.validation_report_generator import ValidationReportGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Set up paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    xbrl_file = os.path.join(base_dir, 'data', 'raw', 'sec-edgar-filings', '0001045810', '10-K', 'nvda-20240128.xbrl')
    pdf_tables_dir = os.path.join(base_dir, 'data', 'parsed', 'nvda-20240128', 'tables')
    output_dir = os.path.join(base_dir, 'data', 'parsed', 'nvda-20240128', 'comparison')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Step 1: Parse XBRL data
        logger.info("Parsing XBRL file...")
        parser = XBRLParser(xbrl_file)
        parser.load_instance()
        xbrl_data = parser.extract_facts()
        logger.info(f"Extracted {len(xbrl_data)} XBRL facts")
        
        # Step 2: Load PDF tables
        logger.info("Loading PDF tables...")
        loader = PDFTableLoader(pdf_tables_dir)
        loader.load_all_tables()
        pdf_tables = loader.get_financial_tables()
        logger.info(f"Loaded {len(pdf_tables)} financial tables from PDF")
        
        # Step 3: Compare data
        logger.info("Comparing XBRL and PDF data...")
        comparator = DataComparator(xbrl_data, pdf_tables)
        comparison_results = comparator.compare_all()
        
        # Save comparison results
        comparison_file = os.path.join(output_dir, 'detailed_comparison.json')
        with open(comparison_file, 'w') as f:
            json.dump(comparison_results, f, indent=2)
        logger.info(f"Saved comparison results to {comparison_file}")
        
        # Step 4: Generate validation report
        logger.info("Generating validation report...")
        generator = ValidationReportGenerator(comparison_results)
        report_file = os.path.join(output_dir, 'comparison_validation_report.json')
        generator.save_report(report_file)
        logger.info(f"Saved validation report to {report_file}")
        
        # Step 5: Generate summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'xbrl_file': xbrl_file,
            'total_tables_analyzed': len(pdf_tables),
            'total_facts_compared': comparison_results['summary']['total_comparisons'],
            'match_rate': (comparison_results['summary']['matches'] / 
                          comparison_results['summary']['total_comparisons'] * 100
                          if comparison_results['summary']['total_comparisons'] > 0 else 0),
            'status': 'success'
        }
        
        summary_file = os.path.join(output_dir, 'comparison_summary.txt')
        with open(summary_file, 'w') as f:
            for key, value in summary.items():
                if key == 'match_rate':
                    f.write(f"{key}: {value:.2f}%\n")
                else:
                    f.write(f"{key}: {value}\n")
        logger.info(f"Saved summary to {summary_file}")
        
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        raise
    
    logger.info("Processing completed successfully")

if __name__ == "__main__":
    main()