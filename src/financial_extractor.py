"""
Advanced PDF financial table extraction with enhanced formatting and filtering.
"""
import pdfplumber
import pandas as pd
import os
from pathlib import Path
import json
import re
from typing import List, Dict, Any, Tuple
import numpy as np

class FinancialTableExtractor:
    """Enhanced table extractor specifically for financial statements."""
    
    def __init__(self):
        self.financial_keywords = {
            'income_statement': [
                'revenue', 'sales', 'cost of revenue', 'gross profit', 'operating expenses',
                'operating income', 'net income', 'earnings per share', 'ebitda'
            ],
            'balance_sheet': [
                'assets', 'liabilities', 'equity', 'cash and cash equivalents',
                'accounts receivable', 'inventory', 'property and equipment',
                'accounts payable', 'long-term debt'
            ],
            'cash_flow': [
                'cash flow', 'operating activities', 'investing activities',
                'financing activities', 'net increase in cash'
            ]
        }
        # Number patterns for identifying financial tables
        self.number_patterns = [
            r'\$?\d{1,3}(?:,\d{3})*(?:\.\d+)?',  # Regular numbers with commas
            r'\(\$?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)',  # Negative numbers in parentheses
        ]
    
    def is_likely_financial_table(self, df: pd.DataFrame) -> bool:
        """
        Check if the table is likely to be a financial statement based on its structure and content.
        """
        if len(df) < 5 or len(df.columns) < 2:
            return False

        # Count cells that look like financial numbers
        financial_number_pattern = '|'.join(self.number_patterns)
        number_cells = 0
        total_cells = 0

        for col in df.columns[1:]:  # Skip first column which usually has labels
            col_values = df[col].astype(str)
            number_cells += sum(col_values.str.contains(financial_number_pattern, regex=True, na=False))
            total_cells += len(col_values)

        if total_cells == 0:
            return False

        # Calculate percentage of cells that are numbers
        number_percentage = number_cells / total_cells

        # Need at least 30% of cells to be numbers in non-label columns
        if number_percentage < 0.3:
            return False

        # Check for common financial terms in the first column
        first_col_text = ' '.join(df.iloc[:, 0].astype(str)).lower()
        financial_terms = [
            'total', 'revenue', 'cost', 'expense', 'income', 'profit', 'loss',
            'assets', 'liabilities', 'equity', 'cash', 'sales', 'tax', 'net'
        ]
        if not any(term in first_col_text for term in financial_terms):
            return False

        return True

    def detect_statement_type(self, table_text: str) -> str:
        """Detect the type of financial statement based on keywords."""
        table_text = table_text.lower()
        
        # Count matches for each statement type
        matches = {
            'income_statement': sum(1 for kw in self.financial_keywords['income_statement'] if kw in table_text),
            'balance_sheet': sum(1 for kw in self.financial_keywords['balance_sheet'] if kw in table_text),
            'cash_flow': sum(1 for kw in self.financial_keywords['cash_flow'] if kw in table_text)
        }
        
        # Return the type with most matches
        if matches:
            return max(matches.items(), key=lambda x: x[1])[0]
        return 'unknown'
    
    def extract_periods(self, df: pd.DataFrame) -> List[str]:
        """Extract reporting periods from table headers."""
        potential_periods = []
        
        # Common patterns for years and dates
        year_pattern = r'20\d{2}'
        date_pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+20\d{2}'
        
        for col in df.columns:
            if isinstance(col, str):
                # Look for years
                years = re.findall(year_pattern, col)
                potential_periods.extend(years)
                
                # Look for full dates
                dates = re.findall(date_pattern, col)
                potential_periods.extend(dates)
        
        return list(dict.fromkeys(potential_periods))  # Remove duplicates while preserving order
    
    def clean_number(self, value: str) -> float:
        """Convert string numbers to float, handling parentheses for negatives."""
        if not value or not isinstance(value, str):
            return None
            
        # Remove currency symbols and whitespace
        value = value.strip().replace('$', '').replace(',', '')
        
        # Handle parentheses for negative numbers
        if value.startswith('(') and value.endswith(')'):
            value = '-' + value[1:-1]
            
        # Handle special characters
        value = value.replace('—', '0')  # Replace em dash with zero
        
        try:
            return float(value)
        except ValueError:
            return None
            
    def format_number(self, value: float, include_currency: bool = False) -> str:
        """Format numbers consistently with appropriate symbols."""
        if value is None:
            return ''
            
        if np.isnan(value):
            return ''
            
        # Format negative numbers with parentheses
        if value < 0:
            formatted = f"({abs(value):,.1f})"
        else:
            formatted = f"{value:,.1f}"
            
        # Add currency symbol if requested
        if include_currency:
            formatted = '$' + formatted
            
        return formatted
        
    def detect_units(self, text: str, default: str = 'millions') -> str:
        """Detect the units (millions/billions) from context."""
        text = text.lower()
        if 'billions' in text or 'billion' in text or '(b)' in text:
            return 'billions'
        elif 'millions' in text or 'million' in text or '(m)' in text:
            return 'millions'
        return default
        
    def clean_column_headers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize column headers."""
        # Drop completely empty columns
        df = df.dropna(axis=1, how='all')
        
        # Combine split headers
        if df.columns.nlevels > 1:
            df.columns = [' '.join(filter(None, col)) for col in df.columns.values]
        
        # Clean up generic numbered columns
        new_columns = []
        for i, col in enumerate(df.columns):
            if str(col).isdigit() or col == '':
                if i == 0:
                    new_columns.append('Item')
                else:
                    new_columns.append(f'Value_{i}')
            else:
                new_columns.append(str(col).strip())
                
        df.columns = new_columns
        return df
        
    def standardize_table(self, df: pd.DataFrame, include_currency: bool = True) -> pd.DataFrame:
        """
        Standardize table formatting including numbers and headers.
        """
        # First clean the data
        df = self.clean_table_data(df)
        
        # Remove completely empty columns
        df = df.loc[:, df.notna().any()]
        
        # Remove duplicate columns
        df = df.loc[:, ~df.columns.duplicated()]
        
        # Remove rows where all numeric columns are empty/zero
        numeric_cols = df.columns[1:]  # Exclude 'Item' column
        df = df.loc[~((df[numeric_cols] == '') | df[numeric_cols].isna()).all(axis=1)]
        
        return df
        
    def validate_financial_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate common financial statement patterns and relationships.
        """
        # Convert formatted strings back to numbers
        def to_number(x):
            if not x or x == '':
                return 0.0
            try:
                clean = x.replace('$', '').replace(',', '')
                if clean.startswith('(') and clean.endswith(')'):
                    return -float(clean[1:-1])
                return float(clean)
            except:
                return 0.0

        # Create numeric version for calculations
        num_df = pd.DataFrame()
        for col in df.columns:
            if col != 'Item':
                num_df[col] = df[col].apply(to_number)
        
        # Common patterns to check
        patterns = {
            'income_statement': {
                'gross_profit': {
                    'components': ['revenue', 'cost of revenue'],
                    'check': lambda df: df[df['Item'].str.lower().str.contains('revenue')].iloc[0].sum() - 
                                     df[df['Item'].str.lower().str.contains('cost of')].iloc[0].sum()
                },
                'operating_income': {
                    'components': ['gross profit', 'operating expenses', 'research and development'],
                    'check': lambda df: df[df['Item'].str.lower().str.contains('gross profit')].iloc[0].sum() - 
                                     df[df['Item'].str.lower().str.contains('operating expenses|research and development')].sum().sum()
                },
                'net_income': {
                    'components': ['operating income', 'interest', 'tax', 'other'],
                    'check': lambda df: df[df['Item'].str.lower().str.contains('operating income')].iloc[0].sum() + 
                                     df[df['Item'].str.lower().str.contains('interest income')].sum().sum() -
                                     df[df['Item'].str.lower().str.contains('tax')].sum().sum()
                }
            },
            'balance_sheet': {
                'total_assets': {
                    'components': ['current assets', 'property', 'goodwill', 'intangible'],
                    'check': lambda x: x.sum()
                },
                'total_liabilities': {
                    'components': ['current liabilities', 'long-term', 'debt'],
                    'check': lambda x: x.sum()
                },
                'assets_equal_liabilities_equity': {
                    'components': ['total assets', 'total liabilities', 'equity'],
                    'check': lambda x: abs(x['total assets'] - (x['total liabilities'] + x['equity'])) < 0.1
                }
            }
        }
        
        # Check each pattern
        inconsistencies = []
        for statement_type, statement_patterns in patterns.items():
            for pattern_name, pattern_info in statement_patterns.items():
                # Find relevant rows
                relevant_rows = df['Item'].str.lower().str.contains('|'.join(pattern_info['components']), regex=True)
                if relevant_rows.any():
                    try:
                        expected = pattern_info['check'](num_df)
                        relevant_total = df[df['Item'].str.lower().str.contains(pattern_name, regex=True)]
                        if not relevant_total.empty:
                            total_row = relevant_total.index[0]
                            for col in num_df.columns:
                                actual = num_df.loc[total_row, col]
                                if abs(expected - actual) > 0.1:  # Allow for rounding
                                    inconsistencies.append(f"{pattern_name} in column {col}")
                                    df.loc[total_row, col] = f"{df.loc[total_row, col]}*"
                    except (KeyError, IndexError):
                        # Skip if we can't find the required components
                        continue
        
        if inconsistencies:
            print(f"Warning: Found inconsistencies in patterns: {', '.join(inconsistencies)}")
        
        return df

    def clean_table_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean up table data by removing empty rows and fixing formatting issues.
        """
        # Remove rows that are entirely empty or just whitespace
        df = df.dropna(how='all')
        df = df.loc[~(df.astype(str).apply(lambda x: x.str.strip().eq('')).all(axis=1))]
        
        # Clean up column headers
        df = self.clean_column_headers(df)
        
        # Fill empty cells with appropriate values
        df = df.fillna('')
        
        # Process numeric columns
        for col in df.columns:
            if col != 'Item':  # Skip the label column
                # Clean numbers
                df[col] = df[col].apply(self.clean_number)
                
                # Format numbers with currency
                df[col] = df[col].apply(lambda x: self.format_number(x, include_currency=True))
        
        # Validate financial patterns and totals
        df = self.validate_financial_patterns(df)
        df = self.validate_totals(df)
        
        # Remove consecutive empty rows
        df = df.loc[~((df == '').all(axis=1) & (df.shift() == '').all(axis=1))]
        
        return df
        
    def validate_totals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and mark any inconsistencies in financial totals.
        """
        # Convert formatted strings back to numbers for validation
        def to_number(x):
            if not x or x == '':
                return 0.0
            try:
                # Remove currency symbol and handle parentheses
                clean = x.replace('$', '').replace(',', '')
                if clean.startswith('(') and clean.endswith(')'):
                    return -float(clean[1:-1])
                return float(clean)
            except:
                return 0.0
        
        # Create a numeric version of the dataframe for calculations
        num_df = df.copy()
        for col in num_df.columns:
            if col != 'Item':
                num_df[col] = num_df[col].apply(to_number)
        
        # Check common financial statement patterns
        if 'Total' in df['Item'].values:
            # Find rows with 'Total' and validate their values
            total_rows = df[df['Item'].str.contains('Total', case=False, na=False)].index
            for idx in total_rows:
                # Get the total row and the rows above it until the previous total
                prev_total = df.index[df.index < idx].intersection(total_rows)
                start_idx = prev_total[-1] + 1 if len(prev_total) > 0 else df.index[0]
                
                # Calculate sum for each numeric column
                for col in df.columns:
                    if col != 'Item':
                        components = num_df.loc[start_idx:idx-1, col].sum()
                        reported_total = num_df.loc[idx, col]
                        
                        # If there's a significant difference, mark it
                        if abs(components - reported_total) > 0.1:  # Allow for rounding differences
                            df.loc[idx, col] = f"{df.loc[idx, col]}*"  # Mark suspicious totals
        
        return df
        
    def extract_tables(self, pdf_path: str, output_dir: str) -> List[Dict[str, Any]]:
        """Extract and process tables from PDF."""
        os.makedirs(output_dir, exist_ok=True)
        extraction_results = []
        
        with pdfplumber.open(pdf_path) as pdf:
            # Look through all pages
            for page_num, page in enumerate(pdf.pages):
                # Extract text around tables for context
                page_text = page.extract_text() or ''
                
                # Try different table settings
                settings = [
                    {
                        "vertical_strategy": "text",
                        "horizontal_strategy": "text",
                        "intersection_x_tolerance": 5,
                        "intersection_y_tolerance": 5
                    },
                    {
                        "vertical_strategy": "lines",
                        "horizontal_strategy": "text",
                        "intersection_x_tolerance": 3,
                        "intersection_y_tolerance": 3
                    }
                ]
                
                for setting in settings:
                    tables = page.extract_tables(table_settings=setting)
                    
                    for table_num, table in enumerate(tables):
                        if not table:
                            continue
                            
                        # Convert to DataFrame
                        df = pd.DataFrame(table)
                        
                        # Check if it's a financial table
                        if not self.is_likely_financial_table(df):
                            continue
                            
                        # Get table context
                        statement_type = self.detect_statement_type(' '.join(df.iloc[:, 0].astype(str)))
                        periods = self.extract_periods(df)
                        units = self.detect_units(page_text)
                        
                        # Clean and standardize the table
                        df = self.standardize_table(df)
                        
                        # Skip tables that don't have enough data after cleaning
                        if len(df) < 5 or len(df.columns) < 2:
                            continue
                            
                        # Save processed table
                        output_path = os.path.join(
                            output_dir,
                            f'table_{statement_type}_{page_num + 1:03d}_{table_num + 1:03d}.csv'
                        )
                        df.to_csv(output_path, index=False)
                        
                        # Save metadata
                        metadata = {
                            'page': page_num + 1,
                            'table_number': table_num + 1,
                            'statement_type': statement_type,
                            'periods': periods,
                            'units': units,
                            'path': output_path,
                            'rows': len(df),
                            'columns': len(df.columns)
                        }
                        extraction_results.append(metadata)
                        
                        print(f"Processed {statement_type} table from page {page_num + 1}")
        
        # Save extraction summary
        summary_path = os.path.join(output_dir, 'table_extraction_summary.json')
        with open(summary_path, 'w') as f:
            json.dump(extraction_results, f, indent=2)
            
        return extraction_results

def main():
    pdf_path = 'data/raw/pdf/nvda-20240128.pdf'
    output_dir = 'data/parsed/nvda-20240128/tables_enhanced2'
    
    extractor = FinancialTableExtractor()
    results = extractor.extract_tables(pdf_path, output_dir)
    
    print("\nExtraction Summary:")
    print(f"Total tables processed: {len(results)}")
    by_type = {}
    for result in results:
        by_type[result['statement_type']] = by_type.get(result['statement_type'], 0) + 1
    for type_name, count in by_type.items():
        print(f"- {type_name}: {count} tables")

if __name__ == '__main__':
    main()