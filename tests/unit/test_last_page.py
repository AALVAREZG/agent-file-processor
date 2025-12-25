"""Test script to check the last page."""
import pdfplumber

pdf_path = "026_2025_0016_00000623_CML.PDF"

with pdfplumber.open(pdf_path) as pdf:
    num_pages = len(pdf.pages)
    print(f"Total pages: {num_pages}")
    print(f"Checking LAST page (page {num_pages})")
    print(f"=" * 80)

    # Check last page
    page = pdf.pages[num_pages - 1]
    text = page.extract_text()

    print("LAST PAGE TEXT:")
    print("=" * 80)
    print(text)
    print("=" * 80)

    # Try tables
    tables = page.extract_tables()
    print(f"\nFound {len(tables)} tables on this page")

    for i, table in enumerate(tables):
        print(f"\n--- Table {i+1} ---")
        if table:
            for row in table[:15]:  # Show first 15 rows
                print(row)
