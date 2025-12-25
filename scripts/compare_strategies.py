"""
Direct comparison: Current (lines) vs Recommended (text) strategy
"""
import pdfplumber
from pathlib import Path

def show_comparison(pdf_path: Path, page_num: int = 0):
    print(f"\n{'='*80}")
    print(f"COMPARISON: Current vs Recommended Strategy")
    print(f"PDF: {pdf_path.name}, Page: {page_num + 1}")
    print(f"{'='*80}\n")

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num]

        # CURRENT: Default (lines strategy)
        print("CURRENT STRATEGY (lines - default):")
        print("-" * 80)
        tables_lines = page.extract_tables()

        if tables_lines:
            table = tables_lines[0]
            print(f"Tables found: {len(tables_lines)}")
            print(f"Rows in first table: {len(table)}")
            print(f"\nFirst 5 rows (showing first 3 columns):\n")

            for i, row in enumerate(table[:5]):
                print(f"Row {i}:")
                for j, cell in enumerate(row[:3]):
                    cell_str = str(cell) if cell else "[NULL]"
                    # Show newlines explicitly
                    if '\n' in cell_str:
                        lines = cell_str.split('\n')
                        print(f"  Col{j}: MERGED CELL with {len(lines)} values:")
                        for idx, line in enumerate(lines[:3]):  # Show first 3
                            print(f"    [{idx}] {line[:50]}")
                        if len(lines) > 3:
                            print(f"    ... and {len(lines)-3} more")
                    else:
                        print(f"  Col{j}: {cell_str[:50]}")
                print()

        print("\n" + "="*80)
        print("RECOMMENDED STRATEGY (text-based):")
        print("-" * 80)

        # RECOMMENDED: Text-based strategy
        tables_text = page.extract_tables(table_settings={
            "vertical_strategy": "text",
            "horizontal_strategy": "text"
        })

        if tables_text:
            table = tables_text[0]
            print(f"Tables found: {len(tables_text)}")
            print(f"Rows in first table: {len(table)}")
            print(f"\nFirst 10 rows (showing first 3 columns):\n")

            for i, row in enumerate(table[:10]):
                print(f"Row {i}:")
                for j, cell in enumerate(row[:3]):
                    cell_str = str(cell) if cell else "[NULL]"
                    # Check for newlines (should be none!)
                    if '\n' in cell_str:
                        print(f"  Col{j}: STILL HAS NEWLINES: {cell_str[:50]}")
                    else:
                        print(f"  Col{j}: {cell_str[:50]}")
                print()

        print("\n" + "="*80)
        print("KEY DIFFERENCES:")
        print("="*80)
        print(f"Current (lines):     {len(tables_lines[0]) if tables_lines else 0} rows (merged cells)")
        print(f"Recommended (text):  {len(tables_text[0]) if tables_text else 0} rows (separated cells)")
        print(f"\nWith text strategy:")
        print("  ✓ Each row = one value per cell")
        print("  ✓ No newlines to split")
        print("  ✓ Simpler parsing logic needed")
        print("  ✓ Can remove 150+ lines of splitting code!")

def main():
    pdf_files = sorted(Path(".").glob("*.PDF"))

    if not pdf_files:
        print("No PDFs found!")
        return

    print("Testing first PDF...")
    show_comparison(pdf_files[0], page_num=0)

if __name__ == "__main__":
    main()
