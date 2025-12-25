"""
ACCURACY COMPARISON REPORT

Compares pdfplumber vs tabula extraction accuracy by:
1. Extracting with both methods
2. Parsing the actual data values
3. Comparing record counts and totals
4. Identifying which is more accurate
"""
import pdfplumber
import tabula
import pandas as pd
from pathlib import Path
from decimal import Decimal
import re
from typing import List, Dict, Tuple, Any


class AccuracyAnalyzer:
    """Analyzes extraction accuracy for both methods."""

    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path

    def parse_amount(self, value: Any) -> Decimal:
        """Parse amount from string (European format)."""
        if value is None or value == '' or pd.isna(value):
            return Decimal('0')

        value_str = str(value).strip().replace(' ', '')

        if not value_str or value_str == '-':
            return Decimal('0')

        # Handle European format
        if ',' in value_str and '.' in value_str:
            comma_pos = value_str.rfind(',')
            dot_pos = value_str.rfind('.')
            if comma_pos > dot_pos:
                value_str = value_str.replace('.', '').replace(',', '.')
            else:
                value_str = value_str.replace(',', '')
        elif ',' in value_str:
            value_str = value_str.replace('.', '').replace(',', '.')

        try:
            return Decimal(value_str)
        except:
            return Decimal('0')

    def extract_with_pdfplumber(self) -> Dict[str, Any]:
        """Extract and parse records with pdfplumber."""
        records = []

        with pdfplumber.open(self.pdf_path) as pdf:
            page = pdf.pages[0]
            tables = page.extract_tables()

            for table in tables:
                for row in table:
                    if not row or len(row) < 10:
                        continue

                    # Skip headers and totals
                    concepto = str(row[0]) if row[0] else ""
                    if 'CONCEPTO' in concepto.upper() or 'TOTAL' in concepto.upper():
                        continue

                    # Parse amounts from row
                    try:
                        # Check if this is a merged row (has newlines)
                        has_newlines = '\n' in concepto

                        record = {
                            'concepto': concepto.replace('\n', ' ').strip(),
                            'clave_contabilidad': str(row[1]) if row[1] else "",
                            'clave_recaudacion': str(row[2]) if row[2] else "",
                            'voluntaria': self.parse_amount(row[3]),
                            'ejecutiva': self.parse_amount(row[4]),
                            'recargo': self.parse_amount(row[5]),
                            'liquido': self.parse_amount(row[9]) if len(row) > 9 else Decimal('0'),
                            'has_newlines': has_newlines
                        }

                        # Only add if has actual data
                        if record['clave_contabilidad'] or record['voluntaria'] > 0:
                            records.append(record)

                    except Exception as e:
                        continue

        # Calculate totals
        total_voluntaria = sum(r['voluntaria'] for r in records)
        total_ejecutiva = sum(r['ejecutiva'] for r in records)
        total_liquido = sum(r['liquido'] for r in records)

        return {
            'method': 'pdfplumber',
            'records': records,
            'count': len(records),
            'total_voluntaria': total_voluntaria,
            'total_ejecutiva': total_ejecutiva,
            'total_liquido': total_liquido,
            'merged_cells': sum(1 for r in records if r['has_newlines'])
        }

    def extract_with_tabula(self) -> Dict[str, Any]:
        """Extract and parse records with tabula."""
        records = []

        try:
            dfs = tabula.read_pdf(str(self.pdf_path), pages='1', multiple_tables=True, silent=True)

            for df in dfs:
                # Process each row
                for idx, row in df.iterrows():
                    # Skip if first column is empty or NaN
                    if pd.isna(row.iloc[0]) or row.iloc[0] == '':
                        continue

                    concepto = str(row.iloc[0]).strip()

                    # Skip headers and totals
                    if 'CONCEPTO' in concepto.upper() or 'TOTAL' in concepto.upper():
                        continue

                    # Skip rows that are just wrapped text (all other columns empty)
                    if len(row) >= 3:
                        # Check if this looks like a data row (has clave or amounts)
                        has_data = False
                        for col_idx in range(1, min(len(row), 10)):
                            if not pd.isna(row.iloc[col_idx]) and str(row.iloc[col_idx]).strip():
                                has_data = True
                                break

                        if not has_data:
                            # This is just wrapped text from previous row
                            continue

                    # Parse the row
                    try:
                        # Try to extract amounts from the row
                        # Tabula might have different column structure
                        record = {
                            'concepto': concepto,
                            'clave_contabilidad': str(row.iloc[1]) if len(row) > 1 and not pd.isna(row.iloc[1]) else "",
                            'clave_recaudacion': "",
                            'voluntaria': Decimal('0'),
                            'ejecutiva': Decimal('0'),
                            'recargo': Decimal('0'),
                            'liquido': Decimal('0'),
                            'has_newlines': False
                        }

                        # Try to find amounts in the row (they might be in different positions)
                        for col_idx in range(2, len(row)):
                            val = row.iloc[col_idx]
                            if pd.isna(val):
                                continue

                            val_str = str(val).strip()

                            # Check if this looks like a clave_recaudacion (026/...)
                            if '026/' in val_str and not record['clave_recaudacion']:
                                record['clave_recaudacion'] = val_str
                            else:
                                # Try to parse as amount
                                amount = self.parse_amount(val)
                                if amount > 0:
                                    # Heuristic: assign to appropriate field
                                    if record['voluntaria'] == 0:
                                        record['voluntaria'] = amount
                                    elif record['ejecutiva'] == 0:
                                        record['ejecutiva'] = amount
                                    elif record['recargo'] == 0:
                                        record['recargo'] = amount
                                    else:
                                        record['liquido'] = amount

                        # Only add if has meaningful data
                        if record['clave_contabilidad'] or record['voluntaria'] > 0:
                            records.append(record)

                    except Exception as e:
                        continue

        except Exception as e:
            pass

        # Calculate totals
        total_voluntaria = sum(r['voluntaria'] for r in records)
        total_ejecutiva = sum(r['ejecutiva'] for r in records)
        total_liquido = sum(r['liquido'] for r in records)

        return {
            'method': 'tabula',
            'records': records,
            'count': len(records),
            'total_voluntaria': total_voluntaria,
            'total_ejecutiva': total_ejecutiva,
            'total_liquido': total_liquido,
            'merged_cells': 0  # Tabula doesn't merge cells
        }

    def compare_results(self, result1: Dict, result2: Dict) -> Dict[str, Any]:
        """Compare two extraction results."""
        comparison = {
            'pdf': self.pdf_path.name,
            'methods': [result1['method'], result2['method']],
            'record_counts': [result1['count'], result2['count']],
            'merged_cells': [result1['merged_cells'], result2['merged_cells']],
            'totals': {
                result1['method']: {
                    'voluntaria': result1['total_voluntaria'],
                    'ejecutiva': result1['total_ejecutiva'],
                    'liquido': result1['total_liquido']
                },
                result2['method']: {
                    'voluntaria': result2['total_voluntaria'],
                    'ejecutiva': result2['total_ejecutiva'],
                    'liquido': result2['total_liquido']
                }
            },
            'discrepancies': {}
        }

        # Calculate discrepancies
        for field in ['voluntaria', 'ejecutiva', 'liquido']:
            val1 = result1[f'total_{field}']
            val2 = result2[f'total_{field}']
            diff = abs(val1 - val2)

            comparison['discrepancies'][field] = {
                'difference': diff,
                'percentage': (diff / max(val1, val2) * 100) if max(val1, val2) > 0 else 0
            }

        return comparison


def generate_accuracy_report(pdf_files: List[Path]):
    """Generate comprehensive accuracy report for all PDFs."""
    print("="*100)
    print("EXTRACTION ACCURACY COMPARISON REPORT")
    print("="*100)
    print()
    print(f"Analyzing {len(pdf_files)} PDF files...")
    print()

    all_comparisons = []

    for pdf_path in pdf_files:
        print(f"\n{'='*100}")
        print(f"PDF: {pdf_path.name}")
        print(f"{'='*100}\n")

        analyzer = AccuracyAnalyzer(pdf_path)

        # Extract with both methods
        print("Extracting with pdfplumber...")
        result_pdf = analyzer.extract_with_pdfplumber()
        print(f"  Found {result_pdf['count']} records ({result_pdf['merged_cells']} with merged cells)")

        print("Extracting with tabula...")
        result_tab = analyzer.extract_with_tabula()
        print(f"  Found {result_tab['count']} records")

        # Compare
        comparison = analyzer.compare_results(result_pdf, result_tab)
        all_comparisons.append(comparison)

        # Display comparison
        print(f"\n{'-'*100}")
        print("COMPARISON")
        print(f"{'-'*100}")

        print(f"\nRecord counts:")
        print(f"  pdfplumber: {result_pdf['count']} records")
        print(f"  tabula:     {result_tab['count']} records")
        diff = abs(result_pdf['count'] - result_tab['count'])
        if diff > 0:
            print(f"  Difference: {diff} records")

        print(f"\nTotal VOLUNTARIA:")
        print(f"  pdfplumber: {result_pdf['total_voluntaria']:,.2f} EUR")
        print(f"  tabula:     {result_tab['total_voluntaria']:,.2f} EUR")
        print(f"  Difference: {comparison['discrepancies']['voluntaria']['difference']:,.2f} EUR "
              f"({comparison['discrepancies']['voluntaria']['percentage']:.1f}%)")

        print(f"\nTotal EJECUTIVA:")
        print(f"  pdfplumber: {result_pdf['total_ejecutiva']:,.2f} EUR")
        print(f"  tabula:     {result_tab['total_ejecutiva']:,.2f} EUR")
        print(f"  Difference: {comparison['discrepancies']['ejecutiva']['difference']:,.2f} EUR "
              f"({comparison['discrepancies']['ejecutiva']['percentage']:.1f}%)")

        print(f"\nTotal LIQUIDO:")
        print(f"  pdfplumber: {result_pdf['total_liquido']:,.2f} EUR")
        print(f"  tabula:     {result_tab['total_liquido']:,.2f} EUR")
        print(f"  Difference: {comparison['discrepancies']['liquido']['difference']:,.2f} EUR "
              f"({comparison['discrepancies']['liquido']['percentage']:.1f}%)")

        # Show sample records
        print(f"\n{'-'*100}")
        print("SAMPLE RECORDS (first 3)")
        print(f"{'-'*100}")

        print("\npdfplumber:")
        for i, rec in enumerate(result_pdf['records'][:3]):
            merged_flag = " [MERGED]" if rec['has_newlines'] else ""
            print(f"  {i+1}. {rec['concepto'][:40]}{merged_flag}")
            print(f"     Clave: {rec['clave_contabilidad']}, Voluntaria: {rec['voluntaria']:.2f}")

        print("\ntabula:")
        for i, rec in enumerate(result_tab['records'][:3]):
            print(f"  {i+1}. {rec['concepto'][:40]}")
            print(f"     Clave: {rec['clave_contabilidad']}, Voluntaria: {rec['voluntaria']:.2f}")

    # Overall summary
    print(f"\n\n{'='*100}")
    print("OVERALL SUMMARY")
    print(f"{'='*100}\n")

    avg_disc_vol = sum(c['discrepancies']['voluntaria']['percentage'] for c in all_comparisons) / len(all_comparisons)
    avg_disc_eje = sum(c['discrepancies']['ejecutiva']['percentage'] for c in all_comparisons) / len(all_comparisons)
    avg_disc_liq = sum(c['discrepancies']['liquido']['percentage'] for c in all_comparisons) / len(all_comparisons)

    print(f"Average discrepancies across {len(all_comparisons)} PDFs:")
    print(f"  VOLUNTARIA: {avg_disc_vol:.1f}%")
    print(f"  EJECUTIVA:  {avg_disc_eje:.1f}%")
    print(f"  LIQUIDO:    {avg_disc_liq:.1f}%")

    # Recommendation
    print(f"\n{'='*100}")
    print("RECOMMENDATION")
    print(f"{'='*100}\n")

    total_merged = sum(all_comparisons[i]['merged_cells'][0] for i in range(len(all_comparisons)))

    if avg_disc_vol < 5 and avg_disc_eje < 5 and avg_disc_liq < 5:
        print("RESULT: Both methods show GOOD AGREEMENT (<5% discrepancy)")
        print("\nRecommended approach:")
        if total_merged > 10:
            print("  1. PRIMARY: Keep pdfplumber (you already have working splitting logic)")
            print("  2. VALIDATION: Add tabula as validation check")
            print("  3. ALERT: If discrepancy >10%, flag for manual review")
        else:
            print("  1. Either method is acceptable")
            print("  2. pdfplumber recommended (already implemented)")
    else:
        print("RESULT: Methods show SIGNIFICANT DISAGREEMENT (>5% discrepancy)")
        print("\nRecommended approach:")
        print("  1. ENSEMBLE: Extract with both methods")
        print("  2. VALIDATE: Compare results, flag if >10% difference")
        print("  3. MANUAL REVIEW: Required for high-discrepancy cases")
        print("  4. Consider manual verification of a sample set to determine ground truth")

    print(f"\nMerged cells analysis:")
    print(f"  Total merged cells (pdfplumber): {total_merged}")
    print(f"  Average per PDF: {total_merged / len(all_comparisons):.1f}")

    if total_merged > 20:
        print("\n  -> HIGH number of merged cells detected")
        print("  -> Your splitting logic is handling a real problem")
        print("  -> Consider tabula as alternative (may have cleaner extraction)")


def main():
    pdf_files = sorted(Path(".").glob("*.PDF"))

    if not pdf_files:
        print("No PDFs found!")
        return

    generate_accuracy_report(pdf_files)


if __name__ == "__main__":
    main()
