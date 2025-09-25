import os
import json
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Any
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class XBRLDataLoader:
    def __init__(self):
        """Initialize the XBRL data loader."""
        self.namespaces = {
            'us-gaap': 'http://fasb.org/us-gaap/2021-01-31',
            'dei': 'http://xbrl.sec.gov/dei/2021',
            'xbrli': 'http://www.xbrl.org/2003/instance'
        }
    
    def parse_context(self, context_element: ET.Element) -> Dict[str, Any]:
        """Parse an XBRL context element."""
        context_id = context_element.attrib['id']
        
        # Try to find period information
        period = context_element.find('.//xbrli:period', self.namespaces)
        period_info = {}
        if period is not None:
            instant = period.find('xbrli:instant', self.namespaces)
            if instant is not None:
                period_info['type'] = 'instant'
                period_info['date'] = instant.text
            else:
                start = period.find('xbrli:startDate', self.namespaces)
                end = period.find('xbrli:endDate', self.namespaces)
                if start is not None and end is not None:
                    period_info['type'] = 'duration'
                    period_info['startDate'] = start.text
                    period_info['endDate'] = end.text
        
        # Try to find segment information
        segment = context_element.find('.//xbrli:segment', self.namespaces)
        segment_info = {}
        if segment is not None:
            for dimension in segment.findall('.//xbrldi:explicitMember', self.namespaces):
                dimension_name = dimension.attrib.get('dimension', '').replace('us-gaap:', '')
                segment_info[dimension_name] = dimension.text
        
        return {
            'id': context_id,
            'period': period_info,
            'segment': segment_info
        }
    
    def parse_unit(self, unit_element: ET.Element) -> Dict[str, str]:
        """Parse an XBRL unit element."""
        unit_id = unit_element.attrib['id']
        measure = unit_element.find('.//xbrli:measure', self.namespaces)
        return {
            'id': unit_id,
            'measure': measure.text if measure is not None else None
        }
    
    def extract_facts(self, xbrl_file: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract numerical facts from an XBRL file."""
        logger.info(f"Parsing XBRL file: {xbrl_file}")
        
        try:
            # Parse XML tree
            tree = ET.parse(xbrl_file)
            root = tree.getroot()
            
            # Extract contexts and units first
            contexts = {}
            units = {}
            
            for context in root.findall('.//xbrli:context', self.namespaces):
                contexts[context.attrib['id']] = self.parse_context(context)
            
            for unit in root.findall('.//xbrli:unit', self.namespaces):
                units[unit.attrib['id']] = self.parse_unit(unit)
            
            # Extract facts
            facts = {}
            
            # Define namespaces to search for facts
            for prefix, uri in self.namespaces.items():
                if prefix in ['us-gaap', 'dei']:
                    # Find all elements in this namespace
                    for element in root.findall(f'.//{{{uri}}}*'):
                        concept = f"{prefix}:{element.tag.split('}')[-1]}"
                        
                        # Only process if it has a numerical value
                        if element.text and element.text.strip():
                            try:
                                value = float(element.text.strip())
                                
                                fact = {
                                    'value': value,
                                    'decimals': element.attrib.get('decimals'),
                                    'context': contexts[element.attrib['contextRef']],
                                    'unit': units.get(element.attrib.get('unitRef'))
                                }
                                
                                if concept not in facts:
                                    facts[concept] = []
                                facts[concept].append(fact)
                                
                            except (ValueError, KeyError) as e:
                                # Skip non-numerical or invalid facts
                                continue
            
            logger.info(f"Extracted {len(facts)} unique concepts from XBRL file")
            return facts
            
        except Exception as e:
            logger.error(f"Error parsing XBRL file: {str(e)}")
            return {}
    
    def normalize_facts(self, facts: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """Normalize extracted facts for comparison."""
        normalized = {}
        
        for concept, fact_list in facts.items():
            normalized[concept] = []
            
            for fact in fact_list:
                # Get the scaling factor from decimals attribute
                decimals = fact.get('decimals')
                value = fact['value']
                
                if decimals is not None:
                    try:
                        decimals = int(decimals)
                        # Apply scaling based on decimals
                        if decimals < 0:
                            value = value / (10 ** abs(decimals))
                    except ValueError:
                        pass
                
                normalized_fact = {
                    'value': value,
                    'context': fact['context'],
                    'unit': fact['unit']
                }
                
                normalized[concept].append(normalized_fact)
        
        return normalized

def main():
    # File paths
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    xbrl_path = os.path.join(project_root, 'data', 'raw', 'sec-edgar-filings', 
                            '0001045810', '10-K', 'nvda-20240128.xml')
    output_path = os.path.join(project_root, 'data', 'parsed', 'nvda-20240128',
                              'xbrl_data.json')
    
    # Load and process XBRL data
    loader = XBRLDataLoader()
    facts = loader.extract_facts(xbrl_path)
    normalized_facts = loader.normalize_facts(facts)
    
    # Save extracted data
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_concepts': len(normalized_facts),
            'facts': normalized_facts
        }, f, indent=2)
    
    logger.info(f"XBRL data saved to: {output_path}")

if __name__ == "__main__":
    main()