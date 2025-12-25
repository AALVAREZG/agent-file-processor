"""Debug script to trace row parsing for 026_2025_0015_00000506_CML.PDF"""
import pdfplumber
import re

pdf_path = "026_2025_0015_00000506_CML.PDF"

print(f"Analyzing PDF: {pdf_path}")
print("=" * 100)

with pdfplumber.open(pdf_path) as pdf:
    num_pages = len(pdf.pages)
    print(f"\nTotal pages: {num_pages}")

    # Process all pages except last (which has totals)
    pages_to_process = num_pages - 1

    for page_idx in range(pages_to_process):
        page = pdf.pages[page_idx]
        print(f"\n{'='*100}")
        print(f"PAGE {page_idx + 1}")
        print(f"{'='*100}")

        tables = page.extract_tables()
        print(f"\nFound {len(tables)} table(s) on this page")

        for table_idx, table in enumerate(tables):
            if not table or len(table) < 2:
                continue

            print(f"\n--- Table {table_idx + 1} ---")
            print(f"Number of rows: {len(table)}")

            # Look for problematic rows containing multiple multas records
            for row_idx, row in enumerate(table):
                if not row or len(row) < 8:
                    continue

                # Check if this is a header row
                if any(header in str(row[0]).upper() for header in ['CONCEPTO', 'CLAVE']):
                    continue

                concepto_text = str(row[0]) if row[0] else ""

                # Check if this row has "MULTAS" in it
                if 'MULTAS' in concepto_text.upper():
                    print(f"\n{'*'*100}")
                    print(f"ROW {row_idx}: MULTAS RECORD FOUND")
                    print(f"{'*'*100}")

                    # Print each cell
                    for cell_idx, cell in enumerate(row):
                        cell_str = str(cell) if cell else "(None)"
                        print(f"  Cell[{cell_idx}]: {cell_str[:200]}")

                    # Check for newlines in cells
                    print(f"\n  Analysis:")
                    has_newlines = '\n' in concepto_text
                    print(f"    Concepto has newlines: {has_newlines}")
                    if '\n' in concepto_text:
                        lines = concepto_text.split('\n')
                        print(f"    Concepto lines ({len(lines)}):")
                        for i, line in enumerate(lines):
                            print(f"      [{i}]: {line}")

                    # Check clave_recaudacion (cell 2) and clave_contabilidad (cell 1)
                    clave_recaud = str(row[2]) if len(row) > 2 and row[2] else "(None)"
                    clave_cont = str(row[1]) if len(row) > 1 and row[1] else "(None)"

                    print(f"\n    Clave Recaudación (cell[2]): {clave_recaud}")
                    if '\n' in clave_recaud:
                        print(f"      Has newlines! Lines:")
                        for i, line in enumerate(clave_recaud.split('\n')):
                            print(f"        [{i}]: {line}")

                    print(f"\n    Clave Contabilidad (cell[1]): {clave_cont}")
                    if '\n' in clave_cont:
                        print(f"      Has newlines! Lines:")
                        for i, line in enumerate(clave_cont.split('\n')):
                            print(f"        [{i}]: {line}")

                    # Check if this looks like a merged row (has TOTAL EJERCICIO)
                    is_merged_row = (
                        '\n' in concepto_text and
                        'TOTAL' in concepto_text.upper() and
                        'EJERCICIO' in concepto_text.upper() and
                        len(concepto_text.split('\n')) > 2
                    )
                    print(f"\n    Is merged row (with TOTAL EJERCICIO): {is_merged_row}")

                    # Check if this looks like TWO records merged
                    # Count how many clave_contabilidad patterns exist
                    if clave_cont != "(None)":
                        clave_patterns = re.findall(r'\d{4}/[A-Z]/\d+', clave_cont)
                        print(f"\n    Number of clave_contabilidad patterns found: {len(clave_patterns)}")
                        if len(clave_patterns) > 1:
                            print(f"      >>> PROBLEM: Multiple clave_contabilidad in one row!")
                            print(f"      Patterns: {clave_patterns}")

                    if clave_recaud != "(None)":
                        recaud_patterns = re.findall(r'\d{3}/\d{4}/\d{2}/\d{3}/\d{3}', clave_recaud)
                        print(f"\n    Number of clave_recaudacion patterns found: {len(recaud_patterns)}")
                        if len(recaud_patterns) > 1:
                            print(f"      >>> PROBLEM: Multiple clave_recaudacion in one row!")
                            print(f"      Patterns: {recaud_patterns}")

                    print()

print("\n" + "="*100)
print("ANALYSIS COMPLETE")
print("="*100)
