"""
Focused experiment: Tuning the LINES strategy parameters
to reduce merged cells while keeping the same basic approach.
"""
import pdfplumber
from pathlib import Path
from typing import List, Dict, Any

def analyze_table(table: List[List]) -> Dict[str, Any]:
    """Quick analysis of table structure."""
    if not table:
        return {"rows": 0, "newlines": 0, "merged": 0}

    newlines = 0
    merged = 0

    for row in table:
        for cell in row:
            if cell and isinstance(cell, str) and '\n' in cell:
                newlines += 1
                if cell.count('\n') > 1:
                    merged += 1

    return {
        "rows": len(table),
        "newlines": newlines,
        "merged": merged
    }

def show_first_data_row(table: List[List]) -> str:
    """Show the first non-header row for comparison."""
    if not table or len(table) < 2:
        return "No data"

    # Skip header row(s), find first data row
    for row in table[1:]:
        if row and len(row) >= 3:
            col0 = str(row[0])[:40] if row[0] else "[NULL]"
            col1 = str(row[1])[:30] if row[1] else "[NULL]"
            col2 = str(row[2])[:30] if row[2] else "[NULL]"

            # Show newline count
            nl0 = row[0].count('\n') if row[0] and isinstance(row[0], str) else 0
            nl1 = row[1].count('\n') if row[1] and isinstance(row[1], str) else 0
            nl2 = row[2].count('\n') if row[2] and isinstance(row[2], str) else 0

            return f"{col0} [{nl0}NL] | {col1} [{nl1}NL] | {col2} [{nl2}NL]"

    return "No data row found"

# Different LINES strategy configurations to test
LINES_CONFIGS = {
    "default": {
        "name": "Default (current)",
        "settings": {}
    },
    "strict": {
        "name": "Lines Strict (stricter line detection)",
        "settings": {
            "vertical_strategy": "lines_strict",
            "horizontal_strategy": "lines_strict",
        }
    },
    "tight_snap": {
        "name": "Tight snap (snap_tolerance=1)",
        "settings": {
            "snap_tolerance": 1,
            "snap_x_tolerance": 1,
            "snap_y_tolerance": 1,
        }
    },
    "no_join": {
        "name": "No joining (join_tolerance=0)",
        "settings": {
            "join_tolerance": 0,
            "join_x_tolerance": 0,
            "join_y_tolerance": 0,
        }
    },
    "tight_all": {
        "name": "Tight snap + No join",
        "settings": {
            "snap_tolerance": 1,
            "snap_x_tolerance": 1,
            "snap_y_tolerance": 1,
            "join_tolerance": 0,
            "join_x_tolerance": 0,
            "join_y_tolerance": 0,
        }
    },
    "longer_edges": {
        "name": "Longer edge minimum (edge_min_length=10)",
        "settings": {
            "edge_min_length": 10,
        }
    },
    "tight_intersection": {
        "name": "Tight intersections (intersection_tolerance=1)",
        "settings": {
            "intersection_tolerance": 1,
            "intersection_x_tolerance": 1,
            "intersection_y_tolerance": 1,
        }
    },
    "explicit_lines": {
        "name": "Explicit strategy (uses explicit coordinates)",
        "settings": {
            "vertical_strategy": "explicit",
            "horizontal_strategy": "explicit",
        }
    },
}

def test_lines_configs(pdf_path: Path, page_num: int = 0):
    """Test different lines strategy configurations."""
    print(f"\n{'='*100}")
    print(f"LINES STRATEGY TUNING EXPERIMENT")
    print(f"PDF: {pdf_path.name}, Page: {page_num + 1}")
    print(f"{'='*100}\n")

    results = []

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num]

        for config_key, config_info in LINES_CONFIGS.items():
            print(f"\n{config_info['name']}")
            print(f"Settings: {config_info['settings']}")
            print("-" * 100)

            try:
                if config_info['settings']:
                    tables = page.extract_tables(table_settings=config_info['settings'])
                else:
                    tables = page.extract_tables()

                if not tables:
                    print("  No tables detected")
                    results.append({
                        "name": config_info['name'],
                        "error": "No tables"
                    })
                    continue

                # Analyze first table (main data table)
                analysis = analyze_table(tables[0])
                first_row = show_first_data_row(tables[0])

                print(f"  Tables: {len(tables)}")
                print(f"  Rows: {analysis['rows']}")
                print(f"  Cells with newlines: {analysis['newlines']}")
                print(f"  Merged cells (>1 NL): {analysis['merged']}")
                print(f"  First data row: {first_row}")

                results.append({
                    "name": config_info['name'],
                    "tables": len(tables),
                    **analysis
                })

            except Exception as e:
                print(f"  ERROR: {e}")
                results.append({
                    "name": config_info['name'],
                    "error": str(e)
                })

    # Summary comparison
    print(f"\n{'='*100}")
    print("COMPARISON SUMMARY")
    print(f"{'='*100}\n")
    print(f"{'Configuration':<45} {'Tables':>8} {'Rows':>8} {'NewLines':>10} {'Merged':>8}")
    print("-" * 100)

    for result in results:
        if "error" in result:
            print(f"{result['name']:<45} {'ERROR':<8} {'-':>8} {'-':>10} {'-':>8}")
        else:
            print(f"{result['name']:<45} {result['tables']:>8} {result['rows']:>8} "
                  f"{result['newlines']:>10} {result['merged']:>8}")

    # Find best configuration
    print(f"\n{'='*100}")
    print("RECOMMENDATIONS")
    print(f"{'='*100}\n")

    valid_results = [r for r in results if "error" not in r]
    if valid_results:
        # Sort by: fewer merged cells, then fewer newlines, then more rows
        best = min(valid_results, key=lambda x: (x['merged'], x['newlines'], -x['rows']))

        print(f"BEST CONFIGURATION: {best['name']}")
        print(f"  - Rows: {best['rows']}")
        print(f"  - Cells with newlines: {best['newlines']}")
        print(f"  - Merged cells: {best['merged']}")
        print(f"\nThis configuration has the FEWEST merged cells!")

        # Show improvement over default
        default_result = next((r for r in valid_results if "Default" in r['name']), None)
        if default_result and best != default_result:
            print(f"\nIMPROVEMENT over default:")
            print(f"  Merged cells: {default_result['merged']} -> {best['merged']} "
                  f"({((default_result['merged'] - best['merged']) / max(default_result['merged'], 1) * 100):.1f}% reduction)")
            print(f"  Newlines: {default_result['newlines']} -> {best['newlines']} "
                  f"({((default_result['newlines'] - best['newlines']) / max(default_result['newlines'], 1) * 100):.1f}% reduction)")

def main():
    pdf_files = sorted(Path(".").glob("*.PDF"))

    if not pdf_files:
        print("No PDFs found!")
        return

    print("Testing all PDFs on page 1...\n")

    for pdf_path in pdf_files:
        test_lines_configs(pdf_path, page_num=0)
        print("\n" + "="*100)
        print()

if __name__ == "__main__":
    main()
