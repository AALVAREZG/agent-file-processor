"""Test script to analyze year 2025 extraction from 026_2025_0008_00000150_CML.PDF"""
from src.extractors.pdf_extractor import extract_liquidation_pdf

pdf_path = "026_2025_0008_00000150_CML.PDF"

print(f"Analyzing: {pdf_path}")
print("=" * 80)

doc = extract_liquidation_pdf(pdf_path)

# Filter records for year 2025
records_2025 = [r for r in doc.tribute_records if r.ejercicio == 2025]

print(f"\nTotal records in document: {doc.total_records}")
print(f"Records for year 2025: {len(records_2025)}")
print(f"\nExpected: 11 records")
print(f"Found: {len(records_2025)} records")
print(f"Missing: {11 - len(records_2025)} record(s)")

print(f"\n{'='*80}")
print("RECORDS FOR YEAR 2025:")
print(f"{'='*80}\n")

# Expected records based on screenshot
expected_claves = [
    "2025/V/0000103",
    "2025/G/0000240",
    "2025/V/0000087",
    "2025/V/0000283",
    "2025/G/0001717",
    "2025/G/0002109",
    "2025/M/0000422",
    "2025/M/0000421",
    "2025/M/0000569",
    "2025/M/0000570",
    "2025/M/0000731"
]

print(f"{'#':<4} {'Concepto':<30} {'Clave Contabilidad':<20} {'Clave Recaudación':<25} {'Líquido':>15}")
print("-" * 100)

for idx, record in enumerate(records_2025, 1):
    print(f"{idx:<4} {record.concepto:<30} {record.clave_contabilidad:<20} {record.clave_recaudacion:<25} {record.liquido:>15,.2f}")

print("\n" + "=" * 80)
print("CHECKING WHICH EXPECTED RECORD IS MISSING:")
print("=" * 80)

found_claves = [r.clave_contabilidad for r in records_2025]

for expected_clave in expected_claves:
    if expected_clave in found_claves:
        print(f"[OK] {expected_clave} - FOUND")
    else:
        print(f"[MISSING!] {expected_clave} - NOT FOUND")

print("\n" + "=" * 80)
print("ANALYZING PDF TABLE STRUCTURE:")
print("=" * 80)

# Now let's manually check what's in the PDF tables
import pdfplumber

with pdfplumber.open(pdf_path) as pdf:
    print(f"\nTotal pages in PDF: {len(pdf.pages)}")

    # Check pages to process (all except last)
    pages_to_process = len(pdf.pages) - 1
    print(f"Pages to process (excluding last): {pages_to_process}")

    print(f"\nSearching for year 2025 records across all pages...")

    for page_idx in range(pages_to_process):
        page = pdf.pages[page_idx]
        tables = page.extract_tables()

        print(f"\n--- Page {page_idx + 1}: Found {len(tables)} table(s) ---")

        for table_idx, table in enumerate(tables):
            if not table or len(table) < 2:
                continue

            # Look for rows that might contain 2025 data
            rows_with_2025 = []
            for row_idx, row in enumerate(table):
                if not row:
                    continue

                # Check if any cell contains 2025
                row_text = ' '.join([str(cell) if cell else '' for cell in row])
                if '2025' in row_text:
                    rows_with_2025.append((row_idx, row))

            if rows_with_2025:
                print(f"\n  Table {table_idx + 1}: Found {len(rows_with_2025)} row(s) with '2025':")
                for row_idx, row in rows_with_2025:
                    print(f"    Row {row_idx}: {row[:5]}...")  # Show first 5 cells
