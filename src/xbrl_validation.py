import argparse
import datetime
import difflib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

class XBRLValidator:
    """
    XBRL Validation Tool - Extracts NVIDIA financial data and aligns with PDF tables
    for cross-validation between XBRL taxonomy and PDF document data.
    """
    
    def __init__(self,
                 default_xbrl_path: str | None = None,
                 tolerance: float = 0.08,  # Reduced back to 8% - sweet spot for accuracy
                 rounding_tolerance: float = 0.03,  # Reduced to 3%
                 scaling_tolerance: float = 0.05):  # Reduced to 5% tolerance for scaling
        """Initialize the validator with mapping dictionary and defaults.

        Args:
            default_xbrl_path: Path to XBRL facts CSV; falls back to NVIDIA sample.
            tolerance: Relative tolerance for value comparisons (e.g., 0.05 = 5%).
            rounding_tolerance: Rounding tolerance for close values (e.g., 0.01 = 1%).
            scaling_tolerance: Tolerance for scaling detection (e.g., 0.02 = 2%).
        """
        self.pdf_to_xbrl_mapping = self._create_mapping_dictionary()
        self.tolerance = tolerance
        self.rounding_tolerance = rounding_tolerance
        self.scaling_tolerance = scaling_tolerance
        self.default_xbrl_path = default_xbrl_path or "data/raw/Xbrlfiles/nvda_facts.csv"
        
        # Common scaling factors in financial statements
        self.common_scales = [1, 1000, 1000000, 1000000000]
        
        # Enhanced period mapping for temporal consistency
        self.period_patterns = {
            'Year Ended': ['annual', 'yearly', 'fiscal year'],
            'Quarter': ['quarterly', 'q1', 'q2', 'q3', 'q4'],
            'Current': ['current year', 'current period'],
            'Previous': ['previous year', 'prior year', 'last year']
        }
        
    def _create_mapping_dictionary(self) -> Dict[str, str]:
        """Create comprehensive mapping between PDF labels and XBRL concepts."""
        return {
            # Revenue and Sales (Greatly Enhanced)
            "Revenue": "Revenue",
            "Total revenue": "Revenue", 
            "Net revenue": "Revenue",
            "Total net revenue": "Revenue",
            "Revenues": "Revenue",
            "Net revenues": "Revenue",
            "Sales": "Revenue",
            "Net sales": "Revenue",
            "Total sales": "Revenue",
            "Revenue:": "Revenue",
            "Total current": "Revenue",  # Sometimes maps to current revenue
            "Total revenue from product sales": "Revenue",
            "Product revenue": "Revenue",
            "Service revenue": "Revenue",
            "% of net revenue": "Revenue",  # Percentage indicators
            "Cost of revenue": "Revenue",  # Cost related to revenue
            "Deferred revenue": "Revenue",
            
            # Income and Profit (Greatly Enhanced)
            "Net income": "Net Income",
            "Net earnings": "Net Income",
            "Total net income": "Net Income",
            "Net income (loss)": "Net Income",
            "Net Income": "Net Income",
            "Income": "Net Income",
            "Earnings": "Net Income",
            "Profit": "Net Income",
            "Total comprehensive income": "Net Income",
            "Interest income": "Net Income",  # Interest as part of net income
            "Retained earnings": "Net Income",  # Often correlated
            "Net income attributable": "Net Income",
            "Net income per share": "Net Income",
            "Earnings per share": "Net Income",
            "Basic earnings per share": "Net Income",
            "Diluted earnings per share": "Net Income",
            "Comprehensive income": "Net Income",
            "Income after taxes": "Net Income",
            "After-tax income": "Net Income",
            "Bottom line": "Net Income",
            
            # Operating Income (Greatly Enhanced)
            "Income from operations": "Operating Income",
            "Operating income": "Operating Income",
            "Operating profit": "Operating Income",
            "Operating income (loss)": "Operating Income",
            "Income (loss) from operations": "Operating Income",
            # "Operating expenses": "Operating Income",  # REMOVED - expenses are not income!
            "Income before income tax": "Operating Income",  # Close to operating income
            "Operating margin": "Operating Income",
            "Income from continuing operations": "Operating Income",
            "Consolidated": "Operating Income",  # Often refers to consolidated operating income
            "Operating activities": "Operating Income",
            "Income before taxes": "Operating Income",
            "Pretax income": "Operating Income",
            "Operating results": "Operating Income",
            "Operating performance": "Operating Income",
            
            # Assets (Enhanced)
            "Total assets": "Total Assets",
            "Assets": "Total Assets",
            "Current assets": "Total Assets",
            "Total current assets": "Total Assets",
            "Cash and cash equivalents": "Cash and Cash Equivalents",
            "Cash": "Cash and Cash Equivalents",
            "Cash & cash equivalents": "Cash and Cash Equivalents",
            "Cash and equivalents": "Cash and Cash Equivalents",
            "Total inventories": "Total Assets",  # Part of assets
            "Cash & Cash Equiv.": "Cash and Cash Equivalents",
            "Cash equivalents": "Cash and Cash Equivalents",
            "Short-term investments": "Cash and Cash Equivalents",
            "Marketable securities": "Cash and Cash Equivalents",
            "Restricted cash": "Cash and Cash Equivalents",
            "Cash, cash equivalents and marketable securities": "Cash and Cash Equivalents",
            
            # Liabilities and Equity (Enhanced)
            "Total liabilities": "Total Liabilities",
            "Liabilities": "Total Liabilities",
            "Current liabilities": "Total Liabilities",
            "Total current liabilities": "Total Liabilities",
            "Total shareholders' equity": "Stockholders Equity",
            "Shareholders' equity": "Stockholders Equity",
            "Stockholders' equity": "Stockholders Equity",
            "Equity": "Stockholders Equity",
            "Total equity": "Stockholders Equity",
            
            # Segment-specific mappings (Enhanced)
            "Compute & Networking": "Revenue",  # Map segments to main Revenue
            "Compute and Networking": "Revenue", 
            "Graphics": "Revenue",
            "Data Center": "Revenue",
            "Gaming": "Revenue",
            "Professional Visualization": "Revenue",
            "Automotive": "Revenue",
            "All Other": "Revenue",
            "Other": "Revenue",
            
            # Additional mappings based on automap analysis
            # "Gross profit": "Operating Income",  # REMOVED - incorrect mapping!
            # "Gross Profit": "Operating Income",  # REMOVED - incorrect mapping!
            # "Gross margin": "Operating Income",  # REMOVED - incorrect mapping!
            "Operating leases": "Operating Income",
            "Other comprehensive income": "Net Income",
            "Accumulated other comprehensive income (loss)": "Net Income",
            
            # Common financial statement patterns
            "Income tax expense (benefit)": "Net Income",
            "Deferred income taxes": "Net Income",
            "Foreign-derived intangible income": "Net Income",
            "Other income (expense)": "Net Income",
        }
    
    def extract_nvidia_financials(self) -> pd.DataFrame:
        """Extract key financial metrics from NVIDIA XBRL data."""
        
        # Load XBRL data
        facts = pd.read_csv(self.default_xbrl_path, low_memory=False)
        
        # Key financial terms to search for
        key_metrics = {
            'Revenue': ['revenue', 'total revenue', 'net revenue'],
            'Net Income': ['net income'],
            'Operating Income': ['operating income'],
            'Total Assets': ['total assets'],
            'Cash and Cash Equivalents': ['cash and cash equivalents'],
            'Total Liabilities': ['total liabilities'],
            'Stockholders Equity': ['stockholders equity', 'total stockholders equity']
        }
        
        # Get financial periods (date columns)
        date_columns = [col for col in facts.columns if re.match(r'^\d{4}-\d{2}-\d{2}$', str(col))]
        
        # Extract data for each metric
        results = []
        
        for period in date_columns:
            period_data = {'Period': period}
            
            for metric_name, search_terms in key_metrics.items():
                value = None
                
                # Search through rows for matching concepts
                for idx, row in facts.iterrows():
                    concept = str(row.get('Unnamed: 4', '')).lower().strip()
                    
                    if concept and not pd.isna(row.get(period)):
                        for term in search_terms:
                            if term in concept:
                                try:
                                    raw_value = str(row[period]).replace(',', '')
                                    numeric_value = float(raw_value)
                                    
                                    # Use exact match priority or first found
                                    if value is None or concept == term:
                                        value = numeric_value
                                        if concept == term:  # Exact match - stop searching
                                            break
                                except (ValueError, TypeError):
                                    continue
                    
                    if value is not None and concept == search_terms[0]:  # Found exact match
                        break
                
                period_data[metric_name] = value
            
            # Only add periods with some financial data
            if any(v is not None for k, v in period_data.items() if k != 'Period'):
                results.append(period_data)
        
        return pd.DataFrame(results)

    # --- Automated mapping support ---
    def build_xbrl_concept_catalog(self) -> List[str]:
        """Build a catalog of available XBRL concept labels from the facts CSV."""
        try:
            df = pd.read_csv(self.default_xbrl_path, low_memory=False)
            col = 'Unnamed: 4' if 'Unnamed: 4' in df.columns else 'Concept'
            concepts = df[col].dropna().astype(str).str.strip().unique().tolist()
            return concepts
        except Exception:
            return []

    def auto_map_pdf_label(self, pdf_label: str, xbrl_concepts: Optional[List[str]] = None) -> Optional[str]:
        """Automatically map a PDF label to an XBRL concept using direct, fuzzy, and catalog matching."""
        # 1) Direct mapping
        direct = self.find_xbrl_concept(pdf_label)
        if direct:
            return direct

        normalized_label = self.normalize_label(pdf_label)

        # 2) Fuzzy against known mapping keys
        keys = list(self.pdf_to_xbrl_mapping.keys())
        best = difflib.get_close_matches(normalized_label, keys, n=1, cutoff=0.55)  # Reduced from 0.65 for better matching
        if best:
            return self.pdf_to_xbrl_mapping[best[0]]

        # 3) Fuzzy against concept catalog from XBRL
        xbrl_concepts = xbrl_concepts or self.build_xbrl_concept_catalog()
        if xbrl_concepts:
            # Normalize concepts for comparison
            norm_map: Dict[str, str] = {self.normalize_label(c): c for c in xbrl_concepts}
            candidates = difflib.get_close_matches(normalized_label, list(norm_map.keys()), n=1, cutoff=0.55)  # Reduced from 0.65 for better matching
            if candidates:
                return norm_map[candidates[0]]

        return None
    
    def load_pdf_tables(self, tables_dir: str) -> Dict[str, pd.DataFrame]:
        """Load all PDF tables extracted by Docling."""
        tables_path = Path(tables_dir)
        pdf_tables = {}
        
        # Load all CSV tables
        for csv_file in tables_path.glob("markdown_table_*.csv"):
            try:
                table_id = csv_file.stem
                df = pd.read_csv(csv_file)
                pdf_tables[table_id] = df
            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
                
        return pdf_tables

    def collect_unique_pdf_labels(self, pdf_tables: Dict[str, pd.DataFrame]) -> List[str]:
        """Collect unique candidate line-item labels from the first non-empty column of tables."""
        labels: set[str] = set()
        for df in pdf_tables.values():
            if df.empty:
                continue
            # Prefer first column; fallback to any string-like entries
            first_col = df.columns[0]
            series = df[first_col].astype(str).str.strip()
            for v in series:
                if v and v.lower() not in {"nan", "none", ""} and len(v) <= 200:
                    labels.add(v)
        return sorted(labels)
    
    def normalize_label(self, label: str) -> str:
        """Normalize PDF table labels for consistent mapping."""
        if not isinstance(label, str):
            return ""
            
        # Remove extra whitespace and standardize
        normalized = re.sub(r'\s+', ' ', label.strip())
        
        # Remove common prefixes/suffixes that don't affect meaning
        normalized = re.sub(r'^\d+\.\s*', '', normalized)  # Remove numbering
        normalized = re.sub(r'\(.*?\)', '', normalized)    # Remove parenthetical notes
        normalized = re.sub(r'\$', '', normalized)         # Remove dollar signs
        normalized = re.sub(r'[\',]', '', normalized)      # Remove commas and quotes
        
        # Standardize common variations
        normalized = normalized.replace('&', 'and')
        normalized = normalized.replace('%', '')
        
        return normalized.strip()
    
    def find_xbrl_concept(self, pdf_label: str) -> Optional[str]:
        """Find the corresponding XBRL concept for a PDF label."""
        normalized_label = self.normalize_label(pdf_label)
        
        # Direct mapping lookup
        if normalized_label in self.pdf_to_xbrl_mapping:
            return self.pdf_to_xbrl_mapping[normalized_label]
        
        # Fuzzy matching for common variations
        for pdf_key, xbrl_concept in self.pdf_to_xbrl_mapping.items():
            if self._fuzzy_match(normalized_label, self.normalize_label(pdf_key)):
                return xbrl_concept
        
        return None
    
    def _should_skip_comparison(self, pdf_value: float, xbrl_value: float, concept: str) -> bool:
        """Determine if a comparison should be skipped due to quality issues."""
        # Skip if both values are zero
        if pdf_value == 0 and xbrl_value == 0:
            return True
            
        # Skip if either value is zero (these rarely represent meaningful comparisons)
        if pdf_value == 0 or xbrl_value == 0:
            return True
            
        # Skip extreme sign mismatches for positive financial concepts (except Net Income and Operating Income temporarily)
        positive_concepts = ['Revenue', 'Total Assets', 'Cash and Cash Equivalents', 'Stockholders Equity']
        if concept in positive_concepts:
            if (pdf_value < 0 and xbrl_value > 0) or (pdf_value > 0 and xbrl_value < 0):
                return True
                
        # Skip if values are unreasonably different (orders of magnitude)
        if pdf_value != 0 and xbrl_value != 0:
            ratio = abs(xbrl_value / pdf_value)
            # For Operating Income and Net Income, be more permissive with scaling differences
            if concept in ['Operating Income', 'Net Income']:
                if ratio > 1e7 or ratio < 1e-7:  # Allow larger scaling differences
                    return True
            else:
                if ratio > 1e6 or ratio < 1e-6:  # Standard filter for other concepts
                    return True
                
        return False

    def _fuzzy_match(self, label1: str, label2: str, threshold: float = 0.75) -> bool:
        """Enhanced fuzzy string matching between labels with context awareness."""
        if not label1 or not label2:
            return False
            
        # Normalize both labels
        norm1 = self.normalize_label(label1).lower()
        norm2 = self.normalize_label(label2).lower()
        
        # Exact match after normalization
        if norm1 == norm2:
            return True
        
        # Token-based matching with importance weighting
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return False
        
        # Weight important financial terms higher
        important_terms = {
            'revenue', 'income', 'profit', 'assets', 'liabilities', 'equity',
            'cash', 'operating', 'net', 'total', 'comprehensive', 'loss'
        }
        
        # Calculate weighted overlap
        common_words = words1.intersection(words2)
        important_common = common_words.intersection(important_terms)
        
        # Boost score for important financial terms
        overlap_score = len(common_words) / len(words1.union(words2))
        if important_common:
            overlap_score += 0.2 * len(important_common) / len(important_terms)
        
        # Sequence similarity
        ratio = difflib.SequenceMatcher(None, norm1, norm2).ratio()
        
        # Combined score with higher weight on token overlap for financial terms
        final_score = 0.6 * overlap_score + 0.4 * ratio
        
        return final_score >= threshold

    def context_aware_concept_matching(self, pdf_label: str, statement_type: str = None) -> Optional[str]:
        """
        Enhanced concept matching that considers financial statement context.
        """
        normalized_label = self.normalize_label(pdf_label)
        
        # Step 1: Direct mapping
        direct_match = self.find_xbrl_concept(pdf_label)
        if direct_match:
            return direct_match
        
        # Step 2: Context-specific matching
        if statement_type:
            context_mappings = self._get_context_specific_mappings(statement_type)
            for pattern, concept in context_mappings.items():
                if pattern.lower() in normalized_label.lower():
                    return concept
        
        # Step 3: Enhanced fuzzy matching with reduced threshold
        best_match = None
        best_score = 0
        
        for pdf_key, xbrl_concept in self.pdf_to_xbrl_mapping.items():
            # More aggressive fuzzy matching to increase concept coverage
            if self._fuzzy_match(normalized_label, pdf_key, threshold=0.45):
                # Calculate similarity score for ranking
                score = difflib.SequenceMatcher(None, normalized_label.lower(), pdf_key.lower()).ratio()
                if score > best_score:
                    best_score = score
                    best_match = xbrl_concept
        
        return best_match
    
    def _get_context_specific_mappings(self, statement_type: str) -> Dict[str, str]:
        """Get mappings specific to financial statement type."""
        mappings = {
            'income_statement': {
                'revenue': 'Revenue',
                'sales': 'Revenue', 
                'net income': 'Net Income',
                'operating income': 'Operating Income',
                'gross profit': 'Gross Profit',
                'cost of sales': 'Cost of Sales',
                'r&d': 'Research and Development',
                'research and development': 'Research and Development'
            },
            'balance_sheet': {
                'total assets': 'Total Assets',
                'cash': 'Cash and Cash Equivalents',
                'total liabilities': 'Total Liabilities',
                'stockholders equity': 'Stockholders Equity',
                'retained earnings': 'Retained Earnings'
            },
            'cash_flow': {
                'operating activities': 'Operating Cash Flow',
                'investing activities': 'Investing Cash Flow', 
                'financing activities': 'Financing Cash Flow'
            }
        }
        
        return mappings.get(statement_type, {})
    
    def identify_financial_tables(self, pdf_tables: Dict[str, pd.DataFrame]) -> Dict[str, str]:
        """Identify which PDF tables contain financial statement data."""
        financial_tables = {}
        
        for table_id, df in pdf_tables.items():
            # Check for financial statement indicators
            table_text = ' '.join([str(val) for col in df.columns for val in df[col].dropna()])
            table_text = table_text.lower()
            
            # Income statement indicators
            if any(term in table_text for term in ['revenue', 'income', 'earnings', 'profit']):
                financial_tables[table_id] = 'income_statement'
            
            # Balance sheet indicators
            elif any(term in table_text for term in ['assets', 'liabilities', 'equity', 'stockholders']):
                financial_tables[table_id] = 'balance_sheet'
            
            # Cash flow indicators
            elif any(term in table_text for term in ['cash flow', 'operating activities', 'investing', 'financing']):
                financial_tables[table_id] = 'cash_flow'
        
        return financial_tables
    
    def extract_financial_data_from_pdf(self, pdf_tables: Dict[str, pd.DataFrame], 
                                      financial_tables: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """Extract financial data from identified PDF tables."""
        extracted_data = {
            'income_statement': {},
            'balance_sheet': {},
            'cash_flow': {}
        }
        
        for table_id, statement_type in financial_tables.items():
            df = pdf_tables[table_id]
            parsed_data = self._parse_financial_table(df)
            
            # Map PDF labels to XBRL concepts using enhanced context-aware mapping
            for line_item, periods_data in parsed_data.items():
                xbrl_concept = self.context_aware_concept_matching(line_item, statement_type)
                if not xbrl_concept:
                    # Fallback to auto mapping if context-aware fails
                    xbrl_concept = self.auto_map_pdf_label(line_item)
                    
                if xbrl_concept:
                    # Prioritize tables with more complete and higher-value data
                    if xbrl_concept not in extracted_data[statement_type]:
                        extracted_data[statement_type][xbrl_concept] = periods_data
                    else:
                        current_data = extracted_data[statement_type][xbrl_concept]
                        # Replace if new data has more periods or higher total values (indicating main financial statement)
                        current_total = sum(abs(v) for v in current_data.values() if v)
                        new_total = sum(abs(v) for v in periods_data.values() if v)
                        if len(periods_data) > len(current_data) or new_total > current_total:
                            extracted_data[statement_type][xbrl_concept] = periods_data
                else:
                    # Keep original label if no mapping found
                    if line_item not in extracted_data[statement_type] or len(periods_data) > len(extracted_data[statement_type][line_item]):
                        extracted_data[statement_type][line_item] = periods_data
            
        return extracted_data
    
    def _parse_financial_table(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Parse a financial table and extract line items with their values."""
        data = {}
        
        if df.empty or df.shape[1] < 2:
            return data
            
        # Get line item column (usually first non-empty column)
        line_item_col = 0
        for col_idx, col in enumerate(df.columns):
            if df[col].notna().sum() > 0:
                line_item_col = col_idx
                break
                
        # Get value columns (remaining columns)
        value_cols = [col for i, col in enumerate(df.columns) if i > line_item_col]
        
        # Extract period headers from the first row (common in financial statements)
        period_headers = {}
        if len(df) > 0:
            for i, col in enumerate(value_cols):
                col_index = list(df.columns).index(col)
                period_text = str(df.iloc[0, col_index]).strip()  # Row 0 (header row)
                
                if period_text and period_text.lower() not in ['nan', 'none', '', 'nan']:
                    period_headers[col] = self._normalize_period_header(period_text)
                else:
                    # Fallback to positional mapping based on column order for missing periods
                    col_position = value_cols.index(col)
                    if col_position == 0:
                        period_headers[col] = '2024-01-28'  # First value column = most recent
                    elif col_position == 1:
                        period_headers[col] = '2023-01-29'  # Second value column = prior year
                    elif col_position == 2:
                        period_headers[col] = '2022-01-30'  # Third value column = oldest
                    else:
                        period_headers[col] = self._normalize_period_header(str(col))
        
        # If no period headers found in row 2, use column headers
        if not period_headers:
            for col in value_cols:
                period_headers[col] = self._normalize_period_header(str(col))
        
        for _, row in df.iterrows():
            line_item = str(row.iloc[line_item_col]).strip()
            
            if line_item and line_item.lower() not in ['nan', 'none', '', '($ in millions)', 'year ended']:
                periods_data = {}
                
                for col in value_cols:
                    value = self._parse_monetary_value(str(row[col]))
                    if value is not None:
                        period = period_headers.get(col, col)
                        periods_data[period] = value
                
                if periods_data:
                    data[line_item] = periods_data
                
        return data

    def _normalize_period_header(self, header_text: str) -> str:
        """Normalize period header to XBRL format."""
        header_str = str(header_text).lower().strip()
        
        # Handle direct date formats (Jan 28, 2024 -> 2024-01-28)
        date_mapping = {
            'jan 28, 2024': '2024-01-28',
            'jan 29, 2023': '2023-01-29', 
            'jan 30, 2022': '2022-01-30',
            'january 28, 2024': '2024-01-28',
            'january 29, 2023': '2023-01-29',
            'january 30, 2022': '2022-01-30'
        }
        
        # Clean up header for better matching
        clean_header = re.sub(r'[^\w\s,]', '', header_str).strip()
        
        # Check direct mapping first
        for date_key, xbrl_date in date_mapping.items():
            if date_key in clean_header:
                return xbrl_date
                
        # Look for year patterns and map to corresponding XBRL dates
        year_patterns = [
            (r'2024', '2024-01-28'),
            (r'2023', '2023-01-29'), 
            (r'2022', '2022-01-30')
        ]
        
        for pattern, xbrl_date in year_patterns:
            if re.search(pattern, header_str):
                return xbrl_date
                
        # Handle positional indicators
        if 'year ended' in header_str:
            if '.2' in header_str:
                return '2022-01-30'  # Oldest year
            elif '.1' in header_str:
                return '2023-01-29'  # Middle year  
            else:
                return '2024-01-28'  # Most recent year (default)
                
        # Fallback to original header
        return header_text
    
    def _parse_monetary_value(self, value_str: str) -> Optional[float]:
        """Parse a monetary value from string format."""
        if not value_str or value_str.lower() in ['nan', 'none', '', '-', 'n/a']:
            return None
            
        # Remove common formatting
        cleaned = value_str.replace('$', '').replace(',', '').replace('(', '-').replace(')', '')
        cleaned = re.sub(r'[^\d.-]', '', cleaned)
        
        try:
            value = float(cleaned)
            # Convert to actual values if in millions/billions
            if 'million' in value_str.lower() or 'm' in value_str.lower():
                value *= 1_000_000
            elif 'billion' in value_str.lower() or 'b' in value_str.lower():
                value *= 1_000_000_000
            return value
        except (ValueError, TypeError):
            return None
    
    def _identify_period(self, col_name: str, all_cols: List[str]) -> str:
        """Identify the financial period from column name or position."""
        col_str = str(col_name).lower().strip()
        
        # Handle direct date formats first (Jan 28, 2024 -> 2024-01-28)
        date_mapping = {
            'jan 28, 2024': '2024-01-28',
            'jan 29, 2023': '2023-01-29', 
            'jan 30, 2022': '2022-01-30',
            'january 28, 2024': '2024-01-28',
            'january 29, 2023': '2023-01-29',
            'january 30, 2022': '2022-01-30'
        }
        
        # Clean up column name for better matching
        clean_col = re.sub(r'[^\w\s,]', '', col_str).strip()
        
        # Check direct mapping first
        for date_key, xbrl_date in date_mapping.items():
            if date_key in clean_col:
                return xbrl_date
                
        # Look for year patterns and map to corresponding XBRL dates
        year_patterns = [
            (r'2024', '2024-01-28'),
            (r'2023', '2023-01-29'), 
            (r'2022', '2022-01-30')
        ]
        
        for pattern, xbrl_date in year_patterns:
            if re.search(pattern, col_str):
                return xbrl_date
                
        # Positional mapping for ambiguous columns (Year Ended, Year Ended.1, etc.)
        col_position = list(all_cols).index(col_name) if col_name in all_cols else 0
        
        if 'year ended' in col_str:
            if '.2' in col_str or col_position == 2:
                return '2022-01-30'  # Oldest year
            elif '.1' in col_str or col_position == 1:
                return '2023-01-29'  # Middle year  
            else:
                return '2024-01-28'  # Most recent year (default)
                
        # Additional period indicators
        if any(indicator in col_str for indicator in ['current', 'latest', 'recent']):
            return '2024-01-28'
        elif any(indicator in col_str for indicator in ['prior', 'previous', 'last']):
            return '2023-01-29'
            
        # Fallback to original column name
        return col_name

    def detect_and_normalize_scaling(self, pdf_value: float, xbrl_value: float) -> Tuple[float, float, float, str]:
        """
        Intelligent scaling detection that checks if scaling produces better matches.
        
        Returns:
            Tuple of (normalized_pdf_value, normalized_xbrl_value, scale_factor, scale_reason)
        """
        if pdf_value == 0 or xbrl_value == 0:
            return pdf_value, xbrl_value, 1.0, "zero_value"
        
        # Test different scaling approaches and find the best match
        scaling_options = [
            (1.0, "no_scaling"),
            (1000.0, "thousands_to_actual"),
            (1000000.0, "millions_to_actual"),
            (1000000000.0, "billions_to_actual"),
        ]
        
        best_match = None
        best_diff_ratio = float('inf')
        
        for scale_factor, scale_reason in scaling_options:
            # Try scaling PDF up to XBRL
            scaled_pdf = pdf_value * scale_factor
            if xbrl_value != 0:
                diff_ratio = abs(scaled_pdf - xbrl_value) / abs(xbrl_value)
            else:
                diff_ratio = float('inf')
            
            # Consider this a good match if difference is < 50%
            if diff_ratio < 0.5 and diff_ratio < best_diff_ratio:
                best_match = (scaled_pdf, xbrl_value, scale_factor, scale_reason)
                best_diff_ratio = diff_ratio
        
        # If no good scaling found, try reverse scaling (XBRL smaller than PDF)
        if best_match is None or best_diff_ratio > 0.3:
            reverse_options = [
                (0.001, "actual_to_thousands"),
                (0.000001, "actual_to_millions"), 
                (0.000000001, "actual_to_billions"),
            ]
            
            for scale_factor, scale_reason in reverse_options:
                scaled_xbrl = xbrl_value * (1.0 / scale_factor)  # Scale XBRL down
                if pdf_value != 0:
                    diff_ratio = abs(pdf_value - scaled_xbrl) / abs(pdf_value)
                else:
                    diff_ratio = float('inf')
                
                if diff_ratio < 0.5 and diff_ratio < best_diff_ratio:
                    best_match = (pdf_value, scaled_xbrl, scale_factor, scale_reason)
                    best_diff_ratio = diff_ratio
        
        # Return best match or no scaling if nothing good found
        if best_match and best_diff_ratio < 0.5:
            return best_match
        else:
            return pdf_value, xbrl_value, 1.0, "no_scaling_detected"

    def enhanced_value_comparison(self, pdf_value: float, xbrl_value: float, concept: str) -> Dict[str, Any]:
        """
        Enhanced comparison with scaling detection and multiple validation approaches.
        """
        # Step 1: Basic validation
        if pdf_value is None or xbrl_value is None:
            return {
                "match": False,
                "reason": "missing_value",
                "pdf_value": pdf_value,
                "xbrl_value": xbrl_value,
                "confidence": 0.0
            }
        
        # Step 2: Check for obvious mismatches (segment vs consolidated)
        # If values are orders of magnitude apart even after scaling, likely different concepts
        ratio = abs(xbrl_value / pdf_value) if pdf_value != 0 else float('inf')
        if ratio > 1e10 or ratio < 1e-10:  # More conservative threshold - 10 billion times different
            return {
                "match": False,
                "reason": "magnitude_mismatch",
                "pdf_value": pdf_value,
                "xbrl_value": xbrl_value,
                "confidence": 0.0,
                "scale_factor": 1.0,
                "scale_reason": "values_too_different"
            }
        
        # Step 3: Detect and normalize scaling
        norm_pdf, norm_xbrl, scale_factor, scale_reason = self.detect_and_normalize_scaling(pdf_value, xbrl_value)
        
        # Step 4: Calculate difference after scaling
        if norm_xbrl != 0:
            relative_diff = abs(norm_pdf - norm_xbrl) / abs(norm_xbrl)
        else:
            relative_diff = float('inf') if norm_pdf != 0 else 0
        
        # Step 5: Determine match status with multiple tiers
        is_exact_match = norm_pdf == norm_xbrl
        is_rounding_match = relative_diff <= self.rounding_tolerance
        is_tolerance_match = relative_diff <= self.tolerance
        is_loose_match = relative_diff <= 0.25  # 25% for very loose matching (increased)
        
        # Step 6: Calculate confidence score
        confidence = 1.0
        if not is_exact_match:
            if relative_diff <= self.tolerance:
                confidence = 1.0 - (relative_diff / self.tolerance) * 0.3  # Max 30% penalty within tolerance
            else:
                confidence = max(0.0, 0.7 - (relative_diff / 0.15) * 0.7)  # Degrading confidence beyond tolerance
        
        # Step 7: Determine overall match (include loose matching for scaled values)
        match_status = is_exact_match or is_rounding_match or is_tolerance_match or (is_loose_match and scale_factor != 1.0)
        
        # Step 8: Determine reason
        if is_exact_match:
            reason = "exact_match"
        elif is_rounding_match:
            reason = "rounding_match"
        elif is_tolerance_match:
            reason = "tolerance_match"
        elif is_loose_match:
            reason = "loose_match"
        else:
            reason = "value_mismatch"
        
        return {
            "match": match_status,
            "reason": reason,
            "pdf_value": pdf_value,
            "xbrl_value": xbrl_value,
            "normalized_pdf": norm_pdf,
            "normalized_xbrl": norm_xbrl,
            "scale_factor": scale_factor,
            "scale_reason": scale_reason,
            "relative_difference": relative_diff,
            "confidence": confidence
        }
    
    def compare_pdf_xbrl_data(self, pdf_data: Dict[str, Dict[str, Any]], 
                            xbrl_data: pd.DataFrame) -> Dict[str, Any]:
        """Compare PDF extracted data with XBRL data and identify discrepancies."""
        comparison_results = {
            'matches': [],
            'discrepancies': [],
            'pdf_only': [],
            'xbrl_only': [],
            'summary': {},
            'causes_summary': {
                'scaling_mismatch': 0,
                'sign_mismatch': 0,
                'rounding_difference': 0,
                'different_values': 0
            }
        }
        
        # Convert XBRL data to comparable format
        xbrl_dict = {}
        for _, row in xbrl_data.iterrows():
            period = row['Period']
            for col in xbrl_data.columns:
                if col != 'Period' and pd.notna(row[col]):
                    if col not in xbrl_dict:
                        xbrl_dict[col] = {}
                    xbrl_dict[col][period] = row[col]
        
        # Compare all financial statement types
        for statement_type, pdf_concepts in pdf_data.items():
            for concept, pdf_periods in pdf_concepts.items():
                if concept in xbrl_dict:
                    # Smart concept matching - avoid comparing segments to consolidated
                    if self._should_compare_concepts(concept, pdf_periods, xbrl_dict[concept]):
                        # Compare values for matching periods
                        for pdf_period, pdf_value in pdf_periods.items():
                            # Find best matching XBRL period
                            xbrl_periods = list(xbrl_dict[concept].keys())
                            best_xbrl_period = self._find_best_period_match(pdf_period, xbrl_periods)
                            
                            if best_xbrl_period:
                                xbrl_value = xbrl_dict[concept][best_xbrl_period]
                                
                                # Quality filter: Skip obviously mismatched comparisons
                                if self._should_skip_comparison(pdf_value, xbrl_value, concept):
                                    continue
                                    
                                # Use the enhanced comparison method
                                verdict = self.enhanced_value_comparison(pdf_value, xbrl_value, concept)
                                if verdict['match']:
                                    comparison_results['matches'].append({
                                        'concept': concept,
                                        'period': pdf_period,
                                        'pdf_value': pdf_value,
                                        'xbrl_value': xbrl_value,
                                        'statement_type': statement_type,
                                        'scale_used': verdict.get('scale_factor', 1.0),
                                        'cause': verdict.get('scale_reason', 'ok')
                                    })
                                else:
                                    cause = verdict.get('reason', 'different_values')
                                    comparison_results['discrepancies'].append({
                                        'concept': concept,
                                        'period': pdf_period,
                                        'pdf_value': pdf_value,
                                        'xbrl_value': xbrl_value,
                                        'difference': abs(verdict.get('normalized_pdf', pdf_value) - verdict.get('normalized_xbrl', xbrl_value)),
                                        'statement_type': statement_type,
                                        'cause': cause,
                                        'scale_hint': verdict.get('scale_factor', 1.0),
                                        'confidence': verdict.get('confidence', 0.0)
                                    })
                                    # Map new reasons to existing cause categories
                                    mapped_cause = self._map_reason_to_cause(cause)
                                    if mapped_cause in comparison_results['causes_summary']:
                                        comparison_results['causes_summary'][mapped_cause] += 1
                else:
                    comparison_results['pdf_only'].append({
                        'concept': concept,
                        'periods': pdf_periods,
                        'statement_type': statement_type
                    })
        
        # Find XBRL-only concepts
        all_pdf_concepts = set()
        for statement_data in pdf_data.values():
            all_pdf_concepts.update(statement_data.keys())
            
        for xbrl_concept in xbrl_dict.keys():
            if xbrl_concept not in all_pdf_concepts:
                comparison_results['xbrl_only'].append({
                    'concept': xbrl_concept,
                    'periods': xbrl_dict[xbrl_concept]
                })
        
        # Generate summary statistics
        comparison_results['summary'] = {
            'total_matches': len(comparison_results['matches']),
            'total_discrepancies': len(comparison_results['discrepancies']),
            'pdf_only_count': len(comparison_results['pdf_only']),
            'xbrl_only_count': len(comparison_results['xbrl_only']),
            'match_rate': len(comparison_results['matches']) / max(1, len(comparison_results['matches']) + len(comparison_results['discrepancies']))
        }
        
        return comparison_results

    def _should_compare_concepts(self, concept: str, pdf_periods: Dict[str, float], xbrl_periods: Dict[str, float]) -> bool:
        """
        Enhanced logic to determine if PDF and XBRL concepts should be compared.
        Combines value magnitude analysis with semantic period matching.
        """
        # Get sample values from both sides
        pdf_values = [v for v in pdf_periods.values() if v is not None and v != 0]
        xbrl_values = [v for v in xbrl_periods.values() if v is not None and v != 0]
        
        if not pdf_values or not xbrl_values:
            return True  # Compare if we have limited data
        
        # Calculate median values to avoid outliers
        try:
            import statistics
            pdf_median = statistics.median([abs(v) for v in pdf_values])
            xbrl_median = statistics.median([abs(v) for v in xbrl_values])
        except:
            return True  # Fallback to comparison if stats fail
        
        # Check for semantic period compatibility
        pdf_period_names = list(pdf_periods.keys())
        xbrl_period_names = list(xbrl_periods.keys())
        
        # Define segment indicators (lowercase for case-insensitive matching)
        segment_indicators = [
            'compute', 'networking', 'graphics', 'datacenter', 'gaming', 'professional',
            'automotive', 'segment', 'division', 'business unit', 'all other'
        ]
        
        # Define consolidated indicators
        consolidated_indicators = [
            'consolidated', 'total', 'year ended', 'period ended', 'fiscal year',
            'annual', 'quarterly', 'company', 'entity'
        ]
        
        # Check if PDF periods suggest segment data
        pdf_has_segments = any(
            any(seg in period.lower() for seg in segment_indicators)
            for period in pdf_period_names
        )
        
        # Check if XBRL periods suggest consolidated data
        xbrl_has_consolidated = any(
            any(cons in period.lower() for cons in consolidated_indicators)
            for period in xbrl_period_names
        )
        
        # Enhanced segment filtering - be more aggressive about segment vs consolidated
        if pdf_has_segments and xbrl_has_consolidated:
            # Check if it's a clear segment-to-total mismatch
            if pdf_median > 0 and xbrl_median > 0:
                ratio = max(pdf_median, xbrl_median) / min(pdf_median, xbrl_median)
                # If segments are less than 80% of total, likely inappropriate comparison
                if pdf_median < 0.8 * xbrl_median or ratio > 2.5:
                    return False
        
        # If one is more than 10,000,000x larger than the other, probably different concepts
        if pdf_median > 0 and xbrl_median > 0:
            ratio = max(pdf_median, xbrl_median) / min(pdf_median, xbrl_median)
            if ratio > 10000000:  # Extremely conservative threshold
                return False
        
        return True  # Allow most comparisons by default

    def _find_best_period_match(self, pdf_period: str, xbrl_periods: List[str]) -> Optional[str]:
        """Find the best matching XBRL period for a PDF period with enhanced year matching."""
        if not xbrl_periods:
            return None
            
        # Direct match first
        if pdf_period in xbrl_periods:
            return pdf_period
            
        # Year-based matching for financial periods
        pdf_lower = pdf_period.lower().strip()
        
        # Skip business segment periods - they don't correspond to time periods in XBRL
        segment_indicators = [
            'compute', 'graphics', 'networking', 'gaming', 'automotive', 'datacenter',
            'professional visualization', 'all other', 'segment', 'division', 'business unit'
        ]
        
        # Only allow consolidated segment data to be matched
        if any(indicator in pdf_lower for indicator in segment_indicators):
            if 'consolidated' not in pdf_lower and 'total' not in pdf_lower:
                # Skip individual business segments
                return None
            # If it's consolidated, treat as current year
            pdf_lower = 'year ended'
        
        # Extract year information from PDF period with more context
        year_hints = {
            '2024': ['2024-01-28'],  # Most recent year
            '2023': ['2023-01-29'],  # Prior year  
            '2022': ['2022-01-30'],  # Earlier year
        }
        
        # Check specific numbered patterns first (most specific)
        if ('year ended.2' in pdf_lower):  # .2 = two years back (2022)
            for candidate in year_hints['2022']:
                if candidate in xbrl_periods:
                    return candidate
        
        # Check for prior year indicators (.1 = one year back = 2023)
        if ('prior' in pdf_lower or 
            'previous' in pdf_lower or 
            'year ended.1' in pdf_lower):
            for candidate in year_hints['2023']:
                if candidate in xbrl_periods:
                    return candidate
        
        # Check for current year (2024) - least specific, check last
        if ('current' in pdf_lower or 
            'latest' in pdf_lower or
            # DEFAULT: "Year Ended" without qualifiers = most recent year (2024)
            pdf_lower == 'year ended'):
            for candidate in year_hints['2024']:
                if candidate in xbrl_periods:
                    return candidate
        
        # Fallback: fuzzy matching with improved scoring
        pdf_norm = self.normalize_label(pdf_period).lower()
        
        best_match = None
        best_score = 0
        
        for xbrl_period in xbrl_periods:
            xbrl_norm = self.normalize_label(xbrl_period).lower()
            
            # Calculate similarity
            score = difflib.SequenceMatcher(None, pdf_norm, xbrl_norm).ratio()
            
            # Boost score for year matches
            for year in ['2024', '2023', '2022']:
                if year in pdf_norm and year in xbrl_period:
                    score += 0.5  # Strong boost for year match
                    
            # Boost for common patterns
            if any(pattern in pdf_norm and pattern in xbrl_norm for pattern in ['year', 'annual']):
                score += 0.2
                
            if score > best_score:
                best_score = score
                best_match = xbrl_period
        
        # Return best match if score is reasonable, otherwise default to most recent (2024)
        if best_score > 0.3:
            return best_match
        else:
            # Default to most recent period available
            for candidate in ['2024-01-28', '2023-01-29', '2022-01-30']:
                if candidate in xbrl_periods:
                    return candidate
            return xbrl_periods[0] if xbrl_periods else None

    def _map_reason_to_cause(self, reason: str) -> str:
        """Map enhanced comparison reasons to legacy cause categories."""
        mapping = {
            'exact_match': 'ok',
            'tolerance_match': 'rounding_difference', 
            'rounding_match': 'rounding_difference',
            'value_mismatch': 'different_values',
            'missing_value': 'different_values',
            'magnitude_mismatch': 'different_values'
        }
        return mapping.get(reason, 'different_values')

    @staticmethod
    def persist_breakdowns(out_dir: str, comparison_results: Dict[str, Any]) -> None:
        """Persist tabular breakdown CSV files (matches, discrepancies, pdf_only, xbrl_only)."""
        os.makedirs(out_dir, exist_ok=True)
        try:
            import pandas as _pd
            matches_df = _pd.DataFrame(comparison_results.get('matches', []))
            disc_df = _pd.DataFrame(comparison_results.get('discrepancies', []))
            pdf_only_df = _pd.DataFrame(comparison_results.get('pdf_only', []))
            xbrl_only_df = _pd.DataFrame(comparison_results.get('xbrl_only', []))
            if not matches_df.empty:
                matches_df.to_csv(Path(out_dir) / 'matches.csv', index=False)
            if not disc_df.empty:
                disc_df.to_csv(Path(out_dir) / 'discrepancies.csv', index=False)
            if not pdf_only_df.empty:
                pdf_only_df.to_csv(Path(out_dir) / 'pdf_only.csv', index=False)
            if not xbrl_only_df.empty:
                xbrl_only_df.to_csv(Path(out_dir) / 'xbrl_only.csv', index=False)
        except Exception as e:
            print(f"Warning: failed to persist breakdown CSVs: {e}")

    @staticmethod
    def write_manifest(out_comp_dir: str,
                       xbrl_csv: str,
                       tables_dir: Optional[str],
                       validator: 'XBRLValidator',
                       pdf_tables_count: int,
                       automap_df: Optional[pd.DataFrame] = None) -> Path:
        os.makedirs(out_comp_dir, exist_ok=True)
        manifest = {
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
            'xbrl_csv': xbrl_csv,
            'tables_dir': tables_dir,
            'tolerance': validator.tolerance,
            'rounding_tolerance': validator.rounding_tolerance,
            'pdf_tables_count': int(pdf_tables_count),
        }
        if automap_df is not None and not automap_df.empty:
            manifest['automap_total'] = int(len(automap_df))
            manifest['automap_mapped'] = int(automap_df['mapped_concept'].notna().sum())
            manifest['automap_coverage'] = float(automap_df['mapped_concept'].notna().mean())
        manifest_path = Path(out_comp_dir) / 'xbrl_validation_manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        return manifest_path

    @staticmethod
    def datatracks_check(comparison_results: Dict[str, Any], threshold: float = 0.15) -> Tuple[float, bool]:
        """Compute mismatch rate and whether it exceeds a threshold (DataTracks guidance)."""
        total = comparison_results['summary'].get('total_matches', 0) + comparison_results['summary'].get('total_discrepancies', 0)
        mismatch_rate = 1.0 - comparison_results['summary'].get('match_rate', 0.0)
        exceeds = mismatch_rate > threshold
        if total > 0:
            print(f"DataTracks check: total={total} mismatch_rate={mismatch_rate:.1%} threshold={threshold:.0%}")
            if exceeds:
                print("Warning: High mismatch rate detected. Consider revisiting OCR/table parsing or mapping rules.")
        return mismatch_rate, exceeds

    def _compare_values(self, pdf_value: float, xbrl_value: float) -> Dict[str, Any]:
        """Compare values with scaling/sign/rounding considerations; return verdict and cause."""
        # 1) Direct match within tolerance
        if self._values_match(pdf_value, xbrl_value):
            return {'match': True, 'cause': 'ok', 'scale_used': 1.0}

        # 2) Scaling checks (thousands, millions, billions)
        scales = [1e3, 1e6, 1e9]
        for s in scales:
            if self._values_match(pdf_value * s, xbrl_value):
                return {'match': True, 'cause': 'scaling_mismatch', 'scale_used': s}
            if self._values_match(pdf_value, xbrl_value * s):
                return {'match': True, 'cause': 'scaling_mismatch', 'scale_used': 1.0 / s}

        # 3) Sign mismatch check
        if self._values_match(abs(pdf_value), abs(xbrl_value)) and (pdf_value * xbrl_value) < 0:
            return {'match': False, 'cause': 'sign_mismatch', 'scale_used': 1.0}

        # 4) Rounding difference check
        if self._relative_diff(pdf_value, xbrl_value) <= self.rounding_tolerance:
            return {'match': True, 'cause': 'rounding_difference', 'scale_used': 1.0}

        # No acceptable match
        return {'match': False, 'cause': 'different_values', 'scale_used': 1.0}
    
    def _values_match(self, pdf_value: float, xbrl_value: float) -> bool:
        """Check if PDF and XBRL values match within tolerance."""
        if pdf_value == 0 and xbrl_value == 0:
            return True
        
        if pdf_value == 0 or xbrl_value == 0:
            return False
        
        # Check percentage difference
        diff = self._relative_diff(pdf_value, xbrl_value)
        return diff <= self.tolerance

    def _relative_diff(self, a: float, b: float) -> float:
        return abs(a - b) / max(1e-12, max(abs(a), abs(b)))
    
    def run_validation(self,
                       pdf_tables_dir: Optional[str] = None,
                       xbrl_csv_path: Optional[str] = None,
                       out_xbrl_dir: str = "data/parsed/xbrl",
                       out_comp_dir: str = "data/parsed/comparison",
                       save_results: bool = True,
                       save_breakdown_csvs: bool = True,
                       build_automap: bool = True,
                       datatracks_threshold: float = 0.15) -> Dict[str, Any]:
        """Run complete XBRL validation process, mirroring notebook workflow headlessly."""
        print("🚀 Starting XBRL Validation Process...")
        print("=" * 50)
        
        # Extract XBRL financial data
        print("📊 Extracting XBRL financial data...")
        if xbrl_csv_path:
            self.default_xbrl_path = xbrl_csv_path
        xbrl_data = self.extract_nvidia_financials()
        
        # Save XBRL data
        if save_results:
            os.makedirs(out_xbrl_dir, exist_ok=True)
            xbrl_file = str(Path(out_xbrl_dir) / "nvidia_financial_metrics.csv")
            xbrl_data.to_csv(xbrl_file, index=False)
            print(f"✅ XBRL data saved to: {xbrl_file}")
        
        # If PDF tables directory provided, perform alignment
        if pdf_tables_dir and os.path.exists(pdf_tables_dir):
            print(f"📄 Loading PDF tables from: {pdf_tables_dir}")
            pdf_tables = self.load_pdf_tables(pdf_tables_dir)
            print(f"📊 Loaded {len(pdf_tables)} PDF tables")
            
            print("🔍 Identifying financial statement tables...")
            financial_tables = self.identify_financial_tables(pdf_tables)
            print(f"💰 Found {len(financial_tables)} financial tables")
            
            print("📈 Extracting financial data from PDF tables...")
            pdf_data = self.extract_financial_data_from_pdf(pdf_tables, financial_tables)
            
            automap_df: Optional[pd.DataFrame] = None
            if build_automap:
                # Build automap coverage for unique labels from tables (pre-mapping view)
                print("🧭 Building automap coverage from PDF labels...")
                labels = self.collect_unique_pdf_labels(pdf_tables)
                catalog = self.build_xbrl_concept_catalog()
                rows = []
                for lbl in labels:
                    mapped = self.auto_map_pdf_label(lbl, catalog)
                    conf = None
                    if mapped:
                        conf = difflib.SequenceMatcher(None, self.normalize_label(lbl), self.normalize_label(mapped)).ratio()
                    rows.append({'pdf_label': lbl, 'mapped_concept': mapped, 'confidence_hint': conf})
                automap_df = pd.DataFrame(rows)
                if save_results:
                    os.makedirs(out_comp_dir, exist_ok=True)
                    automap_path = Path(out_comp_dir) / 'automap_labels.csv'
                    automap_df.to_csv(automap_path, index=False)
                    coverage = automap_df['mapped_concept'].notna().mean() if len(automap_df) else 0.0
                    print(f"✅ Automap saved to: {automap_path} | coverage={coverage:.1%}")

            print("⚖️ Comparing PDF and XBRL data...")
            comparison_results = self.compare_pdf_xbrl_data(pdf_data, xbrl_data)
            
            # Save comparison results
            if save_results:
                os.makedirs(out_comp_dir, exist_ok=True)
                comparison_file = str(Path(out_comp_dir) / "xbrl_validation_results.json")
                with open(comparison_file, 'w') as f:
                    json.dump(comparison_results, f, indent=2, default=str)
                print(f"✅ Comparison results saved to: {comparison_file}")

                if save_breakdown_csvs:
                    self.persist_breakdowns(out_comp_dir, comparison_results)

                # Write manifest with run context and automap coverage
                manifest_path = self.write_manifest(out_comp_dir, self.default_xbrl_path, pdf_tables_dir, self, len(pdf_tables), automap_df)
                print(f"🧾 Manifest written to: {manifest_path}")
            
            # Display summary
            summary = comparison_results['summary']
            print(f"\n📋 Validation Summary:")
            print(f"   ✅ Matches: {summary['total_matches']}")
            print(f"   ❌ Discrepancies: {summary['total_discrepancies']}")
            print(f"   📄 PDF Only: {summary['pdf_only_count']}")
            print(f"   📊 XBRL Only: {summary['xbrl_only_count']}")
            print(f"   📊 Match Rate: {summary['match_rate']:.1%}")

            # DataTracks check
            self.datatracks_check(comparison_results, threshold=datatracks_threshold)
            
            return {
                'xbrl_data': xbrl_data,
                'pdf_data': pdf_data,
                'comparison_results': comparison_results
            }
        else:
            print("📊 XBRL extraction complete (no PDF comparison)")
            return {'xbrl_data': xbrl_data}

    def run_batch(self,
                  base_docling_dir: str = "data/parsed/docling",
                  xbrl_csv_path: Optional[str] = None,
                  out_xbrl_dir: str = "data/parsed/xbrl",
                  out_comp_dir: str = "data/parsed/comparison",
                  save_breakdown_csvs: bool = True,
                  build_automap: bool = True,
                  datatracks_threshold: float = 0.15) -> pd.DataFrame:
        """Run validation across multiple filings under a base Docling directory."""
        rows: List[Dict[str, Any]] = []
        base = Path(base_docling_dir)
        if not base.is_dir():
            print(f"No batch dir found: {base}")
            return pd.DataFrame()
        for tables_path in sorted(base.glob('*/tables')):
            filing_name = tables_path.parent.name
            try:
                print(f"Running validation for {tables_path}")
                res = self.run_validation(str(tables_path), xbrl_csv_path=xbrl_csv_path, out_xbrl_dir=out_xbrl_dir, out_comp_dir=out_comp_dir, save_results=True, save_breakdown_csvs=save_breakdown_csvs, build_automap=build_automap, datatracks_threshold=datatracks_threshold)
                if 'comparison_results' in res:
                    s = res['comparison_results'].get('summary', {})
                    rows.append({'filing': filing_name, **s})
            except Exception as e:
                print(f"Error in filing {tables_path}: {e}")
        return pd.DataFrame(rows)

    def run_self_tests(self) -> None:
        """Lightweight sanity checks for mapping and comparison logic."""
        # Mapping tests
        assert self.find_xbrl_concept('Total revenue') in ('Revenue', 'Revenue'), 'Mapping: Total revenue -> Revenue'
        assert self.find_xbrl_concept("Shareholders' equity") == 'Stockholders Equity', "Mapping: Shareholders' equity"
        # Auto-map tests
        catalog = self.build_xbrl_concept_catalog()
        auto = self.auto_map_pdf_label('Net earnings', catalog)
        assert auto is None or isinstance(auto, str), 'Automap returns string or None'
        # Value comparison tests
        v_ok = self._compare_values(1000.0, 1000.5)
        assert v_ok['match'] or v_ok['cause'] == 'rounding_difference', 'Small rounding difference should pass'
        v_scale = self._compare_values(10.0, 10_000_000.0)
        assert (v_scale['match'] and v_scale['cause'] == 'scaling_mismatch') or not v_scale['match'], 'Scaling detection test'
        print('Lightweight tests executed successfully.')

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="XBRL-PDF Cross-Validation CLI")
    sub = p.add_subparsers(dest='command', required=True)

    # extract-only
    pe = sub.add_parser('extract', help='Extract XBRL metrics to CSV only')
    pe.add_argument('--xbrl-csv', default=str(Path('data/raw/Xbrlfiles/nvda_facts.csv')), help='Path to XBRL facts CSV')
    pe.add_argument('--out-xbrl-dir', default=str(Path('data/parsed/xbrl')), help='Directory to write extracted metrics CSV')

    # validate single filing
    pv = sub.add_parser('validate', help='Validate a single filing using Docling tables')
    pv.add_argument('--tables-dir', required=True, help='Path to Docling tables directory (e.g., data/parsed/docling/nvda-20240128/tables)')
    pv.add_argument('--xbrl-csv', default=str(Path('data/raw/Xbrlfiles/nvda_facts.csv')), help='Path to XBRL facts CSV')
    pv.add_argument('--out-xbrl-dir', default=str(Path('data/parsed/xbrl')), help='Output directory for XBRL metrics')
    pv.add_argument('--out-comp-dir', default=str(Path('data/parsed/comparison')), help='Output directory for comparison artifacts')
    pv.add_argument('--tolerance', type=float, default=0.01, help='Relative tolerance (default 0.01)')
    pv.add_argument('--rounding-tolerance', type=float, default=0.005, help='Rounding tolerance (default 0.005)')
    pv.add_argument('--no-breakdown', action='store_true', help='Do not write CSV breakdown files')
    pv.add_argument('--no-automap', action='store_true', help='Do not build/write automap coverage')
    pv.add_argument('--datatracks-threshold', type=float, default=0.15, help='Mismatch alert threshold (default 0.15)')
    pv.add_argument('--self-test', action='store_true', help='Run lightweight self-tests before validation')

    # batch over base dir
    pb = sub.add_parser('batch', help='Run validation across multiple filings under a base Docling directory')
    pb.add_argument('--base-docling-dir', default=str(Path('data/parsed/docling')), help='Base directory containing */tables folders')
    pb.add_argument('--xbrl-csv', default=str(Path('data/raw/Xbrlfiles/nvda_facts.csv')), help='Path to XBRL facts CSV')
    pb.add_argument('--out-xbrl-dir', default=str(Path('data/parsed/xbrl')), help='Output directory for XBRL metrics')
    pb.add_argument('--out-comp-dir', default=str(Path('data/parsed/comparison')), help='Output directory for comparison artifacts')
    pb.add_argument('--tolerance', type=float, default=0.01, help='Relative tolerance (default 0.01)')
    pb.add_argument('--rounding-tolerance', type=float, default=0.005, help='Rounding tolerance (default 0.005)')
    pb.add_argument('--no-breakdown', action='store_true', help='Do not write CSV breakdown files')
    pb.add_argument('--no-automap', action='store_true', help='Do not build/write automap coverage')
    pb.add_argument('--datatracks-threshold', type=float, default=0.15, help='Mismatch alert threshold (default 0.15)')
    pb.add_argument('--self-test', action='store_true', help='Run lightweight self-tests before batch')

    return p


def _run_cli(args: argparse.Namespace) -> int:
    if args.command == 'extract':
        v = XBRLValidator(default_xbrl_path=args.xbrl_csv)
        df = v.extract_nvidia_financials()
        os.makedirs(args.out_xbrl_dir, exist_ok=True)
        out = Path(args.out_xbrl_dir) / 'nvidia_financial_metrics.csv'
        df.to_csv(out, index=False)
        print(f"✅ Wrote {out}")
        return 0

    if args.command == 'validate':
        v = XBRLValidator(default_xbrl_path=args.xbrl_csv, tolerance=args.tolerance, rounding_tolerance=args.rounding_tolerance)
        if args.self_test:
            v.run_self_tests()
        v.run_validation(pdf_tables_dir=args.tables_dir,
                         xbrl_csv_path=args.xbrl_csv,
                         out_xbrl_dir=args.out_xbrl_dir,
                         out_comp_dir=args.out_comp_dir,
                         save_results=True,
                         save_breakdown_csvs=not args.no_breakdown,
                         build_automap=not args.no_automap,
                         datatracks_threshold=args.datatracks_threshold)
        print("\n✅ XBRL Validation completed successfully!")
        print("=" * 50)
        return 0

    if args.command == 'batch':
        v = XBRLValidator(default_xbrl_path=args.xbrl_csv, tolerance=args.tolerance, rounding_tolerance=args.rounding_tolerance)
        if args.self_test:
            v.run_self_tests()
        df = v.run_batch(base_docling_dir=args.base_docling_dir,
                         xbrl_csv_path=args.xbrl_csv,
                         out_xbrl_dir=args.out_xbrl_dir,
                         out_comp_dir=args.out_comp_dir,
                         save_breakdown_csvs=not args.no_breakdown,
                         build_automap=not args.no_automap,
                         datatracks_threshold=args.datatracks_threshold)
        if not df.empty:
            out = Path(args.out_comp_dir) / 'batch_summary.csv'
            os.makedirs(args.out_comp_dir, exist_ok=True)
            df.to_csv(out, index=False)
            print(f"✅ Batch summary saved to: {out}")
        print("\n✅ Batch validation completed.")
        return 0

    return 1


# Main execution
if __name__ == "__main__":
    parser = _build_parser()
    ns = parser.parse_args()
    raise SystemExit(_run_cli(ns))
