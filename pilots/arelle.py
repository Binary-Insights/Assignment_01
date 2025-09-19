import os
import json
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Tuple
from bs4 import BeautifulSoup

class XBRLParser:
    def __init__(self, xbrl_file_path: str):
        """Initialize the XBRL parser with the path to the XBRL file."""
        self.xbrl_file_path = xbrl_file_path
        self.controller = Cntlr.Cntlr()
        self.model = None
        self.facts_dict = {}
        self.tables_data = {}
        
    def load_instance(self) -> None:
        """Load the XBRL instance file."""
        self.model = self.controller.modelManager.load(self.xbrl_file_path)
        if self.model is None:
            raise ValueError(f"Failed to load XBRL file: {self.xbrl_file_path}")
    
    def extract_facts(self) -> Dict[str, Any]:
        """Extract all facts from the XBRL instance."""
        for fact in self.model.facts:
            concept = fact.concept.qname
            context_ref = fact.contextID
            value = fact.value
            unit = fact.unit.value if fact.unit else None
            
            fact_key = str(concept)
            if fact_key not in self.facts_dict:
                self.facts_dict[fact_key] = []
            
            self.facts_dict[fact_key].append({
                'value': value,
                'context': context_ref,
                'unit': unit,
                'period': self._get_period_str(fact.context.period) if fact.context else None
            })
        
        return self.facts_dict
    
    def _get_period_str(self, period) -> str:
        """Convert period object to string representation."""
        if period.isInstant:
            return period.instantDatetime.strftime('%Y-%m-%d')
        else:
            start = period.startDatetime.strftime('%Y-%m-%d')
            end = period.endDatetime.strftime('%Y-%m-%d')
            return f"{start} to {end}"
    
    def extract_tables(self) -> Dict[str, pd.DataFrame]:
        """Extract tables from the XBRL instance based on presentation linkbase."""
        for relationship_set in self.model.relationshipSets.values():
            if relationship_set.arcrole.endswith('parentChild'):  # Presentation relationships
                for root in relationship_set.rootConcepts:
                    table_data = self._process_concept_tree(root, relationship_set)
                    if table_data:
                        table_name = str(root.qname)
                        self.tables_data[table_name] = pd.DataFrame(table_data)
        
        return self.tables_data
    
    def _process_concept_tree(self, concept, relationship_set, depth=0) -> List[Dict]:
        """Process a concept and its children in the presentation tree."""
        results = []
        
        # Get facts for this concept
        concept_facts = self.facts_dict.get(str(concept.qname), [])
        
        for fact_data in concept_facts:
            row_data = {
                'concept': str(concept.qname),
                'depth': depth,
                'label': concept.label(),
                **fact_data
            }
            results.append(row_data)
        
        # Process children
        for rel in relationship_set.fromModelObject(concept):
            child_results = self._process_concept_tree(rel.toModelObject, relationship_set, depth + 1)
            results.extend(child_results)
        
        return results
    
    def save_results(self, output_dir: str) -> None:
        """Save extracted data to files."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save facts
        with open(os.path.join(output_dir, 'xbrl_facts.json'), 'w') as f:
            json.dump(self.facts_dict, f, indent=2)
        
        # Save tables
        for table_name, df in self.tables_data.items():
            safe_name = "".join(c if c.isalnum() else "_" for c in table_name)
            df.to_csv(os.path.join(output_dir, f'table_{safe_name}.csv'), index=False)

def compare_values(xbrl_value: str, pdf_value: str, tolerance: float = 0.01) -> Tuple[bool, float]:
    """Compare numerical values from XBRL and PDF, handling different formats."""
    try:
        # Clean and convert values
        xbrl_num = float(str(xbrl_value).replace(',', ''))
        pdf_num = float(str(pdf_value).replace(',', ''))
        
        # Calculate difference
        diff = abs(xbrl_num - pdf_num)
        relative_diff = diff / abs(xbrl_num) if xbrl_num != 0 else diff
        
        return relative_diff <= tolerance, relative_diff
    except (ValueError, TypeError):
        return False, float('inf')

def create_validation_report(xbrl_data: Dict, pdf_tables: List[pd.DataFrame], output_path: str) -> None:
    """Create a validation report comparing XBRL and PDF data."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'matches': [],
        'mismatches': [],
        'unmatched': [],
        'summary': {
            'total_comparisons': 0,
            'matched': 0,
            'mismatched': 0,
            'unmatched': 0
        }
    }
    
    # Implementation of comparison logic here
    # This will need to be customized based on the specific structure of your PDF tables
    # and XBRL data
    
    # Save report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

def main():
    # Example usage
    xbrl_file_path = "path/to/your/xbrl/file.xbrl"
    output_dir = "path/to/output/directory"
    
    parser = XBRLParser(xbrl_file_path)
    parser.load_instance()
    parser.extract_facts()
    parser.extract_tables()
    parser.save_results(output_dir)

if __name__ == "__main__":
    main()
