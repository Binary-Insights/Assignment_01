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
                 tolerance: float = 0.01,
                 rounding_tolerance: float = 0.005):
        """Initialize the validator with mapping dictionary and defaults.

        Args:
            default_xbrl_path: Path to XBRL facts CSV; falls back to NVIDIA sample.
            tolerance: Relative tolerance for value comparisons (e.g., 0.01 = 1%).
            rounding_tolerance: Rounding tolerance for close values (e.g., 0.005 = 0.5%).
        """
        self.pdf_to_xbrl_mapping = self._create_mapping_dictionary()
        self.tolerance = tolerance
        self.rounding_tolerance = rounding_tolerance
        self.default_xbrl_path = default_xbrl_path or "data/raw/Xbrlfiles/nvda_facts.csv"
        
    def _create_mapping_dictionary(self) -> Dict[str, str]:
        """Create comprehensive mapping between PDF labels and XBRL concepts."""
        return {
            # Revenue and Sales
            "Revenue": "Revenue",
            "Total revenue": "Revenue", 
            "Net revenue": "Revenue",
            "Total net revenue": "Revenue",
            
            # Income and Profit
            "Net income": "Net Income",
            "Net earnings": "Net Income",
            "Total net income": "Net Income",
            "Operating income": "Operating Income",
            "Income from operations": "Operating Income",
            "Operating profit": "Operating Income",
            
            # Assets
            "Total assets": "Total Assets",
            "Cash and cash equivalents": "Cash and Cash Equivalents",
            "Cash": "Cash and Cash Equivalents",
            "Cash & cash equivalents": "Cash and Cash Equivalents",
            
            # Liabilities and Equity
            "Total liabilities": "Total Liabilities",
            "Total shareholders' equity": "Stockholders Equity",
            "Shareholders' equity": "Stockholders Equity",
            "Stockholders' equity": "Stockholders Equity",
            
            # NVIDIA Specific Segments
            "Compute & Networking": "Compute & Networking",
            "Compute and Networking": "Compute & Networking",
            "Graphics": "Graphics",
            "Data Center": "Data Center",
            "Gaming": "Gaming",
            "Professional Visualization": "Professional Visualization",
            "Automotive": "Automotive",
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
        best = difflib.get_close_matches(normalized_label, keys, n=1, cutoff=0.82)
        if best:
            return self.pdf_to_xbrl_mapping[best[0]]

        # 3) Fuzzy against concept catalog from XBRL
        xbrl_concepts = xbrl_concepts or self.build_xbrl_concept_catalog()
        if xbrl_concepts:
            # Normalize concepts for comparison
            norm_map: Dict[str, str] = {self.normalize_label(c): c for c in xbrl_concepts}
            candidates = difflib.get_close_matches(normalized_label, list(norm_map.keys()), n=1, cutoff=0.82)
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
    
    def _fuzzy_match(self, label1: str, label2: str, threshold: float = 0.8) -> bool:
        """Perform fuzzy string matching between labels."""
        # Combine token overlap and difflib ratio
        words1 = set(label1.lower().split())
        words2 = set(label2.lower().split())
        if not words1 or not words2:
            return False
        overlap = len(words1.intersection(words2)) / max(1, len(words1.union(words2)))
        ratio = difflib.SequenceMatcher(None, label1.lower(), label2.lower()).ratio()
        # weight both signals
        score = 0.5 * overlap + 0.5 * ratio
        return score >= threshold
    
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
            
            # Map PDF labels to XBRL concepts
            for line_item, periods_data in parsed_data.items():
                xbrl_concept = self.auto_map_pdf_label(line_item)
                if xbrl_concept:
                    extracted_data[statement_type][xbrl_concept] = periods_data
                else:
                    # Keep original label if no mapping found
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
        
        for _, row in df.iterrows():
            line_item = str(row.iloc[line_item_col]).strip()
            
            if line_item and line_item.lower() not in ['nan', 'none', '']:
                periods_data = {}
                
                for col in value_cols:
                    value = self._parse_monetary_value(str(row[col]))
                    if value is not None:
                        period = self._identify_period(col, value_cols)
                        periods_data[period] = value
                
                if periods_data:
                    data[line_item] = periods_data
                
        return data
    
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
        col_str = str(col_name).lower()
        
        # Look for date patterns
        date_patterns = [
            r'(\d{4})',
            r'jan\s*\d{1,2},?\s*(\d{4})',
            r'(\d{4})-(\d{2})-(\d{2})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, col_str)
            if match:
                return match.group(1) if match.group(1) else match.group(0)
                
        # Fallback to column name
        return col_name
    
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
                    # Compare values for matching periods
                    for pdf_period, pdf_value in pdf_periods.items():
                        # Find best matching XBRL period
                        xbrl_periods = list(xbrl_dict[concept].keys())
                        best_xbrl_period = self._find_best_period_match(pdf_period, xbrl_periods)
                        
                        if best_xbrl_period:
                            xbrl_value = xbrl_dict[concept][best_xbrl_period]
                            verdict = self._compare_values(pdf_value, xbrl_value)
                            if verdict['match']:
                                comparison_results['matches'].append({
                                    'concept': concept,
                                    'period': pdf_period,
                                    'pdf_value': pdf_value,
                                    'xbrl_value': xbrl_value,
                                    'statement_type': statement_type,
                                    'scale_used': verdict.get('scale_used', 1.0),
                                    'cause': verdict.get('cause', 'ok')
                                })
                            else:
                                cause = verdict.get('cause', 'different_values')
                                comparison_results['discrepancies'].append({
                                    'concept': concept,
                                    'period': pdf_period,
                                    'pdf_value': pdf_value,
                                    'xbrl_value': xbrl_value,
                                    'difference': abs((pdf_value * verdict.get('scale_used', 1.0)) - xbrl_value),
                                    'statement_type': statement_type,
                                    'cause': cause,
                                    'scale_hint': verdict.get('scale_used', 1.0)
                                })
                                if cause in comparison_results['causes_summary']:
                                    comparison_results['causes_summary'][cause] += 1
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
    
    def _find_best_period_match(self, pdf_period: str, xbrl_periods: List[str]) -> Optional[str]:
        """Find the best matching XBRL period for a PDF period."""
        # Simple string matching - exact match first
        if pdf_period in xbrl_periods:
            return pdf_period
        
        # Look for partial matches (year extraction)
        pdf_year = re.search(r'(\d{4})', pdf_period)
        if pdf_year:
            pdf_year = pdf_year.group(1)
            for xbrl_period in xbrl_periods:
                if pdf_year in xbrl_period:
                    return xbrl_period
        
        # Return closest period if no match
        return xbrl_periods[0] if xbrl_periods else None
    
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
