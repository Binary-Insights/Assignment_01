import os
import pandas as pd
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from datetime import datetime
import logging
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NumpyEncoder(json.JSONEncoder):
    """Special JSON encoder for numpy types."""
    def default(self, obj):
        if isinstance(obj, (np.integer)):
            return int(obj)
        elif isinstance(obj, (np.floating)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def normalize_value(value: str) -> float:
    """Convert a string value to a normalized float."""
    try:
        # Remove currency symbols and commas
        cleaned = value.replace('$', '').replace(',', '').strip()
        
        # Handle parentheses for negative numbers
        if cleaned.startswith('(') and cleaned.endswith(')'):
            cleaned = '-' + cleaned[1:-1]
        
        # Handle percentage values
        if cleaned.endswith('%'):
            return float(cleaned.rstrip('%')) / 100
        
        # Handle "K", "M", "B" suffixes
        if cleaned[-1].upper() in {'K', 'M', 'B'}:
            multiplier = {
                'K': 1000,
                'M': 1000000,
                'B': 1000000000
            }[cleaned[-1].upper()]
            return float(cleaned[:-1]) * multiplier
        
        return float(cleaned)
    except (ValueError, TypeError, IndexError):
        return None

def clean_column_name(col_name: str) -> str:
    """Clean and standardize column names."""
    if pd.isna(col_name):
        return ""
    return str(col_name).strip().lower().replace(" ", "_")

def identify_table_type(df: pd.DataFrame) -> str:
    """Identify the type of financial table based on its content."""
    columns = [clean_column_name(col) for col in df.columns]
    content = "\n".join([" ".join(map(str, row)) for _, row in df.iterrows()]).lower()
    
    if 'stock' in content or 'share' in content:
        return 'stock'
    elif 'asset' in content or 'liability' in content:
        return 'balance_sheet'
    elif 'revenue' in content or 'income' in content:
        return 'income_statement'
    elif 'cash' in content and 'flow' in content:
        return 'cash_flow'
    else:
        return 'unknown'

def load_pdf_table(file_path: str) -> Dict[str, Any]:
    """Load and normalize a table from PDF extraction."""
    df = pd.read_csv(file_path)
    logger.info(f"Original columns: {df.columns.tolist()}")
    logger.info(f"Original data:\n{df.head()}")
    
    # Identify table type
    table_type = identify_table_type(df)
    logger.info(f"Identified table type: {table_type}")
    
    # Process based on table type
    if table_type == 'stock':
        structured_data = process_stock_table(df)
    else:
        structured_data = process_financial_table(df)
    
    # Create metadata
    result = {
        'table_type': table_type,
        'data': structured_data,
        'original_file': os.path.basename(file_path)
    }
    
    logger.info(f"Structured data: {json.dumps(result, indent=2, cls=NumpyEncoder)}")
    return result

def process_stock_table(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Process stock-related tables."""
    structured_data = []
    
    for index, row in df.iterrows():
        period = row.get('October 30, 2023 - November 26, 2023')
        if isinstance(period, str) and not period.strip().lower() == 'total':
            record = {
                'period': period,
                'percentage': normalize_value(str(row.get('0.9', ''))),
                'amount': normalize_value(str(row.get('464.39', ''))),
                'price': normalize_value(str(row.get('24.8', '')))
            }
            structured_data.append(record)
    
    return structured_data

def process_financial_table(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Process financial statement tables."""
    structured_data = []
    
    # Combine multi-line row headers
    current_item = ""
    for index, row in df.iterrows():
        # Get the first column which typically contains line items
        line_item = str(row.iloc[0]).strip()
        
        # Skip empty or purely numeric rows
        if not line_item or line_item.replace(',', '').replace('.', '').replace('-', '').isdigit():
            continue
        
        # If the line ends with a continuation character, append to current item
        if line_item.endswith('(') or line_item.endswith(','):
            current_item += " " + line_item
            continue
            
        # Complete the line item
        if current_item:
            line_item = current_item + " " + line_item
            current_item = ""
        
        # Extract values
        values = []
        for col in df.columns[1:]:  # Skip the first column (line item)
            val = row.get(col)
            if pd.notna(val):
                normalized = normalize_value(str(val))
                if normalized is not None:
                    values.append(normalized)
        
        if values:  # Only add if we found some numeric values
            record = {
                'line_item': line_item,
                'values': values
            }
            structured_data.append(record)
    
    return structured_data

def compare_values(xbrl_value: float, pdf_value: float, tolerance: float = 0.01) -> Dict[str, Any]:
    """Compare two numeric values with tolerance."""
    if pd.isna(xbrl_value) or pd.isna(pdf_value):
        return {
            'match': False,
            'difference': None,
            'reason': 'One or both values are missing'
        }
    
    try:
        difference = abs(xbrl_value - pdf_value)
        relative_diff = difference / abs(xbrl_value) if xbrl_value != 0 else difference
        
        return {
            'match': relative_diff <= tolerance,
            'difference': difference,
            'relative_difference': relative_diff,
            'reason': 'Values within tolerance' if relative_diff <= tolerance else 'Values differ significantly'
        }
    except Exception as e:
        return {
            'match': False,
            'difference': None,
            'reason': f'Comparison error: {str(e)}'
        }

def main():
    # File paths
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_table_dir = os.path.join(project_root, 'data', 'parsed', 'nvda-20240128', 'tables')
    output_dir = os.path.join(project_root, 'data', 'parsed', 'nvda-20240128', 'comparison')
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # List of sample tables to process
    sample_tables = [
        'pdfplumber_page_051_table_001.csv',  # Stock buyback table
        'pdfplumber_page_096_table_001.csv',  # Intangible assets table
    ]
    
    results = []
    
    try:
        for table_file in sample_tables:
            logger.info(f"\nProcessing table: {table_file}")
            table_path = os.path.join(pdf_table_dir, table_file)
            
            # Load and process table
            table_data = load_pdf_table(table_path)
            
            results.append({
                'file_name': table_file,
                'table_type': table_data['table_type'],
                'data': table_data['data']
            })
        
        # Save combined results
        output_file = os.path.join(output_dir, 'table_extraction_results.json')
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_tables': len(results),
                'tables': results
            }, f, indent=2, cls=NumpyEncoder)
        
        logger.info(f"\nResults saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Error processing tables: {str(e)}")
        raise

if __name__ == "__main__":
    main()