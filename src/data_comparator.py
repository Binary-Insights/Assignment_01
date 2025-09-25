import os
import pandas as pd
import json
from typing import Dict, List, Tuple, Any
from datetime import datetime
from .table_normalizer import PDFTableLoader
from .arelle import XBRLParser

class DataComparator:
    def __init__(self, xbrl_data: Dict[str, Any], pdf_tables: Dict[str, pd.DataFrame]):
        """Initialize the comparator with XBRL and PDF data."""
        self.xbrl_data = xbrl_data
        self.pdf_tables = pdf_tables
        self.matches = []
        self.mismatches = []
        self.unmatched_xbrl = []
        self.unmatched_pdf = []
        
    def compare_all(self, tolerance: float = 0.01) -> Dict[str, Any]:
        """Compare all XBRL facts with PDF table data."""
        # Prepare XBRL facts for comparison
        processed_facts = self._process_xbrl_facts()
        
        # Compare each PDF table with XBRL facts
        for table_id, pdf_df in self.pdf_tables.items():
            self._compare_table(table_id, pdf_df, processed_facts, tolerance)
        
        # Compile report
        return self._generate_report()
    
    def _process_xbrl_facts(self) -> Dict[str, List[Dict[str, Any]]]:
        """Process XBRL facts into a more easily comparable format."""
        processed = {}
        
        for concept, facts in self.xbrl_data.items():
            for fact in facts:
                key = self._generate_fact_key(concept, fact)
                if key not in processed:
                    processed[key] = []
                
                processed[key].append({
                    'concept': concept,
                    'value': fact['value'],
                    'context': fact['context'],
                    'unit': fact['unit'],
                    'period': fact['period']
                })
        
        return processed
    
    def _generate_fact_key(self, concept: str, fact: Dict[str, Any]) -> str:
        """Generate a key for matching XBRL facts with PDF data."""
        # Extract meaningful parts from the concept name
        concept_parts = concept.split(':')[-1].lower()
        
        # Include period information if available
        period = fact.get('period', '')
        
        # Include unit if available
        unit = str(fact.get('unit', '')).lower()
        
        return f"{concept_parts}_{period}_{unit}"
    
    def _compare_table(self, table_id: str, pdf_df: pd.DataFrame, 
                      processed_facts: Dict[str, List[Dict]], tolerance: float) -> None:
        """Compare a single PDF table with processed XBRL facts."""
        # Convert PDF table values to numeric where possible
        numeric_df = pd.to_numeric(pdf_df.stack(), errors='coerce').unstack()
        
        for row_idx, row in numeric_df.iterrows():
            for col_name in numeric_df.columns:
                pdf_value = row[col_name]
                if pd.isna(pdf_value):
                    continue
                
                # Generate possible keys for matching
                possible_keys = self._generate_possible_keys(row_idx, col_name, pdf_df)
                
                # Look for matches in XBRL facts
                found_match = False
                for key in possible_keys:
                    if key in processed_facts:
                        for fact in processed_facts[key]:
                            is_match, diff = self._compare_values(
                                fact['value'], pdf_value, tolerance)
                            
                            if is_match:
                                self._record_match(table_id, fact, pdf_value, 
                                                 row_idx, col_name, diff)
                                found_match = True
                                break
                            else:
                                self._record_mismatch(table_id, fact, pdf_value,
                                                    row_idx, col_name, diff)
                
                if not found_match:
                    self._record_unmatched_pdf(table_id, pdf_value, row_idx, col_name)
    
    def _generate_possible_keys(self, row_idx: int, col_name: str, 
                              pdf_df: pd.DataFrame) -> List[str]:
        """Generate possible keys for matching PDF table data with XBRL facts."""
        keys = []
        
        # Get row label if available
        row_label = str(pdf_df.index[row_idx]).lower()
        # Get column label
        col_label = str(col_name).lower()
        
        # Generate variations of keys
        keys.extend([
            f"{row_label}_{col_label}",
            f"{col_label}_{row_label}",
            row_label,
            col_label
        ])
        
        return keys
    
    def _compare_values(self, xbrl_value: Any, pdf_value: float, 
                       tolerance: float) -> Tuple[bool, float]:
        """Compare XBRL and PDF values with tolerance."""
        try:
            xbrl_num = float(str(xbrl_value).replace(',', ''))
            diff = abs(xbrl_num - pdf_value)
            relative_diff = diff / abs(xbrl_num) if xbrl_num != 0 else diff
            
            return relative_diff <= tolerance, relative_diff
        except (ValueError, TypeError):
            return False, float('inf')
    
    def _record_match(self, table_id: str, fact: Dict[str, Any], pdf_value: float,
                     row_idx: int, col_name: str, difference: float) -> None:
        """Record a matching value."""
        self.matches.append({
            'table_id': table_id,
            'concept': fact['concept'],
            'xbrl_value': fact['value'],
            'pdf_value': pdf_value,
            'difference': difference,
            'location': {'row': row_idx, 'column': col_name},
            'context': fact['context'],
            'period': fact['period']
        })
    
    def _record_mismatch(self, table_id: str, fact: Dict[str, Any], pdf_value: float,
                        row_idx: int, col_name: str, difference: float) -> None:
        """Record a mismatched value."""
        self.mismatches.append({
            'table_id': table_id,
            'concept': fact['concept'],
            'xbrl_value': fact['value'],
            'pdf_value': pdf_value,
            'difference': difference,
            'location': {'row': row_idx, 'column': col_name},
            'context': fact['context'],
            'period': fact['period']
        })
    
    def _record_unmatched_pdf(self, table_id: str, pdf_value: float,
                             row_idx: int, col_name: str) -> None:
        """Record an unmatched PDF table value."""
        self.unmatched_pdf.append({
            'table_id': table_id,
            'pdf_value': pdf_value,
            'location': {'row': row_idx, 'column': col_name}
        })
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive comparison report."""
        return {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_comparisons': len(self.matches) + len(self.mismatches),
                'matches': len(self.matches),
                'mismatches': len(self.mismatches),
                'unmatched_pdf': len(self.unmatched_pdf),
                'unmatched_xbrl': len(self.unmatched_xbrl)
            },
            'matches': self.matches,
            'mismatches': self.mismatches,
            'unmatched_pdf': self.unmatched_pdf,
            'unmatched_xbrl': self.unmatched_xbrl
        }

def main():
    # Example usage
    xbrl_file = "path/to/xbrl/file.xbrl"
    pdf_tables_dir = "path/to/pdf/tables"
    output_dir = "path/to/output"
    
    # Parse XBRL
    parser = XBRLParser(xbrl_file)
    parser.load_instance()
    xbrl_data = parser.extract_facts()
    
    # Load PDF tables
    loader = PDFTableLoader(pdf_tables_dir)
    loader.load_all_tables()
    pdf_tables = loader.get_financial_tables()
    
    # Compare data
    comparator = DataComparator(xbrl_data, pdf_tables)
    report = comparator.compare_all()
    
    # Save report
    output_path = os.path.join(output_dir, 'comparison_report.json')
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    main()