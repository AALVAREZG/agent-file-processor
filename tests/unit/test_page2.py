"""Test script to debug page 2 extraction."""
import pdfplumber

pdf_path = "026_2025_0016_00000623_CML.PDF"

with pdfplumber.open(pdf_path) as pdf:
    num_pages = len(pdf.pages)
    print(f"Total pages: {num_pages}")
    print(f"Trying to extract from page {num_pages - 2} (second-to-last)")
    print(f"=" * 80)

    # Try second-to-last page
    page = pdf.pages[num_pages - 2]
    text = page.extract_text()

    print("PAGE TEXT:")
    print("=" * 80)
    print(text)
    print("=" * 80)

    # Try tables
    tables = page.extract_tables()
    print(f"\nFound {len(tables)} tables on this page")

    for i, table in enumerate(tables):
        print(f"\n--- Table {i+1} ---")
        if table:
            for row in table[:10]:  # Show first 10 rows
                print(row)
