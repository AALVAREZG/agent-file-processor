"""
Detailed comparison of pdfplumber vs tabula extraction results.
Shows side-by-side what each library extracts.
"""
import pdfplumber
import tabula
from pathlib import Path
import pandas as pd


def compare_extractors(pdf_path: Path):
    """Compare pdfplumber and tabula extractions in detail."""
    print(f"\n{'='*100}")
    print(f"DETAILED EXTRACTION COMPARISON: {pdf_path.name}")
    print(f"{'='*100}\n")

    # PDFPLUMBER
    print("="*100)
    print("PDFPLUMBER EXTRACTION (current approach)")
    print("="*100)

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        tables_pdf = page.extract_tables()

        print(f"Tables found: {len(tables_pdf)}")

        for table_idx, table in enumerate(tables_pdf):
            print(f"\n--- Table {table_idx + 1} ({len(table)} rows) ---")
            for row_idx, row in enumerate(table[:10]):  # Show first 10 rows
                print(f"Row {row_idx}:")
                for col_idx, cell in enumerate(row[:4]):  # First 4 columns
                    cell_str = str(cell) if cell else "[NULL]"
                    # Show newlines explicitly
                    newline_char = '\n'
                    if newline_char in cell_str:
                        nl_count = cell_str.count(newline_char)
                        print(f"  Col{col_idx}: MERGED [{nl_count} newlines]")
                        for line_idx, line in enumerate(cell_str.split(newline_char)[:3]):
                            print(f"    {line_idx}: {line[:50]}")
                    else:
                        print(f"  Col{col_idx}: {cell_str[:60]}")

    # TABULA
    print(f"\n{'='*100}")
    print("TABULA EXTRACTION (Java-based alternative)")
    print("="*100)

    try:
        dfs = tabula.read_pdf(str(pdf_path), pages='1', multiple_tables=True, silent=True)

        print(f"Tables found: {len(dfs)}")

        for table_idx, df in enumerate(dfs):
            print(f"\n--- Table {table_idx + 1} ({len(df)} rows) ---")
            print(df.head(10).to_string())

    except Exception as e:
        print(f"ERROR: {e}")

    # COMPARISON
    print(f"\n{'='*100}")
    print("KEY DIFFERENCES")
    print("="*100)

    if tables_pdf and dfs:
        pdf_rows = sum(len(t) for t in tables_pdf)
        tabula_rows = sum(len(df) for df in dfs)

        print(f"\nTotal rows:")
        print(f"  pdfplumber: {pdf_rows}")
        print(f"  tabula:     {tabula_rows}")

        if tabula_rows > pdf_rows:
            print(f"\n  -> Tabula found {tabula_rows - pdf_rows} MORE rows")
            print(f"     This suggests pdfplumber may be merging cells")
        elif pdf_rows > tabula_rows:
            print(f"\n  -> pdfplumber found {pdf_rows - tabula_rows} MORE rows")
            print(f"     This suggests tabula may be missing data")

        # Check merged cells in pdfplumber
        merged_count = 0
        for table in tables_pdf:
            for row in table:
                for cell in row:
                    if cell and isinstance(cell, str) and '\n' in cell:
                        merged_count += 1

        print(f"\nMerged cells in pdfplumber: {merged_count}")
        print(f"  -> These need splitting logic to process correctly")

        print(f"\n{'='*100}")
        print("RECOMMENDATION")
        print("="*100)

        if merged_count > 5:
            print("\nHigh number of merged cells detected!")
            print("Options:")
            print("  1. Keep pdfplumber + current splitting logic (already works)")
            print("  2. Use tabula extraction (may have better separation)")
            print("  3. Use ENSEMBLE: extract with both, compare results, use consensus")
            print("\nEnsemble approach would:")
            print("  - Validate extraction by comparing both")
            print("  - Use tabula when pdfplumber merges too much")
            print("  - Flag discrepancies for manual review")


def main():
    pdf_files = sorted(Path(".").glob("*.PDF"))

    if not pdf_files:
        print("No PDFs found!")
        return

    # Test all PDFs
    for pdf_path in pdf_files[:2]:  # First 2 PDFs
        compare_extractors(pdf_path)
        print("\n" * 2)


if __name__ == "__main__":
    main()
