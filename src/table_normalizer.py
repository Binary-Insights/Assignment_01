import os
import pandas as pd
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class PDFTableLoader:
    def __init__(self, tables_dir: str):
        """Initialize the PDF table loader with the directory containing extracted tables."""
        self.tables_dir = tables_dir
        self.tables: Dict[str, pd.DataFrame] = {}
        self.table_metadata: Dict[str, Dict] = {}
        
    def load_all_tables(self) -> None:
        """Load all CSV tables from the directory."""
        for filename in os.listdir(self.tables_dir):
            if filename.endswith('.csv'):
                table_path = os.path.join(self.tables_dir, filename)
                table_id = filename.replace('.csv', '')
                
                try:
                    df = pd.read_csv(table_path)
                    self._analyze_table_content(df, table_id)
                except Exception as e:
                    print(f"Error loading table {filename}: {str(e)}")
    
    def _analyze_table_content(self, df: pd.DataFrame, table_id: str) -> None:
        """Analyze table content to determine its type and structure."""
        # Count numeric columns
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        
        # Check for date-like columns
        date_cols = [col for col in df.columns if 'date' in col.lower() or 'year' in col.lower()]
        
        # Check for common financial terms
        financial_terms = ['revenue', 'income', 'expense', 'asset', 'liability', 'cash', 'total']
        financial_cols = [col for col in df.columns 
                         if any(term in str(col).lower() for term in financial_terms)]
        
        metadata = {
            'row_count': len(df),
            'col_count': len(df.columns),
            'numeric_cols': list(numeric_cols),
            'date_cols': date_cols,
            'financial_cols': financial_cols,
            'has_financial_data': len(financial_cols) > 0 or self._has_financial_content(df)
        }
        
        if metadata['has_financial_data']:
            self.tables[table_id] = df
            self.table_metadata[table_id] = metadata
    
    def _has_financial_content(self, df: pd.DataFrame) -> bool:
        """Check if the table contains financial data based on content analysis."""
        # Convert DataFrame to string to search through all content
        content = df.to_string().lower()
        financial_terms = ['revenue', 'income', 'expense', 'asset', 'liability', 'cash',
                         'total', 'balance', 'profit', 'loss', 'earnings', 'million',
                         'billion', 'thousand', 'usd', '$']
        
        return any(term in content for term in financial_terms)
    
    def get_financial_tables(self) -> Dict[str, pd.DataFrame]:
        """Return only tables that contain financial data."""
        return {table_id: self.tables[table_id]
                for table_id in self.tables
                if self.table_metadata[table_id]['has_financial_data']}
    
    def normalize_table_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize numeric values in the table for comparison."""
        df_copy = df.copy()
        
        for col in df_copy.columns:
            if df_copy[col].dtype in ['object']:
                # Try to convert string numbers with commas and currency symbols
                df_copy[col] = df_copy[col].apply(self._normalize_value)
        
        return df_copy
    
    def _normalize_value(self, value: any) -> Optional[float]:
        """Convert a value to a normalized number if possible."""
        if pd.isna(value):
            return None
        
        try:
            # Remove currency symbols and commas
            if isinstance(value, str):
                value = value.replace('$', '').replace(',', '').strip()
                
                # Handle parentheses for negative numbers
                if value.startswith('(') and value.endswith(')'):
                    value = '-' + value[1:-1]
                
                # Handle percentage values
                if value.endswith('%'):
                    value = float(value.rstrip('%')) / 100
                
                # Handle "K", "M", "B" suffixes
                multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
                if value[-1].upper() in multipliers:
                    return float(value[:-1]) * multipliers[value[-1].upper()]
            
            return float(value)
        except (ValueError, TypeError):
            return None

def save_comparison_report(report_data: Dict, output_path: str) -> None:
    """Save the comparison report to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)

def main():
    # Example usage
    tables_dir = "path/to/pdf/tables"
    loader = PDFTableLoader(tables_dir)
    loader.load_all_tables()
    
    # Get financial tables
    financial_tables = loader.get_financial_tables()
    print(f"Found {len(financial_tables)} financial tables")
    
    # Process and normalize tables
    for table_id, df in financial_tables.items():
        normalized_df = loader.normalize_table_values(df)
        print(f"\nTable {table_id} summary:")
        print(normalized_df.info())

if __name__ == "__main__":
    main()