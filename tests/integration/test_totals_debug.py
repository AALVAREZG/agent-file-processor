"""Debug script for totals extraction."""
import pdfplumber
import re
from decimal import Decimal

def parse_amount(amount_str):
    """Parse amount string to Decimal."""
    if not amount_str:
        return Decimal('0')
    # Remove thousands separator and replace comma with decimal point
    cleaned = str(amount_str).replace('.', '').replace(',', '.')
    try:
        return Decimal(cleaned)
    except:
        return Decimal('0')

pdf_path = "026_2025_0016_00000623_CML.PDF"

with pdfplumber.open(pdf_path) as pdf:
    num_pages = len(pdf.pages)
    page = pdf.pages[num_pages - 1]  # Last page

    print(f"Extracting from last page (page {num_pages})")
    print("=" * 80)

    tables = page.extract_tables()

    print(f"\nFound {len(tables)} tables\n")

    # Process each table
    for table_idx, table in enumerate(tables):
        print(f"\n{'='*80}")
        print(f"TABLE {table_idx + 1}")
        print(f"{'='*80}")

        if not table or len(table) == 0:
            print("  (empty table)")
            continue

        # Check if this is the totals table
        table_text = ' '.join([' '.join([str(cell) for cell in row if cell]) for row in table])

        print(f"\nTable text (combined): {table_text[:200]}...")
        print(f"\nIs this the TOTAL table? {'VOLUNTARIA' in table_text and 'EJECUTIVA' in table_text}")

        # Process rows for ALL tables to see what's there
        print(f"\nNumber of rows: {len(table)}")
        for row_idx, row in enumerate(table):
            print(f"\nRow {row_idx}: {row}")
            if row:
                row_text = ' '.join([str(cell) for cell in row if cell])
                print(f"  Combined text: '{row_text}'")

        # Now check if this is totals table and try extraction
        if 'VOLUNTARIA' in table_text and 'EJECUTIVA' in table_text and 'LIQUIDO' in table_text.upper():
            print("\n>>> THIS IS THE TOTALS TABLE - EXTRACTING! <<<\n")

            # Process each row
            for row_idx, row in enumerate(table):
                if not row:
                    continue

                row_text = ' '.join([str(cell) for cell in row if cell])
                print(f"\nExtracting from row {row_idx}: '{row_text}'")

                # Try to extract values
                if 'VOLUNTARIA' in row_text and 'DIPUTACI' not in row_text.upper():
                    match = re.search(r'VOLUNTARIA\s+([\d.,]+)', row_text)
                    print(f"  Checking VOLUNTARIA... DIPUTACI in text? {'DIPUTACI' in row_text.upper()}")
                    if match:
                        print(f"  >>> FOUND VOLUNTARIA: {match.group(1)} -> {parse_amount(match.group(1))}")
                    else:
                        print(f"  No match for VOLUNTARIA pattern")

                if 'EJECUTIVA' in row_text and 'DIPUTACI' not in row_text.upper() and 'TASA' not in row_text.upper():
                    match = re.search(r'EJECUTIVA\s+([\d.,]+)', row_text)
                    print(f"  Checking EJECUTIVA... DIPUTACI? {'DIPUTACI' in row_text.upper()}, TASA? {'TASA' in row_text.upper()}")
                    if match:
                        print(f"  >>> FOUND EJECUTIVA: {match.group(1)} -> {parse_amount(match.group(1))}")
                    else:
                        print(f"  No match for EJECUTIVA pattern")

                if 'RECARGO' in row_text and 'DIPUTACI' not in row_text.upper():
                    match = re.search(r'RECARGO\s+([\d.,]+)', row_text)
                    print(f"  Checking RECARGO... DIPUTACI in text? {'DIPUTACI' in row_text.upper()}")
                    if match:
                        print(f"  >>> FOUND RECARGO: {match.group(1)} -> {parse_amount(match.group(1))}")
                    else:
                        print(f"  No match for RECARGO pattern")

                if re.search(r'L[IÍ]QUIDO', row_text, re.IGNORECASE):
                    match = re.search(r'L[IÍ]QUIDO\s+([\d.,]+)', row_text, re.IGNORECASE)
                    if match:
                        print(f"  >>> FOUND LÍQUIDO: {match.group(1)} -> {parse_amount(match.group(1))}")
                    else:
                        print(f"  No match for LÍQUIDO pattern")
